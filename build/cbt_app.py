# -*- coding: utf-8 -*-
"""클릭해서 푸는 화면 — 시험용과 학습용을 아예 다른 파일로 낸다.

  {연도}_{회}회_CBT.html    시험 — 3시간 타이머, 답만 고르고 제출, 그 뒤 채점·복습
  {연도}_{회}회_학습.html    학습 — 타이머·제출 없음, 문항마다 해설 여닫기·암기카드 팝업

답안과 진도도 서로 다른 자리에 저장돼 섞이지 않는다.
"""
import json

SUBJ_SHORT = ['안전관리론', '인간공학·시스템', '기계위험방지', '전기위험방지',
              '화학설비위험방지', '건설안전']

CBT_CSS = """
:root{--ink:#1f2937;--mut:#64748b;--line:#e2e8f0;--accent:#ea580c;--accbg:#fff7ed;
--bg:#f1f5f9;--card:#fff;--ok:#059669;--no:#dc2626}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',system-ui,sans-serif;
background:var(--bg);color:var(--ink);line-height:1.65;-webkit-text-size-adjust:100%}
button{font-family:inherit;cursor:pointer}
header{background:linear-gradient(90deg,#ea580c,#f59e0b);color:#fff;padding:10px 16px;
display:flex;align-items:center;gap:12px;flex-wrap:wrap;position:sticky;top:0;z-index:20;
box-shadow:0 2px 8px rgba(0,0,0,.12)}
header.study{background:linear-gradient(90deg,#0e7490,#0891b2)}
header h1{font-size:15px;font-weight:800}
header .kind{font-size:11.5px;font-weight:800;background:rgba(255,255,255,.22);
border-radius:20px;padding:2px 10px}
header .sp{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.timer{font-variant-numeric:tabular-nums;font-weight:800;font-size:16px;
background:rgba(255,255,255,.2);padding:3px 12px;border-radius:20px}
.timer.warn{background:#b91c1c}
.rate{font-size:12.5px;font-weight:700;background:rgba(255,255,255,.2);
padding:3px 12px;border-radius:20px}
.hbtn{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.45);color:#fff;
padding:5px 12px;border-radius:20px;font-size:12.5px;font-weight:700;text-decoration:none}
.hbtn:hover{background:rgba(255,255,255,.32)}
main{max-width:820px;margin:0 auto;padding:16px 14px 130px}
.wrap{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.qh{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:10px}
.qno{font-weight:800;color:var(--accent);font-size:19px}
.study .qno{color:#0e7490}
.tag{font-size:11px;font-weight:700;color:#fff;border-radius:20px;padding:2px 9px}
.subj{font-size:12px;color:var(--mut)}
.acts{margin-left:auto;display:flex;gap:6px}
.mini{border:1px solid var(--line);background:#fff;border-radius:20px;padding:4px 12px;
font-size:12px;font-weight:700;color:#475569;white-space:nowrap}
.mini:hover{background:#f8fafc;border-color:#cbd5e1}
.mini.on{background:var(--accbg);border-color:var(--accent);color:#c2410c}
.mini.cd{background:#ecfeff;border-color:#a5f3fc;color:#0e7490}
.mini.cd:hover{background:#cffafe}
.stem{font-weight:600;font-size:16.5px;margin:6px 0 14px;word-break:keep-all}
.cond{border:1px solid #cbd5e1;background:#f8fafc;border-radius:8px;padding:9px 12px;
margin:8px 0;font-size:14.5px}
.opt{display:flex;gap:9px;align-items:flex-start;width:100%;text-align:left;
border:1.5px solid var(--line);background:#fff;border-radius:10px;padding:11px 13px;
margin:7px 0;font-size:15.5px;color:inherit;transition:.12s;word-break:keep-all}
.opt:hover{border-color:#fdba74;background:#fffbf6}
.opt .n{font-weight:800;color:#94a3b8;flex:none}
.opt.sel{border-color:var(--accent);background:var(--accbg)}
.opt.sel .n{color:var(--accent)}
.opt.right{border-color:var(--ok);background:#ecfdf5}
.opt.right .n{color:var(--ok)}
.opt.wrong{border-color:var(--no);background:#fef2f2}
.opt.wrong .n{color:var(--no)}
.opt img{max-width:100%;display:block;margin:6px 0}
.stemimg{max-width:92%;display:block;margin:10px 0;border:1px solid #eee;border-radius:8px;
padding:6px;background:#fff}
.vline{font-size:13.5px;font-weight:700;margin:10px 2px 0}
.vline.o{color:var(--ok)}
.vline.x{color:var(--no)}
.sol{margin-top:14px;border-top:1px dashed var(--line);padding-top:14px}
.lbl{display:inline-block;font-size:11.5px;font-weight:700;color:#fff;background:var(--accent);
border-radius:20px;padding:2px 10px;margin:12px 0 6px}
.lbl.g{background:#0891b2}
.box{border:1px solid #cbd5e1;background:#f8fafc;border-radius:8px;padding:10px 12px;margin:6px 0}
.sol img{max-width:92%;display:block;margin:10px 0;border:1px solid #eee;border-radius:8px;
padding:6px;background:#fff}
.sol table{border-collapse:collapse;margin:10px auto;font-size:.94em}
nav{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--line);
box-shadow:0 -2px 10px rgba(0,0,0,.06);z-index:20}
.navin{max-width:820px;margin:0 auto;padding:8px 14px;display:flex;gap:8px;align-items:center}
.nbtn{border:1px solid var(--line);background:#fff;border-radius:10px;padding:8px 16px;
font-size:14px;font-weight:700}
.nbtn:disabled{opacity:.4;cursor:default}
.nbtn.pri{background:var(--accent);color:#fff;border-color:var(--accent)}
.study .nbtn.pri{background:#0891b2;border-color:#0891b2}
.prog{flex:1;text-align:center;font-size:13px;color:var(--mut)}
.prog b{color:var(--ink)}
.pal{max-width:820px;margin:0 auto;padding:0 14px 10px;display:none}
.pal.open{display:block}
.palgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(34px,1fr));gap:5px;
max-height:38vh;overflow:auto;padding:4px 0}
.pg{border:1px solid var(--line);background:#fff;border-radius:7px;padding:5px 0;font-size:12px;
font-weight:700;color:#94a3b8}
.pg.done{background:#fff7ed;border-color:#fdba74;color:#c2410c}
.pg.cur{background:var(--accent);border-color:var(--accent);color:#fff}
.study .pg.cur{background:#0891b2;border-color:#0891b2}
.pg.ok{background:#ecfdf5;border-color:#6ee7b7;color:var(--ok)}
.pg.no{background:#fef2f2;border-color:#fca5a5;color:var(--no)}
.palhd{font-size:12px;color:var(--mut);margin:8px 0 3px;font-weight:700}
.result{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px}
.score{font-size:42px;font-weight:800;text-align:center;margin:6px 0}
.verdict{text-align:center;font-size:17px;font-weight:800;padding:8px;border-radius:10px;margin:10px 0}
.verdict.pass{background:#ecfdf5;color:var(--ok)}
.verdict.fail{background:#fef2f2;color:var(--no)}
.stab{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
.stab th,.stab td{border:1px solid var(--line);padding:7px 9px;text-align:center}
.stab th{background:#f8fafc;font-weight:700}
.stab td.bad{background:#fef2f2;color:var(--no);font-weight:700}
.rowbtns{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:14px}
.intro{text-align:center;padding:34px 20px}
.intro h2{font-size:22px;margin-bottom:8px}
.intro p{color:var(--mut);font-size:14px;margin-bottom:6px}
.big{background:var(--accent);color:#fff;border:none;border-radius:12px;padding:13px 34px;
font-size:16px;font-weight:800;margin-top:18px}
/* 법령 원문 */
details.law{border:1px solid #e2e8f0;border-radius:8px;margin:10px 0;background:#fcfcfd}
details.law>summary{cursor:pointer;padding:8px 12px;font-size:13px;font-weight:700;
color:#475569;list-style:none;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
details.law>summary::-webkit-details-marker{display:none}
details.law[open]>summary{border-bottom:1px solid #eef2f6}
.eff{margin-left:auto;color:#a3aab5;font-size:11px;font-weight:600;letter-spacing:-.2px}
.lawin{padding:4px 14px 12px}
.lawart{margin:9px 0;font-size:13.5px;line-height:1.72}
.lawart .h{font-weight:700;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.lawart .h a{color:#334155;text-decoration:none}
.lawart .h a:hover{text-decoration:underline}
.lawmiss a{color:#94a3b8}
.lawart .t{white-space:normal;color:#334155;margin-top:3px}
.ln{display:block;white-space:pre-wrap;padding:1px 0}
.ln.hit{background:#fffbeb;border-left:3px solid #f59e0b;padding:4px 8px;margin:3px 0 3px -11px;border-radius:0 5px 5px 0}
.here{display:inline-block;margin-left:8px;font-size:10.5px;font-weight:800;color:#b45309;background:#fef3c7;border:1px solid #fde68a;border-radius:20px;padding:0 8px;vertical-align:middle;white-space:nowrap}
.lawart mark{background:#fde68a;color:inherit;padding:0 2px;border-radius:3px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.lawmiss{font-size:12px;color:#94a3b8;padding:2px 0}
/* 암기카드 팝업 */
.modal{position:fixed;inset:0;background:rgba(15,23,42,.58);display:none;
align-items:center;justify-content:center;z-index:60;padding:22px}
.modal.on{display:flex}
.mbox{width:min(660px,100%);position:relative;perspective:1600px}
.mx{position:absolute;top:-13px;right:-13px;z-index:3;background:#fff;border:1px solid var(--line);
width:36px;height:36px;border-radius:50%;font-size:16px;font-weight:800;color:#475569;
box-shadow:0 4px 12px rgba(0,0,0,.28)}
.mcard{position:relative;width:100%;height:min(560px,76vh);transform-style:preserve-3d;
transition:transform .5s;cursor:pointer}
.mcard.flip{transform:rotateY(180deg)}
.mface{position:absolute;inset:0;backface-visibility:hidden;background:#fff;border-radius:18px;
box-shadow:0 22px 55px rgba(0,0,0,.35);padding:26px 28px;display:flex;flex-direction:column;
overflow:auto}
.mface.back{transform:rotateY(180deg);background:#fffdfb}
.mmeta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px;
font-size:12px;color:var(--mut)}
.badge{padding:3px 10px;border-radius:12px;color:#fff;font-weight:700;font-size:12px}
.b-공식형{background:#8a3ec4}.b-단답형{background:#d9822b}.b-용어형{background:#0f766e}
.stars{color:#e8a013;letter-spacing:1px}
.mcid{margin-left:auto;font-family:monospace;font-size:11px;color:#b9aca4}
.mq{font-size:21px;font-weight:800;line-height:1.55;margin:auto 0;text-align:center;
padding:10px 4px;word-break:keep-all}
.ma{font-size:15px;line-height:1.78;flex:1;word-break:keep-all}
.ma table{border-collapse:collapse;margin:10px auto;font-size:.93em}
.mhint{text-align:center;font-size:12px;color:#b9aca4;margin-top:12px}
.mfoot{border-top:1px dashed var(--line);margin-top:12px;padding-top:9px;font-size:12px;
color:var(--mut);display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.mfoot a{text-decoration:none;background:#fff7ed;border:1px solid #fed7aa;color:#c2410c;
border-radius:20px;padding:3px 11px;font-weight:700;font-size:11.5px}
.katex{font-size:1.01em}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:3px 0;margin:7px 0}
.katex .text{font-family:'Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',sans-serif}
@media(max-width:520px){main{padding:12px 10px 130px}.wrap{padding:14px 13px}
.stem{font-size:15.5px}.opt{font-size:14.5px}.acts{width:100%;margin-left:0}
.mq{font-size:18px}.ma{font-size:14.2px}.mface{padding:20px 18px}}
"""

