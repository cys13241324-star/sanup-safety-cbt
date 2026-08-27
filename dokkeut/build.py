# -*- coding: utf-8 -*-
"""산업안전기사 제1회 120문항 → 독끝 조판 규격 HWPX 생성"""
import zipfile, io, os, re, json, shutil, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.environ.get('DOKKEUT_TPL', os.path.join(HERE, 'partC.hwpx'))
FRAG = os.path.join(HERE, 'frag2')
# 원본 디자인 자산(약물 EMF·박스 타일) 폴더 — 각자 환경에 맞게
LAYOUT = os.environ.get('DOKKEUT_LAYOUT', r'.\레이아웃')
# 문항 그림 폴더
FIGDIR = os.environ.get('DOKKEUT_FIG', r'.\fig')
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0      # 0 = 전체
_pos = [a for a in sys.argv[2:] if not a.startswith('--') and a.endswith('.hwpx')]
OUTNAME = _pos[0] if _pos else '산업안전기사_제01회_독끝조판.hwpx'

Z = zipfile.ZipFile(TPL)
SEC_RAW = Z.read('Contents/section0.xml').decode('utf-8')
NS = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', SEC_RAW[:2500]))
for k, v in NS.items():
    ET.register_namespace(k, v)
HP = NS['hp']; HC = NS['hc']; HS = NS['hs']
Q = lambda p, t: '{%s}%s' % (NS[p], t)

SUBJECTS = {1: '산업재해예방·안전보건교육', 2: '인간공학·위험성평가',
            3: '기계·기구설비 안전', 4: '전기설비 안전',
            5: '화학설비 안전', 6: '건설공사 안전'}
MARK = ['①', '②', '③', '④']
ANSMARK = ['➊', '➋', '➌', '➍']
STAR = {3: 'image117', 2: 'image119', 1: 'image124'}       # 상/중/하
_HDR0 = Z.read('Contents/header.xml').decode('utf-8')


def _next_id(tag, n=1):
    """해당 그룹의 마지막 id 다음 번호들 (id 는 배열 인덱스라 연속이어야 한다)"""
    ids = [int(x) for x in re.findall(r'<hh:%s id="(\d+)"' % tag, _HDR0)]
    m = max(ids) + 1
    return [str(m + i) for i in range(n)]


# 문서가 부르는 이름 -> 이 PC 에 실제 설치된 패밀리 이름
FONT_REMAP = {
    'G마켓 산스 Bold':        'G마켓 산스 TTF Bold',
    'G마켓 산스 Medium':      'G마켓 산스 TTF Medium',
    'G마켓 산스 Light':       'G마켓 산스 TTF Light',
    'Yoon 윤고딕 110_TT':     'YDIYGO110-KSCPC-EUC-H',
    'Yoon 윤고딕 120_TT':     'YDIYGO120-KSCPC-EUC-H',
    'Yoon 윤고딕 130_TT':     'YDIYGO130-KSCPC-EUC-H',
    'Yoon 윤고딕 320_TT':     'YDIYGO130-KSCPC-EUC-H',   # 320 미보유 → 130
    'Yoon가변 윤고딕 140_TT': 'YDIYGO130-KSCPC-EUC-H',   # 미보유 → 130
    'Yoon 윤명조 120_TT':     'YDIYMjO160-KSCPC-EUC-H',  # 120 미보유 → 160
    'DIN 2014 Condensed':      'Bahnschrift',
    'DIN 2014 Condensed Demi': 'Bahnschrift',
    'DIN 2014 Demi':           'Bahnschrift',
    'DIN 2014 Extra Bold':     'Bahnschrift',
}

# 한두 글자가 넘칠 때 윗줄을 조여 끌어올리기 위한 단계 (자간 추가%, 장평 추가%)
TIGHT_STEPS = [(-2, 0), (-4, 0), (-6, -1), (-8, -2), (-11, -3)]
TIGHT_BASES = ['88', '89', '9', '13', '23', '21']          # 사본을 만들 글자모양

GAP_PTS = [7, 9, 11, 13, 16, 19, 23, 27, 32, 38, 45, 53, 62, 72, 84]
#          문항 사이 간격 단계(pt) — 행간 170%% 라 최대 약 143pt 까지 벌어진다

_CPIDS = _next_id('charPr',
                  1 + len(TIGHT_BASES) * len(TIGHT_STEPS) + len(GAP_PTS))
BAND_CP = _CPIDS[0]                                        # 과목띠 전용 9pt
GAP_CP = _CPIDS[1 + len(TIGHT_BASES) * len(TIGHT_STEPS):]  # 간격 단계별 글자모양
TIGHTCP = {}
_k = 1
for _b in TIGHT_BASES:
    TIGHTCP[_b] = _CPIDS[_k:_k + len(TIGHT_STEPS)]
    _k += len(TIGHT_STEPS)


def _base_metrics(cid):
    """글자모양의 (장평%, 자간%)"""
    m = re.search(r'<hh:charPr id="%s".*?</hh:charPr>' % cid, _HDR0, re.S)
    if not m:
        return 100, 0
    r = re.search(r'<hh:ratio[^>]*hangul="(-?\d+)"', m.group(0))
    sp = re.search(r'<hh:spacing[^>]*hangul="(-?\d+)"', m.group(0))
    return (int(r.group(1)) if r else 100), (int(sp.group(1)) if sp else 0)


# 각 단계가 기본 대비 몇 배로 줄어드는지
TIGHT_FACTOR = {}
for _b in TIGHT_BASES:
    _r0, _s0 = _base_metrics(_b)
    _base = (_r0 / 100.0) * (1 + _s0 / 100.0)
    TIGHT_FACTOR[_b] = [((_r0 + rd) / 100.0) * (1 + (_s0 + sd) / 100.0) / _base
                        for sd, rd in TIGHT_STEPS]

# 수식은 쪼갤 수 없는 개체라, 양쪽정렬 문단에 들어가면 남은 낱말이 줄 끝까지 밀린다.
# 아래 (문단모양, 스타일) 쌍마다 왼쪽정렬 사본을 만들어 둔다.
# (이름, 바탕 paraPr, 바탕 style, 정렬, 다음문단과 함께)
VARIANTS = [
    ('title', '31', '31', 'LEFT',    True),    # 표 캡션·박스 제목
    ('sol',   '12', '23', 'LEFT',    False),   # 수식 든 해설
    ('w1',    '78', '29', 'LEFT',    False),   # 수식 든 오답 첫 줄
    ('w2',    '79', '29', 'LEFT',    False),   # 수식 든 오답 이어지는 줄
    ('box',   '73', '33', 'LEFT',    False),   # 수식 든 박스 내용
    ('cell',  '80', '35', 'CENTER',  False),   # 표 본문셀
    ('src',   '73', '33', 'RIGHT',   False),   # 학습 Point 의 기출 줄
    ('w1k',   '78', '29', None,      True),    # 오답 첫 줄 — 뒤와 붙인다
    ('w2k',   '79', '29', None,      True),    # 오답 둘째 줄 — 뒤와 붙인다
    ('figk',  '13', '0',  'CENTER',  True),    # 그림 — 캡션과 붙인다
    ('numk',  '33', '15', None,      True),    # 문제번호 — 발문과 붙인다
    ('stemk', '19', '16', None,      True),    # 발문 — 보기와 붙인다
    ('chk',   '22', '18', None,      True),    # 보기 — 다음 보기와 붙인다
    ('boxk',  '30', '30', None,      True),    # 학습 Point 박스 — 관련이론 바와 붙인다
    # ── 덩어리 첫 문단: 위 여백을 없애 단 최상단에 붙게 한다 ──
    ('icon0', '17', '21', None,      True,  0,    None),   # 해설·오답분석 약물
    ('box0',  '30', '30', None,      True,  0,    None),   # 학습 Point 박스
    # ── 덩어리 안쪽: 다음 문단과 붙인다 ──
    ('sol1',  '12', '23', None,      True),                # 해설 본문(마지막 아님)
    ('tblk',  '13', '0',  'CENTER',  True),                # 정리표 — 뒤와 붙인다
    # ── 덩어리 마지막: 다음 덩어리와의 사이 여백을 여기에 준다 ──
    ('ch_e',  '22', '18', None,      False, None, 1600),   # 보기 마지막
    ('sol_e', '12', '23', None,      False, None, 1600),   # 해설 마지막
    ('tbl_e', '13', '0',  'CENTER',  False, None, 1600),   # 표·그림 마지막
    ('w_e',   '79', '29', None,      False, None, 1600),   # 오답 마지막
]
VARIANTS = [tuple(v) + (None,) * (7 - len(v)) for v in VARIANTS]
_PPS = _next_id('paraPr', len(VARIANTS))
_STS = _next_id('style', len(VARIANTS))
VAR = {}                                   # 이름 -> (paraPr, style)
for _i, _v in enumerate(VARIANTS):
    VAR[_v[0]] = (_PPS[_i], _STS[_i])

