# -*- coding: utf-8 -*-
"""산업안전기사 제1회 자동 조판 과정을 세로 모니터에서 녹화한다.

  python record_typeset.py            기본 21덩어리(과목띠 + 1과목 20문항)
  python record_typeset.py 41         41덩어리

문항 조각을 한글에 하나씩 이어 붙여, 문서가 실제로 쌓여 가는 과정을 담는다.
조각은 본편과 같은 header/BinData 를 쓰므로 결과물은 한 번에 만든 것과 같다.

record_build.py(기관별 10문항)의 교훈을 그대로 쓴다.
  · gdigrab 의 창 캡처(-i title=)는 한글에서 빈 화면만 나온다 → 화면 영역(-i desktop + offset)
  · SetForegroundWindow 는 포그라운드 탈취 방지에 막힌다 → HWND_TOPMOST 로 올린다
  · 좀비 Hwp 가 남아 있으면 COM 이 그쪽을 잡는다 → 먼저 정리
"""
import ctypes, os, pathlib, subprocess, sys, threading, time
import win32gui, win32con
import win32com.client as win32

HERE = pathlib.Path(__file__).parent.resolve()
REC = HERE / '녹화'
OUT = REC / '산업안전기사_제1회_자동조판.mp4'

MON = (1920, 0, 1080, 1920)     # 세로 모니터 (DISPLAY1)
STEP_SEC = 1.25                 # 문항 하나 붙이고 머무는 시간
HEAD_SEC = 2.5
TAIL_SEC = 4.0

ctypes.windll.user32.SetProcessDPIAware()


def kill_hwp():
    subprocess.run(['taskkill', '/F', '/IM', 'Hwp.exe'], capture_output=True)
    time.sleep(1.0)


def find_hwp():
    hits = []

    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h)
            if t and t.endswith('한글'):
                hits.append(h)
    win32gui.EnumWindows(cb, None)
    return hits


def close_popups():
    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h) or ''
            if '자동 업데이트' in t or ('업데이트' in t and '한컴' in t):
                win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
    win32gui.EnumWindows(cb, None)


class Keeper(threading.Thread):
    """한글 창을 세로 모니터에 딱 맞춰 맨 앞에 붙잡아 둔다."""
    daemon = True

    def __init__(self):
        super().__init__()
        self.stop = threading.Event()
        self.hwnd = None

    def run(self):
        x, y, w, h = MON
        while not self.stop.is_set():
            hits = find_hwp()
            if hits:
                self.hwnd = hits[0]
                try:
                    win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                    win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST,
                                          x, y, w, h, win32con.SWP_SHOWWINDOW)
                except Exception:
                    pass
            close_popups()
            self.stop.wait(1.5)

    def release(self):
        self.stop.set()
        if self.hwnd:
            try:
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            except Exception:
                pass


def start_ffmpeg():
    OUT.unlink(missing_ok=True)
    x, y, w, h = MON
    return subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error',
         '-f', 'gdigrab', '-framerate', '12',
         '-offset_x', str(x), '-offset_y', str(y),
         '-video_size', '%dx%d' % (w, h), '-i', 'desktop',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
         '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT)],
        stdin=subprocess.PIPE)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 21

    # ① 조각 만들기 (녹화 전에 끝낸다)
    print('조각 생성 …')
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    subprocess.run([sys.executable, str(HERE / 'build.py'), '0', '--frags', str(n)],
                   env=env, capture_output=True, text=True,
                   encoding='utf-8', errors='replace')
    frags = sorted(f for f in os.listdir(REC)
                   if f.startswith('c') and f.endswith('.hwpx'))[:n]
    print('  %d개' % len(frags))

    kill_hwp()
    keeper = Keeper()
    keeper.start()

    hwp = win32.gencache.EnsureDispatch('HWPFrame.HwpObject')
    try:
        hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
    except Exception:
        pass
    hwp.XHwpWindows.Item(0).Visible = True
    hwp.Open(str(REC / 'seed.hwpx'), '', 'forceopen:true')
    try:
        hwp.HAction.Run('ViewZoomFitPage')
    except Exception:
        pass
    time.sleep(2.0)                       # 창이 자리를 잡을 때까지

    print('녹화 시작 — 세로 모니터 %dx%d' % (MON[2], MON[3]))
    ff = start_ffmpeg()
    time.sleep(HEAD_SEC)
    t0 = time.time()

    # ② 문항을 하나씩 이어 붙인다
    act = hwp.CreateAction('InsertFile')
    for i, f in enumerate(frags):
        hwp.HAction.Run('MoveDocEnd')
        pset = act.CreateSet()
        act.GetDefault(pset)
        pset.SetItem('FileName', str(REC / f))
        pset.SetItem('KeepSection', 0)
        pset.SetItem('KeepCharshape', 1)
        pset.SetItem('KeepParashape', 1)
        pset.SetItem('KeepStyle', 1)
        act.Execute(pset)
        hwp.HAction.Run('MoveDocEnd')
        time.sleep(STEP_SEC)
        if (i + 1) % 5 == 0:
            print('  %d/%d · %d쪽' % (i + 1, len(frags), hwp.PageCount))

    time.sleep(TAIL_SEC)
    took = time.time() - t0
    ff.communicate(b'q')
    keeper.release()
    pages = hwp.PageCount
    try:
        hwp.Clear(1)
        hwp.Quit()
    except Exception:
        pass
    kill_hwp()

    mb = OUT.stat().st_size / 1024 / 1024 if OUT.exists() else 0
    print('완료 · %d쪽 · %.1f분 · %s %.0fMB' % (pages, took / 60, OUT.name, mb))


if __name__ == '__main__':
    main()
