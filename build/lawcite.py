# -*- coding: utf-8 -*-
"""원고가 든 법령 인용을 읽어, 법제처 원문 조문을 붙인다.

원고의 관련개념(kn)은 「근거 — 개념명」 꼴이라 대시 앞이 곧 인용이다.
    산업안전보건법 제139조 · 시행령 제99조 — 유해·위험작업의 근로시간 제한
    안전보건규칙 별표3 — 프레스등의 작업시작 전 점검
해설 보충(key)에도 조문이 더 붙는 일이 있어 함께 훑는다.
"""
import io
import json
import os
import re

from render import esc, plain

HERE = os.path.dirname(os.path.abspath(__file__))
LAWFILE = os.path.join(HERE, '_laws.json')

# 긴 이름을 먼저 봐야 「산업안전보건법 시행령」이 「산업안전보건법」으로 잘리지 않는다
ALIAS = [
    ('산업안전보건기준에 관한 규칙', '안전보건규칙'),
    ('안전보건규칙', '안전보건규칙'),
    ('산업안전보건법 시행규칙', '시행규칙'),
    ('산업안전보건법 시행령', '시행령'),
    ('산업안전보건법', '산업안전보건법'),
    ('산업재해보상보험법', '산업재해보상보험법'),
    ('중대재해 처벌 등에 관한 법률', '중대재해처벌법'),
    ('중대재해처벌법', '중대재해처벌법'),
    ('건설기술 진흥법', '건설기술진흥법'),
    ('건설기술진흥법', '건설기술진흥법'),
    ('위험물안전관리법', '위험물안전관리법'),
    ('고압가스 안전관리법', '고압가스안전관리법'),
    ('고압가스안전관리법', '고압가스안전관리법'),
    ('화학물질관리법', '화학물질관리법'),
    ('전기사업법', '전기사업법'),
    ('시설물의 안전 및 유지관리에 관한 특별법', '시설물안전법'),
    ('시행규칙', '시행규칙'),
    ('시행령', '시행령'),
]
TOK = re.compile(
    '(' + '|'.join(re.escape(a) for a, _ in ALIAS) + ')'
    r'|제\s?(\d+)\s?조(?:의\s?(\d+))?'
    r'|별표\s?(\d+)')

_LAWS = None


def laws():
    global _LAWS
    if _LAWS is None:
        with io.open(LAWFILE, encoding='utf-8') as fp:
            _LAWS = json.load(fp)
        for k, v in _LAWS.items():
            v['index'] = {(a['no'], a['branch']): a for a in v['arts']}
    return _LAWS


def effdate(short):
    d = laws().get(short, {}).get('eff', '')
    return '%s. %d. %d.' % (d[:4], int(d[4:6]), int(d[6:8])) if len(d) == 8 else ''


def refs(*texts):
    """인용 문자열들 -> [(법령약칭, 'jo'|'byp', 번호, 가지번호)] (순서 유지·중복 제거)"""
    out, seen, cur = [], set(), None
    for t in texts:
        if not t:
            continue
        cur = None
        for m in TOK.finditer(plain(t)):
            if m.group(1):
                cur = dict(ALIAS)[m.group(1)]
            elif m.group(2):
                if cur:
                    k = (cur, 'jo', m.group(2), m.group(3) or '')
                    if k not in seen:
                        seen.add(k)
                        out.append(k)
            elif m.group(4):
                if cur:
                    k = (cur, 'byp', m.group(4), '')
                    if k not in seen:
                        seen.add(k)
                        out.append(k)
    return out


def cite_source(rec):
    """법령 인용이 담긴 자리 — 관련개념의 근거 부분과 해설 보충."""
    kn = rec.get('kn') or ''
    head = kn.split('—')[0] if '—' in kn else ''
    return head, rec.get('key') or ''


def article(short, no, branch):
    v = laws().get(short)
    if not v:
        return None
    return v['index'].get((no, branch))


ORDER = ['안전보건규칙', '시행규칙', '시행령', '산업안전보건법']


def _tkey(s):
    return re.sub(r'[^가-힣A-Za-z0-9]', '', plain(s or ''))


def resolve(short, no, branch, concept):
    """인용한 법령이 어긋나는 자리가 있다.

    원고가 「안전보건규칙 제79조 — 협의체의 구성 및 운영」이라 적었지만 그 조문은
    산업안전보건법 시행규칙 제79조다. 대시 뒤 개념명과 조문 제목을 맞춰 바로잡는다.
    """
    first = article(short, no, branch)
    ck = _tkey(concept)
    if not ck:
        return short, first
    if first and (_tkey(first['title']) in ck or ck in _tkey(first['title'])):
        return short, first
    for k in [short] + [x for x in ORDER if x != short]:
        a = article(k, no, branch)
        if not a:
            continue
        tk = _tkey(a['title'])
        if tk and (tk in ck or ck in tk):
            return k, a
    return short, first


