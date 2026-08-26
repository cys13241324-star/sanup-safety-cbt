# -*- coding: utf-8 -*-
"""원고 표기 -> HTML(+LaTeX).

원고(src/past/R##_S#.ps1)의 인라인 표기는 lib.ps1 의 Put-Rich 와 같은 규칙이다.

    **굵게**      핵심 낱말        -> <strong>
    ==형광==      노란 형광펜      -> <strong>
    ~~연두~~      정의·요건        -> <em>
    __밑줄__      밑줄             -> <u>
    #{ 12 kW }#   수량             -> $...$
    #= ... =#     한글 수식        -> $...$

CBT 등록양식(v3)이 허용하는 인라인 태그는 <i> <em> <strong> <u> <sub> <sup>
<br> <code> 뿐이라 형광펜은 <strong> 으로 내린다.
"""
import html
import re

from hwpeq import hwp2tex

# lib.ps1 $script:RX_RICH 과 순서까지 같게 둔다 (앞선 대안이 이긴다)
RX_RICH = re.compile(
    r'\*\*(.+?)\*\*|==(.+?)==|~~(.+?)~~|#\{(.*?)\}#|#=(.*?)=#|__(.+?)__', re.S)
RX_EQ = re.compile(r'#\{(.*?)\}#|#=(.*?)=#', re.S)
RX_ONLY_EQ = re.compile(r'^\s*(?:#\{(.*?)\}#|#=(.*?)=#)\s*$', re.S)


def esc(s):
    """HTML 특수문자. LaTeX 의 < > 도 여기서 실체참조로 바꿔야 브라우저가
    태그로 오해하지 않는다."""
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _eq(tex, display=False):
    tex = esc(tex)
    return ('$$%s$$' if display else '$%s$') % tex


def _span(inner, open_tag, close_tag):
    """꾸밈 구간 안에 수식이 섞여 있을 수 있다."""
    if not RX_EQ.search(inner):
        return open_tag + esc(inner) + close_tag
    out, pos = [], 0
    for m in RX_EQ.finditer(inner):
        if m.start() > pos:
            out.append(open_tag + esc(inner[pos:m.start()]) + close_tag)
        out.append(_eq(hwp2tex(m.group(1) if m.group(1) is not None else m.group(2))))
        pos = m.end()
    if pos < len(inner):
        out.append(open_tag + esc(inner[pos:]) + close_tag)
    return ''.join(out)


# 원고는 강조 뒤 조사를 띄어 적었다. 한글 조판에서 조사까지 굵어지는 것을 피하려는
# 손버릇인데, HTML 로 옮기면 「34시간 을」처럼 벌어져 보인다. 조사만 도로 붙인다.
# 「것이 · 때문이다 · 한다 · 세 가지」처럼 띄는 것이 맞는 말은 건드리지 않는다.
JOSA = ['으로서', '으로써', '이라도', '이라는', '이므로', '이라야', '으로', '로서', '로써',
        '이라', '이란', '이며', '이고', '이지', '이면', '이다', '이든', '이나', '이자', '이었',
        '에서', '에게', '에는', '에도', '까지', '부터', '보다', '처럼', '마다', '라야',
        '조차', '마저', '한테', '라는', '라도', '므로', '지만', '뿐이다',
        '뿐', '씩', '든', '나', '라', '며', '고', '지', '면', '다',
        '인', '임', '일', '을', '를', '은', '는', '이', '가', '의', '에', '와', '과',
        '로', '도', '만', '께', '란']
# 「밖에」 는 뺐다 — 「화염이 식어 밖에 불이 붙지 않는다」 처럼 이름씨일 때가 있다.

_TAIL = r'(?=$|[\s.,)\]}·…—?!:;」』’”"\'=_*~#])'
_SPAN = r'(==.+?==|__.+?__|\*\*.+?\*\*|~~.+?~~|#=.+?=#|#\{.+?\}#|」)'

RX_TIGHT = re.compile(
    _SPAN + r' (' + '|'.join(sorted(JOSA, key=len, reverse=True)) + r')' + _TAIL, re.S)

