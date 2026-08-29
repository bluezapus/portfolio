// Public "Reading Room": click a book card -> open PDF in a modal reader.
// No dependencies. Accessible: ESC to close, focus trap, restores focus.
(function () {
  "use strict";
  var modal = document.getElementById("readerModal");
  if (!modal) return;
  var frame = document.getElementById("readerFrame");
  var titleEl = document.getElementById("readerTitle");
  var download = document.getElementById("readerDownload");
  var lastFocused = null;

  function openReader(card) {
    var pdf = card.getAttribute("data-pdf");
    if (!pdf) return;
    lastFocused = document.activeElement;
    titleEl.textContent = card.getAttribute("data-title") || "Book";
    var author = card.getAttribute("data-author");
    download.href = pdf;
    frame.src = pdf + "#toolbar=1&navpanes=0&view=FitH";
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    var closeBtn = modal.querySelector("[data-book-close]");
    if (closeBtn) closeBtn.focus();
  }

  function closeReader() {
    modal.hidden = true;
    document.body.style.overflow = "";
    frame.src = "about:blank";
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  document.addEventListener("click", function (e) {
    var card = e.target.closest("[data-book-open]");
    if (card && !e.target.closest("a[href]:not([href='#'])")) {
      // Only open when clicking the card or the Read button (not external links).
      e.preventDefault();
      openReader(card);
    }
    if (e.target.closest("[data-book-close]")) {
      closeReader();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) {
      closeReader();
    }
  });
})();
