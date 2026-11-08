// Progressive enhancement only: the site is fully usable without JavaScript.
// On costs.html, lets the reader show one amount across all method tables.
(function () {
  "use strict";
  var sel = document.getElementById("amount-filter");
  if (!sel) return;
  var tables = document.querySelectorAll(".table-scroll table");
  function apply() {
    var v = sel.value;
    tables.forEach(function (table) {
      var body = table.tBodies[0];
      if (!body) return;
      Array.prototype.forEach.call(body.rows, function (row) {
        var first = row.cells[0];
        if (!first) return;
        var amount = first.textContent.replace(/[^0-9]/g, "");
        row.hidden = v !== "all" && amount !== v;
      });
    });
    var note = document.getElementById("filter-note");
    if (note) {
      note.textContent = v === "all"
        ? "Showing all 40 increments per method."
        : "Showing $" + Number(v).toLocaleString("en-US") + " rows only.";
    }
  }
  sel.addEventListener("change", apply);
})();
