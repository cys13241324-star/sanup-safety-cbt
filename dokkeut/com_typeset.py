# -*- coding: utf-8 -*-
"""한글 COM 으로 문항을 직접 찍어 넣는다 (녹화용).

  python com_typeset.py 10        1~10번

XML 을 만들어 한 번에 여는 build.py 와 달리, 여기서는 한글 안에서
스타일을 고르고 글자를 넣고 그림·표를 만든다 — 화면에 조판 과정이 그대로 남는다.

박스 배경 타일과 관련이론 바 EMF 는 COM 으로 붙이기 어려워
테두리 표로 대신한다. 최종 결과물은 build.py 쪽이 정본이다.
"""
import io, json, os, pathlib, re, subprocess, sys, time
import win32com.client as win32

HERE = pathlib.Path(__file__).parent.resolve()
LAYOUT = pathlib.Path(os.environ.get('DOKKEUT_LAYOUT', r'.\레이아웃'))
FIGDIR = pathlib.Path(os.environ.get('DOKKEUT_FIG', r'.\fig'))
ELEM = HERE / '녹화' / 'elems'

STYLE = {'번호': 15, '문제': 16, '문항': 18, '아이콘': 21, '해설': 23,
         '오답': 29, '박스제목': 31, '박스내용': 33, '관련이론': 37,
         '과목': 13, '바탕': 0,
         '표구분': 34,          # 학습포인트-표구분 (가운데)
         '표내용': 53}          # 학습포인트-표내용(가운데) — build.py 가 추가한 사본
STAR_EMF = {3: '빈출도-상.emf', 2: '빈출도-중.emf', 1: '빈출도-하.emf'}
MARK = ['①', '②', '③', '④']
ANSMARK = ['➊', '➋', '➌', '➍']
MAGENTA = 0xFF00FF                    # 한글은 BGR 정수 — #FF00FF 는 값이 같다
BLACK = 0x000000

TYPE_CHUNK = 24                       # 이만큼씩 끊어 넣어 찍히는 느낌을 준다
TYPE_PAUSE = 0.05
STEP_PAUSE = 0.12

EMPH = re.compile(r'#=(.+?)=#|==(.+?)==|__(.+?)__', re.S)

# 조각을 끼우면 그 문단모양이 뒤로 흘러 정렬이 틀어진다 — 스타일마다 못박는다
ALIGN = {'번호': 0, '문제': 0, '문항': 0, '아이콘': 0, '해설': 0, '오답': 0,
         '박스제목': 1, '박스내용': 0, '관련이론': 1, '과목': 1, '바탕': 0}


