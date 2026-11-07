'use strict';
const search = document.getElementById('search');
const statusFilter = document.getElementById('status');
const rows = Array.from(document.querySelectorAll('tbody tr'));
const count = document.getElementById('result-count');
function filterRows() {
  const query = (search?.value || '').trim().toLocaleLowerCase();
  const status = statusFilter?.value || '';
  let visible = 0;
  for (const row of rows) {
    const matches = row.textContent.toLocaleLowerCase().includes(query)
      && (!status || row.querySelector('.badge')?.textContent === status);
    row.hidden = !matches;
    if (matches) visible++;
  }
  if (count) count.textContent = `${visible} of ${rows.length} entries`;
  const empty = document.querySelector('.empty-state');
  if (empty) empty.hidden = visible !== 0;
}
if (search) {
  // Ledger rows have no finding status; don't show an inapplicable filter.
  if (!document.querySelector('tbody .badge')) statusFilter.closest('label').hidden = true;
  search.addEventListener('input', filterRows);
  statusFilter?.addEventListener('change', filterRows);
  filterRows();
}
document.querySelector('.print')?.addEventListener('click', () => window.print());