CBT_JS = r"""
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const STUDY=MODE==='study';
const KEY=(STUDY?'safestudy_':'safecbt_')+D.round;
let S={i:0,ans:{},open:{},started:STUDY?1:0,elapsed:0,done:false};
try{const raw=localStorage.getItem(KEY); if(raw) S=Object.assign(S,JSON.parse(raw));}catch(e){}
if(!S.open)S.open={};
if(STUDY)S.started=1;
function save(){try{localStorage.setItem(KEY,JSON.stringify(S));}catch(e){}}
function kx(el){if(window.renderMathInElement)renderMathInElement(el,{delimiters:[
 {left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false});}

const MARK=['①','②','③','④'];
const LV={1:['#10b981','쉬움'],2:['#f59e0b','보통'],3:['#ef4444','어려움']};

function fmt(s){const m=Math.floor(s/60),x=s%60;
 return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')+':'+String(x).padStart(2,'0');}

let tick=null;
function startTimer(){
 if(STUDY)return;
 clearInterval(tick);tick=setInterval(()=>{
  if(S.done)return;
  S.elapsed++;const left=D.limit-S.elapsed;
  const t=$('#timer'); if(!t)return;
  t.textContent=left>0?fmt(left):'00:00:00';
  t.classList.toggle('warn',left<600);
  if(left<=0)submit();
  if(S.elapsed%10===0)save();
 },1000);}

function intro(){
 $('#app').innerHTML=`<div class="wrap intro">
  <h2>${D.title}</h2>
  <p>6과목 120문항 · 시험시간 3시간</p>
  <p>합격 기준 — 과목당 40점 이상, 전 과목 평균 60점 이상</p>
  <p style="margin-top:14px;font-size:13px">답만 고르고 끝에 제출합니다.
   해설과 암기카드는 채점한 뒤에 열립니다.</p>
  <button class="big" id="go">시험 시작</button>
  ${Object.keys(S.ans).length?'<div style="margin-top:12px;font-size:13px;color:#64748b">이어서 풀면 지난번 답안이 그대로 살아 있습니다</div>':''}
 </div>`;
 $('#go').onclick=()=>{S.started=1;save();render();startTimer();};
}

// 해설이 열려 있는가 — 직접 여닫은 적이 있으면 그 뜻을 따른다
function solOpen(q){
 if(S.open[q.n]!==undefined)return S.open[q.n];
 return S.done||(STUDY&&!!S.ans[q.n]);
}

function qHTML(q){
 const a=S.ans[q.n], graded=(STUDY&&a)||S.done, show=STUDY||S.done;
 let h=`<div class="wrap"><div class="qh"><span class="qno">${String(q.n).padStart(3,'0')}</span>
  <span class="tag" style="background:${LV[q.lv][0]}">난이도 ${q.lv}·${LV[q.lv][1]}</span>
  <span class="tag" style="background:#6366f1">${q.kind}</span>
  <span class="tag" style="background:#f59e0b">빈출 ${'★'.repeat(q.fq)+'☆'.repeat(3-q.fq)}</span>
  <span class="subj">제${q.s}과목 ${D.subj[q.s-1]}</span>`;
 if(show){
   h+=`<span class="acts">
    <button class="mini${solOpen(q)?' on':''}" id="tsol">📖 해설 ${solOpen(q)?'닫기':'보기'}</button>
    ${q.card&&D.cards[q.card]?'<button class="mini cd" id="tcard">🃏 암기카드</button>':''}
   </span>`;
 }
 h+=`</div><div class="stem">${q.t}</div>`;
 if(q.cond)h+=`<div class="cond">${q.cond}</div>`;
 if(q.img)h+=`<img class="stemimg" src="img/${q.img}">`;
 for(let k=0;k<4;k++){
   let cls='opt';
   if(a===k+1)cls+=' sel';
   if(graded){ if(k+1===q.a)cls='opt right'; else if(a===k+1)cls='opt wrong'; }
   h+=`<button class="${cls}" data-k="${k+1}"><span class="n">${MARK[k]}</span><span>${q.c[k]}</span></button>`;
 }
 if(graded){
   h+= a===q.a ? `<div class="vline o">정답입니다 · 정답 ${q.a}번</div>`
              : `<div class="vline x">${a?'틀렸습니다 · 고른 답 '+a+'번 · ':'미응답 · '}정답 ${q.a}번</div>`;
 }
 if(show&&solOpen(q)){
   h+=`<div class="sol"><div class="lbl">해설</div><div>${q.sol}</div>`;
   if(q.w)h+=`<div class="lbl">오답 분석</div><div>${q.w}</div>`;
   if(q.pt)h+=`<div class="lbl g">관련 개념 · 암기</div><div class="box">${q.pt}</div>`;
   if(q.law)h+=q.law;
   h+=`</div>`;
 }
 return h+'</div>';
}

function render(){
 if(!S.started){intro();return;}
 if(!STUDY&&S.done&&S.i<0){result();return;}
 const q=D.q[S.i];
 $('#app').innerHTML=qHTML(q);
 $$('.opt').forEach(b=>b.onclick=()=>{
   S.ans[q.n]=+b.dataset.k;
   if(STUDY&&S.open[q.n]===undefined)S.open[q.n]=true;
   save();
   if(STUDY||S.done){render();}
   else{$$('.opt').forEach(x=>x.classList.toggle('sel',x===b));paint();}
 });
 const ts=$('#tsol'); if(ts)ts.onclick=()=>{S.open[q.n]=!solOpen(q);save();render();};
 const tc=$('#tcard'); if(tc)tc.onclick=()=>openCard(q.card);
 kx($('#app'));
 stat();
 $('#prev').disabled=S.i===0; $('#next').disabled=S.i===119;
 paint();
 window.scrollTo(0,0);
}

function stat(){
 const n=Object.keys(S.ans).length;
 if(STUDY){
   let ok=0; D.q.forEach(q=>{if(S.ans[q.n]===q.a)ok++;});
   $('#prog').innerHTML=`<b>${S.i+1}</b> / 120 · 푼 문항 <b>${n}</b> · 맞힘 <b>${ok}</b>`;
   const r=$('#rate');
   if(r)r.textContent=n?`정답률 ${Math.round(ok/n*100)}%`:'정답률 —';
 }else{
   $('#prog').innerHTML=S.done?`채점 완료`:`<b>${S.i+1}</b> / 120 · 푸는 중 <b>${n}</b>`;
 }
}

/* 암기카드 팝업 */
let mflip=false;
function openCard(id){
 const c=D.cards[id]; if(!c)return;
 mflip=false;
 $('#mbody').innerHTML=`<button class="mx" id="mx">✕</button>
  <div class="mcard" id="mcard">
   <div class="mface">
    <div class="mmeta"><span class="badge b-${c.kind}">${c.kind}</span>
     <span class="stars">${'★'.repeat(c.fq)+'☆'.repeat(3-c.fq)}</span>
     <span>${c.subject}${c.chapter?' · '+c.chapter:''}</span>
     <span class="mcid">${id}</span></div>
    <div class="mq">${c.front}</div>
    <div class="mhint">카드를 누르면 뒤집힙니다 · Esc 닫기</div>
   </div>
   <div class="mface back">
    <div class="mmeta"><span class="badge b-${c.kind}">${c.kind}</span>
     <span>${c.mid}</span><span class="mcid">${id}</span></div>
    <div class="ma">${c.back}</div>
    <div class="mfoot"><span>이 개념을 묻는 문항 ${c.nq}개</span>
     <a href="../_암기카드.html#${id}" target="_blank">카드 전체 보기 →</a></div>
   </div>
  </div>`;
 $('#modal').classList.add('on');
 kx($('#mbody'));
 fitCard(); setTimeout(fitCard,260);
 $('#mcard').onclick=()=>{mflip=!mflip;$('#mcard').classList.toggle('flip',mflip);};
 $('#mx').onclick=e=>{e.stopPropagation();closeCard();};
}
function fitCard(){
 const mc=$('#mcard'); if(!mc)return;
 mc.style.height='120px';
 const h=Math.max(...[...mc.querySelectorAll('.mface')].map(f=>f.scrollHeight));
 mc.style.height=Math.min(window.innerHeight*0.78,Math.max(300,h+4))+'px';
}
function closeCard(){$('#modal').classList.remove('on');}
$('#modal').onclick=e=>{if(e.target.id==='modal')closeCard();};
window.addEventListener('resize',()=>{if($('#modal').classList.contains('on'))fitCard();});

function paint(){
 $$('.pg').forEach(b=>{
   const n=+b.dataset.n, q=D.q[n-1];
   const marked=STUDY?!!S.ans[n]:S.done;
   let c='pg';
   if(marked&&(STUDY||S.done))c+=(S.ans[n]===q.a?' ok':' no');
   else if(S.ans[n])c+=' done';
   if(n-1===S.i)c+=' cur';
   b.className=c;
 });
}

function submit(){
 if(STUDY||S.done)return;
 const un=120-Object.keys(S.ans).length;
 if(un>0&&!confirm('안 푼 문제가 '+un+'개 있습니다. 제출할까요?'))return;
 S.done=true;clearInterval(tick);save();S.i=-1;result();
}

function result(){
 const per=[0,0,0,0,0,0],tot=[0,0,0,0,0,0];
 let right=0;
 D.q.forEach(q=>{tot[q.s-1]++;if(S.ans[q.n]===q.a){per[q.s-1]++;right++;}});
 const scores=per.map((v,i)=>Math.round(v/tot[i]*100));
 const avg=Math.round(right/120*100);
 const pass=avg>=60&&scores.every(s=>s>=40);
 let h=`<div class="result"><div style="text-align:center;color:#64748b;font-size:13px">${D.title} · 채점 결과</div>
  <div class="score">${avg}<span style="font-size:20px;color:#94a3b8">점</span></div>
  <div style="text-align:center;color:#64748b;font-size:14px">120문항 중 <b>${right}</b>문항 정답 · 소요 ${fmt(S.elapsed)}</div>
  <div class="verdict ${pass?'pass':'fail'}">${pass?'합격':'불합격'}</div>
  <table class="stab"><tr><th>과목</th><th>맞힌 문항</th><th>점수</th></tr>`;
 for(let i=0;i<6;i++){
   h+=`<tr><td style="text-align:left">제${i+1}과목 ${D.subj[i]}</td>
    <td>${per[i]} / ${tot[i]}</td><td class="${scores[i]<40?'bad':''}">${scores[i]}</td></tr>`;
 }
 h+=`</table><div style="font-size:12.5px;color:#64748b;text-align:center">합격 — 과목당 40점 이상, 평균 60점 이상</div>
  <div class="rowbtns">
   <button class="nbtn pri" id="rw">틀린 문제만 다시 보기</button>
   <button class="nbtn" id="rall">전체 해설 보기</button>
   <button class="nbtn" id="rst">다시 풀기</button>
  </div></div>`;
 $('#app').innerHTML=h;
 paint(); stat();
 $('#rw').onclick=()=>{const bad=D.q.findIndex(q=>S.ans[q.n]!==q.a);S.i=bad<0?0:bad;render();};
 $('#rall').onclick=()=>{S.i=0;render();};
 $('#rst').onclick=()=>{if(confirm('답안을 지우고 처음부터 다시 풀까요?')){
   S={i:0,ans:{},open:{},started:1,elapsed:0,done:false};save();render();startTimer();}};
}

function build(){
 let p='';
 for(let s=1;s<=6;s++){
   p+=`<div class="palhd">제${s}과목 ${D.subj[s-1]}</div><div class="palgrid">`;
   D.q.filter(q=>q.s===s).forEach(q=>{p+=`<button class="pg" data-n="${q.n}">${q.n}</button>`;});
   p+='</div>';
 }
 $('#pal').innerHTML=p;
 $$('.pg').forEach(b=>b.onclick=()=>{S.i=+b.dataset.n-1;save();render();$('#pal').classList.remove('open');});
}

$('#prev').onclick=()=>{if(S.i>0){S.i--;save();render();}};
$('#next').onclick=()=>{if(S.i<119){S.i++;save();render();}};
$('#palbtn').onclick=()=>$('#pal').classList.toggle('open');
const sb=$('#sub'); if(sb)sb.onclick=submit;
const rs=$('#reset'); if(rs)rs.onclick=()=>{if(confirm('푼 기록을 모두 지울까요?')){
 S={i:0,ans:{},open:{},started:1,elapsed:0,done:false};save();render();}};
document.addEventListener('keydown',e=>{
 if($('#modal').classList.contains('on')){
   if(e.key==='Escape')closeCard();
   if(e.key===' '){e.preventDefault();$('#mcard').click();}
   return;
 }
 if(e.key==='ArrowLeft')$('#prev').click();
 if(e.key==='ArrowRight')$('#next').click();
 if('1234'.includes(e.key)){const b=$$('.opt')[+e.key-1];if(b)b.click();}
 if(e.key==='s'||e.key==='S'){const t=$('#tsol');if(t)t.click();}
 if(e.key==='c'||e.key==='C'){const t=$('#tcard');if(t)t.click();}
});
build();
const hm=location.hash.match(/^#q(\d+)/);
if(hm){S.started=1;S.i=Math.max(0,Math.min(119,+hm[1]-1));save();}
if(!STUDY&&S.done){if(hm){render();}else{S.i=-1;result();}}
else{render();if(S.started)startTimer();}
"""

