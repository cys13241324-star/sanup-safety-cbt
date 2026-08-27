# -*- coding: utf-8 -*-
"""
빌드가 남긴 문단 순서(paras.json)와 PDF 의 줄 스트림을 순차 정렬해
「마지막 줄이 한두 글자인 문단」을 정확히 집어낸다.
--write 를 주면 tighten.json 의 압축 단계를 한 칸씩 올린다.
"""
import fitz, json, io, re, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, '산업안전기사_제01회_독끝조판.pdf')
COL_W, COL_GAP, LEFT_ODD, LEFT_EVEN = 188.5, 28.3, 85.0, 70.9
def cols_of(pg):
    x0 = LEFT_ODD if pg % 2 == 0 else LEFT_EVEN
    return [(x0, x0 + COL_W), (x0 + COL_W + COL_GAP, x0 + 2 * COL_W + COL_GAP)]
COLS = cols_of(0)
MAXLEVEL = 4
TAIL_MAX = 2                      # 이 글자 수 이하로 끝나면 외톨이


def norm(t):
    t = re.sub(r'[-]', '', t)          # 수식 사설영역 글리프 제거
    return re.sub(r'\s+', '', t)


def clean(t):
    return norm(re.sub(r'#=.*?=#|==|__', '', str(t)))


def line_stream(doc):
    out = []
    for j in range(doc.page_count):
        rows = []
        for b in doc[j].get_text('dict')['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans'])
                if not t.strip():
                    continue
                x0 = l['bbox'][0]
                _cs = cols_of(j)
                col = 0 if x0 < _cs[0][1] + 10 else 1
                rows.append((col, round(l['bbox'][1], 1), x0, t, j + 1))
        rows.sort(key=lambda r: (r[0], r[1], r[2]))
        out += rows
    return out


def main():
    doc = fitz.open(PDF)
    lines = line_stream(doc)
    paras = json.load(io.open(os.path.join(HERE, 'paras.json'), encoding='utf-8'))

    ptr = 0
    orphans, aligned, skipped = [], 0, 0
    for pa in paras:
        tgt = clean(pa['text'])
        if len(tgt) < 14:
            continue
        if '#=' in pa['text']:                      # 수식 문단은 정렬 불가
            skipped += 1
            continue
        head = tgt[:10]
        start = None
        for i in range(ptr, min(ptr + 60, len(lines))):
            lt = norm(lines[i][3])
            lt = re.sub(r'^[①②③④➊➋➌➍]', '', lt)
            if not lt:
                continue
            if lt.startswith(head[:8]) or head.startswith(lt[:8]):
                start = i
                break
        if start is None:
            skipped += 1
            continue
        acc, used, before = '', 0, 0
        for i in range(start, min(start + 12, len(lines))):
            lt = norm(lines[i][3])
            lt = re.sub(r'^[①②③④➊➋➌➍]', '', lt)
            before = len(acc)
            acc += lt
            used += 1
            if len(acc) >= len(tgt):
                break
        aligned += 1
        ptr = start + used
        if used >= 2:
            tail = len(tgt) - before
            if 0 < tail <= TAIL_MAX:
                orphans.append({'key': pa['key'], 'kind': pa['kind'],
                                'page': lines[start][4], 'tail': tail,
                                'text': pa['text'][:56]})

    print('정렬된 문단 %d개 (건너뜀 %d)' % (aligned, skipped))
    print('마지막 줄이 %d글자 이하인 문단: %d개' % (TAIL_MAX, len(orphans)))
    print('종류별:', collections.Counter(o['kind'] for o in orphans).most_common())
    print()
    for o in orphans[:10]:
        print('  p%-3d %-6s 꼬리%d  %s' % (o['page'], o['kind'], o['tail'], o['text']))

    if '--write' in sys.argv:
        tf = os.path.join(HERE, 'tighten.json')
        cur = json.load(io.open(tf, encoding='utf-8')) if os.path.exists(tf) else {}
        n = 0
        for o in orphans:
            v = cur.get(o['key'], -1)
            if v < MAXLEVEL:
                cur[o['key']] = v + 1
                n += 1
            else:
                # 최대까지 조여도 안 붙는다 — 글자만 눌리므로 되돌린다
                cur[o['key']] = 0
        json.dump(cur, io.open(tf, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print()
        print('tighten.json: %d개 문단 단계 상향 (누적 %d개)' % (n, len(cur)))


main()
