# -*- coding: utf-8 -*-
"""한글(HWP) 수식 스크립트 -> LaTeX(KaTeX) 변환기.

원본 원고(src/past/R##_S#.ps1)의 #= ... =# / #{ ... }# 안은 한글 수식편집기
스크립트다. 이를 KaTeX 가 읽는 LaTeX 로 옮긴다.
"""
import re

SYM = {
    'times': r'\times', 'cdot': r'\cdot', 'cdots': r'\cdots', 'ldots': r'\ldots',
    'div': r'\div', 'pm': r'\pm', 'mp': r'\mp', 'prop': r'\propto',
    'sim': r'\sim', 'cup': r'\cup', 'cap': r'\cap',
    'fallingdotseq': r'\fallingdotseq', 'risingdotseq': r'\risingdotseq',
    'sum': r'\sum', 'prod': r'\prod', 'int': r'\int', 'infty': r'\infty',
    'leq': r'\le', 'geq': r'\ge', 'neq': r'\ne', 'approx': r'\approx',
    'equiv': r'\equiv', 'therefore': r'\therefore', 'because': r'\because',
    'alpha': r'\alpha', 'beta': r'\beta', 'gamma': r'\gamma', 'delta': r'\delta',
    'epsilon': r'\varepsilon', 'varepsilon': r'\varepsilon', 'zeta': r'\zeta',
    'eta': r'\eta', 'theta': r'\theta', 'iota': r'\iota', 'kappa': r'\kappa',
    'lambda': r'\lambda', 'mu': r'\mu', 'nu': r'\nu', 'xi': r'\xi',
    'rho': r'\rho', 'sigma': r'\sigma', 'tau': r'\tau', 'upsilon': r'\upsilon',
    'phi': r'\phi', 'varphi': r'\varphi', 'chi': r'\chi', 'psi': r'\psi',
    'omega': r'\omega', 'pi': r'\pi',
    'GAMMA': r'\Gamma', 'DELTA': r'\Delta', 'THETA': r'\Theta',
    'LAMBDA': r'\Lambda', 'SIGMA': r'\Sigma', 'OMEGA': r'\Omega',
    'PHI': r'\Phi', 'PSI': r'\Psi',
    'Delta': r'\Delta', 'Sigma': r'\Sigma', 'Omega': r'\Omega',
    'Phi': r'\Phi', 'Gamma': r'\Gamma', 'Lambda': r'\Lambda', 'Theta': r'\Theta',
}
FUNC = {'log', 'ln', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'exp',
        'sinh', 'cosh', 'tanh', 'arcsin', 'arccos', 'arctan'}
PREFIX = {'sqrt': r'\sqrt', 'bar': r'\bar', 'hat': r'\hat', 'vec': r'\vec',
          'dot': r'\dot', 'tilde': r'\tilde', 'rm': r'\mathrm', 'it': None}

CHAR = {
    'Ω': r'\Omega', 'Δ': r'\Delta', '△': r'\triangle',
    'μ': r'\mu', 'π': r'\pi', 'θ': r'\theta',
    'ε': r'\varepsilon', 'α': r'\alpha', 'β': r'\beta',
    'γ': r'\gamma', 'λ': r'\lambda', 'ρ': r'\rho',
    'σ': r'\sigma', 'τ': r'\tau', 'φ': r'\phi',
    'ω': r'\omega', 'Σ': r'\Sigma',
    '×': r'\times', '÷': r'\div', '·': r'\cdot',
    '±': r'\pm', '≤': r'\le', '≥': r'\ge', '≠': r'\ne',
    '≒': r'\fallingdotseq', '→': r'\rightarrow',
    '←': r'\leftarrow', '⇒': r'\Rightarrow',
    '−': '-', '–': '-', '—': '-',
    '％': r'\%', '%': r'\%',
    '℃': r'{}^{\circ}\mathrm{C}', '℉': r'{}^{\circ}\mathrm{F}',
    '∞': r'\infty', '∠': r'\angle', '∴': r'\therefore',
    '&': r'\&', '#': r'\#',
}

TOK = re.compile(
    r'(?P<ws>[ \t\r\n]+)'
    r'|(?P<num>\d+(?:\.\d+)?)'
    r'|(?P<word>[A-Za-z]+)'
    r'|(?P<han>[가-힣]+)'
    r'|(?P<lb>\{)|(?P<rb>\})'
    r'|(?P<op>->|<=|>=|\+-|-\+|.)', re.S)


def _lex(s):
    out, ws = [], False
    for m in TOK.finditer(s):
        k = m.lastgroup
        if k == 'ws':
            ws = True
            continue
        out.append((k, m.group(0), ws))
        ws = False
    return out


def _tree(toks, i=0):
    node = []
    while i < len(toks):
        k, v, ws = toks[i]
        if k == 'lb':
            sub, i = _tree(toks, i + 1)
            node.append(('grp', sub, ws))
            continue
        if k == 'rb':
            return node, i + 1
        node.append((k, v, ws))
        i += 1
    return node, i


def _unbrace(s):
    if len(s) > 1 and s[0] == '{' and s[-1] == '}':
        d = 0
        for j, ch in enumerate(s):
            if ch == '{':
                d += 1
            elif ch == '}':
                d -= 1
                if d == 0 and j != len(s) - 1:
                    return s
        return s[1:-1]
    return s


