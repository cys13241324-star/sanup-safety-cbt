# -*- coding: utf-8 -*-
"""암기카드 뷰어 — 파일 하나로 도는 플립카드."""
import json

CSS = """
:root{--tl:#ea580c;--tl2:#c2410c;--bg:#faf7f4;--ink:#1e2a28;--line:#e6ddd6;--mut:#7c6f68}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',sans-serif;
background:var(--bg);color:var(--ink);min-height:100vh;line-height:1.6}
button,select,input{font-family:inherit}
header{background:linear-gradient(90deg,#ea580c,#f59e0b);color:#fff;padding:13px 20px;
display:flex;align-items:center;gap:14px;flex-wrap:wrap}
header h1{font-size:17px;font-weight:800}
header .cnt{font-size:13px;opacity:.9}
header .sp{margin-left:auto;display:flex;gap:8px}
.hbtn{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.45);color:#fff;
padding:5px 12px;border-radius:20px;font-size:12.5px;font-weight:700;text-decoration:none}
.hbtn:hover{background:rgba(255,255,255,.32)}
.bar{background:#fff;border-bottom:1px solid var(--line);padding:9px 20px;display:flex;gap:9px;
align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:5}
select,input[type=search]{padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px}
input[type=search]{width:190px}
.chip{padding:5px 11px;border:1px solid var(--line);border-radius:20px;cursor:pointer;
font-size:12px;background:#fff}
.chip.on{color:#fff;border-color:transparent;background:#455}
.chip.on[data-t="공식형"]{background:#8a3ec4}
.chip.on[data-t="단답형"]{background:#d9822b}
.chip.on[data-t="용어형"]{background:#0f766e}
.right{margin-left:auto;display:flex;gap:8px;align-items:center;font-size:12.5px;color:var(--mut)}
.btn{padding:6px 12px;border:1px solid var(--line);background:#fff;border-radius:8px;
cursor:pointer;font-size:13px}
.btn:hover{background:#fdf5ef}
main{max-width:860px;margin:22px auto;padding:0 16px 60px}
.stage{perspective:1600px}
.card{position:relative;width:100%;min-height:440px;transform-style:preserve-3d;
transition:transform .5s;cursor:pointer}
.card.flip{transform:rotateY(180deg)}
.face{position:absolute;inset:0;backface-visibility:hidden;background:#fff;
border:1px solid var(--line);border-radius:16px;box-shadow:0 6px 24px rgba(234,88,12,.10);
padding:26px 30px;display:flex;flex-direction:column;overflow:auto}
.face.back{transform:rotateY(180deg);background:#fffdfb}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px;
font-size:12px;color:var(--mut)}
.badge{padding:3px 10px;border-radius:12px;color:#fff;font-weight:700;font-size:12px}
.b-공식형{background:#8a3ec4}.b-단답형{background:#d9822b}.b-용어형{background:#0f766e}
.stars{color:#e8a013;letter-spacing:1px}
.cid{margin-left:auto;font-family:monospace;font-size:11px;color:#b9aca4}
.qtext{font-size:21px;font-weight:800;line-height:1.55;margin:auto 0;text-align:center;
padding:10px 4px;word-break:keep-all}
.atext{font-size:15.5px;line-height:1.78;flex:1;word-break:keep-all}
.atext table{border-collapse:collapse;margin:10px auto;font-size:.94em}
.atext img{max-width:92%;display:block;margin:10px auto}
.hint{text-align:center;font-size:12px;color:#b9aca4;margin-top:12px}
.ex{border-top:1px dashed var(--line);margin-top:14px;padding-top:10px;font-size:12.5px;
color:var(--mut)}
.ex a{display:inline-block;margin:3px 5px 0 0;text-decoration:none;background:#fff7ed;
border:1px solid #fed7aa;color:#c2410c;border-radius:20px;padding:3px 10px;font-weight:700;
font-family:monospace;font-size:11.5px}
.ex a:hover{background:#ffedd5}
.pager{display:flex;gap:10px;align-items:center;justify-content:center;margin-top:18px}
.pager .btn{padding:9px 20px;font-weight:700}
.pos{font-size:14px;color:var(--mut);min-width:120px;text-align:center}
.katex{font-size:1.01em}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:3px 0;margin:7px 0}
.katex .text{font-family:'Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',sans-serif}
.qtext .katex,.atext .katex{display:inline-block;margin:2px 0}
.none{text-align:center;padding:60px 20px;color:var(--mut)}
@media(max-width:520px){.face{padding:20px 18px}.qtext{font-size:18px}.atext{font-size:14.5px}
.card{min-height:480px}main{margin:14px auto}}
"""

