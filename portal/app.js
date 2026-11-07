(function () {
  function initTableFilter() {
    var searchInput = document.getElementById("table-search");
    var catSelect = document.getElementById("category-filter");
    var eligSelect = document.getElementById("elig-filter");
    var table = document.querySelector("table[data-filterable='true']");
    var countEl = document.getElementById("row-count");
    if (!table) return;

    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var total = rows.length;

    function applyFilter() {
      var q = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var cat = catSelect ? catSelect.value : "ALL";
      var elig = eligSelect ? eligSelect.value : "ALL";
      var shown = 0;

      rows.forEach(function (tr) {
        var textMatch = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var catMatch = cat === "ALL" || tr.getAttribute("data-category") === cat;
        var eligMatch = elig === "ALL" || tr.getAttribute("data-elig") === elig;
        var visible = textMatch && catMatch && eligMatch;
        tr.style.display = visible ? "" : "none";
        if (visible) shown += 1;
      });

      if (countEl) {
        countEl.textContent = "Showing " + shown + " of " + total + " verified rows";
      }
    }

    if (searchInput) searchInput.addEventListener("input", applyFilter);
    if (catSelect) catSelect.addEventListener("change", applyFilter);
    if (eligSelect) eligSelect.addEventListener("change", applyFilter);
    applyFilter();
  }

  function initCsvExport() {
    var btn = document.getElementById("export-csv");
    var table = document.querySelector("table[data-filterable='true']") || document.querySelector("table");
    if (!btn || !table) return;

    btn.addEventListener("click", function () {
      var lines = [];
      var allRows = table.querySelectorAll("tr");
      Array.prototype.forEach.call(allRows, function (tr) {
        if (tr.style.display === "none") return;
        var cells = tr.querySelectorAll("th, td");
        var vals = Array.prototype.map.call(cells, function (cell) {
          var clean = cell.textContent.replace(/\s+/g, " ").trim();
          var a = cell.querySelector("a.src-link");
          if (a && clean.indexOf("http") === -1) {
            clean = clean + " (" + a.getAttribute("href") + ")";
          }
          return '"' + clean.replace(/"/g, '""') + '"';
        });
        lines.push(vals.join(","));
      });
      var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
      var url = URL.createObjectURL(blob);
      var link = document.createElement("a");
      link.href = url;
      link.download = (document.title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "table") + ".csv";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initTableFilter();
      initCsvExport();
    });
  } else {
    initTableFilter();
    initCsvExport();
  }
})();
