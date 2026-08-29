// Admin: mobile sidebar toggle. No dependencies.
(function () {
  var toggle = document.querySelector(".nav-toggle");
  if (!toggle) return;
  toggle.addEventListener("click", function () {
    var sidebar = document.querySelector(".admin-sidebar");
    if (sidebar) {
      var open = sidebar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
  });
})();