class Typesetter:
    def __init__(self, hwp):
        self.h = hwp

    # ── 기본 동작 ───────────────────────────────────────────
    def style(self, name):
        act = self.h.CreateAction('Style')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('Apply', STYLE[name])     # 'Apply' 가 스타일 인덱스다
        act.Execute(p)
        if name in ALIGN:
            self.align(ALIGN[name])

    def align(self, t):
        try:
            act = self.h.CreateAction('ParagraphShape')
            p = act.CreateSet()
            act.GetDefault(p)
            p.SetItem('AlignType', t)
            act.Execute(p)
        except Exception:
            pass

    def color(self, rgb):
        act = self.h.CreateAction('CharShape')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('TextColor', rgb)
        act.Execute(p)

    def put(self, text, typed=False):
        if not text:
            return
        if not typed or len(text) <= TYPE_CHUNK:
            self._put(text)
            return
        for i in range(0, len(text), TYPE_CHUNK):
            self._put(text[i:i + TYPE_CHUNK])
            time.sleep(TYPE_PAUSE)

    def _put(self, text):
        act = self.h.CreateAction('InsertText')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('Text', text)
        act.Execute(p)

    def br(self):
        self.h.HAction.Run('BreakPara')

    def tab(self):
        self.h.HAction.Run('InsertTab')

    def rich(self, text, typed=False):
        """==형광== · __밑줄__ 은 별색, #=수식=# 은 수식 개체로"""
        pos = 0
        for m in EMPH.finditer(text):
            if m.start() > pos:
                self.put(text[pos:m.start()], typed)
            if m.group(1) is not None:
                self.equation(m.group(1))
            else:
                self.color(MAGENTA)
                self.put(m.group(2) or m.group(3))
                self.color(BLACK)
            pos = m.end()
        if pos < len(text):
            self.put(text[pos:], typed)

    def equation(self, script):
        try:
            act = self.h.CreateAction('EquationCreate')
            p = act.CreateSet()
            act.GetDefault(p)
            p.SetItem('EqEdit', script.strip())
            p.SetItem('String', script.strip())
            act.Execute(p)
        except Exception:
            self.put(script.strip())

    def picture_fit(self, path, w_mm):
        """원본 비율을 지켜 폭 w_mm 으로 넣는다"""
        try:
            from PIL import Image
            im = Image.open(str(path))
            h_mm = w_mm * im.height / im.width
        except Exception:
            h_mm = w_mm * 0.4
        self.picture(path, w_mm, round(h_mm, 1))

    def picture(self, path, w, hgt):
        try:
            # sizeoption 1 = 원래 크기 무시하고 지정한 폭·높이로
            self.h.InsertPicture(str(path), True, 1, False, 0, 0, w, hgt)
        except Exception:
            try:
                self.h.InsertPicture(str(path), True, 1, False, 0, 0, False, w, hgt)
            except Exception:
                pass

    def insert(self, path):
        """완성된 조각(표·박스·바)을 그대로 끼워 넣는다"""
        if not os.path.exists(path):
            return False
        act = self.h.CreateAction('InsertFile')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('FileName', str(path))
        p.SetItem('KeepSection', 0)
        p.SetItem('KeepCharshape', 1)
        p.SetItem('KeepParashape', 1)
        p.SetItem('KeepStyle', 1)
        act.Execute(p)
        self.h.HAction.Run('MoveDocEnd')
        self.style('바탕')               # 조각의 문단모양이 뒤로 흐르지 않게
        return True

    def table(self, rows, cols):
        act = self.h.CreateAction('TableCreate')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('Rows', rows)
        p.SetItem('Cols', cols)
        p.SetItem('WidthType', 0)
        p.SetItem('WidthValue', 66.5)
        p.SetItem('HeightType', 0)
        act.Execute(p)

    def cell_next(self):
        self.h.HAction.Run('TableRightCell')

    def table_out(self):
        self.h.HAction.Run('CloseEx')
        self.h.HAction.Run('MoveDocEnd')

    # ── 문항 하나 ───────────────────────────────────────────
    def question(self, q):
        h = self.h
        hits = len(q['src'].split('·'))
        stars = 3 if hits >= 3 else (2 if hits == 2 else 1)

        # 번호 + 빈출도
        self.style('번호')
        self.put('%03d' % q['n'])
        self.tab()                      # paraPr 33 의 오른쪽 탭 정지점으로
        self.picture(LAYOUT / STAR_EMF[stars], 15.8, 2.8)
        self.br()
        time.sleep(STEP_PAUSE)

        # 발문
        self.style('문제')
        self.rich(q['t'], typed=True)
        self.br()
        time.sleep(STEP_PAUSE)

        # 보기 — 넷 다 짧으면 2×2, 아니면 1열
        self.style('문항')
        if all(len(x) <= 14 for x in q['c']):
            for a, b in ((0, 1), (2, 3)):
                self.put(MARK[a]); self.tab(); self.rich(q['c'][a])
                self.tab()
                self.put(MARK[b]); self.tab(); self.rich(q['c'][b])
                self.br()
                time.sleep(STEP_PAUSE)
        else:
            for i, c in enumerate(q['c']):
                self.put(MARK[i])
                self.tab()
                self.rich(c)
                self.br()
                time.sleep(STEP_PAUSE * 0.6)

        # 해설 약물
        self.style('아이콘')
        self.picture(LAYOUT / '해설-해설.emf', 12.4, 4.9)
        self.br()

        # 해설 본문
        self.style('해설')
        for para in [s for s in re.split(r'\n+', q['sol']) if s.strip()]:
            self.rich(para.strip(), typed=True)
            self.br()
            time.sleep(STEP_PAUSE)

        # 정리표 — 셀 채움색은 COM 으로 못 넣어 완성 조각을 쓴다
        if q.get('tbl'):
            self.style('바탕')
            self.insert(ELEM / ('q%03d_tbl.hwpx' % q['n']))
            time.sleep(STEP_PAUSE)

        # 해설 그림
        if q.get('fig'):
            fp = FIGDIR / q['fig']
            if fp.exists():
                self.style('바탕')
                self.picture_fit(fp, 60)
                self.br()
                if q.get('figcap'):
                    self.style('관련이론')
                    self.put('▲ ' + q['figcap'])
                    self.br()
                time.sleep(STEP_PAUSE)

        # 오답분석
        ws = q.get('w') or []
        if ws:
            self.style('박스제목')          # 7.8pt 굵은 고딕
            self.color(MAGENTA)
            self.put('오답분석')
            self.color(BLACK)
            self.br()
            self.style('오답')
            others = [i for i in range(4) if i != q['a'] - 1]
            for k, w in enumerate(ws[:len(others)]):
                self.put(MARK[others[k]])
                self.tab()
                self.rich(w)
                self.br()
                time.sleep(STEP_PAUSE * 0.6)

        # 학습 Point 박스 — 상/중/하 타일 배경이라 완성 조각을 쓴다
        self.style('바탕')
        self.insert(ELEM / ('q%03d_box.hwpx' % q['n']))
        time.sleep(STEP_PAUSE)

        # 관련이론 바 — 배경이 EMF 라 완성 조각을 쓴다
        self.style('바탕')
        self.insert(ELEM / ('q%03d_bar.hwpx' % q['n']))

        self.style('바탕')
        self.br()
        time.sleep(STEP_PAUSE * 2)

    def data_table(self, tbl):
        head = tbl.get('head') or []
        rows = tbl.get('rows') or []
        if not head or not rows:
            return
        if tbl.get('cap'):
            self.style('박스제목')
            self.put(tbl['cap'])
            self.br()
        self.style('바탕')
        self.table(len(rows) + 1, len(head))
        first = True
        for ri, r in enumerate([head] + [list(x) for x in rows]):
            for c in range(len(head)):
                if not first:
                    self.cell_next()
                first = False
                self.style('표구분' if (ri == 0 or c == 0) else '표내용')
                self.put(str(r[c]) if c < len(r) else '')
        self.table_out()
        self.br()
        time.sleep(STEP_PAUSE)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    qs = json.load(io.open(HERE / 'R01.json', encoding='utf-8-sig'))
    qs = sorted(qs, key=lambda q: (q['s'], q['n']))[:n]

    subprocess.run(['taskkill', '/F', '/IM', 'Hwp.exe'], capture_output=True)
    time.sleep(1)
    hwp = win32.gencache.EnsureDispatch('HWPFrame.HwpObject')
    try:
        hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
    except Exception:
        pass
    hwp.XHwpWindows.Item(0).Visible = True
    hwp.Open(str(HERE / '녹화' / 'seed.hwpx'), '', 'forceopen:true')
    try:
        hwp.HAction.Run('ViewZoomFitPage')
    except Exception:
        pass

    ts = Typesetter(hwp)
    ts.style('과목')
    ts.put('제1과목  산업재해예방·안전보건교육')
    ts.br()

    t0 = time.time()
    for q in qs:
        ts.question(q)
        print('  %03d · %d쪽' % (q['n'], hwp.PageCount))

    print('%d문항 · %.0f초 · %d쪽' % (len(qs), time.time() - t0, hwp.PageCount))
    return hwp


if __name__ == '__main__':
    h = main()
    if '--save' in sys.argv:
        try:
            h.HAction.Run('Cancel')
        except Exception:
            pass
        h.HAction.Run('MoveDocEnd')
        out = str(HERE / '녹화' / 'com_test.hwpx')
        h.SaveAs(out, 'HWPX', '')
        print('saved', out)
    time.sleep(2)
    try:
        h.Clear(1); h.Quit()
    except Exception:
        pass
    subprocess.run(['taskkill', '/F', '/IM', 'Hwp.exe'], capture_output=True)
