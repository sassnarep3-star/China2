
(function(){
  var q=document.getElementById('q'), t=document.getElementById('tbl'), c=document.getElementById('blankonly');
  if(t&&q){
    var rows=[].slice.call(t.tBodies[0].rows);
    function apply(){
      var v=(q.value||'').toLowerCase(), onlyBlank=c&&c.checked;
      rows.forEach(function(r){
        var ok=v?r.innerText.toLowerCase().indexOf(v)>-1:true;
        if(ok&&onlyBlank){ok=r.querySelectorAll('td .blank').length>0;}
        r.style.display=ok?'':'none';
      });
      var shown=rows.filter(function(r){return r.style.display!=='none'}).length;
      var n=document.getElementById('count'); if(n){n.textContent=shown+' of '+rows.length+' rows shown';}
    }
    q.addEventListener('input',apply); if(c){c.addEventListener('change',apply);}
    var b=document.getElementById('reset');
    if(b){b.addEventListener('click',function(){q.value='';if(c){c.checked=false;}apply();});}
    apply();
  }
})();