# ── 조문에서 「이 문항이 묻는 대목」 찾아 칠하기 ──────────────────
# 원고는 해설·암기에서 핵심 어구를 ==형광== · __밑줄__ 로 이미 짚어 두었다.
# 그 어구가 조문 원문에 그대로 있으면 같은 자리를 칠한다.
RX_MARK = re.compile(r'==(.+?)==|__(.+?)__|\*\*(.+?)\*\*|~~(.+?)~~', re.S)
STOP = {'사업주', '근로자', '작업', '경우', '기준', '조치', '사항', '대상', '방법',
        '위험', '안전', '보건', '설치', '해당', '실시', '필요', '관리', '장소',
        '다음각호', '고용노동부령', '대통령령'}


def _norm(s):
    """빈칸·가운뎃점 차이를 지운 글자열과, 그 글자가 원문 몇 번째였는지."""
    out, idx = [], []
    for i, ch in enumerate(s):
        if ch.isspace():
            continue
        if ch in 'ㆍ⋅‧·':
            ch = '·'
        out.append(ch)
        idx.append(i)
    return ''.join(out), idx


def needles(rec):
    """칠할 어구 — 해설·관련개념·암기의 강조 표시와 정답 보기."""
    got, seen = [], set()
    for src in (rec.get('sol'), rec.get('key'), rec.get('mem'), rec.get('old')):
        if not src:
            continue
        for m in RX_MARK.finditer(str(src)):
            t = plain(next(g for g in m.groups() if g is not None))
            n, _ = _norm(t)
            if len(n) < 4 or n in STOP or n in seen:
                continue
            seen.add(n)
            got.append(t)
    a = (rec.get('c') or [None] * 4)[(rec.get('a') or 1) - 1]
    if a:
        t = plain(a)
        n, _ = _norm(t)
        if 4 <= len(n) <= 40 and n not in seen:
            seen.add(n)
            got.append(t)
    return got


# 「6시간」「34시간」「30일」처럼 수치가 곧 답인 문항이 많다
RX_QTY = re.compile(r'\d+(?:\.\d+)?\s*(?:시간|일|주일|주|개월|년|분|초|미터|밀리미터|'
                    r'센티미터|킬로그램|톤|퍼센트|명|회|배|도|층|개|호|급|종|'
                    r'[%℃]|m|cm|mm|kg|t|lx|dB)')


# 원고는 「30cm」, 법령은 「30센티미터」로 적는다. 같은 수치로 봐야 한다.
UNIT_ALT = [('센티미터', 'cm'), ('밀리미터', 'mm'), ('킬로그램', 'kg'),
            ('킬로와트', 'kW'), ('미터', 'm'), ('퍼센트', '%'), ('톤', 't')]


def qty_variants(q):
    out = [q]
    for long, short in UNIT_ALT:
        if q.endswith(long):
            out.append(q[:-len(long)] + short)
        elif q.endswith(short) and not q.endswith(long):
            out.append(q[:-len(short)] + long)
    return out


def _find(body, idx, nt, cap=3):
    hits, at = [], body.find(nt)
    while at >= 0:
        hits.append((idx[at], idx[at + len(nt) - 1] + 1))
        at = body.find(nt, at + 1)
    return hits if 0 < len(hits) <= cap else []


def _pieces(t):
    """어구가 통째로 안 맞을 때 쓸 이음말 조각 — 긴 것부터."""
    w = [x for x in re.split(r'\s+', t.strip()) if x]
    out = []
    for size in range(len(w) - 1, 1, -1):
        for i in range(len(w) - size + 1):
            out.append(' '.join(w[i:i + size]))
    return out


# ── 조문 안에서 「몇 항 몇 호」인지 짚기 ────────────────────────
CIRCLE = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
RX_HANG = re.compile(r'제\s?(\d+)\s?항')
RX_HO = re.compile(r'제\s?(\d+)\s?호')
RX_MOK = re.compile(r'([가-힣])\s?목')
WORD = re.compile(r'[가-힣]{2,}')


def where(*texts):
    """인용에 적힌 항·호·목 번호."""
    blob = ' '.join(plain(t) for t in texts if t)
    return (set(RX_HANG.findall(blob)), set(RX_HO.findall(blob)),
            set(RX_MOK.findall(blob)))


