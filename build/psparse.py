# -*- coding: utf-8 -*-
"""src/past/R##_S#.ps1 의 $QS += @{...} 해시테이블 리터럴 파서"""
import re, glob, os, json

class P:
    def __init__(self, s, i=0):
        self.s, self.i = s, i
    def ws(self):
        while self.i < len(self.s):
            ch = self.s[self.i]
            if ch in ' \t\r\n': self.i += 1
            elif ch == '#':  # 주석
                j = self.s.find('\n', self.i)
                self.i = len(self.s) if j < 0 else j+1
            else: break
    def string(self):
        assert self.s[self.i] == '"', self.s[self.i-30:self.i+30]
        self.i += 1
        out = []
        while True:
            ch = self.s[self.i]
            if ch == '`':                     # PowerShell 백틱 이스케이프
                nxt = self.s[self.i+1]
                out.append({'n':'\n','t':'\t','r':'\r','0':'\0'}.get(nxt, nxt))
                self.i += 2
            elif ch == '"':
                if self.i+1 < len(self.s) and self.s[self.i+1] == '"':
                    out.append('"'); self.i += 2   # "" = 리터럴 따옴표
                else:
                    self.i += 1; break
            else:
                out.append(ch); self.i += 1
        return ''.join(out)
    def value(self):
        self.ws()
        ch = self.s[self.i]
        if ch == '"': return self.string()
        if ch == '@':
            if self.s[self.i+1] == '(': return self.array()
            if self.s[self.i+1] == '{': return self.hash()
            raise ValueError('bad @ at %d' % self.i)
        m = re.match(r'-?[\d.]+', self.s[self.i:])
        if m:
            self.i += m.end()
            v = m.group(0)
            return int(v) if re.fullmatch(r'-?\d+', v) else float(v)
        m = re.match(r'\$\w+|\w+', self.s[self.i:])
        if m:
            self.i += m.end(); return m.group(0)
        raise ValueError('bad value at %d: %r' % (self.i, self.s[self.i:self.i+40]))
    def array(self):
        self.i += 2  # @(
        out = []
        while True:
            self.ws()
            if self.s[self.i] == ')': self.i += 1; break
            if self.s[self.i] == ',': self.i += 1; continue
            out.append(self.value())
        return out
    def hash(self):
        self.i += 2  # @{
        out = {}
        while True:
            self.ws()
            if self.s[self.i] == '}': self.i += 1; break
            if self.s[self.i] in ';,': self.i += 1; continue
            m = re.match(r'[A-Za-z_]\w*', self.s[self.i:])
            if not m: raise ValueError('bad key at %d: %r' % (self.i, self.s[self.i:self.i+40]))
            k = m.group(0); self.i += m.end()
            self.ws()
            assert self.s[self.i] == '=', (k, self.s[self.i-20:self.i+20])
            self.i += 1
            out[k] = self.value()
        return out

def parse_file(path):
    src = open(path, encoding='utf-8-sig').read()
    items, pos = [], 0
    for m in re.finditer(r'\$QS\s*\+=\s*', src):
        p = P(src, m.end())
        items.append(p.hash())
    return items

def load_all(root):
    rounds = {}
    for f in sorted(glob.glob(os.path.join(root, 'R[0-9][0-9]_S[1-6].ps1'))):
        b = os.path.basename(f)
        r = int(b[1:3])
        rounds.setdefault(r, []).extend(parse_file(f))
    return rounds

if __name__ == '__main__':
    import sys, collections
    root = r'D:\project\산업안전기사\산업안전기사\src\past'
    rounds = load_all(root)
    tot = sum(len(v) for v in rounds.values())
    print('rounds:', len(rounds), 'items:', tot)
    bad = [(r, len(v)) for r, v in sorted(rounds.items()) if len(v) != 120]
    print('회차별 120문항 아닌 것:', bad or '없음')
    keys = collections.Counter()
    for v in rounds.values():
        for it in v: keys.update(it.keys())
    print(dict(keys))
    # 무결성
    prob = 0
    for r, v in rounds.items():
        for it in v:
            if not it.get('t') or len(it.get('c') or []) != 4 or not (1 <= (it.get('a') or 0) <= 4):
                prob += 1; print('BAD', r, it.get('n'), str(it)[:120])
    print('결함 문항:', prob)
    json.dump({str(k): v for k, v in rounds.items()}, open(os.path.join(os.path.dirname(__file__), 'rounds.json'), 'w', encoding='utf-8'), ensure_ascii=False)
