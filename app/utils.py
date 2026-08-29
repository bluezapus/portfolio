"""
Reusable helpers: slug generation, simple safe Markdown, secure upload,
and a lightweight in-memory login rate limiter.
No external dependencies. Pure stdlib + Flask.
"""
import os
import re
import secrets
import hashlib
import mimetypes
from pathlib import Path
from flask import current_app

# --------------------------------------------------------------------------
# Slug
# --------------------------------------------------------------------------
def slugify(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)  # drop punctuation
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "item"


# --------------------------------------------------------------------------
# Simple, SAFE Markdown -> HTML
# We intentionally avoid pulling in a full Markdown lib. This supports the
# subset used in write-ups: headings, bold, italic, code, lists, links,
# blockquotes, horizontal rules, paragraphs. Output is escaped first, then
# a tiny whitelist of tags is allowed. Relative/anchor/https links only.
# --------------------------------------------------------------------------
from html import escape

_ALLOWED_LINK = re.compile(r"^(https?:|/|#)")


def _sanitize_url(url):
    url = url.strip()
    # Only allow safe schemes; block javascript:, data:, etc.
    if _ALLOWED_LINK.match(url):
        return url
    return "#"


def render_markdown(text):
    if not text:
        return ""
    lines = text.splitlines()
    out = []
    in_code = False
    list_buf = []
    para_buf = []

    def flush_para():
        if para_buf:
            out.append("<p>" + _inline(" ".join(para_buf)) + "</p>")
            para_buf.clear()

    def flush_list():
        if list_buf:
            out.append("<ul>")
            for item in list_buf:
                out.append("<li>" + _inline(item) + "</li>")
            out.append("</ul>")
            list_buf.clear()

    for raw in lines:
        line = raw.rstrip()

        # Fenced code block
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                flush_para(); flush_list()
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(escape(line) + "\n")
            continue

        # Blank line
        if not line.strip():
            flush_para(); flush_list()
            continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            flush_para(); flush_list()
            out.append("<hr>")
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para(); flush_list()
            level = len(m.group(1))
            out.append(f"<h{level}>" + _inline(m.group(2)) + f"</h{level}>")
            continue

        # Blockquote
        m = re.match(r"^>\s?(.*)$", line)
        if m:
            flush_para(); flush_list()
            out.append("<blockquote>" + _inline(m.group(1)) + "</blockquote>")
            continue

        # Unordered list
        m = re.match(r"^[-*+]\s+(.*)$", line)
        if m:
            flush_para()
            list_buf.append(m.group(1))
            continue

        # Ordered list
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            # treat as unordered for simplicity
            flush_para()
            list_buf.append(m.group(1))
            continue

        # Default: paragraph text
        flush_list()
        para_buf.append(line)

    flush_para(); flush_list()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def _inline(text):
    # Escape first — this is what neutralizes XSS in user content.
    text = escape(text)
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic *text*
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", text)
    # Inline code `code`
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Links [label](url) — url re-sanitized after unescape of entities.
    def _link(m):
        label = m.group(1)
        url = m.group(2)
        # entities were introduced by escape(); decode the few we need.
        url = url.replace("&amp;", "&")
        safe = _sanitize_url(url)
        return f'<a href="{escape(safe)}" rel="noopener noreferrer">{label}</a>'
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
    return text