def lines_of(text):
    """조문을 줄 단위로 갈라 각 줄이 항인지 호인지 목인지 매긴다."""
    out = []
    for ln in text.split('\n'):
        s = ln.strip()
        kind, num = '', ''
        if s[:1] in CIRCLE:
            kind, num = 'hang', str(CIRCLE.index(s[0]) + 1)
        else:
            m = re.match(r'(\d+)\.', s)
            if m:
                kind, num = 'ho', m.group(1)
            else:
                m = re.match(r'([가-힣])\.', s)
                if m:
                    kind, num = 'mok', m.group(1)
        out.append({'raw': ln, 'kind': kind, 'num': num})
    return out


def focus(text, rec, cite, spans):
    """짚어야 할 줄 번호. 인용에 적힌 항·호가 먼저, 없으면 낱말이 가장 많이 겹치는 줄."""
    ls = lines_of(text)
    hang, ho, mok = where(*cite)
    hit = set()

    if hang or ho or mok:
        cur_h = None
        for i, l in enumerate(ls):
            if l['kind'] == 'hang':
                cur_h = l['num']
            in_h = (not hang) or (cur_h in hang)
            if l['kind'] == 'hang' and l['num'] in hang and not ho and not mok:
                hit.add(i)
            elif l['kind'] == 'ho' and l['num'] in ho and in_h:
                hit.add(i)
            elif l['kind'] == 'mok' and l['num'] in mok and in_h:
                hit.add(i)
        if hit:
            return hit

    if spans:                       # 형광이 앉은 줄이 곧 그 자리다
        pos, at = [], 0
        for l in ls:
            pos.append((at, at + len(l['raw'])))
            at += len(l['raw']) + 1
        for a, b in spans:
            for i, (x, y) in enumerate(pos):
                if a < y and b > x:
                    hit.add(i)
        return hit

    # 마지막으로, 해설·정답 보기와 낱말이 가장 많이 겹치는 줄
    hay = set(WORD.findall(plain(rec.get('sol') or '')))
    a = (rec.get('c') or [None] * 4)[(rec.get('a') or 1) - 1]
    hay |= set(WORD.findall(plain(a or '')))
    hay |= set(WORD.findall(plain(rec.get('key') or '')))
    hay -= STOP
    if not hay:
        return set()
    body = [i for i, l in enumerate(ls) if len(l['raw'].strip()) >= 8]
    if len(body) <= 2:            # 서너 줄짜리 조문은 통째로 읽으면 된다
        return set()
    best, score = None, 0
    for i in body:
        w = set(WORD.findall(ls[i]['raw']))
        c = len(w & hay)
        # 짧고 정확히 겹치는 줄을 앞세운다
        v = c + (0.3 if c and len(w) <= 12 else 0)
        if v > score:
            best, score = i, v
    return {best} if score >= 2 else set()


def spans_of(text, ns):
    """형광을 칠할 자리."""
    body, idx = _norm(text)
    spans = []
    for t in ns:
        nt, _ = _norm(t)
        if len(nt) < 4:
            continue
        hits = _find(body, idx, nt)
        if not hits:
            # 통째로는 없어도 이음말 일부가 조문에 그대로 있는 일이 많다
            for p in _pieces(t):
                np, _ = _norm(p)
                if len(np) < 5:
                    continue
                hits = _find(body, idx, np)
                if hits:
                    break
        if not hits:
            # 그래도 없으면 수치만이라도 짚는다
            for q in RX_QTY.findall(t):
                for v in qty_variants(q):
                    nq, _ = _norm(v)
                    if len(nq) >= 3:
                        got = _find(body, idx, nq, 2)
                        if got:
                            spans += got
                            break
            continue
        spans += hits
    if not spans:
        return []
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def _paint(s, base, spans, tag):
    """한 줄에 걸린 형광만 입힌다. base 는 이 줄이 원문에서 시작하는 자리."""
    out, pos = [], 0
    for a, b in spans:
        a, b = max(a - base, 0), min(b - base, len(s))
        if b <= pos:
            continue
        out.append(esc(s[pos:a]))
        out.append('<%s>%s</%s>' % (tag, esc(s[a:b]), tag))
        pos = b
    out.append(esc(s[pos:]))
    return ''.join(out)


def body_html(text, rec, cite, ns, tag='mark'):
    """조문 원문 -> 줄마다 형광과 「이 자리」 표시를 붙인 HTML."""
    spans = spans_of(text, ns)
    hit = focus(text, rec, cite, spans)
    ls = lines_of(text)
    out, at = [], 0
    for i, l in enumerate(ls):
        s, base = l['raw'], at
        at += len(s) + 1
        mine = [x for x in spans if x[0] < base + len(s) and x[1] > base]
        inner = _paint(s, base, mine, tag) if mine else esc(s)
        if tag != 'mark':          # 등록 엑셀은 div·mark 를 못 쓴다
            out.append(('▶ %s' % inner) if i in hit else inner)
            continue
        if i in hit:
            out.append('<div class="ln hit">%s<span class=here>이 문항이 묻는 자리</span>'
                       '</div>' % inner)
        else:
            out.append('<div class=ln>%s</div>' % inner)
    if tag != 'mark':
        return '<br>'.join(out), bool(hit), bool(spans)
    return ''.join(out), bool(hit), bool(spans)


