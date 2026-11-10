// Acceptance audit: simple table filter (no dependencies).
document.addEventListener("DOMContentLoaded", function () {
  var input = document.getElementById("filter");
  if (!input) return;
  input.addEventListener("input", function () {
    var q = input.value.toLowerCase();
    document.querySelectorAll("table.stack tbody tr").forEach(function (tr) {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
    });
  });
});
