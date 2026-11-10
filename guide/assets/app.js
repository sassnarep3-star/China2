/* Progressive enhancement only: everything on these pages is already in the
   HTML. With scripting off, the tables are complete and readable. */
(function () {
  "use strict";

  /* ---- method filter on methods.html ---- */
  var list = document.querySelector("[data-method-list]");
  if (list) {
    var input = document.querySelector("[data-method-search]");
    var select = document.querySelector("[data-method-status]");
    var count = document.querySelector("[data-method-count]");
    var articles = Array.prototype.slice.call(list.querySelectorAll(".method"));

    function apply() {
      var q = (input && input.value || "").toLowerCase().trim();
      var st = select && select.value || "all";
      var shown = 0;
      articles.forEach(function (a) {
        var text = a.textContent.toLowerCase();
        var okText = !q || text.indexOf(q) !== -1;
        var okStatus = st === "all" || a.classList.contains(st);
        var show = okText && okStatus;
        a.hidden = !show;
        if (show) { shown++; }
      });
      if (count) {
        count.textContent = shown + " of " + articles.length + " methods shown";
      }
      var groups = list.querySelectorAll("section[data-method-group]");
      Array.prototype.forEach.call(groups, function (g) {
        var any = g.querySelector(".method:not([hidden])");
        g.hidden = !any;
      });
    }
    if (input) { input.addEventListener("input", apply); }
    if (select) { select.addEventListener("change", apply); }
    apply();
  }

  /* ---- tier selector on costs.html: jump between the per-tier tables ---- */
  var tierSelect = document.querySelector("[data-tier-jump]");
  if (tierSelect) {
    tierSelect.addEventListener("change", function () {
      var target = document.getElementById("tier-" + tierSelect.value);
      if (target) { target.scrollIntoView({ behavior: "smooth", block: "start" }); }
    });
  }

  /* ---- sort a table by clicking its header (numeric-aware) ---- */
  Array.prototype.forEach.call(document.querySelectorAll("table[data-sortable]"), function (table) {
    var tbody = table.tBodies[0];
    if (!tbody) { return; }
    Array.prototype.forEach.call(table.tHead ? table.tHead.rows[0].cells : [], function (th, index) {
      if (th.dataset.nosort !== undefined) { return; }
      th.style.cursor = "pointer";
      th.title = "Sort by this column";
      var dir = 1;
      th.addEventListener("click", function () {
        var rows = Array.prototype.slice.call(tbody.rows);
        var num = rows.every(function (r) {
          var t = (r.cells[index] && r.cells[index].textContent || "").replace(/[^0-9.\-]/g, "");
          return t !== "" && !isNaN(parseFloat(t));
        });
        rows.sort(function (a, b) {
          var x = (a.cells[index] && a.cells[index].textContent || "").trim();
          var y = (b.cells[index] && b.cells[index].textContent || "").trim();
          if (num) { return (parseFloat(x.replace(/[^0-9.\-]/g, "")) - parseFloat(y.replace(/[^0-9.\-]/g, ""))) * dir; }
          return x.localeCompare(y) * dir;
        });
        dir = -dir;
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });
  });
})();
