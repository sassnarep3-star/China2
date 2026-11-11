/* Client-side filtering for the data tables. No network calls, no third-party code.
   The pages are complete and readable without this script. */
(function () {
  "use strict";

  function norm(s) {
    return (s || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function init() {
    var tables = document.querySelectorAll("table.data");
    if (!tables.length) return;

    tables.forEach(function (table) {
      var search = document.getElementById("tableSearch");
      var status = document.getElementById("statusFilter");
      var method = document.getElementById("methodFilter");
      if (!search && !status && !method) return;

      var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
      var counter = document.createElement("p");
      counter.className = "rowcount";
      counter.setAttribute("aria-live", "polite");
      table.parentNode.insertBefore(counter, table.parentNode.nextSibling);

      function apply() {
        var q = norm(search && search.value);
        var st = status ? status.value.toLowerCase() : "";
        var md = method ? method.value.toLowerCase() : "";
        var shown = 0;
        rows.forEach(function (row) {
          var text = norm(row.textContent).replace(/\u2014/g, " blank ");
          var ok = true;
          if (q && text.indexOf(q) === -1) ok = false;
          if (ok && st && text.indexOf(st) === -1) ok = false;
          if (ok && md) {
            var first = norm(row.querySelector("td") ? row.querySelector("td").textContent : "");
            if (first.indexOf(md) === -1 && text.indexOf(md) === -1) ok = false;
          }
          row.hidden = !ok;
          if (ok) shown++;
        });
        counter.textContent = shown + " of " + rows.length + " rows shown" +
          (shown === 0 ? " — nothing matches this filter." : "");
      }

      [search, status, method].forEach(function (el) {
        if (el) el.addEventListener("input", apply);
        if (el) el.addEventListener("change", apply);
      });
      apply();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