def _word(v):
    """낱말 하나의 서체.

    한글 수식편집기는 라틴 글자를 이탤릭으로 찍는다. 단위·원소기호(mA, kg, Al)와
    세 글자 이상 약어(MTBF, LFL)만 정체로 세우고, 두 글자 대문자(CV, EI, AB)는
    변수의 곱이므로 원본대로 이탤릭에 둔다.
    """
    if len(v) == 1:
        return v
    if any(c.islower() for c in v):
        return r'\mathrm{%s}' % v
    if len(v) >= 3:
        return r'\mathrm{%s}' % v
    return v


def _sym(v):
    if v in CHAR:
        return CHAR[v]
    if v == '~':
        return r'\,'
    if v == '->':
        return r'\rightarrow'
    if v == '<=':
        return r'\le'
    if v == '>=':
        return r'\ge'
    if v in ('+-', '-+'):
        return r'\pm'
    if v == '°':
        return r'^{\circ}'
    return v


def _atom(nodes, i):
    if i >= len(nodes):
        return '', i
    k, v, _ = nodes[i]
    if k == 'grp':
        return '{' + _conv(v) + '}', i + 1
    if k == 'op' and v in '+-':
        inner, j = _atom(nodes, i + 1)
        return v + _unbrace(inner), j
    if k == 'word':
        if v in SYM:
            return SYM[v], i + 1
        if v in PREFIX:
            return _one(nodes, i)
        if v in FUNC:
            return '\\' + v, i + 1
        return _word(v), i + 1
    if k == 'num':
        return v, i + 1
    if k == 'han':
        return r'\text{' + v + '}', i + 1
    return _sym(v), i + 1


def _one(nodes, i):
    v = nodes[i][1]
    cmd = PREFIX[v]
    arg, j = _atom(nodes, i + 1)
    if cmd is None:
        return _unbrace(arg), j
    return cmd + '{' + _unbrace(arg) + '}', j


def _plainword(n):
    return (n[0] == 'word' and len(n[1]) > 1 and n[1] not in SYM
            and n[1] not in FUNC and n[1] not in PREFIX
            and n[1] not in ('over', 'atop'))


def _conv(nodes):
    out = []
    i = 0
    while i < len(nodes):
        k, v, ws = nodes[i]

        if k == 'grp':
            out.append('{' + _conv(v) + '}')
            i += 1
            continue

        if k == 'han':
            buf, i = [v], i + 1
            while i < len(nodes) and nodes[i][0] == 'han':
                buf.append((' ' if nodes[i][2] else '') + nodes[i][1])
                i += 1
            out.append(r'\text{' + ''.join(buf) + '}')
            continue

        if k == 'word':
            if v == 'over':
                num = _unbrace(out.pop()) if out else ''
                den, i = _atom(nodes, i + 1)
                out.append(r'\dfrac{%s}{%s}' % (num, _unbrace(den)))
                continue
            if v == 'atop':
                num = _unbrace(out.pop()) if out else ''
                den, i = _atom(nodes, i + 1)
                out.append(r'{%s \atop %s}' % (num, _unbrace(den)))
                continue
            if v in PREFIX:
                s, i = _one(nodes, i)
                out.append(s)
                continue
            if v in SYM:
                out.append(SYM[v])
                i += 1
                continue
            if v in FUNC:
                out.append('\\' + v)
                i += 1
                continue
            buf, i = [v], i + 1
            while i < len(nodes) and nodes[i][2] and _plainword(nodes[i]):
                buf.append(nodes[i][1])
                i += 1
            out.append(_word(buf[0]) if len(buf) == 1
                       else r'\text{' + ' '.join(buf) + '}')
            continue

        if k == 'op' and v in ('^', '_'):
            # R_(병렬) 처럼 괄호로 묶어 쓴 첨자는 괄호째 한 덩이로 본다
            if i + 1 < len(nodes) and nodes[i + 1][:2] == ('op', '('):
                j, depth = i + 1, 0
                while j < len(nodes):
                    if nodes[j][:2] == ('op', '('):
                        depth += 1
                    elif nodes[j][:2] == ('op', ')'):
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                arg, i = _conv(nodes[i + 2:j]), j + 1
                arg = '(' + arg + ')'
            else:
                arg, i = _atom(nodes, i + 1)
            if not out:
                out.append('{}')
            out[-1] = out[-1] + v + '{' + _unbrace(arg) + '}'
            continue

        if k == 'op' and v == '~':
            prev_num = bool(out) and re.search(r'[\d}]$', out[-1]) is not None
            nxt = nodes[i + 1] if i + 1 < len(nodes) else None
            out.append(r'\sim' if (prev_num and nxt and nxt[0] == 'num') else r'\,')
            i += 1
            continue

        if k == 'op' and v == '°':
            out.append(r'^{\circ}' if out else r'{}^{\circ}')
            i += 1
            continue

        if k == 'num':
            out.append(v)
            i += 1
            continue

        out.append(_sym(v))
        i += 1
    return ' '.join(x for x in out if x != '')


def hwp2tex(s):
    if not s:
        return ''
    s = s.strip()
    if not s:
        return ''
    nodes, _ = _tree(_lex(s))
    out = re.sub(r'\s+', ' ', _conv(nodes)).strip()
    # 홑부호는 뒤 수에 붙인다  { - 7 } -> {-7}
    out = re.sub(r'(^|[{(\[=,])\s*([+-])\s+', r'\1\2', out)
    return out.strip()
