"use strict";

(function () {
  const table = document.getElementById("cost-table");
  if (!table) return;
  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const method = document.getElementById("method-filter");
  const status = document.getElementById("status-filter");
  const amount = document.getElementById("amount-filter");
  const search = document.getElementById("cost-search");
  const blankOnly = document.getElementById("blank-only");
  const reset = document.getElementById("reset-filters");
  const count = document.getElementById("visible-count");

  function apply() {
    const methodValue = method ? method.value : "";
    const statusValue = status ? status.value : "";
    const amountValue = amount ? amount.value : "";
    const needle = search ? search.value.trim().toLowerCase() : "";
    const requireBlank = blankOnly ? blankOnly.checked : false;
    let visible = 0;
    rows.forEach(function (row) {
      const dataMethod = row.getAttribute("data-method") || "";
      const dataStatus = row.getAttribute("data-status") || "";
      const dataAmount = row.getAttribute("data-amount") || "";
      const dataBlank = row.getAttribute("data-has-blank") || "";
      const text = (row.textContent || "").toLowerCase();
      const show = (!methodValue || dataMethod === methodValue)
        && (!statusValue || dataStatus === statusValue)
        && (!amountValue || dataAmount === amountValue)
        && (!requireBlank || dataBlank === "yes")
        && (!needle || text.indexOf(needle) !== -1);
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (count) count.textContent = String(visible);
  }

  [method, status, amount, search, blankOnly].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", apply);
    el.addEventListener("change", apply);
  });

  if (reset) {
    reset.addEventListener("click", function () {
      if (method) method.value = "";
      if (status) status.value = "";
      if (amount) amount.value = "";
      if (search) search.value = "";
      if (blankOnly) blankOnly.checked = false;
      apply();
    });
  }

  apply();
})();