LEFTPAIR = {'31': VAR['title'], '12': VAR['sol'], '78': VAR['w1'],
            '79': VAR['w2'], '73': VAR['box'], '80': VAR['cell']}
LEFT_PP, TITLE_LEFT_ST = VAR['title']
SOL_LEFT_PP, SOL_LEFT_ST = VAR['sol']
CELL_PP, CELL_ST = VAR['cell']


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def frag(name):
    return io.open(os.path.join(FRAG, name + '.xml'), encoding='utf-8').read()


def ser(el):
    x = ET.tostring(el, encoding='unicode')
    return re.sub(r'\s+xmlns:\w+="[^"]*"', '', x)


def strip_lineseg(x):
    return re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>', '', x, flags=re.S)


LSEG = ''            # 한글이 열 때 다시 계산하도록 비워 둔다


# ══ 원본 조각 ════════════════════════════════════════════════
F_NUM = frag('p00_s15_1')          # 문제번호 + 빈출도
F_ICON = frag('p06_s21_1')         # 해설 약물
F_WLAB = frag('w_08_s21')          # 오답분석 라벨
F_BAR = frag('bar_relation')       # 관련이론 바
F_BOX = frag('box_learnpoint')     # 학습포인트 박스
F_BAND = frag('band_subject')      # 과목띠
F_GAP = frag('p13_s0_1')           # 문항 간 여백


# ══ 문단 템플릿 ══════════════════════════════════════════════
def p_stem(text):
    lv = note('stem', text)
    cp = cp_at('21', lv)
    _pp, _st = VAR['stemk']                    # 보기와 떨어지지 않게
    return ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
            'columnBreak="0" merged="0">%s</hp:p>'
            % (_pp, _st, runs(text, base=cp, hi=cp, pt=9.0)))


def p_choice(mark, text, keep=True):
    lv = note('choice', text)
    pp, st = VAR['chk'] if keep else ('22', '18')
    if '#=' not in text:
        # 원본과 동일한 단일 run — 탭이 내어쓰기 위치로 정확히 붙는다
        return ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
                'columnBreak="0" merged="0"><hp:run charPrIDRef="%s"><hp:t>%s'
                '<hp:tab width="232" leader="0" type="1"/>%s</hp:t></hp:run></hp:p>'
                % (pp, st, cp_at('23', lv), mark, esc(text)))
    return ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
            'columnBreak="0" merged="0"><hp:run charPrIDRef="23"><hp:t>%s'
            '<hp:tab width="232" leader="0" type="1"/></hp:t></hp:run>%s</hp:p>'
            % (pp, st, mark, runs(text, base='23', hi='23', pt=8.5)))


def p_choice2(m1, t1, m2, t2, keep=True):
    """2×2 배치 — 한 문단에 보기 두 개"""
    pp, st = VAR['chk'] if keep else ('22', '18')
    return ('<hp:p id="2147483648" paraPrIDRef="' + pp + '" styleIDRef="' + st + '" pageBreak="0" '
            'columnBreak="0" merged="0"><hp:run charPrIDRef="23"><hp:t>%s'
            '<hp:tab width="232" leader="0" type="1"/>%s'
            '<hp:tab width="3400" leader="0" type="1"/>%s'
            '<hp:tab width="232" leader="0" type="1"/>%s</hp:t></hp:run></hp:p>'
            % (m1, esc(t1), m2, esc(t2)))


JOSA = ['으로서', '으로써', '이라도', '이라는', '이므로', '으로', '로서', '로써',
        '이라', '이란', '이며', '이고', '이지', '이면', '이다', '이든', '이나',
        '에서', '에게', '에는', '에도', '까지', '부터', '보다', '처럼', '마다',
        '조차', '마저', '밖에', '한테', '라는', '라도', '므로', '이자', '이었',
        '뿐', '씩', '든', '나', '라', '며', '고', '지', '면', '다',
        '인', '임', '을', '를', '은', '는', '이', '가', '의', '에', '와', '과',
        '로', '도', '만', '께']
# 강조·수식·단위 뒤에 바로 붙는 조사의 앞 공백을 뗀다.
# 「50[kV] 이상」 처럼 조사가 아닌 말은 그대로 띄어 둔다.
RX_TIGHT = re.compile(
    r'(==.+?==|__.+?__|#=.+?=#|\[[^\]]{1,10}\]) ('
    + '|'.join(sorted(JOSA, key=len, reverse=True))
    + r')(?=$|[\s.,)\]}·…—?!:;」』’”"\'=_*~#])', re.S)


RX_UNIT = re.compile(r'(\d)\s+(\[|%|℃|°|㎜|㎝|㎡|㎥)')   # 숫자와 단위는 붙인다


def tighten(t):
    """강조·수식 뒤 조사의 앞 공백을 떼고, 숫자와 단위를 붙인다"""
    prev = None
    t = str(t)
    while prev != t:
        prev = t
        t = RX_TIGHT.sub(r'\1\2', t)
    prev = None
    while prev != t:
        prev = t
        t = RX_UNIT.sub(r'\1\2', t)
    return t


EMPH = re.compile(r'==(.+?)==|__(.+?)__')
TOKEN = re.compile(r'#=(.+?)=#|==(.+?)==|__(.+?)__', re.S)

EQ_TPL = ('<hp:equation id="0" zOrder="0" numberingType="EQUATION" '
          'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
          'dropcapstyle="None" version="Equation Version 60" baseLine="86" '
          'textColor="#000000" baseUnit="%d" lineMode="CHAR" font="HYhwpEQ">'
          '<hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" '
          'heightRelTo="ABSOLUTE" protect="0"/>'
          '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" '
          'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" '
          'vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
          '<hp:outMargin left="56" right="56" top="0" bottom="0"/>'
          '<hp:shapeComment>수식입니다.</hp:shapeComment>'
          '<hp:script>%s</hp:script></hp:equation>')


def run_t(cp, txt):
    return '<hp:run charPrIDRef="%s"><hp:t>%s</hp:t></hp:run>' % (cp, esc(txt))


EQ_KW = re.compile(
    r'\b(over|times|cdot|sqrt|left|right|rm|it|bold|approx|leq|geq|neq|pm|div|'
    r'sum|int|lim|alpha|beta|gamma|theta|lambda|mu|pi|rho|sigma|omega|Delta|'
    r'Omega|angle|degree|prime)\b')


def eq_size(script, unit):
    """보이는 글자 수로 폭을, 분수 유무로 높이를 잡는다"""
    vis = EQ_KW.sub('', script)
    vis = re.sub(r'[{}^_\\]', '', vis)
    vis = re.sub(r'\s+', '', vis)
    n = max(1, len(vis))
    frac = ' over ' in script
    if frac:
        n = int(n * 0.6) + 2
    w = max(400, int(n * unit * 0.48))
    h = int(unit * 2.1) if frac else unit
    return w, h