# 숫자·영문 뒤도 같다.  「L 에 따라」 「P 를 바꾸는」.
# 「도(度)」 「만(萬)」 은 조사가 아닐 수 있어 뺐고, 수식 안은 건드리지 않는다.
JOSA_N = ['이라는', '이므로', '이라도', '으로', '라는', '이며', '이고', '이다', '이라',
          '에서', '까지', '부터', '보다', '은', '는', '이', '가', '을', '를', '의', '에',
          '로', '와', '과', '다', '뿐']
RX_TIGHT_N = re.compile(
    r'(?<=[0-9A-Za-z\]\)%]) (' + '|'.join(sorted(JOSA_N, key=len, reverse=True))
    + r')(?![가-힣])')

# 「하다 · 되다」 는 앞말이 이름씨일 때만 붙는다.  「초과 하는」 은 붙이지만
# 「열리게 하고」 「멈춰야 하므로」 는 보조용언이라 띄우는 것이 맞다.
HADA = ['하므로', '하도록', '합니다', '하여야', '한다면', '해서는', '해야만',
        '한다', '하다', '하는', '하고', '하며', '하면', '하기', '하지', '하여', '하되',
        '한', '할', '함', '해', '해서', '해야', '했다', '했고',
        '되므로', '되도록', '된다', '되다', '되는', '되고', '되며', '되면', '되어', '되지',
        '된', '될', '됨', '됐다']
RX_HADA = re.compile(
    r'(?<![게야어아여지려록면서고])(==|__|\*\*|~~) ('
    + '|'.join(sorted(HADA, key=len, reverse=True)) + r')(?![가-힣])', re.S)

RX_EQSPAN = re.compile(r'#=.*?=#|#\{.*?\}#', re.S)


