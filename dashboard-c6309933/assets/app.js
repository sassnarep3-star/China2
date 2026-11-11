/* dashboard-c6309933/assets/app.js - progressive enhancement only.
 * Every page is complete and readable with JavaScript disabled.
 * No third-party requests. No network calls. */
(function () {
  'use strict';

  // 1. Mark the nav link for the page we are actually on, even if the build
  //    did not set aria-current (e.g. when served from a different path).
  var here = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav.jump a').forEach(function (a) {
    if (a.getAttribute('href') === here) {
      a.setAttribute('aria-current', 'page');
    }
  });

  // 2. On wide screens, let a horizontally scrollable table shadow its edges so
  //    the reader can see there is more to the right.
  document.querySelectorAll('.tscroll').forEach(function (w) {
    function paint() {
      var over = w.scrollWidth - w.clientWidth > 2;
      var atEnd = w.scrollLeft + w.clientWidth >= w.scrollWidth - 2;
      w.style.boxShadow = (over && !atEnd)
        ? 'var(--shadow), inset -14px 0 12px -12px rgba(16,24,40,.30)'
        : 'var(--shadow)';
    }
    w.addEventListener('scroll', paint, { passive: true });
    window.addEventListener('resize', paint);
    paint();
  });

  // 3. Expand every <details> on the page at once, for printing and for readers
  //    who do not want to click through thirteen methods.
  var anyDetails = document.querySelector('details');
  if (anyDetails && window.matchMedia) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Expand all sections';
    btn.className = 'small';
    btn.style.cssText = 'margin:4px 0 12px;padding:6px 12px;border:1px solid var(--line);'
      + 'border-radius:6px;background:var(--panel);cursor:pointer;font-size:.85rem';
    var open = false;
    btn.addEventListener('click', function () {
      open = !open;
      document.querySelectorAll('details').forEach(function (d) { d.open = open; });
      btn.textContent = open ? 'Collapse all sections' : 'Expand all sections';
    });
    anyDetails.parentNode.insertBefore(btn, anyDetails);
  }

  // 4. Print with everything open.
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('details').forEach(function (d) { d.open = true; });
  });
})();
