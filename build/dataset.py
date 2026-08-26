# -*- coding: utf-8 -*-
"""원고 + 재배열 메타를 한 줄짜리 문항 레코드로 합친다.

원고   D:\\project\\산업안전기사\\산업안전기사\\src\\past\\R##_S#.ps1   (본문·해설)
메타   D:\\project\\산업안전기사\\산업안전기사\\기출_재배열\\R##.json    (분류·출제이력·점검표시)
"""
import os
import json
import re

import psparse

def pick(*cands):
    """컴퓨터마다 자리가 달라 실제로 있는 쪽을 고른다."""
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


ROOT = pick(r'D:\project\산업안전기사\산업안전기사',
            os.path.join(os.path.expanduser('~'), 'Desktop', 'project', '산업안전기사'))

SRC = os.path.join(ROOT, 'src', 'past')
META = os.path.join(ROOT, '기출_재배열')
FIG = os.path.join(ROOT, 'src', 'fig')

SUBJ = ['안전관리론', '인간공학 및 시스템안전공학', '기계위험방지기술',
        '전기위험방지기술', '화학설비위험방지기술', '건설안전기술']

COURSE = '산업안전기사'
BOOK = '산업안전기사 필기 기출 재배열'
BOOKCODE = 'A'
PREFIX = 'safe'

# 재배열 24회 -> 4회차씩 한 해로 (2026년이 제1~4회)
YEARS = [2026, 2025, 2024, 2023, 2022, 2021]


