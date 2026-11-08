/* Progressive enhancement only. Every page is complete and printable without JS. */
(function () {
  "use strict";
  var jump = document.getElementById("tier-jump");
  if (jump) {
    jump.addEventListener("change", function () {
      var el = document.querySelector('details[data-tier="' + jump.value + '"]');
      if (!el) return;
      el.open = true;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
  var filter = document.getElementById("route-filter");
  if (filter) {
    filter.addEventListener("change", function () {
      var v = filter.value;
      var blocks = document.querySelectorAll("details.tier");
      Array.prototype.forEach.call(blocks, function (block) {
        var rows = block.querySelectorAll("tbody tr");
        Array.prototype.forEach.call(rows, function (row) {
          var idCell = row.querySelector(".sub");
          var id = idCell ? idCell.textContent.trim() : "";
          var lawful = !row.querySelector(":scope > td:last-child");
          var show = !v || v === id || (v === "lawful" && lawful) || (id === "");
          row.style.display = show ? "" : "none";
        });
      });
    });
  }
})();
