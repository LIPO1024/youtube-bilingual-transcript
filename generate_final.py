"""
Final markdown generator for YouTube bilingual transcript.

Reads:
  - sentences_final.json   (Stage 0-2 output)
  - translations.json      (Stage 5 output)
  - video_config.json      (per-video metadata + chapter structure)

Writes:
  - out.md                 (final Obsidian markdown)

Usage:
  python generate_final.py [SENTENCES] [TRANSLATIONS] [CONFIG] [OUT]

Defaults: sentences_final.json translations.json video_config.json out.md
"""
import json
import sys

SENTENCES_PATH = sys.argv[1] if len(sys.argv) > 1 else "sentences_final.json"
TRANSLATIONS_PATH = sys.argv[2] if len(sys.argv) > 2 else "translations.json"
CONFIG_PATH = sys.argv[3] if len(sys.argv) > 3 else "video_config.json"
OUT_PATH = sys.argv[4] if len(sys.argv) > 4 else "out.md"

with open(SENTENCES_PATH, "r", encoding="utf-8") as f:
    sentences = json.load(f)
with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
    translations = json.load(f)
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

assert len(sentences) == len(translations), \
    f"sentence count {len(sentences)} != translation count {len(translations)}"

VIDEO_ID = cfg["video_id"]
SOURCE_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
TITLE = cfg["title"]
AUTHOR = cfg["author"]
PUBLISHED = cfg["published"]
CLIPS_SOURCE = cfg["clips_source"]
TAGS = cfg["tags"]
SPEAKER_INFO = cfg["speaker_info"]
CORE_THESIS = cfg["core_thesis"]
CHAPTERS = cfg["chapters"]


def fmt_time_short(seconds):
    """MM:SS form."""
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def fmt_time_full(seconds):
    """HH:MM:SS.mmm form, always with leading zeros."""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    rem = total_ms % 3600000
    minutes = rem // 60000
    rem %= 60000
    secs = rem // 1000
    ms = rem % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def jv_link(start_s, end_s):
    return (
        f"jv://?url=https://www.youtube.com/watch?v={VIDEO_ID}"
        f"&time={fmt_time_full(start_s)}-{fmt_time_full(end_s)}"
        f"&app=jump-video-extension"
    )


def me_link(start_s):
    return f"https://www.youtube.com/watch?v={VIDEO_ID}&t={int(start_s)}s"


def render_sentence_block(idx):
    s = sentences[idx]
    cn = translations[idx]
    rng = f"【{fmt_time_short(s['start'])}-{fmt_time_short(s['end'])}】"
    jv = jv_link(s["start"], s["end"])
    me = me_link(s["start"])
    return (
        "---\n"
        f"- {rng}[▶JV]({jv});[▶ME]({me})\n"
        f"\t- {s['text'].strip()}\n"
        f"\t\t- {cn.strip()}\n"
    )


# ============================================================
# Render
# ============================================================

out = []

# Frontmatter
out.append("---")
out.append(f'title: "{TITLE}"')
out.append(f"source: {SOURCE_URL}")
out.append(f"video-id: {VIDEO_ID}")
out.append("author:")
out.append(f'  - "[[{AUTHOR}]]"')
out.append(f"published: {PUBLISHED}")
out.append(f'clips-source: "[[{CLIPS_SOURCE}]]"')
out.append("tags:")
for tag in TAGS:
    out.append(f'  - "{tag}"')
out.append("---\n")

# Title block
out.append(f"# {TITLE}\n")
out.append("> **演讲信息**")
for line in SPEAKER_INFO:
    out.append(f"> - {line}")
out.append(f"> - 视频地址：[YouTube]({SOURCE_URL})")
out.append(f"> - 核心论点：{CORE_THESIS}\n")
out.append("---\n")

# TOC
out.append("# 内容总览\n")
out.append("> **阅读提示**：")
out.append("> - 点击 `[▶JV]` 用 JumpVideo 浏览器扩展跳转")
out.append("> - 点击 `[▶ME]` 用 Media Extended 在 Obsidian 内跳转")
out.append("> - 点击下方目录条目可跳转到对应章节\n")
out.append("## 目录\n")
for ch in CHAPTERS:
    head = f"{ch['num']}、{ch['title']}"
    out.append(f"- [[#{head}|{head}]]")
    for sub in ch["subs"]:
        sub_head = f"{sub['id']} {sub['title']}"
        out.append(f"  - [[#{sub_head}|{sub_head}]]")
out.append("\n---\n")

# Body
out.append("# 正文\n")

for ch in CHAPTERS:
    head = f"{ch['num']}、{ch['title']}"
    out.append(f"## {head}\n")
    out.append("```mermaid")
    out.append(ch["mermaid"])
    out.append("```\n")
    out.append("> [!tip] 学习借鉴")
    for tip in ch["tips"]:
        out.append(f"> - {tip}")
    out.append("")
    for sub in ch["subs"]:
        sub_head = f"{sub['id']} {sub['title']}"
        out.append(f"### {sub_head}\n")
        a, b = sub["range"]
        for i in range(a, b + 1):
            out.append(render_sentence_block(i))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(out).rstrip() + "\n")

print(f"Wrote {OUT_PATH} ({len(out)} lines)", file=sys.stderr)
print(f"Total sentences: {len(sentences)}", file=sys.stderr)
