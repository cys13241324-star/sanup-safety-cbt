# -*- coding: utf-8 -*-
"""암기카드(플립카드) 생성.

전기기능사 `(플립카드)등록템플릿.xlsx` 15열 양식을 그대로 따른다.
원고가 문항마다 들고 있는 관련개념(kn·key)·암기(mem)·정리표(tbl)가 곧 카드 재료다.
같은 개념을 묻는 문항을 한 장으로 묶어 앞면(물음)과 뒷면(답)을 짓는다.
"""
import collections
import re

from render import rich, table, plain

# 과목 약자 — 전기기능사의 thy/mac/fac 와 같은 자리
ABBR = ['mgt', 'erg', 'mac', 'ele', 'chm', 'con']

RX_EQ = re.compile(r'#\{(.*?)\}#|#=(.*?)=#', re.S)
RX_DEF = re.compile(r'이론|법칙|정의|원리|효과|가설|모형|이란|개념')


def josa(word):
    """받침을 보고 은/는 을 고른다."""
    w = re.sub(r'[^가-힣A-Za-z0-9]', '', word)
    if not w:
        return '는'
    ch = w[-1]
    if '가' <= ch <= '힣':
        return '는' if (ord(ch) - 0xAC00) % 28 == 0 else '은'
    if ch.isdigit():
        return '은' if ch in '0136780' else '는'
    return '은' if ch.lower() in 'lmnrg' else '는'


def kind_of(rs):
    blob = ' '.join((r['key'] or '') + (r['mem'] or '') + (r['sol'] or '') for r in rs)
    if RX_EQ.search(blob):
        return '공식형'
    if RX_DEF.search(rs[0]['mid'] or ''):
        return '용어형'
    return '단답형'


def front(name, kind):
    name = plain(name).strip().rstrip('.')
    if not name:
        return ''
    if kind == '공식형':
        return '%s의 식은?' % name
    if kind == '용어형':
        return '%s이란?' % name if josa(name) == '은' else '%s란?' % name
    return '%s%s?' % (name, josa(name))


def _uniq(seq):
    seen, out = set(), []
    for x in seq:
        k = re.sub(r'\s+', '', plain(x))
        if x and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def back(rs):
    """뒷면 — 답(해설) · 암기 · 판별 요령 · 정리표 · 근거 차례."""
    buf = []
    sols = _uniq([r['sol'] for r in rs])[:3]
    if len(sols) == 1:
        buf.append(rich(sols[0], False))
    else:
        buf.append('<ul>%s</ul>'
                   % ''.join('<li>%s</li>' % rich(s, False) for s in sols))

    mem = _uniq([r['mem'] for r in rs if r['mem']])[:2]
    if mem:
        buf.append('<p><strong>◈ 암기</strong> %s</p>'
                   % ' · '.join(rich(m, False) for m in mem))

    keys = _uniq([r['key'] for r in rs if r['key']])[:2]
    if keys:
        buf.append('<p>%s</p>' % '<br>'.join(rich(k, False) for k in keys))

    for r in rs:
        if r['tbl']:
            buf.append(table(r['tbl']))
            break

    법 = [r['kn'].split('—')[0].strip() for r in rs if '—' in (r['kn'] or '')]
    법 = _uniq(법)[:1]
    if 법:
        buf.append('<p><em>근거 — %s</em></p>' % rich(법[0], False))
    return ''.join(buf)


def build(recs):
    """문항 목록 -> (카드 목록, 문항코드->카드ID)."""
    groups = collections.OrderedDict()
    for r in recs:
        key = (r['s'], plain(r['mid']) or plain(r['small']))
        groups.setdefault(key, []).append(r)

    cards, bycode = [], {}
    seq = collections.Counter()
    for (s, name), rs in groups.items():
        seq[s] += 1
        cid = 'card_%s_t%03d' % (ABBR[s - 1], seq[s])
        kind = kind_of(rs)
        # 분류는 그 개념을 가장 많이 대표하는 값으로
        def top(field):
            c = collections.Counter(plain(r[field]) for r in rs if r[field])
            return c.most_common(1)[0][0] if c else ''
        card = {
            'id': cid,
            'code': '%s%02d-C%03d' % (ABBR[s - 1][0].upper(), s, seq[s]),
            's': s, 'subject': rs[0]['subject'],
            'chapter': top('chapter'), 'big': top('big'),
            'mid': name, 'small': top('small'),
            'kind': kind,
            'freq': max(r['freq'] for r in rs),
            'level': round(sum(r['level'] for r in rs) / len(rs)),
            'front': front(name, kind),
            'back': back(rs),
            'codes': [r['code'] for r in rs][:5],
            'nq': len(rs),
        }
        cards.append(card)
        for r in rs:
            bycode[r['code']] = cid
    return cards, bycode