JS = r"""
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
let view=C.slice(), i=0, flip=false;
const KEY='safecard';
try{const r=localStorage.getItem(KEY); if(r) i=Math.max(0,Math.min(C.length-1,+r||0));}catch(e){}

function kx(el){if(window.renderMathInElement)renderMathInElement(el,{delimiters:[
 {left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false});}

function exLinks(codes){
 return codes.map(c=>{
   const m=c.match(/^safe_A_(\d{4})_(\d{2})_(\d{3})$/);
   if(!m)return '<span>'+c+'</span>';
   const y=m[1],r=+m[2],n=+m[3];
   return `<a href="CBT_${y}_${r}회/${y}_${r}회_학습.html#q${n}" target="_blank">${y}·${r}회 ${n}번</a>`;
 }).join('');
}

function render(){
 if(!view.length){$('#stage').innerHTML='<div class=none>조건에 맞는 카드가 없습니다</div>';
  $('#pos').textContent='0 / 0';return;}
 i=Math.max(0,Math.min(view.length-1,i));
 const c=view[i];
 $('#stage').innerHTML=`<div class="card${flip?' flip':''}" id=cd>
  <div class="face">
   <div class=meta><span class="badge b-${c.kind}">${c.kind}</span>
    <span class=stars>${'★'.repeat(c.fq)+'☆'.repeat(3-c.fq)}</span>
    <span>${c.subject} · ${c.chapter||'—'} · ${c.big||'—'}</span>
    <span class=cid>${c.id}</span></div>
   <div class=qtext>${c.front}</div>
   <div class=hint>카드를 누르면 뒤집힙니다 · Space</div>
  </div>
  <div class="face back">
   <div class=meta><span class="badge b-${c.kind}">${c.kind}</span>
    <span>${c.mid}</span><span class=cid>${c.id}</span></div>
   <div class=atext>${c.back}</div>
   ${c.codes.length?`<div class=ex>이 카드가 나온 문항 &nbsp;${exLinks(c.codes)}${c.nq>c.codes.length?' <span>외 '+(c.nq-c.codes.length)+'문항</span>':''}</div>`:''}
  </div></div>`;
 $('#cd').onclick=()=>{flip=!flip;$('#cd').classList.toggle('flip',flip);};
 kx($('#stage'));
 $('#pos').textContent=`${i+1} / ${view.length}`;
 try{localStorage.setItem(KEY,i);}catch(e){}
 location.replace('#'+c.id);
}

function apply(){
 const s=$('#fs').value, ch=$('#fc').value, q=$('#fq').value.trim().toLowerCase();
 const kinds=$$('.chip.on').map(b=>b.dataset.t);
 view=C.filter(c=>(!s||c.subject===s)&&(!ch||c.chapter===ch)
   &&(!kinds.length||kinds.includes(c.kind))
   &&(!q||(c.front+c.back+c.mid+c.small).toLowerCase().includes(q)));
 i=0;flip=false;render();
}

function chapters(){
 const s=$('#fs').value;
 const set=[...new Set(C.filter(c=>!s||c.subject===s).map(c=>c.chapter).filter(Boolean))].sort();
 $('#fc').innerHTML='<option value="">챕터 전체</option>'+set.map(x=>`<option>${x}</option>`).join('');
}

$('#fs').onchange=()=>{chapters();apply();};
$('#fc').onchange=apply;
$('#fq').oninput=apply;
$$('.chip').forEach(b=>b.onclick=()=>{b.classList.toggle('on');apply();});
$('#prev').onclick=()=>{if(i>0){i--;flip=false;render();}};
$('#next').onclick=()=>{if(i<view.length-1){i++;flip=false;render();}};
$('#shuf').onclick=()=>{for(let k=view.length-1;k>0;k--){const j=Math.floor(Math.random()*(k+1));
 [view[k],view[j]]=[view[j],view[k]];}i=0;flip=false;render();};
document.addEventListener('keydown',e=>{
 if(e.target.tagName==='INPUT')return;
 if(e.key==='ArrowLeft')$('#prev').click();
 if(e.key==='ArrowRight')$('#next').click();
 if(e.key===' '){e.preventDefault();const c=$('#cd');if(c){flip=!flip;c.classList.toggle('flip',flip);}}
});

const h=decodeURIComponent(location.hash.slice(1));
if(h){const k=C.findIndex(c=>c.id===h);if(k>=0){i=k;}}
chapters();render();
"""

HTML = """<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>산업안전기사 암기카드 (__N__장)</title>
<link rel=stylesheet href="katex/katex.min.css">
<script defer src="katex/katex.min.js"></script>
<script defer src="katex/auto-render.min.js"></script>
<style>__CSS__</style></head><body>
<header>
 <h1>산업안전기사 암기카드</h1>
 <span class=cnt>__N__장 · 6과목 · 기출 2,880문항에서 뽑음</span>
 <span class=sp><a class=hbtn href="_index.html">처음으로</a></span>
</header>
<div class=bar>
 <select id=fs><option value="">과목 전체</option>__SUBJ__</select>
 <select id=fc></select>
 <span class=chip data-t="단답형">단답형</span>
 <span class=chip data-t="공식형">공식형</span>
 <span class=chip data-t="용어형">용어형</span>
 <input type=search id=fq placeholder="낱말 찾기">
 <span class=right><button class=btn id=shuf>섞기</button></span>
</div>
<main>
 <div class=stage id=stage></div>
 <div class=pager>
  <button class=btn id=prev>◀ 이전</button>
  <span class=pos id=pos></span>
  <button class=btn id=next>다음 ▶</button>
 </div>
</main>
<script>const C=__DATA__;</script>
<script>__JS__</script>
</body></html>"""


def build(cards, subjects):
    data = [{'id': c['id'], 'kind': c['kind'], 'fq': c['freq'], 'lv': c['level'],
             'subject': c['subject'], 'chapter': c['chapter'], 'big': c['big'],
             'mid': c['mid'], 'small': c['small'],
             'front': c['front'], 'back': c['back'],
             'codes': c['codes'], 'nq': c['nq']} for c in cards]
    return (HTML
            .replace('__N__', '{:,}'.format(len(cards)))
            .replace('__SUBJ__', ''.join('<option>%s</option>' % s for s in subjects))
            .replace('__CSS__', CSS)
            .replace('__DATA__', json.dumps(data, ensure_ascii=False))
            .replace('__JS__', JS))
