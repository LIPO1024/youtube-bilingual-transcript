"""Convert inner unescaped ASCII straight quotes in translations.json
to full-width Chinese curly quotes (alternating opening/closing).
The outer JSON string delimiters are preserved.
"""
import json
import re

PATH = "translations.json"

with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()

lines = raw.split("\n")
fixed = []
LINE_RE = re.compile(r'^(\s*)"(.*)"(,?)\s*$')

for line in lines:
    m = LINE_RE.match(line)
    if not m:
        fixed.append(line)
        continue
    indent, content, comma = m.groups()
    out = []
    open_next = True
    i = 0
    while i < len(content):
        ch = content[i]
        if ch == "\\" and i + 1 < len(content):
            out.append(ch)
            out.append(content[i + 1])
            i += 2
            continue
        if ch == '"':
            out.append("“" if open_next else "”")
            open_next = not open_next
            i += 1
            continue
        out.append(ch)
        i += 1
    fixed.append(f'{indent}"{"".join(out)}"{comma}')

with open(PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(fixed))

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Loaded {len(data)} translations after fix")