def round_label(r):
    """재배열 회차 번호(1~24) -> (연도, 그 해의 회차)"""
    return YEARS[(r - 1) // 4], (r - 1) % 4 + 1


def folder(r):
    y, n = round_label(r)
    return 'CBT_%d_%d회' % (y, n)


def qcode(r, n):
    y, rn = round_label(r)
    return '%s_%s_%d_%02d_%03d' % (PREFIX, BOOKCODE, y, rn, n)


RX_EQ = re.compile(r'#\{(.*?)\}#|#=(.*?)=#', re.S)
RX_NUMEQ = re.compile(r'\d')


def _eqs(*vals):
    out = []
    for v in vals:
        if isinstance(v, list):
            out += _eqs(*v)
        elif isinstance(v, dict):
            out += _eqs(*v.values())
        elif isinstance(v, str):
            for m in RX_EQ.finditer(v):
                out.append(m.group(1) if m.group(1) is not None else m.group(2))
    return out


def classify(it):
    """문제유형 — 개념형 / 공식형 / 계산형.

    해설 안에서 숫자를 넣어 값을 뽑아내면 계산형, 식만 세우면 공식형,
    수식이 아예 없으면 개념형.
    """
    sol_eq = _eqs(it.get('sol'), it.get('tbl'))
    any_eq = sol_eq + _eqs(it.get('t'), it.get('c'), it.get('key'),
                           it.get('mem'), it.get('w'), it.get('old'))
    if not any_eq:
        return '개념형'
    for e in sol_eq:
        nums = re.findall(r'\d+(?:\.\d+)?', e)
        if '=' in e and len(nums) >= 2:
            return '계산형'
    return '공식형'


def reps(it):
    """출제 횟수 — src 의 시행일 개수."""
    s = str(it.get('src') or '').strip()
    if not s:
        return 1
    return len([x for x in s.split('·') if x.strip()])


def freq(rep):
    return 1 if rep <= 1 else (2 if rep == 2 else 3)


def level(kind, rep, it):
    """난이도 1~3.

    계산형·공식형은 유형만으로 갈리지만, 문항의 86 %가 개념형이라 그 안을 더
    갈라야 쓸모가 있다. 보기가 길수록·수치를 외워야 할수록·조건이 붙을수록
    어렵고, 여러 해 되풀이된 문항은 눈에 익어 한 단 내린다.
    """
    if kind == '계산형':
        return 3 if rep < 3 else 2
    if kind == '공식형':
        return 2 if rep < 3 else 1
    hard = 0
    c = it.get('c') or []
    if c and sum(len(str(x)) for x in c) / len(c) >= 22:
        hard += 1
    if re.search(r'\d', str(it.get('t', '')) + ''.join(str(x) for x in c)):
        hard += 1
    if it.get('qb'):
        hard += 1
    if rep >= 2:
        hard -= 1
    return 2 if hard >= 1 else 1


def fill_chapters(recs):
    """재배열 메타에 분류가 빠진 문항은 같은 키워드를 쓴 문항에서 끌어온다."""
    import collections
    by_topic, by_kn = collections.defaultdict(collections.Counter), \
        collections.defaultdict(collections.Counter)
    for r in recs:
        if r['chapter']:
            by_topic[r['small']][(r['chapter'], r['big'])] += 1
            by_kn[r['kn']][(r['chapter'], r['big'])] += 1
    filled = 0
    for r in recs:
        if r['chapter']:
            continue
        for tbl, k in ((by_topic, r['small']), (by_kn, r['kn'])):
            if k and tbl.get(k):
                r['chapter'], r['big'] = tbl[k].most_common(1)[0][0]
                filled += 1
                break
    return filled


def load_meta():
    """(회차, 번호) -> 재배열 메타"""
    out = {}
    for r in range(1, 25):
        p = os.path.join(META, 'R%02d.json' % r)
        j = json.load(open(p, encoding='utf-8'))
        items = j['items'] if isinstance(j, dict) and 'items' in j else j
        for it in items:
            out[(r, it.get('no'))] = it
    return out


def build():
    rounds = psparse.load_all(SRC)
    meta = load_meta()
    recs = []
    for r in sorted(rounds):
        for it in sorted(rounds[r], key=lambda x: x['n']):
            m = meta.get((r, it['n']), {})
            kind = classify(it)
            rep = reps(it)
            y, rn = round_label(r)
            recs.append({
                'round': r, 'year': y, 'rno': rn, 'n': it['n'],
                'code': qcode(r, it['n']),
                's': it['s'], 'subject': SUBJ[it['s'] - 1],
                'chapter': m.get('big') or '',
                'big': m.get('small') or '',
                'mid': (it.get('kn') or '').split('—')[-1].strip(),
                'small': it.get('topic') or '',
                'freq': freq(rep), 'level': level(kind, rep, it), 'kind': kind,
                'rep': rep, 'src': it.get('src') or '',
                'hist': m.get('hist') or [],
                'date': m.get('date') or '', 'uid': m.get('uid') or '',
                'flags': {k: m.get(k) for k in
                          ('suspect', 'crossed', 'needfig', 'revised') if m.get(k)},
                't': it['t'], 'qb': it.get('qb') or [], 'qfig': it.get('qfig') or '',
                'c': it['c'], 'a': it['a'],
                'sol': it['sol'], 'tbl': it.get('tbl'),
                'fig': it.get('fig') or '', 'figcap': it.get('figcap') or '',
                'w': it.get('w') or [], 'kn': it.get('kn') or '',
                'key': it.get('key') or '', 'mem': it.get('mem') or '',
                'old': it.get('old') or '',
            })
    fill_chapters(recs)
    return recs


if __name__ == '__main__':
    import collections
    recs = build()
    print('문항', len(recs))
    print('회차별', sorted(collections.Counter(r['round'] for r in recs).values())[:3], '...')
    for k in ('kind', 'freq', 'level'):
        print(k, dict(collections.Counter(r[k] for r in recs).most_common()))
    print('챕터 빈칸', sum(1 for r in recs if not r['chapter']))
    print('그림', sum(1 for r in recs if r['fig']), '발문그림', sum(1 for r in recs if r['qfig']))
    print('점검표시', dict(collections.Counter(
        k for r in recs for k in r['flags'])))
