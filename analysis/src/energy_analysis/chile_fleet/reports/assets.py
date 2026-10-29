"""Small inline assets: reports work offline without third-party scripts."""

STYLE = """
:root{color-scheme:light;--ink:#16302b;--muted:#586d67;--line:#d9e4df;--paper:#f3f6f3;
--green:#157656;--blue:#357cba;--red:#b74b3f;--amber:#98721c}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--green);text-underline-offset:3px}button,input,select{font:inherit}
header{padding:21px max(5vw,20px);background:#102d27;color:#eef8f3;display:flex;
align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
header a{color:#edf9f2;text-decoration:none}.brand{font-weight:750;letter-spacing:.03em}
header nav{display:flex;gap:20px;flex-wrap:wrap;font-size:13px}main{max-width:1440px;
margin:auto;padding:32px max(4vw,18px) 64px}.eyebrow{text-transform:uppercase;
letter-spacing:.14em;font-size:11px;font-weight:800;color:var(--green)}
h1{font-size:clamp(30px,4vw,48px);line-height:1.14;letter-spacing:-.035em;margin:10px 0 14px}
h2{font-size:23px;line-height:1.25;letter-spacing:-.02em;margin:0 0 10px}
h3{font-size:16px;margin:0 0 10px}p{margin:8px 0 16px}.muted,.caption{color:var(--muted)}
.caption{font-size:12px}.hero{max-width:980px;margin-bottom:27px}.notice{background:#fff4d8;
border:1px solid #ebd49a;padding:12px 18px;border-radius:9px;margin:0 0 20px;color:#604b18}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:24px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:12px}
.card{padding:19px 21px}.card .label{font-size:12px;color:var(--muted);display:block}
.card .value{font-size:clamp(23px,2.6vw,34px);letter-spacing:-.04em;font-weight:700;
font-variant-numeric:tabular-nums;line-height:1.3;margin:8px 0;display:block}
.card small{font-size:12px;color:var(--muted)}.panel{padding:24px;margin:20px 0;min-width:0}
.two{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:20px}
.two .panel{margin-top:0}.badge{display:inline-block;border-radius:20px;padding:3px 10px;
font-size:11px;font-weight:700;white-space:nowrap;background:#eaf0ed;color:#53655e}
.underperforming{background:#fbece7;color:#994234}.overperforming{background:#e8f1fa;color:#286591}
.within_tolerance{background:#e6f3eb;color:#286845}
.insufficient_comparison{background:#edf0f0;color:#5c6965}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0 16px}.toolbar label{font-size:12px;
font-weight:650;display:grid;gap:4px}.toolbar input,.toolbar select{padding:9px 12px;
border:1px solid #c5d5cc;border-radius:7px;background:white;color:var(--ink);max-width:100%}
.toolbar input{min-width:min(290px,75vw)}.scroll{overflow:auto;max-width:100%;
border:1px solid var(--line);
border-radius:8px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:12px 14px;
border-bottom:1px solid #e6ede9;text-align:left;vertical-align:top}th{background:#f4f8f5;
white-space:nowrap;font-size:11px;color:#475d53}td.num,th.num{text-align:right;
font-variant-numeric:tabular-nums}
th button{border:0;background:transparent;color:inherit;padding:0;cursor:pointer;font-weight:700}
tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#fafcf9}.site-name{font-weight:650}
.coverage{height:5px;background:#e9eeeb;border-radius:6px;overflow:hidden;min-width:65px;
margin-top:6px}
.coverage span{display:block;height:100%;background:var(--green)}.negative{color:var(--red)}
.positive{color:var(--blue)}.chart{width:100%;height:auto;display:block;overflow:visible}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;margin:9px 0}.dot{display:inline-block;
width:9px;height:9px;border-radius:50%;margin-right:5px}.metric-list{display:grid;
grid-template-columns:minmax(0,1fr) auto;gap:8px 18px;font-size:13px;margin:16px 0}
.metric-list dt{color:var(--muted)}.metric-list dd{margin:0;text-align:right;
font-variant-numeric:tabular-nums}
details{border-top:1px solid var(--line);padding:13px 0}summary{cursor:pointer;font-weight:650}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f8f5;padding:15px;border-radius:7px;
font-size:11px;max-height:420px;overflow:auto}.references li{margin:0 0 16px;overflow-wrap:anywhere}
.references{font-size:13px;padding-left:22px}.tag{font-size:11px;color:var(--muted)}
.method-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:20px}
.method-grid article{border-left:3px solid #b7d9c4;padding-left:14px;font-size:13px}
.method-grid p{margin:5px 0}.small-grid{display:grid;grid-template-columns:repeat(2,
minmax(0,1fr));gap:20px}
footer{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
padding-top:20px;margin-top:30px}
:focus-visible{outline:3px solid #dfaa32;outline-offset:3px}[hidden]{display:none!important}
@media(max-width:900px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}
.two{grid-template-columns:1fr}
.method-grid{grid-template-columns:1fr}.small-grid{grid-template-columns:1fr}}
@media(max-width:520px){main{padding-top:24px}.panel{padding:17px}.card{padding:15px}.cards{gap:9px}
header nav{gap:14px}.toolbar{display:block}.toolbar label{margin-bottom:10px}}
@media print{body{background:white}header,.toolbar{display:none}.panel,.card{break-inside:avoid}
main{padding:10px}.scroll{overflow:visible}.cards{grid-template-columns:repeat(4,minmax(0,1fr))}
a{color:inherit}details{display:block}}
"""

SCRIPT = """
document.querySelectorAll('[data-fleet-table]').forEach(table=>{
 const body=table.tBodies[0], search=document.querySelector('#site-search');
 const group=document.querySelector('#group-filter'),
 count=document.querySelector('#visible-count');
 function filter(){let n=0;const q=(search?.value||'').trim().toLocaleLowerCase();
  [...body.rows].forEach(row=>{const show=(!q||row.textContent.toLocaleLowerCase().includes(q))&&
   (!group?.value||row.dataset.group===group.value);row.hidden=!show;if(show)n++});
  if(count)count.textContent=n+' sites shown';}
 search?.addEventListener('input',filter);group?.addEventListener('change',filter);
 table.querySelectorAll('th button').forEach(button=>button.addEventListener('click',()=>{
  const th=button.closest('th'), idx=th.cellIndex, numeric=th.dataset.kind==='number';
  const ascending=th.getAttribute('aria-sort')!=='ascending';
  table.querySelectorAll('th').forEach(h=>h.removeAttribute('aria-sort'));
  th.setAttribute('aria-sort',ascending?'ascending':'descending');
  const rows=[...body.rows];rows.sort((a,
b)=>{const av=a.cells[idx].dataset.sort??a.cells[idx].textContent;
   const bv=b.cells[idx].dataset.sort??b.cells[idx].textContent;
   if(numeric){if(av==='')return bv===''?0:1;if(bv==='')return -1;
    return (Number(av)-Number(bv))*(ascending?1:-1)}
   return av.localeCompare(bv)*(ascending?1:-1)});rows.forEach(row=>body.appendChild(row));}));
 filter();
});
"""
