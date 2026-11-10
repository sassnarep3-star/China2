// Briefing interactions: method filter + cost-table jump + print. No dependencies.
(function(){
  var sel=document.getElementById('method-filter');
  if(sel){sel.addEventListener('change',function(){
    var v=sel.value;
    document.querySelectorAll('[data-method]').forEach(function(el){
      el.style.display=(!v||el.getAttribute('data-method')===v)?'':'none';
    });
  });}
  var amt=document.getElementById('amount-filter');
  if(amt){amt.addEventListener('change',function(){
    var v=amt.value;
    document.querySelectorAll('tr[data-tier]').forEach(function(row){
      row.style.display=(!v||row.getAttribute('data-tier')===v)?'':'none';
    });
  });}
})();
