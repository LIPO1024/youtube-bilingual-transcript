# YouTube Bilingual Transcript

Turn YouTube speeches and videos into **bilingual, sentence-level timestamped, auto-structured** Obsidian notes.

Supports dual-protocol video jumping: [JumpVideo](https://www.thegodofking.com/) and [Media Extended](https://github.com/aidenlx/media-extended).

---

## Features

- **Precise sentence-level timestamps**: Based on YouTube ASR sliding-window algorithm (`eff_end` + character-ratio interpolation + cross-fragment dedup), start-time error within ±0.3s
- **0.45s tail buffer**: Prevents the last word from being cut off by JumpVideo
- **Dual-protocol links**: `[▶JV](jv://...);[▶ME](https://...)` in a single compact line
- **De-europeanized colloquial Chinese**: Eliminates empty verbs ("进行/加以/予以"), abuse of "被", and over-long attributive chains
- **Auto content layering**: `##` chapters + `###` sub-topics + `####` sub-issues; each chapter includes a Mermaid flowchart and a `[!tip] Key Takeaways` card
- **Parallel batch translation**: `sentences_final.json` split into 6-8 batches, translated in parallel by Claude Code subagents, done in under 5 minutes

---

## Quick Start (30-second install)

**Windows (PowerShell)**:
```powershell
irm https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.ps1 | iex
```

**macOS / Linux**:
```bash
curl -fsSL https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.sh | bash
```

The script auto-installs to `~/.claude/skills/youtube-bilingual-transcript/`.

---

## Full Workflow

### Prerequisites

| Software | Purpose | How to install |
|----------|---------|---------------|
| [Obsidian](https://obsidian.md/) | Note storage and reading | Download from official site |
| [Obsidian Web Clipper](https://obsidian.md/clipper) | Browser extension for capturing YouTube transcripts | Browser extension store |
| [JumpVideo](https://www.thegodofking.com/) | Video timestamp jumping (highly recommended) | Official site |
| [Media Extended](https://github.com/aidenlx/media-extended) | Embedded video playback inside Obsidian | Obsidian Community Plugins |
| Claude Code | AI translation and processing | [claude.ai/code](https://claude.ai/code) |
| Python 3.10+ | Subtitle fetching and processing | [python.org](https://www.python.org/) |

Full setup guide: [DEPENDENCIES.md](DEPENDENCIES.md)

### Step 1: Capture with Obsidian Web Clipper

1. Open a YouTube video, click the **Obsidian Web Clipper** icon
2. Make sure the transcript is captured
3. Save to `Clippings/Video Title.md`

### Step 2: Process with Claude Code

```
/youtube-bilingual-transcript
```

Or describe your need:
```
Process Clippings/xxx.md into a bilingual note
```

Claude Code executes the full 7-stage pipeline automatically.

### Step 3: View in Obsidian

The generated `.md` is placed in `Clippings/`. Open it in Obsidian:
- Click `[▶JV]` to jump to the exact sentence start via JumpVideo
- Click `[▶ME]` to play inside Obsidian via Media Extended
- TOC uses `[[#Heading|Display]]` wikilinks for native Obsidian navigation

---

## Special Thanks: JumpVideo

This project's timestamp jumping relies on **JumpVideo**.

JumpVideo is a free video note-taking tool with a unique timestamp-link technology. It works with browsers, PotPlayer, MPV, and VLC, supporting almost all video platforms and note-taking apps.

**Why JumpVideo**:
- **Unique timestamp-link tech**: Two hotkeys to capture timestamps and screenshots; links never expire and work across devices
- **All note apps supported**: Obsidian, Logseq, Notion, RoamEdit, RemNote, XMind, TheBrain, and more
- **All video platforms supported**: Bilibili, YouTube, TED, Baidu Netdisk, Aliyun Drive, and 30+ others
- **Foolproof and portable**: Notes can migrate to another computer or app anytime
- **Completely free**

Official site: [https://www.thegodofking.com/](https://www.thegodofking.com/)

> This project has no commercial affiliation with JumpVideo. Recommended purely for its utility.

---

## File Structure

| File | Purpose |
|------|---------|
| `skill.md` | Claude Code skill definition (7-stage pipeline + 12 rules) |
| `fetch_and_split.py` | Stage 0: fetch YouTube subtitles + precise sentence splitting |
| `apply_buffer.py` | Stage 2: 0.45s tail buffer |
| `split_long.py` | Stage 2.1: long-sentence splitting |
| `generate_final.py` | Stage 7: Markdown generator |
| `pipeline.ps1` | One-click pipeline: prep → translate → final |
| `fix_quotes.py` / `fix_align.py` | Emergency fix scripts |
| `DEPENDENCIES.md` | Complete setup guide for all tools |
| `SUPPORT.md` | Donations, community, custom services |

---

## License

MIT