def run_eq(cp, script, pt):
    unit = int(pt * 100)
    sc = script.strip()
    w, h = eq_size(sc, unit)
    return ('<hp:run charPrIDRef="%s">%s</hp:run>'
            % (cp, EQ_TPL % (unit, w, h, esc(sc))))


EQ_ONLY = re.compile(r'#=(.+?)=#', re.S)


def _emph_runs(text, cp, pt):
    """강조 구간 — 안에 수식이 섞여 있으면 그것만 개체로 뽑는다"""
    out, pos = [], 0
    for m in EQ_ONLY.finditer(text):
        if m.start() > pos:
            out.append(run_t(cp, text[pos:m.start()]))
        out.append(run_eq(cp, m.group(1), pt))
        pos = m.end()
    if pos < len(text):
        out.append(run_t(cp, text[pos:]))
    return ''.join(out) or run_t(cp, '')


def runs(text, base='9', hi='28', pt=8.0):
    """본문 텍스트를 run 목록으로 — 수식·강조 분리"""
    text = tighten(text)
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append(run_t(base, text[pos:m.start()]))
        if m.group(1) is not None:
            out.append(run_eq(base, m.group(1), pt))
        else:
            out.append(_emph_runs(m.group(2) or m.group(3), hi, pt))
        pos = m.end()
    if pos < len(text):
        out.append(run_t(base, text[pos:]))
    return ''.join(out) or run_t(base, '')


def runs_emph(text, base='9', hi='28'):
    return runs(text, base, hi)


def p_sol(text):
    # 수식은 쪼갤 수 없어 양쪽정렬이 남은 낱말을 줄 끝까지 밀어낸다
    eq = '#=' in text
    pp = SOL_LEFT_PP if eq else '12'
    st = SOL_LEFT_ST if eq else '23'
    lv = note('sol', text)
    return ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
            'columnBreak="0" merged="0">%s</hp:p>'
            % (pp, st, runs(text, base=cp_at('9', lv), pt=8.0)))


def p_wrong(mark, text, first, keep=False):
    base = '78' if first else '79'
    if '#=' in text:
        pp, st = LEFTPAIR[base]
    elif keep:
        pp, st = VAR['w1k'] if first else VAR['w2k']
    else:
        pp, st = base, '29'
    lv = note('wrong', text)
    return ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
            'columnBreak="0" merged="0"><hp:run charPrIDRef="10">'
            '<hp:t charStyleIDRef="22">%s</hp:t></hp:run>'
            '<hp:run charPrIDRef="9"><hp:t>'
            '<hp:tab width="468" leader="0" type="1"/></hp:t></hp:run>%s</hp:p>'
            % (pp, st, mark, runs(text, base=cp_at('9', lv), pt=8.0)))


# ══ 조각 가공 ════════════════════════════════════════════════
def make_num(n, stars):
    el = ET.fromstring(F_NUM)
    runs = [r for r in el.iter(Q('hp', 'run'))]
    s = '%03d' % n
    lead = s[:len(s) - len(s.lstrip('0') or '0')]
    body = s[len(lead):]
    ts = [t for t in runs[0].iter(Q('hp', 't'))]
    ts[0].text = lead
    ts2 = [t for t in runs[1].iter(Q('hp', 't'))]
    ts2[0].text = body
    for img in el.iter(Q('hc', 'img')):
        img.set('binaryItemIDRef', STAR[stars])
    _np, _ns = VAR['numk']                     # 발문과 떨어지지 않게
    el.set('paraPrIDRef', _np)
    el.set('styleIDRef', _ns)
    return strip_lineseg(ser(el))


def make_bar(kn, ans):
    el = ET.fromstring(F_BAR)
    ts = [t for t in el.iter(Q('hp', 't'))]
    # cp22=본문, cp19=빈, cp20=정답마커
    for t in ts:
        parent_cp = None
        if (t.text or '').strip().startswith('['):
            t.text = kn
        elif (t.text or '').strip() in ANSMARK:
            t.text = ANSMARK[ans - 1]
    # 위 조건에 안 걸린 경우 대비: 첫 긴 텍스트를 kn 으로
    longest = max(ts, key=lambda t: len(t.text or ''))
    if kn not in ''.join(x.text or '' for x in ts):
        longest.text = kn
    return strip_lineseg(ser(el))


def make_box(title, lines):
    """학습포인트 박스 — 가운데 셀 내용 교체, 중첩 공식표 제거"""
    el = ET.fromstring(F_BOX)
    cells = [c for c in el.iter(Q('hp', 'tc'))]
    mid = None
    for c in cells:
        if c.get('borderFillIDRef') == '152':
            mid = c
            break
    if mid is None:
        mid = cells[1]
    sublist = mid.find(Q('hp', 'subList'))
    if sublist is None:
        for e in mid.iter(Q('hp', 'subList')):
            sublist = e
            break
    for ch in list(sublist):
        sublist.remove(ch)
    def mk(pp, st, cp, txt, label=''):
        if '#=' in txt and pp in LEFTPAIR:
            pp, st = LEFTPAIR[pp]
        cp = cp_at(cp, note('box', txt))
        head = ('<hp:run charPrIDRef="90"><hp:t>%s </hp:t></hp:run>' % esc(label)
                if label else '')
        return ET.fromstring(
            '<hp:p xmlns:hp="%s" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
            'columnBreak="0" merged="0">%s%s</hp:p>'
            % (HP, pp, st, head, runs(txt, base=cp, hi='28', pt=7.8)))
    _bp, _bs = VAR['box0']                     # 위 여백 없이, 관련이론 바와 붙여
    el.set('paraPrIDRef', _bp)
    el.set('styleIDRef', _bs)
    sublist.append(mk(LEFT_PP, TITLE_LEFT_ST, '90', title))
    for lab, ln in lines:
        if lab == '기출':
            _sp, _ss = VAR['src']
            sublist.append(mk(_sp, _ss, '13', ln, lab))
        else:
            sublist.append(mk('73', '33', '13', ln, lab))
    return strip_lineseg(ser(el))


def make_band(name, no):
    el = ET.fromstring(F_BAND)
    if no == 1:
        el.set('pageBreak', '0')
    ts = [t for t in el.iter(Q('hp', 't')) if (t.text or '').strip()]
    if ts:
        ts[0].text = '제%d과목  %s' % (no, name)
    for r in el.iter(Q('hp', 'run')):
        if any((t.text or '').strip() for t in r.iter(Q('hp', 't'))):
            r.set('charPrIDRef', BAND_CP)
    return strip_lineseg(ser(el))


# ══ 그림 ═════════════════════════════════════════════════════
PX = 75                       # 96dpi 1픽셀 = 75 HWPUNIT
COLW = 17000                  # 단폭 안 최대 그림 폭 (약 60mm)
FIGMAP = {}                   # 파일명 -> binaryItemIDRef

PIC_TPL = (
    '<hp:pic id="0" zOrder="0" numberingType="PICTURE" textWrap="SQUARE" '
    'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" href="" groupLevel="0" '
    'instid="0" reverse="0"><hp:offset x="0" y="0"/>'
    '<hp:orgSz width="%(ow)d" height="%(oh)d"/>'
    '<hp:curSz width="%(w)d" height="%(h)d"/>'
    '<hp:flip horizontal="0" vertical="0"/>'
    '<hp:rotationInfo angle="0" centerX="%(cx)d" centerY="%(cy)d" rotateimage="1"/>'
    '<hp:renderingInfo>'
    '<hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
    '<hc:scaMatrix e1="%(sc).6f" e2="0" e3="0" e4="0" e5="%(sc).6f" e6="0"/>'
    '<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
    '</hp:renderingInfo>'
    '<hc:img binaryItemIDRef="%(id)s" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
    '<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="%(ow)d" y="0"/>'
    '<hc:pt2 x="%(ow)d" y="%(oh)d"/><hc:pt3 x="0" y="%(oh)d"/></hp:imgRect>'
    '<hp:imgClip left="0" right="%(ow)d" top="0" bottom="%(oh)d"/>'
    '<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
    '<hp:imgDim dimwidth="%(ow)d" dimheight="%(oh)d"/><hp:effects/>'
    '<hp:sz width="%(w)d" widthRelTo="ABSOLUTE" height="%(h)d" '
    'heightRelTo="ABSOLUTE" protect="0"/>'
    '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
    'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" '
    'horzAlign="CENTER" vertOffset="0" horzOffset="0"/>'
    '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
    '<hp:shapeComment>그림입니다.</hp:shapeComment></hp:pic>')