# --------------------------------------------------------------------------
# Secure upload
# --------------------------------------------------------------------------
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"}
# PDF is handled by a dedicated helper (different MIME/size rules).
PDF_EXT = ".pdf"
# Mapping of allowed extensions to acceptable MIME types.
ALLOWED_MIME = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".svg": {"image/svg+xml"},  # note: SVG is served with CSP + sanitized below
    ".ico": {"image/x-icon", "image/vnd.microsoft.icon"},
    ".bmp": {"image/bmp"},
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def secure_upload(file_storage, subdir=""):
    """
    Validate and save an uploaded FileStorage. Returns the stored relative
    path (from uploads root) or raises ValueError with a human message.
    Security: extension whitelist, MIME sniff via magic bytes, size limit,
    random filename, no executable content.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")

    max_bytes = int(current_app.config.get("MAX_UPLOAD_MB", 5)) * 1024 * 1024

    # Size check (content_length may be missing; also check stream below).
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > max_bytes:
        raise ValueError(f"File too large. Max {max_bytes // 1024 // 1024} MB.")
    if size == 0:
        raise ValueError("Empty file.")

    # Extension whitelist
    name = file_storage.filename
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("File type not allowed.")

    # MIME check via magic bytes (not trusting client Content-Type).
    head = file_storage.read(2048)
    file_storage.stream.seek(0)
    mime = _sniff_mime(head, ext)
    if mime not in ALLOWED_MIME.get(ext, set()):
        raise ValueError("File content does not match its type.")

    # SVG: sanitize (strip scripts) even though it passed MIME.
    if ext == ".svg":
        content = file_storage.read().decode("utf-8", "replace")
        file_storage.stream.seek(0)
        content = _sanitize_svg(content)
        if content is None:
            raise ValueError("SVG contains disallowed content.")
        data = content.encode("utf-8")
    else:
        data = file_storage.read()

    # Random filename — never use the user-supplied name.
    rand = secrets.token_hex(12)
    stored_name = f"{rand}{ext}"
    rel_dir = os.path.join("uploads", subdir) if subdir else "uploads"
    abs_dir = os.path.join(current_app.root_path, "..", rel_dir)
    Path(abs_dir).mkdir(parents=True, exist_ok=True)
    abs_path = os.path.join(abs_dir, stored_name)
    with open(abs_path, "wb") as f:
        f.write(data)

    return f"{subdir}/{stored_name}" if subdir else stored_name


def _sniff_mime(head, ext):
    # PNG
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    # JPEG
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    # GIF
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    # WEBP
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    # BMP
    if head[:2] == b"BM":
        return "image/bmp"
    # ICO
    if head[:4] == b"\x00\x00\x01\x00":
        return "image/x-icon"
    # SVG (XML)
    if head.lstrip()[:5].lower() in (b"<?xml", b"<svg "):
        return "image/svg+xml"
    return "application/octet-stream"


def _sanitize_svg(svg_text):
    """Strip scripts/event handlers. Return cleaned text, or None if unsafe."""
    lowered = svg_text.lower()
    if any(k in lowered for k in ("<script", "onload=", "onerror=", "javascript:")):
        return None
    # Remove <script> blocks defensively (shouldn't be present if above passed).
    svg_text = re.sub(r"<script.*?</script>", "", svg_text, flags=re.DOTALL | re.IGNORECASE)
    svg_text = re.sub(r"on\w+\s*=", "", svg_text, flags=re.IGNORECASE)
    return svg_text


def secure_pdf_upload(file_storage, subdir="books"):
    """
    Validate and save an uploaded PDF. Security:
    - extension MUST be .pdf
    - magic bytes MUST begin with b"%PDF"
    - size cap (100 MB) — PDFs legitimately are larger than images
    - random filename (never the user-supplied name)
    Returns the stored relative path from uploads root.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")

    name = file_storage.filename
    ext = os.path.splitext(name)[1].lower()
    if ext != PDF_EXT:
        raise ValueError("Only PDF files are allowed.")

    # Size cap for PDFs: 100 MB (independent of image cap).
    pdf_cap = 100 * 1024 * 1024
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > pdf_cap:
        raise ValueError(f"PDF too large. Max {pdf_cap // 1024 // 1024} MB.")
    if size == 0:
        raise ValueError("Empty file.")

    # Verify PDF magic bytes (not just the extension).
    head = file_storage.read(5)
    file_storage.stream.seek(0)
    if head[:4] != b"%PDF":
        raise ValueError("File is not a valid PDF.")

    rand = secrets.token_hex(12)
    stored_name = f"{rand}.pdf"
    rel_dir = os.path.join("uploads", subdir)
    abs_dir = os.path.join(current_app.root_path, "..", rel_dir)
    Path(abs_dir).mkdir(parents=True, exist_ok=True)
    abs_path = os.path.join(abs_dir, stored_name)
    with open(abs_path, "wb") as f:
        f.write(file_storage.read())

    return f"{subdir}/{stored_name}"


# --------------------------------------------------------------------------
# Login rate limiter (simple, in-memory, per-IP)
# --------------------------------------------------------------------------
_RATE = {}
_RATE_WINDOW = 60  # seconds
_RATE_MAX = 5      # max attempts per window


def register_failed_login(key):
    now = int(__import__("time").time())
    bucket = _RATE.setdefault(key, [])
    # purge old
    bucket[:] = [t for t in bucket if now - t < _RATE_WINDOW]
    bucket.append(now)


def login_allowed(key):
    now = int(__import__("time").time())
    bucket = _RATE.get(key)
    if not bucket:
        return True
    bucket[:] = [t for t in bucket if now - t < _RATE_WINDOW]
    return len(bucket) < _RATE_MAX


def clear_login(key):
    _RATE.pop(key, None)
