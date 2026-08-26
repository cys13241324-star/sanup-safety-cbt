# -*- coding: utf-8 -*-
"""검수본 페이지를 실제로 띄워 화면을 본다. 글자 검사만으로는 수식이 깨졌는지 모른다."""
import sys
import os
from playwright.sync_api import sync_playwright

OUT = r'C:\Users\cheer\AppData\Local\Temp\claude\C--Users-cheer' \
      r'\b528d127-0d20-46f0-9e00-05059e3e48c2\scratchpad'

TARGETS = [
    (r'D:\safety-cbt\CBT_2026_1회\2026_1회_검수본.html', 'r01', 0),
    (r'D:\safety-cbt\CBT_2026_1회\2026_1회_검수본.html', 'r01_calc', 1),
    (r'D:\safety-cbt\_index_검수본.html', 'index', -1),
]


def main():
    with sync_playwright() as p:
        # 설치돼 있는 크로미움을 그대로 쓴다 (playwright 판번호와 어긋나 있다)
        b = p.chromium.launch(executable_path=(
            r'C:\Users\cheer\AppData\Local\ms-playwright\chromium-1234'
            r'\chrome-win64\chrome.exe'))
        pg = b.new_page(viewport={'width': 900, 'height': 1400},
                        device_scale_factor=2)
        for path, name, mode in TARGETS:
            pg.goto('file:///' + path.replace('\\', '/'))
            pg.wait_for_timeout(2500)
            if mode == 1:
                # 수식이 많은 자리로 내려간다
                pg.evaluate("""() => {
                  const qs=[...document.querySelectorAll('.q')];
                  const t=qs.find(q=>q.querySelectorAll('.katex').length>3);
                  if(t) t.scrollIntoView();
                }""")
                pg.wait_for_timeout(600)
            pg.screenshot(path=os.path.join(OUT, 'shot_%s.png' % name))
            print('  ', name, pg.evaluate(
                "document.querySelectorAll('.katex-error').length"), '개 수식오류')
        b.close()


if __name__ == '__main__':
    main()