def make_fig(fname, cap=None):
    from PIL import Image
    path = os.path.join(FIGDIR, fname)
    if not os.path.exists(path):
        return ''
    iid = FIGMAP.get(fname)
    if iid is None:
        iid = 'fig%02d' % (len(FIGMAP) + 1)
        FIGMAP[fname] = iid
    im = Image.open(path)
    ow, oh = im.width * PX, im.height * PX
    sc = min(1.0, float(COLW) / ow)
    w, h = int(ow * sc), int(oh * sc)
    pic = PIC_TPL % dict(ow=ow, oh=oh, w=w, h=h, cx=ow // 2, cy=oh // 2,
                         sc=sc, id=iid)
    _fpp, _fst = VAR['figk']
    out = ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" pageBreak="0" '
           'columnBreak="0" merged="0"><hp:run charPrIDRef="9">%s</hp:run></hp:p>'
           % (_fpp, _fst, pic))
    if cap:
        out += repp('<hp:p id="2147483648" paraPrIDRef="13" styleIDRef="0" '
                    'pageBreak="0" columnBreak="0" merged="0">'
                    '<hp:run charPrIDRef="19"><hp:t>▲ %s</hp:t></hp:run></hp:p>'
                    % esc(cap), 'tbl_e')
    return out


# ══ 정리표 ═══════════════════════════════════════════════════
TBLW = 18850                  # 단폭 66.5mm
SHORT_CELL = 10.0             # 이 길이 이하 셀은 줄바꿈되면 안 된다
TBL_STAT = {'tables': 0, 'wrapped_short': 0, 'ragged': 0}
ROWH = 1500

TC_TPL = ('<hp:tc name="" header="%(hd)d" hasMargin="0" protect="0" editable="0" '
          'dirty="0" borderFillIDRef="%(bf)s"><hp:subList id="" '
          'textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
          'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" '
          'hasTextRef="0" hasNumRef="0">%(p)s</hp:subList>'
          '<hp:cellAddr colAddr="%(c)d" rowAddr="%(r)d"/>'
          '<hp:cellSpan colSpan="1" rowSpan="1"/>'
          '<hp:cellSz width="%(w)d" height="%(h)d"/>'
          '<hp:cellMargin left="210" right="210" top="141" bottom="141"/></hp:tc>')


PARAS = []                       # (kind, key, text) — 조판 순서대로
TIGHTEN = {}
_tf = os.path.join(HERE, 'tighten.json')
if os.path.exists(_tf):
    TIGHTEN = json.load(io.open(_tf, encoding='utf-8'))


def pkey(t):
    return re.sub(r'\s+', '', re.sub(r'#=.*?=#|==|__', '', str(t)))[:44]


def note(kind, text):
    """문단 하나를 기록하고, 압축 지시가 있으면 단계를 돌려준다"""
    k = pkey(text)
    PARAS.append((kind, k, str(text)))
    return TIGHTEN.get(k)


def cp_at(base, level):
    """압축 단계 적용 글자모양"""
    if level is None or base not in TIGHTCP:
        return base
    return TIGHTCP[base][min(level, len(TIGHT_STEPS) - 1)]


def _visw(t):
    """한글 한 글자를 1.0, 영숫자·기호를 0.55 로 본 시각 폭"""
    return sum(1.0 if ord(ch) > 0x1100 else 0.55 for ch in str(t))


def _balance(text, colw, cp, pt=7.3):
    """셀 안에서 두 줄이 될 글은 어절 경계에서 균형을 잡아 준다.
    두 줄 길이를 비슷하게 하되 첫 줄이 조금 더 길게 끊는다."""
    r = runs(text, base=cp, hi='28', pt=pt)
    # 강조·수식 표기 한가운데를 자르면 마크업이 깨진다 — 그런 글은 건드리지 않는다
    if '#=' in text or '==' in text or '__' in text or '\n' in text:
        return r
    avail = colw - 2 * 210 - 60
    v = _visw(text)
    need = v * pt * 100
    if need <= avail or need > avail * 2:      # 한 줄이거나 세 줄 이상
        return r
    words = text.split(' ')
    if len(words) < 2:
        return r
    target = min(avail * 0.97, need * 0.56)    # 첫 줄을 살짝 길게
    cands, acc = [], 0.0
    for i, w in enumerate(words[:-1]):
        acc += _visw(w + ' ') * pt * 100
        if acc > avail:
            break
        rest = _visw(' '.join(words[i + 1:])) * pt * 100
        if rest > avail:                       # 둘째 줄이 한 줄에 안 들어감
            continue
        cands.append((abs(acc - target), i + 1, acc))
    if not cands:
        return r
    cands.sort()
    _, cut, first = cands[0]
    if first < avail * 0.55 or first <= _visw(' '.join(words[cut:])) * pt * 100:
        return r                               # 첫 줄이 짧거나 둘째보다 짧으면 그냥 둔다
    a = ' '.join(words[:cut])
    b = ' '.join(words[cut:])
    return (runs(a, base=cp, hi='28', pt=pt)
            + '<hp:run charPrIDRef="%s"><hp:lineBreak/></hp:run>' % cp
            + runs(b, base=cp, hi='28', pt=pt))


def _fit_cp(text, colw, base_cp, pt=7.3):
    """폭을 조금 넘길 때 자간·장평을 조여 한 줄에 넣는다.
    항목명처럼 짧은 글은 조금 더 조여서라도 붙이고,
    크게 넘치는 서술은 건드리지 않는다(여러 줄이 정상)."""
    if base_cp not in TIGHTCP:
        return base_cp
    v = _visw(text)
    if v <= 0:
        return base_cp
    avail = colw - 2 * 210 - 60
    need = v * pt * 100
    if need <= avail:
        return base_cp                       # 이미 한 줄
    tol = 1.16 if v <= SHORT_CELL else 1.12
    if need > avail * tol:
        return base_cp                       # 줄바꿈이 자연스러운 분량
    for i, f in enumerate(TIGHT_FACTOR[base_cp]):
        if need * f <= avail:
            return TIGHTCP[base_cp][i]
    return base_cp


def _fits_after_tighten(text, colw, base_cp, pt=7.3):
    """압축까지 하면 한 줄에 들어가는가 (집계용)"""
    return _fit_cp(text, colw, base_cp, pt) != base_cp or \
        _visw(text) * pt * 100 <= colw - 2 * 210 - 60


ANSMARKS = {'답', '정답', 'O', '○', '●', '√', 'v', 'V'}


