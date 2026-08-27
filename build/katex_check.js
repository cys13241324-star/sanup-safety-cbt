// _math.json 의 수식을 KaTeX 로 실제 렌더해 본다. 깨지는 것만 찍는다.
const fs = require('fs');
const path = require('path');
// 저장소 안의 katex 를 먼저 쓰고, 없으면 전기기능사 쪽에서 빌린다.
const cands = [path.join(__dirname, '..', 'katex', 'katex.min.js'),
               'D:/electrician-cbt/CBT_2025_1회/katex/katex.min.js'];
const katex = require(cands.find(p => fs.existsSync(p)) || cands[0]);

const list = JSON.parse(fs.readFileSync(path.join(__dirname, '_math.json'), 'utf8'));
const bad = [];
for (const m of list) {
  try {
    katex.renderToString(m.tex, { displayMode: m.display, throwOnError: true });
  } catch (e) {
    bad.push({ code: m.code, tex: m.tex, msg: String(e.message).slice(0, 160) });
  }
}
console.log('수식 ' + list.length + ' 개 · 실패 ' + bad.length + ' 개');
const seen = new Set();
for (const b of bad) {
  const key = b.msg.replace(/position \d+/, '');
  if (seen.has(key) && seen.size > 40) continue;
  seen.add(key);
  console.log('--- ' + b.code + '\n    ' + b.tex + '\n    ' + b.msg);
}
fs.writeFileSync(path.join(__dirname, '_math_bad.json'), JSON.stringify(bad, null, 1));