CBT_HTML = """<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>__TITLE__ · __KIND__</title>
<link rel=stylesheet href="katex/katex.min.css">
<script defer src="katex/katex.min.js"></script>
<script defer src="katex/auto-render.min.js"></script>
<style>__CSS__</style></head><body class="__BODY__">
<header class="__BODY__">
 <h1>__TITLE__</h1><span class=kind>__KIND__</span>
 <div class=sp>
__HEADBTN__
  <button class=hbtn id=palbtn>문항표</button>
  <a class=hbtn href="__OTHER__">__OTHERLBL__</a>
  <a class=hbtn href="../_index.html">회차 목록</a>
 </div>
</header>
<main><div id=app></div></main>
<nav>
 <div id=pal class=pal></div>
 <div class=navin>
  <button class="nbtn" id=prev>◀ 이전</button>
  <div class=prog id=prog></div>
  <button class="nbtn pri" id=next>다음 ▶</button>
 </div>
</nav>
<div class=modal id=modal><div class=mbox id=mbody></div></div>
<script>const MODE="__MODE__";const D=__DATA__;</script>
<script>__JS__</script>
</body></html>"""


def build_round(recs, year, rno, rd, qhtml, cardmap, mode):
    """mode — 'exam' 이면 시험용, 'study' 면 학습용."""
    qs, used = [], {}
    for r in recs:
        d = qhtml(r)
        qs.append({'n': r['n'], 's': r['s'], 'a': r['a'],
                   'lv': r['level'], 'fq': r['freq'], 'kind': r['kind'],
                   't': d['t'], 'c': d['c'], 'cond': d['cond'], 'img': d['img'],
                   'sol': d['sol'], 'w': d['w'], 'pt': d['pt'],
                   'law': d.get('law', ''), 'card': d['card']})
        c = cardmap.get(d['card'])
        if c and c['id'] not in used:
            used[c['id']] = {'kind': c['kind'], 'fq': c['freq'],
                             'subject': c['subject'], 'chapter': c['chapter'],
                             'mid': c['mid'], 'front': c['front'],
                             'back': c['back'], 'nq': c['nq']}
    title = '%d년 %d회 산업안전기사 필기' % (year, rno)
    data = {'round': rd, 'title': title, 'limit': 180 * 60,
            'subj': SUBJ_SHORT, 'q': qs, 'cards': used}
    study = mode == 'study'
    head = ('  <span class=rate id=rate></span>\n'
            '  <button class=hbtn id=reset>진도 지우기</button>') if study else (
        '  <span class=timer id=timer>03:00:00</span>\n'
        '  <button class=hbtn id=sub>답안 제출</button>')
    return (CBT_HTML
            .replace('__TITLE__', title)
            .replace('__KIND__', '학습' if study else '시험')
            .replace('__BODY__', 'study' if study else 'exam')
            .replace('__HEADBTN__', head)
            .replace('__OTHER__', '%d_%d회_%s.html' % (year, rno,
                                                       'CBT' if study else '학습'))
            .replace('__OTHERLBL__', '⏱ 시험 보기' if study else '📖 학습하기')
            .replace('__MODE__', mode)
            .replace('__CSS__', CBT_CSS)
            .replace('__DATA__', json.dumps(data, ensure_ascii=False))
            .replace('__JS__', CBT_JS))
