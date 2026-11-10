(function () {
  "use strict";
  function openTarget() {
    var id = window.location.hash.slice(1);
    if (!id) { return; }
    var el = document.getElementById(id);
    if (el && el.tagName === "DETAILS") { el.open = true; el.scrollIntoView(); }
  }
  var pick = document.getElementById("pick");
  if (pick) {
    pick.addEventListener("change", function () {
      if (pick.value) { window.location.hash = pick.value; }
    });
  }
  var all = document.getElementById("openall");
  if (all) {
    all.addEventListener("click", function () {
      var list = document.querySelectorAll("details.method");
      var open = all.getAttribute("data-open") !== "1";
      for (var i = 0; i < list.length; i += 1) { list[i].open = open; }
      all.setAttribute("data-open", open ? "1" : "0");
      all.textContent = open ? "Close all" : "Open all";
    });
  }
  window.addEventListener("hashchange", openTarget);
  openTarget();
}());
