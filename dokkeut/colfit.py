# -*- coding: utf-8 -*-
"""
단 하단 맞추기 — 각 단에서 남는 아래 공간을 그 단 안의 문항 사이로 흩어 넣는다.

  python colfit.py            현황만 본다
  python colfit.py --write    gaps.json 을 갱신한다

문항 번호(Bahnschrift 큰 숫자)로 문항의 단 위치를 잡고,
그 단의 마지막 내용 아래에 남은 공간을 같은 단 안의 간격들에 나눈다.
간격을 늘리면 뒤 내용이 밀리므로 한 번에 다 채우지 않고 눌러서 반복한다.
"""
import fitz, json, io, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, '산업안전기사_제01회_독끝조판.pdf')
GAPS = os.path.join(HERE, 'gaps.json')


TOP = 56.7                                  # 본문 상단 (20mm)
BOTTOM = 705.9                              # 본문 하단 (267-18mm)
GAP_PTS = [7, 9, 11, 13, 16, 19, 23, 27, 32, 38, 45, 53, 62, 72, 84]
LINE = 1.7                                  # 간격 문단 행간 배수
DAMP = 0.85                                 # 한 번에 채우는 비율
KEEP = 40.0                                 # 하단 목표 여백(pt) — 저장본 실측 35~55


COL_W = 188.5          # 단폭 66.5mm
COL_GAP = 28.3         # 단 사이 10mm
LEFT_ODD = 85.0        # 홀수 쪽 좌여백 30mm
LEFT_EVEN = 70.9       # 짝수 쪽 좌여백 25mm (제본 여백이 뒤집힌다)


def cols_of(page):
    x0 = LEFT_ODD if page % 2 == 0 else LEFT_EVEN   # page 는 0부터
    return [(x0, x0 + COL_W), (x0 + COL_W + COL_GAP, x0 + 2 * COL_W + COL_GAP)]


def col_of(x, page=0):
    for i, (a, b) in enumerate(cols_of(page)):
        if a - 10 <= x < b + 10:
            return i
    return None


def scan():
    d = fitz.open(PDF)
    qpos = {}                                # 문항번호 -> (page, col, y)
    bottoms = collections.defaultdict(float)  # (page, col) -> 마지막 내용 bottom
    for j in range(d.page_count):
        pg = d[j]
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                # 문항 번호는 앞자리(연분홍)와 뒷자리가 따로 찍힌다 — 줄 단위로 잇는다
                num = ''.join(s['text'] for s in l['spans']
                              if 'Bahnschrift' in s['font'] and s['size'] > 13)
                num = re.sub(r'\D', '', num)
                for s in l['spans']:
                    c = col_of(s['bbox'][0], j)
                    if c is None:
                        continue
                    if s['bbox'][3] > BOTTOM + 3:      # 꼬리말은 제외
                        continue
                    bottoms[(j, c)] = max(bottoms[(j, c)], s['bbox'][3])
                if len(num) == 3:
                    c = col_of(l['bbox'][0], j)
                    if c is not None:
                        qpos.setdefault(int(num), (j, c, l['bbox'][1]))
        for dr in pg.get_drawings():          # 표·박스 테두리도 내용이다
            r = dr['rect']
            c = col_of(r.x0, j)
            if c is not None and TOP <= r.y1 <= BOTTOM + 3:
                bottoms[(j, c)] = max(bottoms[(j, c)], r.y1)
        for im in pg.get_image_info():
            r = fitz.Rect(im['bbox'])
            c = col_of(r.x0, j)
            if c is not None and TOP <= r.y1 <= BOTTOM + 3:
                bottoms[(j, c)] = max(bottoms[(j, c)], r.y1)
    d.close()
    return qpos, bottoms


def main():
    qs = json.load(io.open(os.path.join(HERE, 'R01.json'), encoding='utf-8-sig'))
    qs = sorted(qs, key=lambda q: (q['s'], q['n']))
    qpos, bottoms = scan()

    # 간격 k(문항 k 뒤)는 「문항 k+1 이 시작하는 단」에 놓인다.
    # 그 단의 맨 위에서 시작한다면 간격이 단 넘김에 눌려 사라지므로 제외한다.
    percol = collections.defaultdict(list)   # (page,col) -> [gap index]
    for k in range(len(qs) - 1):
        b = qpos.get(qs[k + 1]['n'])
        if b and b[2] > TOP + 25:
            percol[(b[0], b[1])].append(k)

    cur = {}
    if os.path.exists(GAPS):
        cur = json.load(io.open(GAPS, encoding='utf-8'))

    used = [k for k in sorted(bottoms) if bottoms[k] > TOP + 20]
    lefts = []
    for key in used:
        room = BOTTOM - KEEP - bottoms[key]
        lefts.append(room)
    if lefts:
        print('단 %d개 · 하단 여백 평균 %.0fpt · 최대 %.0fpt · 20pt 초과 %d개'
              % (len(lefts), sum(lefts) / len(lefts), max(lefts),
                 sum(1 for x in lefts if x > 20)))

    if '--write' not in sys.argv:
        for key in used[:8]:
            print('  p%-3d 단%d  아래 여백 %.0fpt  간격 %d개'
                  % (key[0] + 1, key[1] + 1, BOTTOM - KEEP - bottoms[key],
                     len(percol.get(key, []))))
        return

    n = 0
    for key in used:
        gaps = percol.get(key, [])
        room = BOTTOM - KEEP - bottoms[key]
        if not gaps or room <= 12:
            continue
        add = room * DAMP / len(gaps)          # 간격 하나가 더 먹을 pt
        for g in gaps:
            lv = int(cur.get(str(g), 0))
            want = GAP_PTS[lv] + add / LINE
            best = min(range(len(GAP_PTS)), key=lambda i: abs(GAP_PTS[i] - want))
            if best != lv:
                cur[str(g)] = best
                n += 1
    json.dump(cur, io.open(GAPS, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('gaps.json: %d개 간격 조정 (누적 %d개)' % (n, len(cur)))


main()
