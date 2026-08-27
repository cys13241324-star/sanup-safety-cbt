# -*- coding: utf-8 -*-
"""설치된 폰트의 실제 패밀리 이름을 읽어 문서가 요구하는 이름과 대조"""
import os, glob, zipfile, re
from fontTools.ttLib import TTFont

DIRS = [os.path.join(os.environ['WINDIR'], 'Fonts'),
        os.path.join(os.environ['LOCALAPPDATA'], r'Microsoft\Windows\Fonts'),
        r'C:\Program Files (x86)\Hnc', r'C:\Program Files\Hnc']

WANT_KEYS = ('kopub', 'gmarket', '윤', 'yoon', 'ygo', 'din', 'pretendard', '산스')


def names(path):
    out = {}
    try:
        f = TTFont(path, fontNumber=0, lazy=True)
        for rec in f['name'].names:
            if rec.nameID in (1, 4, 16):
                try:
                    v = rec.toUnicode()
                except Exception:
                    continue
                out.setdefault(rec.nameID, set()).add(v)
        f.close()
    except Exception as e:
        return {'err': str(e)[:40]}
    return out


files = []
for d in DIRS:
    if os.path.isdir(d):
        for ext in ('ttf', 'otf', 'ttc', 'TTF', 'OTF'):
            files += glob.glob(os.path.join(d, '**', '*.' + ext), recursive=True)

seen = set()
rows = []
for p in files:
    b = os.path.basename(p)
    if b.lower() in seen:
        continue
    if not any(k in b.lower() or k in b for k in WANT_KEYS):
        continue
    seen.add(b.lower())
    n = names(p)
    fam = sorted(n.get(1, set()) | n.get(16, set()))
    full = sorted(n.get(4, set()))
    rows.append((b, fam, full))

print('== 설치 폰트의 실제 이름 ==')
for b, fam, full in sorted(rows):
    print('%-34s' % b)
    print('   family : %s' % ' | '.join(fam))
    print('   full   : %s' % ' | '.join(full))

# 문서가 요구하는 이름
Z = zipfile.ZipFile(r'..\hwpdump\partC.hwpx')
h = Z.read('Contents/header.xml').decode('utf-8')
want = sorted(set(re.findall(r'<hh:font id="\d+" face="([^"]*)"', h)))
print()
print('== 문서가 요구하는 서체 ==')
allnames = set()
for b, fam, full in rows:
    allnames |= set(fam) | set(full)
for w in want:
    mark = 'OK ' if w in allnames else '   '
    print('%s %s' % (mark, w))
