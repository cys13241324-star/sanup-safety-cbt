# -*- coding: utf-8 -*-
"""출제 당시 기준과 지금 시행 중인 조문이 어긋나는 문항을 찾는다.

기출은 2011~2022년 것이고 조문은 오늘 판이다. 그 사이에 바뀐 자리가 있으면
해설은 옛 기준을, 바로 아래 조문은 현행 기준을 말하게 된다. 학습자가 가장
헷갈릴 자리이므로 미리 골라 둔다.

판정
  일치      해설이 짚은 수치·어구가 현행 조문에 그대로 있다
  어긋남    같은 단위인데 수가 다르다 (34시간 ↔ 36시간)
  못찾음    조문에서 찾지 못했다 (표현이 다를 뿐일 수도 있다)
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lawcite
from render import plain

RX_NUM = re.compile(r'(\d+(?:\.\d+)?)\s*'
                    r'(시간|일|주일|주|개월|년|분|초|미터|밀리미터|센티미터|'
                    r'킬로그램|퍼센트|명|회|배|도|층|개|호|급|종|[%℃]|'
                    r'm|cm|mm|kg|t|lx|dB)')


def quantities(text):
    """(수, 단위) 짝. 단위를 붙여 봐야 「34시간」과 「34명」이 갈린다."""
    return {(m.group(1), m.group(2)) for m in RX_NUM.finditer(plain(text or ''))}


# 「틀린 것은?」 유형은 정답 보기가 법과 어긋나는 것이 정상이다. 걸러 내야 한다.
RX_NEG = re.compile(r'틀린|옳지\s*않은|맞지\s*않는|아닌\s*것|아닌\s*것은|거리가\s*먼|'
                    r'부적절|적절하지\s*않은|해당하지\s*않는|해당되지\s*않는|'
                    r'포함되지\s*않는|바르지\s*않은|잘못된|아니 되는|없는 것')


def negative(rec):
    return bool(RX_NEG.search(plain(rec.get('t') or '')))


def check(rec):
    """(판정, 근거) — 조문이 붙지 않은 문항은 None."""
    rs = [x for x in lawcite.refs(*lawcite.cite_source(rec))
          if x[0] in lawcite.laws()]
    arts = [lawcite.article(s, n, b) for s, k, n, b in rs if k == 'jo']
    arts = [a for a in arts if a]
    if not arts:
        return None
    body = '\n'.join(a['text'] for a in arts)
    have = quantities(body)
    units_have = {}
    for v, u in have:
        units_have.setdefault(u, set()).add(v)

    if negative(rec):
        # 정답이 곧 「법과 어긋나는 보기」인 유형 — 어긋나는 것이 정상이다
        return ('부정형(대조 안 함)', '')
    ans = (rec.get('c') or [None] * 4)[(rec.get('a') or 1) - 1]
    want = quantities(ans)          # 정답 보기의 수치만 본다
    if not want:
        return ('수치없음', '')

    ok, clash, miss = [], [], []
    for v, u in sorted(want):
        if (v, u) in have:
            ok.append('%s%s' % (v, u))
        elif u in units_have:
            clash.append('%s%s → 조문은 %s'
                         % (v, u, ', '.join(sorted(units_have[u])[:3]) + u))
        else:
            miss.append('%s%s' % (v, u))
    if clash:
        return ('어긋남', ' · '.join(clash))
    if ok:
        return ('일치', ' · '.join(ok))
    return ('못찾음', ' · '.join(miss))


def rec_c(r):
    return r.get('c') or []


def main():
    import collections
    import dataset
    recs = dataset.build()
    tally = collections.Counter()
    rows = []
    for r in recs:
        c = check(r)
        if not c:
            continue
        verdict, why = c
        tally[verdict] += 1
        if verdict == '어긋남':
            rows.append((r, why))
    print('조문이 붙은 문항 판정 —', dict(tally))
    print()
    known = [r for r, _ in rows if r['flags'].get('revised') or r['old']]
    print('「어긋남」 %d문항 · 그 가운데 원고가 이미 주의를 달아 둔 것 %d'
          % (len(rows), len(known)))
    print()
    for r, why in rows[:40]:
        note = '⚠주의사항 있음' if r['old'] else (
            '⚠개정기록 있음' if r['flags'].get('revised') else '— 표시 없음')
        print('%s  %s' % (r['code'], note))
        print('   발문 %s' % plain(r['t'])[:70])
        print('   정답 %s' % plain(r['c'][r['a'] - 1])[:60])
        print('   차이 %s' % why)
        print('   보기 %s' % ' / '.join(plain(x)[:26] for x in rec_c(r)))
        print('   인용 %s' % plain(r['kn'].split('—')[0])[:50])
        print()


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
