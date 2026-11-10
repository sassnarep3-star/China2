// Filter helper: search box + status select filter table rows. No dependencies.
(function () {
  var q = document.getElementById("q");
  var st = document.getElementById("st");
  if (!q) return;
  function apply() {
    var needle = q.value.toLowerCase();
    var status = st ? st.value.toLowerCase() : "";
    document.querySelectorAll("table tbody tr").forEach(function (tr) {
      var text = tr.textContent.toLowerCase();
      var okText = !needle || text.indexOf(needle) !== -1;
      var okStatus = !status || text.indexOf(status) !== -1;
      tr.style.display = okText && okStatus ? "" : "none";
    });
  }
  q.addEventListener("input", apply);
  if (st) st.addEventListener("change", apply);
})();