def make_table(tbl, last=True):
    head = tbl.get('head') or []
    rows = [list(r) for r in (tbl.get('rows') or [])]
    if not head or not rows:
        return ''
    # 「비고」 처럼 답 표시만 들어 있는 열은 지면에 둘 이유가 없다
    drop = []
    for c in range(len(head)):
        vals = [str(r[c]).strip() if c < len(r) else '' for r in rows]
        filled = [v for v in vals if v]
        if filled and all(v in ANSMARKS for v in filled):
            drop.append(c)
    if drop and len(drop) < len(head):
        head = [h for c, h in enumerate(head) if c not in drop]
        rows = [[v for c, v in enumerate(r) if c not in drop] for r in rows]
    nc = len(head)

    # 열 폭은 소스의 w(HTML 용 픽셀값)를 버리고 실제 내용 길이로 잡는다.
    # 항목명처럼 짧은 열은 줄바꿈 없이 들어가야 하므로 폭을 먼저 확보하고,
    # 남는 폭을 서술 열에 비례 배분한다.
    CHARW, PAD, FLOOR = 730, 480, 2400
    cols = [[head[c]] + [(r[c] if c < len(r) else '') for r in rows]
            for c in range(nc)]
    need = [max(1.5, max(_visw(x) for x in cols[c])) for c in range(nc)]

    def _bad(cwx):
        """보기 나쁜 정도 — 짧은 항목명이 깨지면 크게, 긴 서술의 토막은 작게"""
        n = 0.0
        for c in range(nc):
            a = cwx[c] - PAD
            if a < 900:
                return 10 ** 6
            for t in cols[c]:
                vc = _visw(t)
                v = vc * CHARW
                if v <= a:
                    continue
                if vc <= SHORT_CELL:
                    n += 4.0        # 항목명이 줄바꿈되는 것 자체가 문제
                    continue
                lines = int(v / a) + (1 if v % a else 0)
                last = v - (lines - 1) * a
                if last < a * 0.40:
                    n += 1.0
        return n

    tot = float(sum(need)) or 1.0
    cw = [max(FLOOR, int(TBLW * x / tot)) for x in need]
    cw[-1] = TBLW - sum(cw[:-1])

    # ① 짧은 항목이 줄바꿈되지 않는 「딱 맞는 폭」으로 한 번에 뛰어 본다
    best = _bad(cw)
    short_need = []
    for c in range(nc):
        sh = [_visw(t) for t in cols[c] if _visw(t) <= SHORT_CELL]
        short_need.append(max(sh) if sh else 0.0)
    for c in sorted(range(nc), key=lambda x: -short_need[x]):
        if short_need[c] <= 0:
            continue
        target = int(short_need[c] * CHARW) + PAD + 40
        if target <= cw[c] or target > TBLW * 0.55:
            continue
        others = [x for x in range(nc) if x != c]
        pool = sum(max(0, cw[x] - FLOOR) for x in others)
        delta = target - cw[c]
        if pool < delta:
            continue
        trial = list(cw)
        trial[c] = target
        for x in others:
            trial[x] -= int(delta * max(0, cw[x] - FLOOR) / pool)
        trial[others[-1]] += TBLW - sum(trial)
        if min(trial) >= FLOOR and _bad(trial) <= best:
            cw, best = trial, _bad(trial)

    # ② 그 다음 150씩 주고받으며 미세 조정
    STEP = 150
    for _ in range(200):
        moved = False
        for i in range(nc):
            for j in range(nc):
                if i == j or cw[i] - STEP < FLOOR:
                    continue
                trial = list(cw)
                trial[i] -= STEP
                trial[j] += STEP
                sc = _bad(trial)
                if sc < best:
                    cw, best, moved = trial, sc, True
        if not moved:
            break

    def cell(txt, r, c, hd):
        if hd:
            bf = '24' if c == 0 else ('26' if c == nc - 1 else '25')
            pp, st, cp = '29', '34', '89'          # 학습포인트-표구분 (가운데)
        elif c == 0:
            bf = '28'
            pp, st, cp = '29', '34', '89'
        else:
            bf = '10'
            pp, st, cp = CELL_PP, CELL_ST, '88'    # 표내용 — 가운데정렬 사본
        cp2 = _fit_cp(str(txt), cw[c], cp)
        body = _balance(str(txt), cw[c], cp2)
        para = ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" '
                'pageBreak="0" columnBreak="0" merged="0">%s</hp:p>'
                % (pp, st, body))
        return TC_TPL % dict(hd=1 if hd else 0, bf=bf, p=para, c=c, r=r,
                             w=cw[c], h=ROWH)

    TBL_STAT['tables'] += 1
    for c in range(nc):
        a = cw[c] - PAD
        for t in cols[c]:
            vc, v = _visw(t), _visw(t) * CHARW
            if v <= a:
                continue
            if vc <= SHORT_CELL:
                cpx = '89' if c == 0 else '88'
                if not _fits_after_tighten(str(t), cw[c], cpx):
                    TBL_STAT['wrapped_short'] += 1
            else:
                lines = int(v / a) + (1 if v % a else 0)
                if v - (lines - 1) * a < a * 0.40:
                    TBL_STAT['ragged'] += 1

    trs = ['<hp:tr>' + ''.join(cell(head[c], 0, c, True)
                               for c in range(nc)) + '</hp:tr>']
    for i, row in enumerate(rows):
        row = (list(row) + [''] * nc)[:nc]
        trs.append('<hp:tr>' + ''.join(cell(row[c], i + 1, c, False)
                                       for c in range(nc)) + '</hp:tr>')
    nr = len(rows) + 1
    tblxml = ('<hp:tbl id="0" zOrder="0" numberingType="TABLE" '
              'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
              'dropcapstyle="None" pageBreak="CELL" repeatHeader="1" '
              'rowCnt="%d" colCnt="%d" cellSpacing="0" borderFillIDRef="5" '
              'noAdjust="0"><hp:sz width="%d" widthRelTo="ABSOLUTE" height="%d" '
              'heightRelTo="ABSOLUTE" protect="0"/>'
              '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" '
              'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
              'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" '
              'horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/>'
              '<hp:inMargin left="210" right="210" top="141" bottom="141"/>%s</hp:tbl>'
              % (nr, nc, TBLW, nr * ROWH, ''.join(trs)))

    out = ''
    if tbl.get('cap'):
        # 왼쪽정렬 + 다음 문단과 함께 → 표와 떨어지지 않으면서 글자도 안 늘어난다
        out += ('<hp:p id="2147483648" paraPrIDRef="%s" styleIDRef="%s" '
                'pageBreak="0" columnBreak="0" merged="0">'
                '<hp:run charPrIDRef="90"><hp:t>%s</hp:t></hp:run></hp:p>'
                % (LEFT_PP, TITLE_LEFT_ST, esc(tbl['cap'])))
    out += repp('<hp:p id="2147483648" paraPrIDRef="13" styleIDRef="0" pageBreak="0" '
                'columnBreak="0" merged="0"><hp:run charPrIDRef="9">%s</hp:run></hp:p>'
                % tblxml, 'tbl_e' if last else 'tblk')
    return out


ICON = strip_lineseg(re.sub(r'\s+xmlns:\w+="[^"]*"', '', F_ICON))
WLAB = strip_lineseg(re.sub(r'\s+xmlns:\w+="[^"]*"', '', F_WLAB))
GAPS = {}
_gf = os.path.join(HERE, 'gaps.json')
if os.path.exists(_gf):
    GAPS = json.load(io.open(_gf, encoding='utf-8'))
GAP_IDX = [0]                       # 몇 번째 간격인지 세는 카운터


def gap():
    i = GAP_IDX[0]
    GAP_IDX[0] += 1
    lv = int(GAPS.get(str(i), 0))
    lv = max(0, min(lv, len(GAP_PTS) - 1))
    return ('<hp:p id="2147483648" paraPrIDRef="43" styleIDRef="0" pageBreak="0" '
            'columnBreak="0" merged="0"><hp:run charPrIDRef="%s">'
            '<hp:t></hp:t></hp:run></hp:p>' % GAP_CP[lv])


# ══ 본문 조립 ════════════════════════════════════════════════
qs = json.load(io.open(os.path.join(HERE, 'R01.json'), encoding='utf-8-sig'))
qs.sort(key=lambda q: (q['s'], q['n']))
if LIMIT:
    qs = [q for q in qs if q['s'] == 1][:LIMIT]

