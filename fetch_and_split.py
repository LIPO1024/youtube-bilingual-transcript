"""
Stage 0 implementation: Fetch YouTube transcript and split into precise sentences.

Algorithm: eff_end + character-ratio interpolation + cross-fragment dedup.
Output: sentences.json with [{text, start, end}, ...].
"""
import json
import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = sys.argv[1] if len(sys.argv) > 1 else "YM0_8mOaKic"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "sentences.json"

# 1. Fetch fragments
api = YouTubeTranscriptApi()
fetched = api.fetch(VIDEO_ID)
fragments = []
for snip in fetched:
    fragments.append({
        "text": snip.text,
        "start": snip.start,
        "duration": snip.duration,
    })
print(f"Fetched {len(fragments)} raw fragments", file=sys.stderr)

# 2. Compute eff_end for each fragment
for i in range(len(fragments) - 1):
    eff_end = min(
        fragments[i]["start"] + fragments[i]["duration"],
        fragments[i + 1]["start"],
    )
    if eff_end <= fragments[i]["start"]:
        eff_end = fragments[i]["start"] + fragments[i]["duration"]
    fragments[i]["eff_end"] = eff_end
fragments[-1]["eff_end"] = fragments[-1]["start"] + fragments[-1]["duration"]

# 3. Per-fragment character-ratio interpolation, with cross-fragment dedup
def tokenize(text):
    # Split keeping punctuation attached, normalize whitespace
    text = re.sub(r"\s+", " ", text.strip())
    return text.split(" ") if text else []

global_words = []  # [(token, start, end), ...]
prev_tokens = []
for fr in fragments:
    tokens = tokenize(fr["text"])
    if not tokens:
        prev_tokens = []
        continue

    span = fr["eff_end"] - fr["start"]
    if span <= 0:
        prev_tokens = tokens
        continue
    total_chars = sum(len(t) for t in tokens) or 1
    cur = fr["start"]
    word_times = []
    for t in tokens:
        share = (len(t) / total_chars) * span
        word_times.append((t, cur, cur + share))
        cur += share

    # cross-fragment dedup: longest suffix of prev_tokens == prefix of tokens
    overlap = 0
    max_check = min(len(tokens), len(prev_tokens))
    for k in range(max_check, 0, -1):
        if prev_tokens[-k:] == tokens[:k]:
            overlap = k
            break

    for j in range(overlap, len(tokens)):
        global_words.append(word_times[j])
    prev_tokens = tokens

# 4. Monotonic check
non_mono = 0
for i in range(1, len(global_words)):
    if global_words[i][1] < global_words[i - 1][1] - 0.001:
        non_mono += 1
print(f"non-monotonic transitions: {non_mono}", file=sys.stderr)
print(f"deduped global words: {len(global_words)}", file=sys.stderr)

# 5. Sentence boundary detection
ABBREVS = {
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "vs.", "etc.",
    "i.e.", "e.g.", "Inc.", "Ltd.", "Corp.", "U.S.", "U.K.", "Ph.D.",
    "St.", "Mt.", "No.", "Co.", "Gen.", "Lt.", "Capt.", "Rev.",
}

def ends_sentence(token, next_token):
    """Decide whether token ends a sentence (followed by next_token)."""
    if not token:
        return False
    last = token[-1]
    if last not in ".?!":
        return False
    if token in ABBREVS:
        return False
    # Number followed by next? e.g. "1." used as list item — not common in transcript here
    # Check if next token starts with capital letter or quote
    if next_token is None:
        return True
    nt = next_token.lstrip("\"'[(").lstrip()
    if not nt:
        return False
    # Allow proper noun continuations (e.g. "Mr. Smith") only when token is in ABBREVS
    return nt[0].isupper() or nt[0] in '"\'['

sentences = []
buf_words = []
for i, (tok, st, en) in enumerate(global_words):
    buf_words.append((tok, st, en))
    nxt_tok = global_words[i + 1][0] if i + 1 < len(global_words) else None
    if ends_sentence(tok, nxt_tok):
        text = " ".join(t for t, _, _ in buf_words).strip()
        sent_start = buf_words[0][1]
        # End = start of next sentence (= start of next token), or end of last token
        if i + 1 < len(global_words):
            sent_end = global_words[i + 1][1]
        else:
            sent_end = buf_words[-1][2]
        sentences.append({
            "text": text,
            "start": round(sent_start, 3),
            "end": round(sent_end, 3),
        })
        buf_words = []

# Flush remaining
if buf_words:
    text = " ".join(t for t, _, _ in buf_words).strip()
    if text:
        sentences.append({
            "text": text,
            "start": round(buf_words[0][1], 3),
            "end": round(buf_words[-1][2], 3),
        })

print(f"raw sentences: {len(sentences)}", file=sys.stderr)

# 6. Merge tiny sentences (< 3 words) into next
merged = []
i = 0
while i < len(sentences):
    s = sentences[i]
    word_count = len(s["text"].split())
    if word_count < 3 and i + 1 < len(sentences):
        nxt = sentences[i + 1]
        merged.append({
            "text": s["text"] + " " + nxt["text"],
            "start": s["start"],
            "end": nxt["end"],
        })
        i += 2
    else:
        merged.append(s)
        i += 1
sentences = merged
print(f"after merge tiny: {len(sentences)}", file=sys.stderr)

# 7. Fix overlapping adjacent
for i in range(1, len(sentences)):
    if sentences[i]["start"] < sentences[i - 1]["end"]:
        sentences[i - 1]["end"] = sentences[i]["start"]

# 8. Clean repetitive fillers
def clean_repeats(text):
    # Common ASR artifacts: "let's let's", "I I", "the the"
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    return text

for s in sentences:
    s["text"] = clean_repeats(s["text"])

print(f"final sentences = {len(sentences)}", file=sys.stderr)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(sentences, f, ensure_ascii=False, indent=2)
print(f"Wrote {OUT_PATH}", file=sys.stderr)
