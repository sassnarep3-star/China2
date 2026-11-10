/* Small, dependency-free enhancements. The site is fully usable without JS. */
(function () {
  "use strict";

  function addTableLabels() {
    // Give the master ladder cells a data-label so the mobile card layout can
    // label each value. Header text is read from the table's own <thead>.
    document.querySelectorAll("table.ladder").forEach(function (table) {
      var heads = table.querySelectorAll("thead th");
      var labels = Array.prototype.map.call(heads, function (th) {
        return th.textContent.trim();
      });
      table.querySelectorAll("tbody tr").forEach(function (row) {
        Array.prototype.forEach.call(row.children, function (cell, i) {
          if (!cell.hasAttribute("data-label") && labels[i]) {
            cell.setAttribute("data-label", labels[i]);
          }
        });
      });
    });
  }

  function jumpLinks() {
    // Deep links should not hide the target under the sticky header.
    document.documentElement.style.scrollPaddingTop = "1rem";
  }

  function markCurrentYear() {
    var el = document.getElementById("verified-on");
    if (el) { el.setAttribute("data-checked", "true"); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  function init() {
    addTableLabels();
    jumpLinks();
    markCurrentYear();
  }
})();
