# -*- coding: utf-8 -*-
"""깨끗한 템플릿 조각 선별 + 텍스트 노드 지도"""
import zipfile, io, os, re
import xml.etree.ElementTree as ET

HW = r'.'
OUT = os.path.dirname(os.path.abspath(__file__))
FRAG = os.path.join(OUT, 'frag2')
os.makedirs(FRAG, exist_ok=True)

raw = zipfile.ZipFile(HW).read('Contents/section0.xml').decode('utf-8')
NS = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw[:2000]))
for k, v in NS.items():
    ET.register_namespace(k, v)
root = ET.fromstring(raw)


def tg(e):
    return e.tag.split('}')[-1]


def txt(e):
    return ''.join(t.text or '' for t in e.iter() if tg(t) == 't')


tops = [c for c in root if tg(c) == 'p']
marks = [i for i, p in enumerate(tops) if p.get('styleIDRef') == '15']

blocks = []
for a, b in zip(marks, marks[1:]):
    blocks.append((a, b, tuple(tops[i].get('styleIDRef') for i in range(a, b))))


def clean(i):
    """s=15 문단이 머리말/챕터 표를 안 물고 있는지"""
    return not any(tg(e) == 'tbl' for e in tops[i].iter())


def save(el, name):
    io.open(os.path.join(FRAG, name + '.xml'), 'w', encoding='utf-8').write(
        ET.tostring(el, encoding='unicode'))


def runmap(p, label):
    """문단 안 run 구성 출력"""
    print('  ── %s  (s=%s pp=%s)' % (label, p.get('styleIDRef'), p.get('paraPrIDRef')))
    for r in [e for e in p.iter() if tg(e) == 'run']:
        bits = []
        for c in r:
            n = tg(c)
            if n == 't':
                bits.append('T"%s"' % ((c.text or '')[:30]))
            elif n == 'pic':
                bi = [x.get('binaryItemIDRef') for x in c.iter()
                      if tg(x) == 'img']
                bits.append('PIC(%s)' % (bi[0] if bi else '?'))
            elif n == 'tbl':
                bits.append('TBL(%sx%s)' % (c.get('rowCnt'), c.get('colCnt')))
            elif n == 'equation':
                sc = [x.text for x in c.iter() if tg(x) == 'script']
                bits.append('EQ"%s"' % ((sc[0] or '')[:24] if sc else ''))
            elif n in ('tab', 'lineBreak'):
                bits.append(n.upper())
            elif n == 'ctrl':
                bits.append('CTRL')
        print('       cp=%-4s %s' % (r.get('charPrIDRef'), '  '.join(bits)))


# ── 1) 보기 4문단형(1열) 표준 블록 ─────────────────────────────
c4 = None
for a, b, sig in blocks:
    if clean(a) and sig[:6] == ('15', '16', '18', '18', '18', '18'):
        c4 = (a, b, sig)
        break
print('■ 보기 4문단(1열) 블록:', c4[2] if c4 else '없음')
if c4:
    a, b, sig = c4
    names = []
    seen = {}
    for i in range(a, b):
        s = tops[i].get('styleIDRef')
        seen[s] = seen.get(s, 0) + 1
        nm = 'p%02d_s%s_%d' % (i - a, s, seen[s])
        names.append(nm)
        save(tops[i], nm)
        runmap(tops[i], nm)
    print('  저장:', len(names))

# ── 2) 오답분석 3문단 포함 블록 ────────────────────────────────
w3 = None
for a, b, sig in blocks:
    if clean(a) and sig.count('29') == 3:
        w3 = (a, b, sig)
        break
print()
print('■ 오답분석 포함 블록:', w3[2] if w3 else '없음')
if w3:
    a, b, sig = w3
    for i in range(a, b):
        s = tops[i].get('styleIDRef')
        if s in ('21', '29'):
            nm = 'w_%02d_s%s' % (i - a, s)
            save(tops[i], nm)
            runmap(tops[i], nm)

# ── 3) 학습포인트 박스 ───────────────────────────────────────
lp = None
for a, b, sig in blocks:
    if not clean(a):
        continue
    for i in range(a, b):
        p = tops[i]
        if any(tg(e) == 'tbl' for e in p.iter()) and \
           any(q.get('styleIDRef') == '31' for q in p.iter() if tg(q) == 'p'):
            lp = i
            break
    if lp:
        break
print()
if lp:
    print('■ 학습포인트 박스 문단 %d' % lp)
    save(tops[lp], 'box_learnpoint')
    t = tops[lp]
    tb = [e for e in t.iter() if tg(e) == 'tbl'][0]
    print('   표 %sx%s' % (tb.get('rowCnt'), tb.get('colCnt')))
    for tc in [e for e in tb.iter() if tg(e) == 'tc']:
        bf = tc.get('borderFillIDRef')
        inner = [(q.get('styleIDRef'), txt(q)[:34])
                 for q in tc.iter() if tg(q) == 'p']
        print('   셀 bf=%-4s %s' % (bf, inner))

# ── 4) 관련이론 바 ──────────────────────────────────────────
rt = None
for a, b, sig in blocks:
    if not clean(a):
        continue
    for i in range(a, b):
        p = tops[i]
        if p.get('styleIDRef') == '30' and \
           any(q.get('styleIDRef') == '37' for q in p.iter() if tg(q) == 'p'):
            rt = i
            break
    if rt:
        break
print()
if rt:
    print('■ 관련이론 바 문단 %d' % rt)
    save(tops[rt], 'bar_relation')
    runmap(tops[rt], 'bar')
    tb = [e for e in tops[rt].iter() if tg(e) == 'tbl'][0]
    for tc in [e for e in tb.iter() if tg(e) == 'tc']:
        print('   셀 bf=%s  →  %s' % (tc.get('borderFillIDRef'), txt(tc)[:60]))

# ── 5) 과목제목 띠 ──────────────────────────────────────────
for i, p in enumerate(tops):
    if any(q.get('styleIDRef') == '13' for q in p.iter() if tg(q) == 'p'):
        save(p, 'band_subject')
        print()
        print('■ 과목제목 띠 문단 %d → %s' % (i, txt(p)[:30]))
        tb = [e for e in p.iter() if tg(e) == 'tbl']
        if tb:
            for tc in [e for e in tb[0].iter() if tg(e) == 'tc']:
                print('   셀 bf=%s  →  %s' % (tc.get('borderFillIDRef'), txt(tc)[:40]))
        break

print()
print('조각 위치:', FRAG)
