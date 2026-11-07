(() => {
  const R = window.RESEARCH;
  if (!R) return;
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const source = (id) => R.sources.find(s => s.id === id);
  const link = (id, label) => { const ids = Array.isArray(id) ? id : [id]; const links = ids.map(key => { const s = source(key); return s ? `<a class="source-link" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(label || s.agency)} ↗</a>` : `<span class="unverified">Source missing — flagged</span>`; }); return links.join("<br>"); };
  const categories = [...new Set(R.options.map(x => x.category))];
  const sourcesBadge = document.querySelector('body[data-page="sources"] .review-pill');
  if (sourcesBadge) sourcesBadge.textContent = `${R.sources.length} official references`;

  const home = document.getElementById("home-options");
  if (home) {
    const chosen = ["bank-quota","bank-overquota","foreign-income","asset-transfer","third-party"].map(id => R.options.find(x => x.id === id));
    home.innerHTML = chosen.map(x => `<tr><td><b>${esc(x.method)}</b><small class="cell-sub">${esc(x.category)}</small></td><td>${esc(x.eligibility)}</td><td>${esc(x.pros)}<small class="cell-sub"><b>Watch for:</b> ${esc(x.cons)}</small></td><td>${link(x.source)}</td></tr>`).join("");
  }

  const optionsRoot = document.getElementById("option-groups");
  if (optionsRoot) {
    const select = document.getElementById("option-filter");
    categories.forEach(c => { const o = document.createElement("option"); o.value = c; o.textContent = c; select.appendChild(o); });
    const render = () => {
      const term = (document.getElementById("option-search").value || "").toLowerCase().trim();
      const filter = select.value;
      const visible = R.options.filter(x => (filter === "all" || x.category === filter) && (!term || Object.values(x).join(" ").toLowerCase().includes(term)));
      const grouped = categories.map((c, i) => ({c, rows: visible.filter(x => x.category === c)})).filter(g => g.rows.length);
      optionsRoot.innerHTML = grouped.map((g, i) => `<section class="option-group" id="${i === 0 ? "bank-routes" : i === 1 ? "source-routes" : "group-" + i}"><div class="group-heading"><div><span class="eyebrow">${String(g.rows.length).padStart(2,"0")} ROUTE${g.rows.length === 1 ? "" : "S"}</span><h2>${esc(g.c)}</h2></div></div><div class="table-wrap"><table class="option-table"><thead><tr><th>Method</th><th>Eligibility / evidence</th><th>Tax / direct cost</th><th>Pros</th><th>Cons &amp; next step</th><th>Source</th></tr></thead><tbody>${g.rows.map(x => `<tr><td><b>${esc(x.method)}</b>${x.flag ? `<small class="flag-inline">${esc(x.flag)}</small>` : ""}</td><td>${esc(x.eligibility)}</td><td>${esc(x.tax)}</td><td>${esc(x.pros)}</td><td>${esc(x.cons)}<small class="cell-sub"><b>Next:</b> ${esc(x.next)}</small></td><td>${link(x.source)}</td></tr>`).join("")}</tbody></table></div></section>`).join("") || `<div class="empty-state">No routes match your search. Try another term or clear the category filter.</div>`;
    };
    document.getElementById("option-search").addEventListener("input", render);
    select.addEventListener("change", render);
    render();
  }

  const taxRows = document.getElementById("tax-rows");
  if (taxRows) taxRows.innerHTML = R.taxRows.map(x => `<tr><td><b>${esc(x.topic)}</b>${x.flag ? `<small class="flag-inline">${esc(x.flag)}</small>` : ""}</td><td>${x.rate ? esc(x.rate) : ""}</td><td>${esc(x.basis)}</td><td>${esc(x.impact)}</td><td>${link(x.source)}</td></tr>`).join("");

  const reportingRows = document.getElementById("reporting-rows");
  if (reportingRows) reportingRows.innerHTML = R.reportingRows.map(x => `<tr><td><b>${esc(x.item)}</b>${x.flag ? `<small class="flag-inline">${esc(x.flag)}</small>` : ""}</td><td>${esc(x.rule)}</td><td>${esc(x.when)}</td><td>${link(x.source)}</td></tr>`).join("");

  const flagCards = document.getElementById("flag-cards");
  if (flagCards) flagCards.innerHTML = R.flags.map((x,i) => `<article class="flag-card"><div class="flag-number">${String(i+1).padStart(2,"0")}</div><div><h3>${esc(x.title)}</h3><p>${esc(x.detail)}</p>${link(x.source)}</div></article>`).join("");

  const sourceList = document.getElementById("source-list");
  if (sourceList) {
    const renderSources = () => {
      const q = document.getElementById("source-search").value.toLowerCase().trim();
      const items = R.sources.filter(x => !q || `${x.agency} ${x.title} ${x.note}`.toLowerCase().includes(q));
      sourceList.innerHTML = items.map((x,i) => `<article class="source-card"><div class="source-index">${String(i+1).padStart(2,"0")}</div><div class="source-main"><span class="source-agency">${esc(x.agency)}</span><h3><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.title)} ↗</a></h3><p>${esc(x.note)}</p><span class="source-url">${esc(x.url)}</span></div></article>`).join("") || `<div class="empty-state">No sources match.</div>`;
    };
    document.getElementById("source-search").addEventListener("input", renderSources);
    renderSources();
  }
})();
