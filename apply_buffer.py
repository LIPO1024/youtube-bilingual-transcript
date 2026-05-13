"""
Stage 6 §尾部 buffer + Stage 2 长句拆分

1. 把相邻片段过短的句末连接修正
2. 给每个句末加 0.45s buffer，clamp 到下一句末 -0.05s
3. 标记需要拆分的过长句（> 40 词）供后续处理
"""
import json
import re
import sys

IN_PATH = sys.argv[1] if len(sys.argv) > 1 else "sentences.json"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "sentences_buffered.json"

END_BUFFER = 0.45

with open(IN_PATH, "r", encoding="utf-8") as f:
    sentences = json.load(f)

# Apply tail buffer
VIDEO_END = max(s["end"] for s in sentences) + 0.5

for i, s in enumerate(sentences):
    raw_end = s["end"] + END_BUFFER
    if i + 1 < len(sentences):
        cap = sentences[i + 1]["end"] - 0.05
    else:
        cap = VIDEO_END
    s["end"] = round(min(raw_end, cap), 3)

# Stats
long_sents = [(i, s) for i, s in enumerate(sentences) if len(s["text"].split()) > 40]
print(f"Total sentences: {len(sentences)}", file=sys.stderr)
print(f"Sentences > 40 words: {len(long_sents)}", file=sys.stderr)
for i, s in long_sents[:10]:
    wc = len(s["text"].split())
    print(f"  #{i}: {wc} words, {s['start']:.1f}-{s['end']:.1f}s: {s['text'][:80]}...", file=sys.stderr)

# Print first 5 and last 5 to verify
print("\nFirst 5 sentences:", file=sys.stderr)
for i, s in enumerate(sentences[:5]):
    print(f"  #{i} [{s['start']:.2f}-{s['end']:.2f}] {s['text']}", file=sys.stderr)
print("\nLast 5 sentences:", file=sys.stderr)
for i, s in enumerate(sentences[-5:]):
    print(f"  #{len(sentences) - 5 + i} [{s['start']:.2f}-{s['end']:.2f}] {s['text']}", file=sys.stderr)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(sentences, f, ensure_ascii=False, indent=2)
print(f"\nWrote {OUT_PATH}", file=sys.stderr)
