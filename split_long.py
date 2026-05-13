"""
Stage 2.1: 在从句边界拆分过长句（> 40 词或 > 15s），按字符比例重新分配时间戳

拆分规则：在 ", but ", ", and ", ", so ", "; " 等边界寻找最接近中点的位置。
"""
import json
import re
import sys

IN_PATH = sys.argv[1] if len(sys.argv) > 1 else "sentences_buffered.json"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "sentences_final.json"

WORD_LIMIT = 40
DUR_LIMIT = 15.0

with open(IN_PATH, "r", encoding="utf-8") as f:
    sentences = json.load(f)

# Boundary patterns ranked by preference
BOUNDARY_PATTERNS = [
    r"\.\s+(?=[A-Z])",  # period+space+capital
    r"\?\s+(?=[A-Z])",  # question mark
    r"!\s+(?=[A-Z])",
    r",\s+but\s+",
    r",\s+so\s+",
    r",\s+and\s+",
    r";\s+",
    r"\s+--\s+",
    r"\s+—\s+",
]

def find_split_points(text):
    """Find all candidate split points in text."""
    points = []
    for pat in BOUNDARY_PATTERNS:
        for m in re.finditer(pat, text):
            points.append((m.end(), m.start(), pat))
    return sorted(set(points))

def split_sentence(s, max_words=WORD_LIMIT, max_dur=DUR_LIMIT):
    """Split sentence recursively. Return list of {text, start, end}."""
    text = s["text"]
    words = text.split()
    duration = s["end"] - s["start"]

    if len(words) <= max_words and duration <= max_dur:
        return [s]

    points = find_split_points(text)
    if not points:
        return [s]

    # Pick split point closest to middle
    text_len = len(text)
    mid = text_len / 2
    best = min(points, key=lambda p: abs(p[0] - mid))
    cut_end, cut_start, _ = best

    left_text = text[:cut_start].strip()
    right_text = text[cut_end:].strip()

    if not left_text or not right_text:
        return [s]

    # Allocate time by character ratio
    total_chars = len(left_text) + len(right_text) or 1
    left_share = len(left_text) / total_chars
    cut_time = s["start"] + duration * left_share

    left = {
        "text": left_text,
        "start": round(s["start"], 3),
        "end": round(cut_time, 3),
    }
    right = {
        "text": right_text,
        "start": round(cut_time, 3),
        "end": round(s["end"], 3),
    }

    # Recursively split if still too long
    return split_sentence(left, max_words, max_dur) + split_sentence(right, max_words, max_dur)

result = []
for s in sentences:
    result.extend(split_sentence(s))

# Re-apply tail buffer for newly split sentences (to ensure no cut-off)
END_BUFFER_REAPPLY = 0.0  # already applied in apply_buffer.py to outer end; inner cuts inherit chain

# Verify monotonic
for i in range(1, len(result)):
    if result[i]["start"] < result[i - 1]["start"]:
        print(f"WARN non-monotonic at #{i}", file=sys.stderr)

print(f"Before split: {len(sentences)} sentences", file=sys.stderr)
print(f"After split:  {len(result)} sentences", file=sys.stderr)

# Stats
long_sents = [s for s in result if len(s["text"].split()) > 40]
print(f"Remaining > 40 words: {len(long_sents)}", file=sys.stderr)
for s in long_sents[:5]:
    wc = len(s["text"].split())
    print(f"  {wc}w {s['start']:.1f}-{s['end']:.1f}: {s['text'][:80]}...", file=sys.stderr)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"Wrote {OUT_PATH}", file=sys.stderr)
