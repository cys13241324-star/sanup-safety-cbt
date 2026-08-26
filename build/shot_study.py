# -*- coding: utf-8 -*-
"""학습 화면 — 해설 단추·암기카드 팝업·근거 법령이 실제로 도는지 눌러 본다."""
import os
from playwright.sync_api import sync_playwright

OUT = (r'C:\Users\cheer\AppData\Local\Temp\claude\C--Users-cheer'
       r'\b528d127-0d20-46f0-9e00-05059e3e48c2\scratchpad')
EXE = (r'C:\Users\cheer\AppData\Local\ms-playwright\chromium-1234'
       r'\chrome-win64\chrome.exe')
CBT = 'file:///D:/safety-cbt/CBT_2026_1회/2026_1회_학습.html'
EXAM = 'file:///D:/safety-cbt/CBT_2026_1회/2026_1회_CBT.html'


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE)
        pg = b.new_page(viewport={'width': 900, 'height': 1150},
                        device_scale_factor=2)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(CBT)
        pg.wait_for_timeout(800)
        pg.evaluate('() => localStorage.clear()')
        pg.reload()
        pg.wait_for_timeout(1000)
        print('  학습 화면 — 타이머:', pg.locator('#timer').count(),
              '· 제출단추:', pg.locator('#sub').count(), '(둘 다 0이어야 정상)')
        print('  해설단추:', pg.locator('#tsol').count(),
              '· 카드단추:', pg.locator('#tcard').count(),
              '· 해설 열림:', pg.locator('.sol').count())
        pg.screenshot(path=os.path.join(OUT, 'st_1_closed.png'))

        pg.click('#tsol')          # 답을 고르지 않고 해설만 열기
        pg.wait_for_timeout(900)
        print('  해설 열기 뒤:', pg.locator('.sol').count(),
              '·', pg.locator('#tsol').inner_text().strip())
        pg.screenshot(path=os.path.join(OUT, 'st_2_open.png'))

        pg.click('#tsol')          # 다시 닫기
        pg.wait_for_timeout(400)
        print('  해설 닫기 뒤:', pg.locator('.sol').count())

        # 답을 고르면 정오와 해설이 함께
        pg.click('.opt:nth-of-type(4)')
        pg.wait_for_timeout(900)
        print('  오답 고른 뒤:', pg.locator('.vline').inner_text().strip(),
              '· 해설:', pg.locator('.sol').count())

        # 카드 팝업
        pg.click('#tcard')
        pg.wait_for_timeout(900)
        print('  팝업 열림:', pg.locator('#modal.on').count(),
              '· 앞면:', pg.locator('.mq').inner_text().strip()[:40])
        pg.screenshot(path=os.path.join(OUT, 'st_3_card_front.png'))

        pg.click('#mcard')
        pg.wait_for_timeout(900)
        print('  뒤집힘:', pg.locator('.mcard.flip').count())
        pg.screenshot(path=os.path.join(OUT, 'st_4_card_back.png'))

        pg.keyboard.press('Escape')
        pg.wait_for_timeout(400)
        print('  Esc 닫힘:', pg.locator('#modal.on').count() == 0)

        # 근거 법령
        pg.click('#tsol'); pg.wait_for_timeout(800)
        print('  근거 법령 블록:', pg.locator('details.law').count())
        if pg.locator('details.law').count():
            pg.click('details.law > summary'); pg.wait_for_timeout(500)
            print('  조문 수:', pg.locator('.lawart').count(),
                  '· 시행일:', pg.locator('.lawart .eff').first.inner_text().strip())

        # 수식이 든 문항에서도
        pg.click('#palbtn')
        pg.wait_for_timeout(250)
        pg.click('.pg[data-n="21"]')
        pg.wait_for_timeout(900)
        pg.click('#tcard')
        pg.wait_for_timeout(1100)
        pg.click('#mcard')
        pg.wait_for_timeout(900)
        pg.screenshot(path=os.path.join(OUT, 'st_5_card_math.png'))
        print('  수식카드 오류:', pg.evaluate(
            "document.querySelectorAll('#modal .katex-error').length"))

        # 시험 화면에는 해설·카드 단추가 없어야 한다
        pg.goto(EXAM); pg.wait_for_timeout(900)
        pg.click('#go'); pg.wait_for_timeout(600)
        print('  시험 화면 — 해설단추:', pg.locator('#tsol').count(),
              '· 카드단추:', pg.locator('#tcard').count(),
              '· 타이머:', pg.locator('#timer').count())

        print('  JS 오류:', errs or '없음')
        b.close()


if __name__ == '__main__':
    main()
