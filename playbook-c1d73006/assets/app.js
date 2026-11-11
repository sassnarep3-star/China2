(function(){
var b=document.querySelector('.menu'),n=document.getElementById('nav');
if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');});}
var t=document.getElementById('ct');if(!t){return;}
var fm=document.getElementById('fm'),fa=document.getElementById('fa'),fc=document.getElementById('fc');
var rows=Array.prototype.slice.call(t.tBodies[0].rows);
var q=new URLSearchParams(location.search);
if(q.get('m')){fm.value=q.get('m');}else{fm.value='L01';}
if(q.get('a')){fa.value=q.get('a');}
function go(){var m=fm.value,a=fa.value,k=0;
rows.forEach(function(r){var ok=(!m||r.getAttribute('data-m')===m)&&(!a||r.getAttribute('data-amt')===a);r.hidden=!ok;if(ok){k++;}});
fc.textContent=k+' of '+rows.length+' rows shown';}
fm.addEventListener('change',go);fa.addEventListener('change',go);go();
})();
