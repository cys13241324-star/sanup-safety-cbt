# -*- coding: utf-8 -*-
"""전 문항을 HTML 로 옮긴 뒤, 그 안의 수식을 모두 뽑아 파일로 낸다.
node katex_check.js 가 이 파일을 읽어 실제로 렌더해 본다."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset
import build_all
from render import rich, table, wrongs, point

RX = re.compile(r'\$\$(.+?)\$\$|\$(.+?)\$', re.S)


def unesc(s):
    return s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def main():
    recs = dataset.build()
    found = []
    for r in recs:
        parts = [rich(r['t']), build_all.solution_html(r),
                 wrongs(r['w'], r['a']), point(r['kn'], r['key'], r['mem'], r['old']),
                 '<br>'.join(rich(x, False) for x in r['qb']),
                 rich(r['figcap'], False)]
        parts += [rich(c, False) for c in r['c']]
        for html in parts:
            for m in RX.finditer(html):
                tex = m.group(1) if m.group(1) is not None else m.group(2)
                found.append({'code': r['code'], 'display': m.group(1) is not None,
                              'tex': unesc(tex)})
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_math.json')
    with open(out, 'w', encoding='utf-8') as fp:
        json.dump(found, fp, ensure_ascii=False)
    print('수식 %d 개 -> %s' % (len(found), out))


if __name__ == '__main__':
    main()