MEM_CLEAN = re.compile(r'^[「\s]*|[」\s]*$')


def concept_of(q):
    """kn 의 「법령 — 개념명」 중 개념명. 없으면 topic"""
    kn = q.get('kn') or ''
    if '—' in kn:
        c = kn.split('—', 1)[1].strip()
        if c:
            return c
    return q.get('topic') or ''


def law_of(q):
    """kn 의 법령 근거 부분"""
    return (q.get('kn') or '').split('—')[0].strip()


RX_LAW = re.compile(r'제\s*\d+\s*조|별표|시행령|시행규칙|고시|안전보건규칙|[가-힣]+법(?:령)?\b')


def split_ref(q):
    """(근거 줄, 풀이 줄) — 없으면 빈 문자열"""
    kn = (q.get('kn') or '').strip()
    law = kn.split('—')[0].strip()
    key = (q.get('key') or '').strip()
    if not RX_LAW.search(law):
        # 법령이 아니라 개념 요약이면 근거 줄을 만들지 않는다.
        # 그 요약이 key 첫머리와 겹치면(같은 말 반복) 버린다.
        if law and key:
            key = lead_off(key)
            headword = re.sub(r'[^가-힣A-Za-z0-9]', '', law)[:4]
            if headword and headword in re.sub(r'[^가-힣A-Za-z0-9]', '', key[:24]):
                return '', key
            return '', law.rstrip(' .,') + ' — ' + key
        return '', lead_off(law or key)
    # key 안에서 되풀이되는 법령 조각을 덜어 낸다
    for piece in re.split(r'[·,]', law):
        piece = piece.strip()
        if len(piece) >= 4:
            key = key.replace(piece, '')
    key = re.sub(r'^\s*[.,·)]\s*', '', key)
    key = re.sub(r'\s{2,}', ' ', key).strip()
    # 조문 제목 「(…)」 은 근거 줄로 올린다
    m = re.match(r'^(\([^)]*\)[^.]{0,20}\.?)\s*(.*)$', key, re.S)
    head, tail = (m.group(1), m.group(2)) if m else ('', key)
    line = (law + (' ' + head.strip().rstrip('.,') if head else '')).strip()
    return line.rstrip(' ,.·'), lead_off(tail.strip())


RX_LEAD = re.compile(r'^(?:[가-힣]{1,3}\s*가지|네\s*가지|세\s*가지|두\s*가지|'
                     r'[0-9]+\s*가지|의?\s*비교|의?\s*구분|의?\s*종류)[.·]?\s*')


def lead_off(t):
    """「네 가지.」 처럼 앞말과 겹치는 도입구는 뗀다"""
    return RX_LEAD.sub('', t).strip()


def as_lines(t):
    """여러 문장이면 문장마다 줄을 나눈다 (수식·강조 안은 건드리지 않는다)"""
    if not t:
        return []
    parts, buf, depth = [], '', 0
    i = 0
    while i < len(t):
        ch = t[i]
        if t.startswith('#=', i) or t.startswith('==', i) or t.startswith('__', i):
            tok = t[i:i + 2]
            j = t.find(tok if tok != '#=' else '=#', i + 2)
            j = len(t) if j < 0 else j + 2
            buf += t[i:j]
            i = j
            continue
        buf += ch
        if ch == '.' and i + 1 < len(t) and t[i + 1] == ' ':
            parts.append(buf.strip())
            buf = ''
            i += 2
            continue
        i += 1
    if buf.strip():
        parts.append(buf.strip())
    return [x for x in parts if x]


def repp(xml, key):
    """문단의 문단모양·스타일을 변형 사본으로 갈아끼운다(첫 문단만)"""
    pp, st = VAR[key]
    return re.sub(r'paraPrIDRef="\d+" styleIDRef="\d+"',
                  'paraPrIDRef="%s" styleIDRef="%s"' % (pp, st), xml, count=1)


def build_q(q):
    out = []
    hits = len(q['src'].split('·'))
    stars = 3 if hits >= 3 else (2 if hits == 2 else 1)
    out.append(make_num(q['n'], stars))
    out.append(p_stem(q['t']))
    if q.get('qfig'):                      # 발문 그림 (R01 에는 없음)
        out.append(make_fig(q['qfig']))

    ch = q['c']
    short = all(len(x) <= 14 for x in ch)
    if short:
        out.append(p_choice2(MARK[0], ch[0], MARK[1], ch[1]))
        out.append(p_choice2(MARK[2], ch[2], MARK[3], ch[3]))
    else:
        for i, x in enumerate(ch):
            out.append(p_choice(MARK[i], x))

    # ── 덩어리 B : 해설 약물 + 해설 본문 (+ 정리표 + 그림) ──
    out.append(repp(ICON, 'icon0'))
    paras = [x for x in re.split(r'\n+', q['sol']) if x.strip()]
    has_tbl, has_fig = bool(q.get('tbl')), bool(q.get('fig'))
    for i, para in enumerate(paras):
        # 표·그림은 각자 흐르게 둔다 — 다 묶으면 못 들어가 빈 단이 커진다
        out.append(repp(p_sol(para.strip()), 'sol_e' if i == len(paras) - 1 else 'sol1'))
    if has_tbl:
        out.append(make_table(q['tbl'], last=True))
    if has_fig:                            # fig 는 해설 그림이다
        out.append(make_fig(q['fig'], (q.get('figcap') or '').split('—')[0].strip()))

    ws = q.get('w') or []
    if ws:
        out.append(repp(WLAB, 'icon0'))
        others = [i for i in range(4) if i != q['a'] - 1]
        _n = len(ws[:len(others)])
        for k, w in enumerate(ws[:_n]):
            _p = p_wrong(MARK[others[k]], w, k == 0, keep=(k < _n - 1))
            out.append(repp(_p, 'w_e') if k == _n - 1 else _p)

    # 학습포인트 박스 — mem 우선, 없으면 key
    body = []
    if q.get('mem'):
        body.append(('', q['mem']))
    _ref, _desc = split_ref(q)
    if _ref:
        body.append(('근거', _ref))
    _dl = as_lines(_desc)
    for _i, _ln in enumerate(_dl):
        body.append(('풀이' if _i == 0 else '', _ln))
    if q.get('old'):
        body.append(('주의', q['old']))
    if q.get('src'):
        body.append(('기출', q['src']))
    if body:
        out.append(make_box(q.get('topic') or '학습 Point', body))

    out.append(make_bar(concept_of(q), q['a']))
    out.append(gap())
    return ''.join(out)


body = []
CHUNKS = []                      # 녹화용 — (이름, XML) 덩어리
cur = None
for q in qs:
    if q['s'] != cur:
        cur = q['s']
        _b = make_band(SUBJECTS[cur], cur)
        body.append(_b)
        CHUNKS.append(('과목%d' % cur, _b))
    _x = build_q(q)
    body.append(_x)
    CHUNKS.append(('%03d' % q['n'], _x))

# 첫 문단: 원본 p0 에서 secPr 를 품은 run 과 linesegarray 만 남긴다
_root = ET.fromstring(SEC_RAW)
_p0 = [c for c in _root if c.tag == Q('hp', 'p')][0]
for _r in [c for c in _p0 if c.tag == Q('hp', 'run')][1:]:
    _p0.remove(_r)
ctrl_open = ser(_p0)

root_open = re.search(r'<hs:sec\b[^>]*>', SEC_RAW).group(0)

# secPr 를 품은 빈 문단을 따로 두면 헤드가 한 줄 내려간다.
# 그 안의 run 들을 첫 문단(과목 띠) 머리로 옮겨 붙인다.
_head_runs = re.sub(r'^<hp:p\b[^>]*>|</hp:p>$', '', ctrl_open)
_head_runs = re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>', '', _head_runs, flags=re.S)
if body:
    _m0 = re.match(r'(<hp:p\b[^>]*>)', body[0])
    if _m0:
        body[0] = _m0.group(1) + _head_runs + body[0][_m0.end():]
        ctrl_open = ''

section = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           + root_open + ctrl_open + ''.join(body) + '</hs:sec>')

# ══ 패키지 ═══════════════════════════════════════════════════
OUT = os.path.join(HERE, OUTNAME)
if os.path.exists(OUT):
    os.remove(OUT)

# 링크 EMF 를 임베드로
EMBED = {'image117': '빈출도-상.emf', 'image119': '빈출도-중.emf',
         'image124': '빈출도-하.emf', 'image118': '해설-해설.emf',
         'image120': '해설-상세풀이(작은).emf',      # 오답분석 알약
         'image4': '관련이론.emf', 'image5': '과목띠.emf'}
hpf = Z.read('Contents/content.hpf').decode('utf-8')
added = {}
for iid, fn in EMBED.items():
    src = os.path.join(LAYOUT, fn)
    if not os.path.exists(src):
        print('  ! EMF 없음:', fn); continue
    target = 'BinData/%s.emf' % iid
    added[target] = io.open(src, 'rb').read()
    hpf = re.sub(r'(<opf:item[^>]*id="%s"[^>]*href=")[^"]*("[^>]*isEmbeded=")0(")' % iid,
                 lambda mm: mm.group(1) + target + mm.group(2) + '1' + mm.group(3),
                 hpf)

# 섹션 1개만 남기도록 manifest/spine 정리
for i in range(1, 15):
    hpf = re.sub(r'<opf:item[^>]*id="section%d"[^>]*/>' % i, '', hpf)
    hpf = re.sub(r'<opf:itemref[^>]*idref="section%d"[^>]*/>' % i, '', hpf)
for i in range(2, 16):
    hpf = re.sub(r'<opf:item[^>]*id="masterpage%d"[^>]*/>' % i, '', hpf)

# container.rdf 에서 삭제한 섹션 참조 제거
rdf = Z.read('META-INF/container.rdf').decode('utf-8')
_dead = set('Contents/section%d.xml' % i for i in range(1, 15))
_parts = rdf.split('</rdf:Description>')
_keep = [c for c in _parts if not any(d in c for d in _dead)]
rdf = '</rdf:Description>'.join(_keep)

# 섹션 수 · 캐럿 위치를 1섹션 문서에 맞춘다
hdr_xml = Z.read('Contents/header.xml').decode('utf-8')
hdr_xml = hdr_xml.replace('secCnt="15"', 'secCnt="1"', 1)
for _old, _new in FONT_REMAP.items():
    hdr_xml = hdr_xml.replace('face="%s"' % _old, 'face="%s"' % _new)
# 과목띠용 9pt 글자모양 (charPr 27 복제 — id 는 연속이어야 한다)
_cm = re.search(r'<hh:charPr id="27".*?</hh:charPr>', hdr_xml, re.S)
_cx = _cm.group(0).replace('id="27"', 'id="%s"' % BAND_CP, 1)
_cx = re.sub(r'height="\d+"', 'height="1100"', _cx, count=1)
hdr_xml = hdr_xml.replace('</hh:charProperties>', _cx + '</hh:charProperties>', 1)
_cc = re.search(r'<hh:charProperties itemCnt="(\d+)"', hdr_xml)
hdr_xml = hdr_xml.replace('<hh:charProperties itemCnt="%s"' % _cc.group(1),
                          '<hh:charProperties itemCnt="%d"' % (int(_cc.group(1)) + 1), 1)

# 자간·장평 압축 사본 (한두 글자 넘침을 윗줄로 끌어올리는 용도)
_cp_add = []
for _b in TIGHT_BASES:
    _bm = re.search(r'<hh:charPr id="%s".*?</hh:charPr>' % _b, hdr_xml, re.S)
    _r0, _s0 = _base_metrics(_b)
    for _i, (_sd, _rd) in enumerate(TIGHT_STEPS):
        _t = _bm.group(0).replace('id="%s"' % _b, 'id="%s"' % TIGHTCP[_b][_i], 1)
        _t = re.sub(r'(<hh:ratio[^>]*?)hangul="-?\d+"',
                    lambda mm: mm.group(1) + 'hangul="%d"' % (_r0 + _rd), _t, count=1)
        _t = re.sub(r'(<hh:spacing[^>]*?)hangul="-?\d+"',
                    lambda mm: mm.group(1) + 'hangul="%d"' % (_s0 + _sd), _t, count=1)
        _cp_add.append(_t)
for _i, _pt in enumerate(GAP_PTS):
    _gm = re.search(r'<hh:charPr id="19".*?</hh:charPr>', hdr_xml, re.S)
    _g = _gm.group(0).replace('id="19"', 'id="%s"' % GAP_CP[_i], 1)
    _g = re.sub(r'height="\d+"', 'height="%d"' % (_pt * 100), _g, count=1)
    _cp_add.append(_g)
hdr_xml = hdr_xml.replace('</hh:charProperties>',
                          ''.join(_cp_add) + '</hh:charProperties>', 1)
_ca = re.search(r'<hh:charProperties itemCnt="(\d+)"', hdr_xml)
hdr_xml = hdr_xml.replace('<hh:charProperties itemCnt="%s"' % _ca.group(1),
                          '<hh:charProperties itemCnt="%d"'
                          % (int(_ca.group(1)) + len(_cp_add)), 1)

# 왼쪽정렬 문단모양·스타일 사본 (id 는 배열 인덱스라 연속이어야 한다)
_pp_add, _st_add = [], []
for _key, _bp, _bs, _al, _keep, _prev, _next in VARIANTS:
    _np, _ns = VAR[_key]
    _m = re.search(r'<hh:paraPr id="%s".*?</hh:paraPr>' % _bp, hdr_xml, re.S)
    _x = _m.group(0).replace('id="%s"' % _bp, 'id="%s"' % _np, 1)
    if _al:
        _x = re.sub(r'(<hh:align[^>]*?)horizontal="\w+"',
                    lambda mm: mm.group(1) + 'horizontal="%s"' % _al, _x, count=1)
    if _keep:
        _x = _x.replace('keepWithNext="0"', 'keepWithNext="1"', 1)
    if _prev is not None:
        _x = re.sub(r'(<hc:prev )value="-?\d+"',
                    lambda mm: mm.group(1) + 'value="%d"' % _prev, _x)
    if _next is not None:
        _x = re.sub(r'(<hc:next )value="-?\d+"',
                    lambda mm: mm.group(1) + 'value="%d"' % _next, _x)
    _pp_add.append(_x)
    _sm = re.search(r'<hh:style id="%s"[^>]*/>' % _bs, hdr_xml)
    _y = _sm.group(0).replace('id="%s"' % _bs, 'id="%s"' % _ns, 1)
    _y = re.sub(r'paraPrIDRef="\d+"', 'paraPrIDRef="%s"' % _np, _y, count=1)
    _y = re.sub(r'nextStyleIDRef="\d+"', 'nextStyleIDRef="%s"' % _ns, _y, count=1)
    _y = re.sub(r'name="([^"]*)"',
                lambda mm: 'name="%s(%s)"' % (mm.group(1), _key), _y, count=1)
    _st_add.append(_y)
hdr_xml = hdr_xml.replace('</hh:paraProperties>',
                          ''.join(_pp_add) + '</hh:paraProperties>', 1)
hdr_xml = hdr_xml.replace('</hh:styles>', ''.join(_st_add) + '</hh:styles>', 1)
_pc = re.search(r'<hh:paraProperties itemCnt="(\d+)"', hdr_xml)
hdr_xml = hdr_xml.replace('<hh:paraProperties itemCnt="%s"' % _pc.group(1),
                          '<hh:paraProperties itemCnt="%d"'
                          % (int(_pc.group(1)) + len(VARIANTS)), 1)
