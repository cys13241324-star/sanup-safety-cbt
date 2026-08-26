# -*- coding: utf-8 -*-
"""CBT 화면을 실제로 눌러 본다. 화면이 도는지는 눌러 봐야 안다."""
import os
from playwright.sync_api import sync_playwright

OUT = (r'C:\Users\cheer\AppData\Local\Temp\claude\C--Users-cheer'
       r'\b528d127-0d20-46f0-9e00-05059e3e48c2\scratchpad')
EXE = (r'C:\Users\cheer\AppData\Local\ms-playwright\chromium-1234'
       r'\chrome-win64\chrome.exe')
CBT = 'file:///D:/safety-cbt/CBT_2026_1회/2026_1회_CBT.html'
CARD = 'file:///D:/safety-cbt/_암기카드.html'
MAIN = 'file:///D:/safety-cbt/_index.html'


def shot(pg, name):
    pg.screenshot(path=os.path.join(OUT, 'cbt_%s.png' % name))


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE)
        pg = b.new_page(viewport={'width': 900, 'height': 1250},
                        device_scale_factor=2)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))

        pg.goto(MAIN)
        pg.wait_for_timeout(700)
        shot(pg, '0_main')

        pg.goto(CBT)
        pg.wait_for_timeout(1200)
        pg.click('#go')
        pg.wait_for_timeout(900)
        shot(pg, '1_q1')

        # 시험 화면에서는 제출 전까지 해설이 없다
        pg.click('.opt:nth-of-type(2)')
        pg.wait_for_timeout(1200)
        shot(pg, '2_study')
        print('  제출 전 해설 노출:', pg.locator('.sol').count(), '(0이어야 정상)')

        # 문항표로 건너뛰기 — 수식이 많은 21번
        pg.click('#palbtn')
        pg.wait_for_timeout(300)
        pg.click('.pg[data-n="21"]')
        pg.wait_for_timeout(1200)
        shot(pg, '3_jump21')

        pg.evaluate("""() => {
          for (let n = 1; n <= 120; n++) S.ans[n] = (n % 4) + 1;
          save();
        }""")
        pg.once('dialog', lambda d: d.accept())
        pg.click('#sub')
        pg.wait_for_timeout(900)
        shot(pg, '4_result')
        print('  채점화면:', pg.locator('.score').inner_text().strip(),
              pg.locator('.verdict').inner_text().strip())

        # 틀린 문제만 다시 보기
        pg.click('#rw')
        pg.wait_for_timeout(900)
        shot(pg, '5_review')

        # 카드 뷰어 — 앞면 / 뒤집기
        pg.goto(CARD)
        pg.wait_for_timeout(1500)
        shot(pg, '6_card_front')
        print('  카드 위치:', pg.locator('#pos').inner_text().strip())
        pg.click('#cd')
        pg.wait_for_timeout(900)
        shot(pg, '7_card_back')

        # 문항 딥링크가 실제로 그 문제로 가는지
        href = pg.eval_on_selector('.ex a', 'a => a.getAttribute("href")')
        print('  카드→문항 링크:', href)
        pg.goto('file:///D:/safety-cbt/' + href.replace('#', '#'))
        pg.wait_for_timeout(1200)
        print('  건너간 문항:', pg.locator('.qno').inner_text().strip())
        shot(pg, '8_deeplink')

        print('  JS 오류:', errs or '없음')
        b.close()


if __name__ == '__main__':
    main()
