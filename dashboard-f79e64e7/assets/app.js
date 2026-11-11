(function () {
  var only = document.getElementById('only50');
  if (only) only.addEventListener('change', function () {
    document.body.classList.toggle('only50', only.checked);
  });
  var jump = document.getElementById('jump');
  if (jump) jump.addEventListener('change', function () {
    var el = document.getElementById(jump.value);
    if (!el) return;
    el.open = true;
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  if (location.hash.indexOf('#cost-') === 0) {
    var target = document.getElementById(location.hash.slice(1));
    if (target) target.open = true;
  }
})();
