"""Checks the MAXScript files for two mistakes 3ds Max only reports when the script runs:
reserved words used as names (`local at = ...` is a syntax error) and string escapes MAXScript doesn't know
(only \\\\ \\n \\t \\r \\" are valid). Run: python tools/check_ms.py  (exit code 1 when something is found)."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KW = set("""about and animate as at by case catch collect continue coordsys do else exit fn for from function global if
in level local macroscript mapped max not of off on or parameters persistent plugin rcmenu return rollout set struct
then throw to tool try undo utility when where while with""".split())
STRING = re.compile(r'"(?:\\.|[^"\\])*"')


def names(line):
    """Names a line declares or assigns: locals, globals, loop variables, functions and their parameters."""
    out = [m.group(1) for m in re.finditer(r'\b(?:local|global)\s+(\w+)', line, re.I)]
    out += [m.group(1) for m in re.finditer(r'\bfor\s+(\w+)\s+(?:in|=)', line, re.I)]
    m = re.match(r'\s*(?:mapped\s+)?(?:fn|function)\s+(\w+)((?:\s+\w+(?::\S*)?)*)\s*=', line, re.I)
    if m:
        out.append(m.group(1))
        out += [p.split(":")[0] for p in m.group(2).split()]
    out += [m.group(1) for m in re.finditer(r'(?:^|[(;])\s*(\w+)\s*(?:\+|-|\*|/)?=(?!=)', line)]
    return out


def check(path):
    problems = []
    src = open(path, encoding="utf-8-sig").read()
    for m in STRING.finditer(src):
        for e in re.findall(r'\\(.)', m.group(0)[1:-1]):
            if e not in '\\ntr"':
                problems.append("line %d: unknown escape \\%s" % (src.count("\n", 0, m.start()) + 1, e))
    code = STRING.sub('""', src)
    code = re.sub(r'/\*.*?\*/', lambda m: "\n" * m.group(0).count("\n"), code, flags=re.S)
    code = re.sub(r'--[^\n]*', '', code)
    for n, line in enumerate(code.splitlines(), 1):
        for h in names(line):
            if h.lower() in KW:
                problems.append("line %d: reserved word '%s' used as a name" % (n, h))
    return problems


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "package", "**", "*.ms"), recursive=True)
                                   + glob.glob(os.path.join(ROOT, "package", "*.mcr"))
                                   + glob.glob(os.path.join(ROOT, "*.ms")))
    bad = 0
    for f in files:
        for p in check(f):
            print("%s: %s" % (os.path.relpath(f, ROOT), p))
            bad += 1
    print("%d MAXScript files checked, %d problems" % (len(files), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
