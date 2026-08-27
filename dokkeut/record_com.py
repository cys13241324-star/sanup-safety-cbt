# -*- coding: utf-8 -*-
"""COM 직접 조판 과정을 세로 모니터에서 녹화한다.

  python record_com.py 10

한글 안에서 스타일을 고르고 글자를 찍고 그림·표를 넣는 과정이 그대로 담긴다.
"""
import ctypes, os, pathlib, subprocess, sys, threading, time
import win32gui, win32con

HERE = pathlib.Path(__file__).parent.resolve()
REC = HERE / '녹화'
REC.mkdir(exist_ok=True)
OUT = REC / '산업안전기사_제1회_COM조판.mp4'

MON = (1920, 0, 1080, 1920)     # 세로 모니터
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
            self.stop.wait(1.2)

    def release(self):
        self.stop.set()
        if self.hwnd:
            try:
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            except Exception:
                pass


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    env = dict(os.environ, PYTHONIOENCODING='utf-8')

    print('부품 조각 준비 …')
    subprocess.run([sys.executable, str(HERE / 'build.py'), '0', '--elems', str(n)],
                   env=env, capture_output=True, text=True,
                   encoding='utf-8', errors='replace')

    kill_hwp()
    for p in (OUT,):
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    keeper = Keeper()
    keeper.start()

    x, y, w, h = MON
    ff = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error',
         '-f', 'gdigrab', '-framerate', '12',
         '-offset_x', str(x), '-offset_y', str(y),
         '-video_size', '%dx%d' % (w, h), '-i', 'desktop',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
         '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT)],
        stdin=subprocess.PIPE)
    time.sleep(HEAD_SEC)

    t0 = time.time()
    r = subprocess.run([sys.executable, str(HERE / 'com_typeset.py'), str(n)],
                       env=env, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    took = time.time() - t0
    time.sleep(TAIL_SEC)
    ff.communicate(b'q')
    keeper.release()
    kill_hwp()

    print((r.stdout or '').strip())
    mb = OUT.stat().st_size / 1024 / 1024 if OUT.exists() else 0
    print('녹화 완료 · %.1f분 · %s %.0fMB' % (took / 60, OUT.name, mb))


if __name__ == '__main__':
    main()
