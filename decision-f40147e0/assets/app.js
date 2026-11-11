/* Minimal, dependency-free filter. No data leaves the page. */
(function () {
  "use strict";
  function wire(input) {
    var target = document.querySelector(input.getAttribute("data-filter"));
    if (!target) return;
    var items = Array.prototype.slice.call(target.querySelectorAll("[data-filter-item]"));
    var empty = document.getElementById("no-results");
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      items.forEach(function (el) {
        var hit = !q || el.textContent.toLowerCase().indexOf(q) !== -1;
        el.hidden = !hit;
        if (hit) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    });
  }
  document.querySelectorAll("input[data-filter]").forEach(wire);
})();
