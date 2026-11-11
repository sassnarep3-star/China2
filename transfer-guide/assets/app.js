(function () {
  "use strict";

  function initCostFilter() {
    var table = document.getElementById("ladder-table");
    if (!table) return;
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var tierSel = document.getElementById("filter-tier");
    var methodSel = document.getElementById("filter-method");
    var statusSel = document.getElementById("filter-status");
    var searchInp = document.getElementById("filter-search");
    var resetBtn = document.getElementById("filter-reset");
    var countEl = document.getElementById("filter-count");

    function apply() {
      var tier = tierSel ? tierSel.value : "";
      var method = methodSel ? methodSel.value : "";
      var status = statusSel ? statusSel.value : "";
      var q = searchInp ? searchInp.value.trim().toLowerCase() : "";
      var shown = 0;

      for (var i = 0; i < rows.length; i++) {
        var tr = rows[i];
        var okTier = !tier || tr.getAttribute("data-tier") === tier;
        var okMethod = !method || tr.getAttribute("data-method") === method;
        var okStatus = !status || tr.getAttribute("data-status") === status;
        var okQuery = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var visible = okTier && okMethod && okStatus && okQuery;
        tr.style.display = visible ? "" : "none";
        if (visible) shown++;
      }
      if (countEl) {
        countEl.textContent = "Showing " + shown + " of " + rows.length + " verified rows ($10,000 to $400,000 USD across all 23 methods).";
      }
    }

    if (tierSel) tierSel.addEventListener("change", apply);
    if (methodSel) methodSel.addEventListener("change", apply);
    if (statusSel) statusSel.addEventListener("change", apply);
    if (searchInp) searchInp.addEventListener("input", apply);
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (tierSel) tierSel.value = "";
        if (methodSel) methodSel.value = "";
        if (statusSel) statusSel.value = "";
        if (searchInp) searchInp.value = "";
        apply();
      });
    }
    apply();
  }

  function initGenericSearch() {
    var inp = document.getElementById("page-search");
    var statusSel = document.getElementById("page-status");
    var resetBtn = document.getElementById("page-reset");
    var countEl = document.getElementById("page-count");
    if (!inp && !statusSel) return;

    var items = Array.prototype.slice.call(document.querySelectorAll("[data-filterable='1']"));
    if (!items.length) return;

    function apply() {
      var q = inp ? inp.value.trim().toLowerCase() : "";
      var st = statusSel ? statusSel.value : "";
      var shown = 0;
      for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var okSt = !st || el.getAttribute("data-status") === st || el.getAttribute("data-category") === st || el.getAttribute("data-severity") === st;
        var okQ = !q || el.textContent.toLowerCase().indexOf(q) !== -1;
        var vis = okSt && okQ;
        el.style.display = vis ? "" : "none";
        if (vis) shown++;
      }
      if (countEl) {
        countEl.textContent = "Showing " + shown + " of " + items.length + " entries.";
      }
    }

    if (inp) inp.addEventListener("input", apply);
    if (statusSel) statusSel.addEventListener("change", apply);
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (inp) inp.value = "";
        if (statusSel) statusSel.value = "";
        apply();
      });
    }
    apply();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initCostFilter();
      initGenericSearch();
    });
  } else {
    initCostFilter();
    initGenericSearch();
  }
})();
