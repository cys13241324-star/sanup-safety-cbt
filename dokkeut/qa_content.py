# -*- coding: utf-8 -*-
"""원고 결손 점검 — 발문이 가리키는 자료가 실제로 없는 문항을 찾는다"""
import json, io, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
qs = sorted(json.load(io.open(os.path.join(HERE, 'R01.json'), encoding='utf-8-sig')),
            key=lambda q: q['n'])

RX_REF = re.compile(r'다음\s*(그림|표|중|보기)|아래\s*(그림|표)|그림과\s*같은|'
                    r'표와\s*같은|다음\s*과\s*같|FT\s*도|결함수')
RX_KOR = re.compile(r'^\s*[ㄱ-ㅎ][\s,·]')
RX_PAREN = re.compile(r'\(\s*\)|（\s*）|\(\s*[ㄱ-ㅎ]\s*\)')

found = collections.defaultdict(list)
for q in qs:
    n, t = q['n'], q['t']
    has_fig = bool(q.get('fig') or q.get('qfig'))
    has_tbl = bool(q.get('tbl'))
    has_box = bool(q.get('qb'))

    # ① 보기가 ㄱㄴㄷㄹ 조합인데 정의가 없다
    if all(RX_KOR.match(c) or re.fullmatch(r'[ㄱ-ㅎ][\s,·ㄱ-ㅎ]*', str(c).strip())
           for c in q['c']):
        if not (has_box or re.search(r'[ㄱ-ㅎ]\s*[.:)]', t)):
            found['보기가 ㄱㄴㄷㄹ 조합인데 항목 정의가 없음'].append(n)

    # ② 발문이 그림·표를 가리키는데 없다
    m = RX_REF.search(t)
    if m:
        kind = (m.group(1) or m.group(2) or '')
        if kind == '표' and not has_tbl:
            found['발문이 「표」를 가리키는데 표가 없음'].append(n)
        elif kind == '그림' and not has_fig:
            found['발문이 「그림」을 가리키는데 그림이 없음'].append(n)
        elif kind == '' and not (has_fig or has_tbl or has_box):
            found['발문이 「다음과 같은 자료」를 가리키는데 자료가 없음'].append(n)

    # ③ 빈 괄호를 채울 자료가 없다
    if RX_PAREN.search(t) and not (has_tbl or has_box or has_fig):
        found['발문에 빈 괄호가 있는데 채울 자료가 없음'].append(n)

    # ④ 해설만 그림을 가리킨다
    if not has_fig and re.search(r'그림|도해', str(q.get('sol') or '')):
        found['해설이 그림을 가리키는데 그림이 없음'].append(n)

print('원고 결손 점검 — 120문항')
tot = 0
for k in sorted(found):
    v = sorted(set(found[k]))
    tot += len(v)
    print('\n■ %s (%d건)' % (k, len(v)))
    for n in v:
        print('   %03d  %s' % (n, qs[n - 1]['t'][:58]))
print('\n합계 %d건' % tot)
