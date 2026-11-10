/* landed-cost-b03f272a: optional helpers. Every page is complete without JavaScript. */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function money(x) {
    var neg = x < 0, v = Math.abs(x);
    return (neg ? '-$' : '$') + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function readModel() {
    var el = document.getElementById('model');
    if (!el) { return null; }
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  /* Route filter buttons (routes page). */
  $all('.filters[data-target]').forEach(function (bar) {
    var table = document.getElementById(bar.getAttribute('data-target'));
    if (!table) { return; }
    bar.addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-group]');
      if (!btn) { return; }
      var g = btn.getAttribute('data-group');
      $all('button', bar).forEach(function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      $all('tbody tr', table).forEach(function (tr) {
        tr.hidden = !(g === 'all' || tr.getAttribute('data-group') === g);
      });
    });
  });

  /* Highlight the row for a chosen amount in every $10,000-step table on the page. */
  var pick = document.getElementById('pick-amount');
  if (pick) {
    var mark = function () {
      var v = String(pick.value);
      $all('tr[data-tier]').forEach(function (tr) {
        tr.classList.toggle('hit', tr.getAttribute('data-tier') === v);
      });
    };
    pick.addEventListener('change', mark);
    mark();
  }

  /* Bank-cost calculator (costs page): same arithmetic as build.py, from the published inputs. */
  var m = readModel();
  var costForm = document.getElementById('cost-calc');
  if (m && costForm) {
    var runCost = function () {
      var usd = parseFloat($('#cc-usd', costForm).value);
      var out = $('#cc-out', costForm);
      if (!(usd > 0)) { out.textContent = 'Enter an amount in USD.'; return; }
      var principal = usd * m.sell;
      var pct = Math.min(Math.max(principal * m.boc.pct, m.boc.min), m.boc.max);
      var fee = Math.round(pct * 100) / 100 + m.boc.cable;
      var margin = usd * (m.sell - m.mid);
      var total = (fee + margin) / m.sell;
      out.textContent = 'Bank of China, one wire: about ' + money(total) + ' (' + (total / usd * 100).toFixed(3) +
        '% of the amount): fee ¥' + fee.toFixed(2) + ' plus exchange-rate margin ¥' + margin.toFixed(2) + '.';
    };
    costForm.addEventListener('input', runCost);
    runCost();
  }

  /* Exchange-gain calculator (fx-gain page). */
  var gainForm = document.getElementById('gain-calc');
  if (m && gainForm) {
    var runGain = function () {
      var usd = parseFloat($('#gc-usd', gainForm).value);
      var year = $('#gc-year', gainForm).value;
      var rate = parseFloat($('#gc-rate', gainForm).value);
      var out = $('#gc-out', gainForm);
      var r = m.years[year];
      if (!(usd > 0) || !r) { out.textContent = 'Enter an amount and pick a year.'; return; }
      var gain = usd * (1 - m.sell / r);
      if (gain <= 0) {
        out.textContent = 'Exchange loss of ' + money(-gain) + ': no U.S. tax on a loss; whether it is deductible is not confirmed.';
      } else if (gain <= m.exclusion) {
        out.textContent = 'Exchange gain of ' + money(gain) + ': not more than $' + m.exclusion + ', so not recognised if this is a personal transaction.';
      } else {
        out.textContent = 'Exchange gain of ' + money(gain) + '. Tax at ' + rate + '%: ' + money(gain * rate / 100) +
          ' (' + (gain * rate / usd).toFixed(2) + '% of the amount).';
      }
    };
    gainForm.addEventListener('input', runGain);
    runGain();
  }
}());
