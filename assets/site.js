/* Progressive enhancement only. Every table is fully readable with JavaScript disabled. */
(function () {
  'use strict';

  function norm(s) { return (s || '').toLowerCase().replace(/[$,]/g, '').replace(/\s+/g, ' ').trim(); }

  /* 1. Text filter for any table marked data-filterable */
  document.querySelectorAll('table[data-filterable]').forEach(function (table) {
    var id = table.id;
    var input = document.querySelector('input[data-filter-for="' + id + '"]');
    if (!input) return;
    var counter = document.querySelector('[data-count-for="' + id + '"]');
    var rows = Array.prototype.slice.call(table.tBodies[0].rows);
    function apply() {
      var q = norm(input.value).trim();
      var shown = 0;
      rows.forEach(function (r) {
        var hit = !q || norm(r.textContent).indexOf(q) !== -1;
        r.hidden = !hit;
        if (hit) shown++;
      });
      if (counter) counter.textContent = shown + ' of ' + rows.length + ' rows';
    }
    input.addEventListener('input', apply);
    apply();
  });

  /* 2. Category / status select filters */
  document.querySelectorAll('select[data-filter-table]').forEach(function (sel) {
    var table = document.getElementById(sel.getAttribute('data-filter-table'));
    if (!table) return;
    var attr = sel.getAttribute('data-filter-attr');
    sel.addEventListener('change', function () {
      var v = sel.value;
      Array.prototype.forEach.call(table.tBodies[0].rows, function (r) {
        r.hidden = !!v && r.getAttribute(attr) !== v;
      });
    });
  });

  /* 3. Amount jump: highlight the matching row in the 41-row cost table */
  var jump = document.getElementById('amount-jump');
  if (jump) {
    jump.addEventListener('change', function () {
      var id = 'tier-' + jump.value;
      var row = document.getElementById(id);
      if (!row) {
        var target = jump.getAttribute('data-target');
        if (target && jump.value) {
          var out0 = document.getElementById('jump-out');
          if (out0) out0.textContent = 'Opening the full table at $' + Number(jump.value).toLocaleString('en-US') + '…';
          window.location.href = target + '#' + id;
        }
        return;
      }
      Array.prototype.forEach.call(document.querySelectorAll('tr.hl'), function (r) { r.classList.remove('hl'); });
      row.classList.add('hl');
      row.scrollIntoView({ block: 'center', behavior: 'smooth' });
      var out = document.getElementById('jump-out');
      if (out) {
        var cells = row.querySelectorAll('td');
        var txt = [];
        cells.forEach(function (c) { txt.push(c.textContent.trim()); });
        out.textContent = txt.join(' | ');
      }
    });
  }

  /* 4. Optional all-in calculator. Nothing is prefilled: the user enters their own quote. */
  var calc = document.getElementById('calc');
  if (calc) {
    var A = document.getElementById('calc-amount');
    var spread = document.getElementById('calc-spread');
    var fixed = document.getElementById('calc-fixed');
    var outEl = document.getElementById('calc-out');
    function num(el) { var v = parseFloat(el.value); return isFinite(v) ? v : null; }
    function run() {
      var a = num(A), s = num(spread), f = num(fixed);
      if (a === null || (s === null && f === null)) {
        outEl.innerHTML = '<span class="muted">Enter an amount and at least one quote component to see a total. No value is assumed for you.</span>';
        return;
      }
      var spreadCost = (s === null) ? 0 : a * (s / 100);
      var fixedCost = (f === null) ? 0 : f;
      var total = spreadCost + fixedCost;
      var pct = a ? (total / a * 100) : 0;
      var fmt = function (n) { return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
      outEl.innerHTML = '<strong>$' + fmt(total) + '</strong> total commercial cost' +
        (a ? ' &middot; ' + pct.toFixed(3) + '% of the amount' : '') +
        ' &middot; net received <strong>$' + fmt(a - total) + '</strong>' +
        '<br><span class="small muted">Spread $' + fmt(spreadCost) + ' + fixed fees $' + fmt(fixedCost) +
        '. Statutory tax is not included here; see the tables above.</span>';
    }
    [A, spread, fixed].forEach(function (el) { el.addEventListener('input', run); });
    run();
  }

  /* 5. Print buttons */
  document.querySelectorAll('[data-print]').forEach(function (b) {
    b.addEventListener('click', function () { window.print(); });
  });
})();