_sc = re.search(r'<hh:styles itemCnt="(\d+)"', hdr_xml)
hdr_xml = hdr_xml.replace('<hh:styles itemCnt="%s"' % _sc.group(1),
                          '<hh:styles itemCnt="%d"'
                          % (int(_sc.group(1)) + len(VARIANTS)), 1)

set_xml = Z.read('settings.xml').decode('utf-8')
set_xml = re.sub('listIDRef="[0-9]+"', 'listIDRef="0"', set_xml, count=1)

mani = Z.read('META-INF/manifest.xml').decode('utf-8')
def fix_mp(x):
    x = x.replace('2027 대비 독끝 전기기능사 필기', '2027 대비 독끝 산업안전기사 필기')
    x = x.replace('PART C 최신 8개년 기출문제', '기출 재배열 제1회')
    # 전기기능사 전용 인덱스 탭 — 외부링크가 깨져 열 때마다 팝업이 뜬다
    for _tag in ('container', 'pic'):
        while True:
            _m = re.search(r'<hp:%s\b' % _tag, x)
            if not _m:
                break
            _e = x.find('</hp:%s>' % _tag, _m.start())
            if _e < 0:
                break
            _e += len('</hp:%s>' % _tag)
            _blk = x[_m.start():_e]
            if 'binaryItemIDRef' not in _blk:
                break
            x = x[:_m.start()] + x[_e:]
    return x
MPS = {'Contents/masterpage0.xml': fix_mp(Z.read('Contents/masterpage0.xml').decode('utf-8')),
       'Contents/masterpage1.xml': fix_mp(Z.read('Contents/masterpage1.xml').decode('utf-8'))}

drop = re.compile(r'^Contents/(section([1-9]|1[0-4])|masterpage([2-9]|1[0-5]))\.xml$')
# 문항 그림을 패키지에 넣고 manifest 에 등록 (zip 쓰기 전에 끝내야 한다)
for _fname, _iid in FIGMAP.items():
    _tgt = 'BinData/%s.png' % _iid
    added[_tgt] = io.open(os.path.join(FIGDIR, _fname), 'rb').read()
    hpf = hpf.replace('</opf:manifest>',
                      '<opf:item id="%s" href="%s" media-type="image/png" '
                      'isEmbeded="1"/></opf:manifest>' % (_iid, _tgt), 1)

# 본문과 테두리채우기가 쓰는 이미지가 모두 임베드됐는지 확인한다
_used = set(re.findall(r'binaryItemIDRef="(\w+)"', section))
_bfids = set(re.findall(r'borderFillIDRef="(\d+)"', section))
_hdr_src = Z.read('Contents/header.xml').decode('utf-8')
for _b in _bfids:
    _m = re.search(r'<hh:borderFill id="%s".*?</hh:borderFill>' % _b, _hdr_src, re.S)
    if _m:
        _used |= set(re.findall(r'binaryItemIDRef="(\w+)"', _m.group(0)))
_linked = []
for _u in sorted(_used):
    _mm = re.search(r'<opf:item[^>]*id="%s"[^>]*>' % _u, hpf)
    if _mm and 'isEmbeded="0"' in _mm.group(0):
        _href = re.search(r'href="([^"]*)"', _mm.group(0)).group(1)
        _linked.append('%s -> %s' % (_u, _href.split(chr(92))[-1]))
if _linked:
    print('  ! 외부링크로 남은 이미지 %d개 (렌더 안 됨):' % len(_linked))
    for _l in _linked:
        print('      ', _l)
else:
    print('  이미지 참조 %d종 전부 임베드 확인' % len(_used))

def write_pkg(section_xml, out_path):
    if os.path.exists(out_path):
        os.remove(out_path)
    zo = zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED)
    zo.writestr('mimetype', Z.read('mimetype'), zipfile.ZIP_STORED)
    for it in Z.infolist():
        n = it.filename
        if n == 'mimetype' or drop.match(n):
            continue
        if n == 'Contents/section0.xml':
            zo.writestr(n, section_xml.encode('utf-8')); continue
        if n == 'Contents/content.hpf':
            zo.writestr(n, hpf.encode('utf-8')); continue
        if n in MPS:
            zo.writestr(n, MPS[n].encode('utf-8')); continue
        if n == 'META-INF/container.rdf':
            zo.writestr(n, rdf.encode('utf-8')); continue
        if n == 'Contents/header.xml':
            zo.writestr(n, hdr_xml.encode('utf-8')); continue
        if n == 'settings.xml':
            zo.writestr(n, set_xml.encode('utf-8')); continue
        zo.writestr(n, Z.read(n))
    for t, d in added.items():
        zo.writestr(t, d)
    zo.close()


def wrap(inner):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            + root_open + ctrl_open + inner + '</hs:sec>')


write_pkg(section, OUT)

print('표 %d개 · 짧은 셀 줄바꿈 %d · 마지막 줄 토막 %d'
      % (TBL_STAT['tables'], TBL_STAT['wrapped_short'], TBL_STAT['ragged']))
json.dump([{'kind': k, 'key': kk, 'text': t} for k, kk, t in PARAS],
          io.open(os.path.join(HERE, 'paras.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
print('문단 기록 %d개 → paras.json' % len(PARAS))
print('생성:', OUT)

if '--elems' in sys.argv:
    _k = sys.argv.index('--elems')
    _n = int(sys.argv[_k + 1]) if len(sys.argv) > _k + 1 else 10
    EDIR = os.path.join(HERE, '녹화', 'elems')
    if not os.path.isdir(EDIR):
        os.makedirs(EDIR)
    for _f in os.listdir(EDIR):
        os.remove(os.path.join(EDIR, _f))
    _cnt = 0
    for _q in qs[:_n]:
        if _q.get('tbl'):
            write_pkg(wrap(make_table(_q['tbl'])),
                      os.path.join(EDIR, 'q%03d_tbl.hwpx' % _q['n']))
            _cnt += 1
        _body = []
        if _q.get('mem'):
            _body.append(_q['mem'])
        _law = law_of(_q)
        _key = (_q.get('key') or '').strip()
        _ref = (_law + ' ' + _key).strip() if _law else _key
        if _ref:
            _body.append('근거 ' + _ref)
        if _q.get('old'):
            _body.append('주의 ' + _q['old'])
        if _q.get('src'):
            _body.append('기출 ' + _q['src'])
        if _body:
            write_pkg(wrap(make_box(_q.get('topic') or '학습 Point', _body)),
                      os.path.join(EDIR, 'q%03d_box.hwpx' % _q['n']))
            _cnt += 1
        write_pkg(wrap(make_bar(concept_of(_q), _q['a'])),
                  os.path.join(EDIR, 'q%03d_bar.hwpx' % _q['n']))
        _cnt += 1
    print('부품 조각 %d개 → %s' % (_cnt, EDIR))

if '--frags' in sys.argv:
    _k = sys.argv.index('--frags')
    _n = int(sys.argv[_k + 1]) if len(sys.argv) > _k + 1 else 20
    RECDIR = os.path.join(HERE, '녹화')
    if not os.path.isdir(RECDIR):
        os.makedirs(RECDIR)
    for _f in os.listdir(RECDIR):
        if _f.endswith('.hwpx'):
            os.remove(os.path.join(RECDIR, _f))
    write_pkg(wrap(''), os.path.join(RECDIR, 'seed.hwpx'))
    for _i, (_nm, _xml) in enumerate(CHUNKS[:_n]):
        write_pkg(wrap(_xml), os.path.join(RECDIR, 'c%03d_%s.hwpx' % (_i, _nm)))
    print('녹화 조각: seed + %d개 → %s' % (min(_n, len(CHUNKS)), RECDIR))
print('  문항 %d개 · 섹션 XML %.0f KB · EMF 임베드 %d' %
      (len(qs), len(section) / 1024, len(added)))
