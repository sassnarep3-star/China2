/* final-f6327e23 — tiny progressive-enhancement script. No dependencies, no network. */
(function () {
  "use strict";

  /* ---- method category filters ---- */
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip[data-filter]"));
  var methods = Array.prototype.slice.call(document.querySelectorAll(".method[data-cat]"));
  if (chips.length && methods.length) {
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.getAttribute("data-filter");
        chips.forEach(function (c) { c.classList.toggle("on", c === chip); });
        methods.forEach(function (m) {
          var cat = m.getAttribute("data-cat");
          var show = f === "all" || cat === f ||
            (f === "other" && ["unverified", "flagged", "does-not-achieve-goal"].indexOf(cat) !== -1);
          m.classList.toggle("hidden", !show);
        });
      });
    });
  }

  /* ---- rank-table filter on the overview: reuse chips if present ---- */
  var rankRows = Array.prototype.slice.call(document.querySelectorAll("#rank-table tbody tr"));
  if (rankRows.length && !methods.length) {
    var bar = document.createElement("div");
    bar.className = "filters";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Filter by status");
    var defs = [["all", "All"], ["lawful", "Lawful"], ["lawful-capped", "Capped"],
                ["lawful-conditional", "Conditional"], ["unlawful", "Unlawful"],
                ["unverified", "Unverified"], ["flagged", "Flagged"],
                ["does-not-achieve-goal", "No goal"]];
    var table = document.getElementById("rank-table");
    defs.forEach(function (d, i) {
      var b = document.createElement("button");
      b.className = "chip" + (i === 0 ? " on" : "");
      b.textContent = d[1];
      b.setAttribute("data-filter", d[0]);
      b.addEventListener("click", function () {
        Array.prototype.forEach.call(bar.querySelectorAll(".chip"), function (c) {
          c.classList.toggle("on", c === b);
        });
        rankRows.forEach(function (tr) {
          tr.classList.toggle("hidden", d[0] !== "all" && tr.getAttribute("data-cat") !== d[0]);
        });
      });
      bar.appendChild(b);
    });
    if (table && table.parentNode) table.parentNode.insertBefore(bar, table);
  }
})();
