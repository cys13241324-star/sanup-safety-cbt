# -*- coding: utf-8 -*-
"""Part C 템플릿에서 문항 블록 XML 조각 추출"""
import zipfile, io, os, re
import xml.etree.ElementTree as ET

HW = r'.'
OUT = os.path.dirname(os.path.abspath(__file__))
FRAG = os.path.join(OUT, 'frag')
os.makedirs(FRAG, exist_ok=True)

Z = zipfile.ZipFile(HW)
raw = Z.read('Contents/section0.xml').decode('utf-8')

# 네임스페이스 등록 (직렬화 시 접두사 보존)
NS = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw[:2000]))
for k, v in NS.items():
    ET.register_namespace(k, v)

root = ET.fromstring(raw)


def tg(e):
    return e.tag.split('}')[-1]


def text_of(e):
    return ''.join(t.text or '' for t in e.iter() if tg(t) == 't')


tops = [c for c in root if tg(c) == 'p']
print('최상위 문단 수:', len(tops))

marks = [i for i, p in enumerate(tops) if p.get('styleIDRef') == '15']
print('문제-번호 문단:', len(marks), '개')


def dump(i, name):
    p = tops[i]
    x = ET.tostring(p, encoding='unicode')
    io.open(os.path.join(FRAG, name + '.xml'), 'w', encoding='utf-8').write(x)
    return len(x)


# 문항 블록들을 훑어 구성 패턴 파악
from collections import Counter
pat = Counter()
blocks = []
for a, b in zip(marks, marks[1:]):
    blk = tops[a:b]
    sig = tuple(p.get('styleIDRef') for p in blk)
    pat[sig] += 1
    blocks.append((a, b, sig))

print()
print('문항 블록 구성 패턴 (상위 8):')
for s, n in pat.most_common(8):
    print('  x%-3d %s' % (n, ' → '.join(s)))

# 학습포인트 박스(표)를 품은 블록 찾기
def has_style(blk, sid):
    return any(p.get('styleIDRef') == sid for p in blk)


target = None
for a, b, sig in blocks:
    blk = tops[a:b]
    # 학습포인트-제목(31) 이 표 안에 들어있는 문단 탐색
    for p in blk:
        if any(tg(e) == 'tbl' for e in p.iter()) and \
           any(q.get('styleIDRef') == '31' for q in p.iter() if tg(q) == 'p'):
            target = (a, b)
            break
    if target:
        break

print()
if target:
    a, b = target
    print('학습포인트 박스 포함 블록: 문단 %d~%d' % (a, b))
    for i in range(a, b):
        p = tops[i]
        kinds = []
        if any(tg(e) == 'tbl' for e in p.iter()):
            kinds.append('표')
        if any(tg(e) == 'pic' for e in p.iter()):
            kinds.append('그림')
        if any(tg(e) == 'equation' for e in p.iter()):
            kinds.append('수식')
        inner = [q.get('styleIDRef') for q in p.iter()
                 if tg(q) == 'p' and q is not p]
        print('  %3d s=%-3s pp=%-3s %-7s inner=%-22s %s'
              % (i, p.get('styleIDRef'), p.get('paraPrIDRef'),
                 ','.join(kinds), ','.join(inner) if inner else '-',
                 text_of(p)[:44]))

# 표준 블록(가장 흔한 패턴) 통째 저장
std_sig, _ = pat.most_common(1)[0]
for a, b, sig in blocks:
    if sig == std_sig:
        for k, i in enumerate(range(a, b)):
            dump(i, 'std_%02d_s%s' % (k, tops[i].get('styleIDRef')))
        print()
        print('표준 블록 저장: 문단 %d~%d (%d개)' % (a, b, b - a))
        break

# 학습포인트 블록도 저장
if target:
    a, b = target
    for k, i in enumerate(range(a, b)):
        dump(i, 'lp_%02d_s%s' % (k, tops[i].get('styleIDRef')))
    print('학습포인트 블록 저장: %d개' % (b - a))

# 과목제목 문단(s=13) 위치
sub = [i for i, p in enumerate(tops) if p.get('styleIDRef') == '13'
       or any(q.get('styleIDRef') == '13' for q in p.iter() if tg(q) == 'p')]
print()
print('과목제목 포함 문단:', sub[:6])
if sub:
    dump(sub[0], 'subject')
    print('  →', text_of(tops[sub[0]])[:40])

# 챕터제목(s=11)
ch = [i for i, p in enumerate(tops)
      if any(q.get('styleIDRef') == '11' for q in p.iter() if tg(q) == 'p')
      or p.get('styleIDRef') == '11']
print('챕터제목 포함 문단:', ch[:6])
if ch:
    dump(ch[0], 'chapter')
    print('  →', text_of(tops[ch[0]])[:60])

io.open(os.path.join(OUT, 'section0_head.txt'), 'w', encoding='utf-8').write(raw[:1500])
print()
print('조각 저장 위치:', FRAG)
