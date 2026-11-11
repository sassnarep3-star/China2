// guide-fb2f2562: progressive enhancements only. Every page works without JavaScript.
(function () {
  'use strict';

  // Costs page: show one method's table.
  var sel = document.getElementById('msel');
  if (sel) {
    var apply = function () {
      var v = sel.value;
      var secs = document.querySelectorAll('section.ctab');
      for (var i = 0; i < secs.length; i++) {
        secs[i].hidden = !!v && secs[i].id !== v;
      }
    };
    sel.addEventListener('change', function () {
      apply();
      if (sel.value && history.replaceState) { history.replaceState(null, '', '#' + sel.value); }
    });
    if (location.hash && location.hash.indexOf('#c-') === 0) {
      sel.value = location.hash.slice(1);
      apply();
    }
  }

  // Repo review: filter the line table.
  var f = document.getElementById('rfilter');
  var t = document.getElementById('rtable');
  if (f && t) {
    f.addEventListener('input', function () {
      var q = f.value.toLowerCase();
      var rows = t.tBodies[0].rows;
      for (var i = 0; i < rows.length; i++) {
        rows[i].hidden = q && rows[i].textContent.toLowerCase().indexOf(q) === -1;
      }
    });
  }

  // Penalty page: personal FX gain calculator (26 USC 988(e)(2) USD 200 threshold).
  var cnyIn = document.getElementById('fx-cny');
  var basisIn = document.getElementById('fx-basis');
  var nowIn = document.getElementById('fx-now');
  var out = document.getElementById('fx-out');
  var note = document.getElementById('fx-note');
  if (cnyIn && basisIn && nowIn && out) {
    var num = function (el) { return parseFloat(String(el.value).replace(/[, ]/g, '')); };
    var calc = function () {
      var c = num(cnyIn), b = num(basisIn), n = num(nowIn);
      if (!(c > 0) || !(b > 0) || !(n > 0)) { out.textContent = 'enter your acquisition rate'; note.textContent = ''; return; }
      var gain = c / n - c / b;
      out.textContent = (gain < 0 ? '−$' : '$') + Math.abs(gain).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      note.textContent = gain > 200
        ? 'Above $200: not excluded by §988(e)(2). Ask a preparer how to report it.'
        : (gain >= 0 ? 'At or below $200 for this conversion: not recognised under §988(e)(2).' : 'A loss on a personal conversion; ask a preparer about its treatment.');
    };
    [cnyIn, basisIn, nowIn].forEach(function (el) { el.addEventListener('input', calc); });
    calc();
  }
})();
