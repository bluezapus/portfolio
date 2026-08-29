// Public site: mobile nav toggle. No dependencies.
(function () {
  var toggles = document.querySelectorAll(".nav-toggle");
  toggles.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var menu = btn.parentElement.querySelector(".nav-links") ||
                 document.querySelector(".nav-links");
      if (menu) {
        var open = menu.classList.toggle("open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      }
    });
  });
})();
