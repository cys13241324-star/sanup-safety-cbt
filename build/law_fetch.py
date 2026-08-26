# -*- coding: utf-8 -*-
"""법제처 국가법령정보 DRF 에서 오늘 시행 중인 판을 받아 laws.json 을 만든다.

target=law 로 받으면 「공포 기준」 최신본이 와서 아직 시행 전인 개정이 섞인다.
반드시 target=eflaw 로 시행일 목록을 받아, 오늘 이하의 가장 늦은 시행일을 고른다.
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_laws.json')
TODAY = date.today().strftime('%Y%m%d')

# (짧은 이름, 법제처 정식 명칭)  — 원고가 인용하는 순서대로
LAWS = [
    ('안전보건규칙', '산업안전보건기준에 관한 규칙'),
    ('산업안전보건법', '산업안전보건법'),
    ('시행령', '산업안전보건법 시행령'),
    ('시행규칙', '산업안전보건법 시행규칙'),
    ('산업재해보상보험법', '산업재해보상보험법'),
    ('중대재해처벌법', '중대재해 처벌 등에 관한 법률'),
    ('건설기술진흥법', '건설기술 진흥법'),
    ('위험물안전관리법', '위험물안전관리법'),
    ('고압가스안전관리법', '고압가스 안전관리법'),
    ('화학물질관리법', '화학물질관리법'),
    ('전기사업법', '전기사업법'),
    ('시설물안전법', '시설물의 안전 및 유지관리에 관한 특별법'),
]


def get(u, tries=3):
    for k in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}),
                timeout=90).read()
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(2)


def pick(name):
    """오늘 시행 중인 판의 (시행일, 법령일련번호, 공포번호)"""
    q = urllib.parse.quote(name)
    d = get('https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=eflaw&type=XML'
            '&display=100&search=1&query=%s' % q).decode('utf-8', 'replace')
    rows = [(m.group(4), m.group(1), m.group(3)) for m in re.finditer(
        r'<법령일련번호>(\d+)</법령일련번호>.*?<법령명한글><!\[CDATA\[(.*?)\]\]></법령명한글>'
        r'.*?<공포번호>(\d+)</공포번호>.*?<시행일자>(\d+)</시행일자>', d, re.S)
        if m.group(2).strip() == name]
    live = [r for r in rows if r[0] <= TODAY]
    if not live:
        return None, None, None, []
    ef, mst, no = max(live)
    future = sorted({r[0] for r in rows if r[0] > TODAY})
    return ef, mst, no, future


def articles(xml):
    """조문단위 -> [{no, branch, title, text}]"""
    out = []
    for jo in ET.fromstring(xml).iter('조문단위'):
        n = jo.find('조문번호')
        if n is None:
            continue
        no = ''.join(n.itertext()).strip()
        br = jo.find('조문가지번호')
        br = ''.join(br.itertext()).strip() if br is not None else ''
        t = jo.find('조문제목')
        title = ''.join(t.itertext()).strip() if t is not None else ''
        body = []
        head = jo.find('조문내용')
        if head is not None:
            body.append(''.join(head.itertext()))
        for hang in jo.iter('항'):
            for tag in ('항내용',):
                for e in hang.iter(tag):
                    body.append(''.join(e.itertext()))
            for ho in hang.iter('호'):
                for e in ho.iter('호내용'):
                    body.append('  ' + ''.join(e.itertext()).strip())
                for mok in ho.iter('목'):
                    for e in mok.iter('목내용'):
                        body.append('    ' + ''.join(e.itertext()).strip())
        lines = []
        for s in body:
            s = re.sub(r'[ \t]+', ' ', s.replace('　', ' ')).rstrip()
            if s.strip():
                lines.append(s)
        # 조문내용의 첫 줄은 「제139조(제목)」 이라 제목과 겹친다. 걷어낸다.
        # 다만 그 줄이 본문의 전부인 조문은 손대지 않는다(내용이 통째로 사라진다).
        if len(lines) > 1 and re.match(r'^\s*제\s?%s조' % re.escape(no), lines[0]):
            head_only = re.sub(r'^\s*제\s?\d+조(?:의\d+)?\s*(\([^)]*\))?\s*', '',
                               lines[0])
            if head_only.strip():
                lines[0] = head_only.strip()
            else:
                lines.pop(0)
        text = '\n'.join(lines).strip()
        if not text:
            continue
        out.append({'no': no, 'branch': br, 'title': title, 'text': text})
    return out


def main():
    laws = {}
    for short, name in LAWS:
        ef, mst, no, future = pick(name)
        if not mst:
            print('  !! %s — 시행 중인 판을 못 찾음' % name)
            continue
        xml = get('https://www.law.go.kr/DRF/lawService.do?OC=test&target=eflaw'
                  '&type=XML&MST=%s' % mst)
        arts = articles(xml)
        laws[short] = {'name': name, 'eff': ef, 'no': no,
                       'future': future, 'arts': arts}
        print('  %-14s %-28s 시행 %s 제%s호 · 조문 %d개%s'
              % (short, name, ef, no, len(arts),
                 ('  (시행 전 개정 %s)' % ', '.join(future)) if future else ''))
        time.sleep(0.4)
    with io.open(OUT, 'w', encoding='utf-8') as fp:
        json.dump(laws, fp, ensure_ascii=False)
    print('법령 %d종 -> %s' % (len(laws), OUT))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