def url(short, kind, no, branch=''):
    """법제처 조문 바로가기. 파일만 열어 보다가도 원문을 확인할 수 있게."""
    import urllib.parse
    name = laws().get(short, {}).get('name', short).replace(' ', '')
    if kind == 'byp':
        return 'https://www.law.go.kr/법령/' + urllib.parse.quote(name)
    tail = '제%s조%s' % (no, ('의%s' % branch) if branch else '')
    return 'https://www.law.go.kr/법령/' + urllib.parse.quote(name + '/' + tail)


def label(short, kind, no, branch):
    name = laws().get(short, {}).get('name', short)
    if kind == 'byp':
        return '%s 별표 %s' % (name, no)
    return '%s 제%s조%s' % (name, no, ('의%s' % branch) if branch else '')


def block(rec, details=True):
    """법령 원문 블록 HTML. 원문이 없으면 시행일만 밝힌다."""
    rs = refs(*cite_source(rec))
    if not rs:
        return ''
    kn = rec.get('kn') or ''
    concept = kn.split('—')[-1].strip() if '—' in kn else ''
    arts, missing, shorts, fixed = [], [], [], []
    for short, kind, no, branch in rs:
        if short not in laws():
            continue
        a = None
        if kind == 'jo':
            got, a = resolve(short, no, branch, concept)
            if a and got != short:
                fixed.append((short, got, no))
                short = got
        if short not in shorts:
            shorts.append(short)
        if a:
            arts.append((short, a))
        else:
            missing.append(label(short, kind, no, branch))
    if not arts and not missing:
        return ''

    eff = ' · '.join('%s 시행 %s' % (laws()[s]['name'], effdate(s)) for s in shorts)
    head = ' · '.join(label(s, k, n, b) for s, k, n, b in rs if s in laws())

    ns = needles(rec)
    cite = cite_source(rec)
    tag = 'mark' if details else 'strong'
    body, spots = [], []
    for short, a in arts:
        ttl = '제%s조%s%s' % (a['no'], ('의%s' % a['branch']) if a['branch'] else '',
                            ('(%s)' % a['title']) if a['title'] else '')
        inner, located, painted = body_html(a['text'], rec, cite, ns, tag)
        if located:
            spots.append('제%s조%s' % (a['no'], ('의%s' % a['branch'])
                                     if a['branch'] else ''))
        body.append(
            '<div class=lawart><div class=h><a href="%s" target="_blank">%s</a>'
            '<span class=eff>%s · 시행 %s</span></div>'
            '<div class=t>%s</div></div>'
            % (url(short, 'jo', a['no'], a['branch']), esc(ttl),
               esc(laws()[short]['name']), esc(effdate(short)), inner))
    for short, kind, no, branch in rs:
        if short not in laws():
            continue
        if kind == 'jo' and article(short, no, branch):
            continue
        body.append('<div class=lawmiss>· <a href="%s" target="_blank">%s</a> — '
                    '%s</div>'
                    % (url(short, kind, no, branch),
                       esc(label(short, kind, no, branch)),
                       '별표는 법제처 원문에서 봅니다' if kind == 'byp'
                       else '현행 조문에 없습니다(조문 이동·삭제)'))

    if not details:
        return ('<p><strong>⚖ 근거 법령</strong> <span class="eff">%s</span></p>%s'
                % (esc(eff), ''.join(body)))
    return ('<details class=law><summary>⚖ 근거 법령 — %s'
            '<span class=eff>%s</span></summary><div class=lawin>%s</div></details>'
            % (esc(head), esc(eff), ''.join(body)))


if __name__ == '__main__':
    import sys
    import collections
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    import dataset
    recs = dataset.build()
    n_ref = n_art = n_miss = 0
    per = collections.Counter()
    unknown = collections.Counter()
    for r in recs:
        rs = refs(*cite_source(r))
        if not rs:
            continue
        n_ref += 1
        got = False
        for short, kind, no, branch in rs:
            if short not in laws():
                unknown[short] += 1
                continue
            per[short] += 1
            if kind == 'jo' and article(short, no, branch):
                got = True
            else:
                n_miss += 1
        if got:
            n_art += 1
    print('법령을 인용한 문항 %d / %d' % (n_ref, len(recs)))
    print('그 가운데 조문 원문이 붙은 문항 %d' % n_art)
    print('원문 없는 인용(별표·없는 조문) %d건' % n_miss)
    print('법령별', dict(per.most_common()))
    if unknown:
        print('받아 두지 않은 법령', dict(unknown))