def tighten(t):
    prev = None
    while prev != t:
        prev = t
        t = RX_TIGHT.sub(r'\1\2', t)
        t = RX_HADA.sub(r'\1\2', t)
    # 숫자·영문 뒤 — 수식 안의 빈칸은 조판기가 쓰는 것이라 건드리지 않는다
    out, pos = [], 0
    for m in RX_EQSPAN.finditer(t):
        out.append(RX_TIGHT_N.sub(r'\1', t[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(RX_TIGHT_N.sub(r'\1', t[pos:]))
    return ''.join(out)


def rich(t, allow_display=True):
    """원고 한 토막 -> HTML."""
    if t is None:
        return ''
    t = tighten(str(t))
    if not t:
        return ''
    # 토막 전체가 수식 하나면 가운데 큰 수식으로 앉힌다.
    # 수식이 둘 붙어 있는 자리(#{A}##{B}#)를 하나로 삼키지 않도록 낱낱이 센다.
    if allow_display:
        st = t.strip()
        ms = list(RX_EQ.finditer(st))
        if len(ms) == 1 and ms[0].start() == 0 and ms[0].end() == len(st):
            raw = ms[0].group(1) if ms[0].group(1) is not None else ms[0].group(2)
            return _eq(hwp2tex(raw), display=True)

    out, pos = [], 0
    for m in RX_RICH.finditer(t):
        if m.start() > pos:
            out.append(esc(t[pos:m.start()]))
        if m.group(1) is not None:
            out.append(_span(m.group(1), '<strong>', '</strong>'))
        elif m.group(2) is not None:
            out.append(_span(m.group(2), '<strong>', '</strong>'))
        elif m.group(3) is not None:
            out.append(_span(m.group(3), '<em>', '</em>'))
        elif m.group(4) is not None:
            out.append(_eq(hwp2tex(m.group(4))))
        elif m.group(5) is not None:
            out.append(_eq(hwp2tex(m.group(5))))
        else:
            out.append(_span(m.group(6), '<u>', '</u>'))
        pos = m.end()
    if pos < len(t):
        out.append(esc(t[pos:]))
    s = ''.join(out)
    return s.replace('\r\n', '<br>').replace('\n', '<br>')


RX_STRIP = re.compile(r'\*\*|==|~~|__|#\{|\}#|#=|=#')


def plain(t):
    """분류 칸처럼 서식이 못 들어가는 자리 — 표기만 걷어내고 글자만 남긴다."""
    if not t:
        return ''
    return re.sub(r'\s+', ' ', RX_STRIP.sub('', str(t))).strip()


TD = ('border:1px solid #cbd5e1;padding:7px 12px;'
      'vertical-align:middle;text-align:%s;')
TH = TD % 'center' + 'background:#f1f5f9;font-weight:700;'


def _blank(x):
    return x is None or not str(x).strip()


def _grid(t):
    """줄마다 칸 수가 들쭉날쭉하므로 네모지게 맞추고, 통째로 빈 열은 버린다."""
    head = list(t.get('head') or [])
    rows = [list(r) for r in (t.get('rows') or [])]
    n = max([len(head)] + [len(r) for r in rows] + [0])
    head += [''] * (n - len(head))
    rows = [r + [''] * (n - len(r)) for r in rows]
    if rows:
        keep = [c for c in range(n) if any(not _blank(r[c]) for r in rows)]
        if keep and len(keep) < n:
            head = [head[c] for c in keep]
            rows = [[r[c] for c in keep] for r in rows]
    return head, rows, len(head)


def _spans(rows, n):
    """머리 칸(왼쪽 분류 열)에서 아래로 이어지는 빈칸은 위 칸과 합친다.

    비고처럼 그냥 값이 없는 칸까지 합치면 뜻이 달라지므로, 왼쪽이 모두 빈
    「이어지는 줄」에서만 합친다.
    """
    sp = [[1] * n for _ in rows]
    for c in range(n):
        r = 0
        while r < len(rows):
            if _blank(rows[r][c]):
                r += 1
                continue
            k = r + 1
            while (k < len(rows) and _blank(rows[k][c])
                   and all(_blank(rows[k][i]) for i in range(c))):
                sp[k][c] = 0
                k += 1
            sp[r][c] = k - r
            r = k
    return sp


def table(t):
    """정리표(tbl) -> HTML <table>. 전기기능사 CBT 와 같은 인라인 서식."""
    if not t:
        return ''
    head, rows, n = _grid(t)
    if not n:
        return ''
    cap = t.get('cap') or ''
    sp = _spans(rows, n)
    buf = []
    if cap:
        buf.append('<div style="margin:12px 0 2px;font-weight:700">%s</div>'
                   % rich(cap, False))
    buf.append('<div style="overflow-x:auto"><table style="border-collapse:collapse;'
               'margin:10px auto;font-size:.96em">')
    if any(not _blank(h) for h in head):
        buf.append('<thead><tr>')
        for h in head:
            buf.append('<th style="%s">%s</th>' % (TH, rich(h, False)))
        buf.append('</tr></thead>')
    buf.append('<tbody>')
    for i, r in enumerate(rows):
        buf.append('<tr>')
        for j, c in enumerate(r):
            if sp[i][j] == 0:
                continue
            al = 'center' if j == 0 else 'left'
            rs = ' rowspan="%d"' % sp[i][j] if sp[i][j] > 1 else ''
            buf.append('<td%s style="%s">%s</td>' % (rs, TD % al, rich(c, False)))
        buf.append('</tr>')
    buf.append('</tbody></table></div>')
    return ''.join(buf)


MARK = ['①', '②', '③', '④']       # 원1 원2 원3 원4


def wrongs(w, ans):
    """오답분석. 원고의 w 는 정답을 뺀 나머지 보기에 차례로 붙는다."""
    if not w:
        return ''
    lines, k = [], 0
    for idx in range(4):
        if idx + 1 == ans:
            continue
        if k < len(w):
            lines.append('%s %s' % (MARK[idx], rich(w[k], False)))
        k += 1
    return '<br>'.join(lines)


def point(kn, key, mem, old):
    """학습포인트 = 관련개념 + 암기 + 주의사항."""
    buf = []
    if key or kn:
        if kn:
            buf.append('<strong>%s</strong><br>' % rich(kn, False))
        if key:
            buf.append(rich(key, False))
    if mem:
        buf.append('<p><strong>◈ 암기</strong> %s</p>' % rich(mem, False))
    if old:
        buf.append('<p><strong>⚠ 주의사항</strong> %s</p>' % rich(old, False))
    return ''.join(buf)
