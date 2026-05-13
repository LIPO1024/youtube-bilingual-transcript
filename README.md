# YouTube Bilingual Transcript

将 YouTube 演讲/视频自动字幕整理为**双语对照、句子级时间戳、自动内容分层**的 Obsidian 笔记。

支持 [JumpVideo](https://github.com/PKM-er/obsidian-jumpvideo) 与 [Media Extended](https://github.com/aidenlx/media-extended) 双协议视频跳转。

## 特性

- **精确句子级时间戳**：基于 YouTube ASR 滑动窗口算法（`eff_end` + 字符比例插值 + 跨片段去重），起始误差 ±0.3 秒
- **0.45 秒尾部 buffer**：避免句末重音/拖音被 JV 切掉
- **双版本时间戳链接**：`[▶JV](jv://...);[▶ME](https://...)` 单行紧凑格式
- **去欧化口语翻译**：根除"进行/加以/予以"空转、"被"字滥用、"基于...的"长定语链
- **内容自动分层**：`##` 大章节 + `###` 细分主题 + `####` 子议题，每章含 Mermaid 流程图与 `[!tip] 学习借鉴` 知识卡片
- **并行批译**： sentences_final.json 拆为 6-8 批，Claude Code subagent 并行翻译，5 分钟内完成

## 文件结构

| 文件 | 用途 |
|------|------|
| `SKILL.md` | Claude Code skill 定义（完整 7 阶段处理流程与 12 条核心军规） |
| `fetch_and_split.py` | Stage 0：YouTube 字幕获取 + 精确句子拆分 |
| `apply_buffer.py` | Stage 2：句末 0.45s buffer + 重叠修复 |
| `split_long.py` | Stage 2.1：长句在从句边界拆分 |
| `generate_final.py` | Stage 7：生成最终 Obsidian Markdown |
| `pipeline.ps1` | 一键流水线：`prep` → 并行翻译 → `final` |
| `fix_quotes.py` | 修复 translations.json 内层 ASCII 引号为中文弯引号 |
| `fix_align.py` | 应急对齐修复（翻译句数与原文不匹配时） |

## 用法

### 1. 配置视频

复制 `video_config.example.json` 为 `video_config.json`，填入视频元数据与章节结构。

### 2. 准备阶段（生成句子级时间戳）

```powershell
pwsh pipeline.ps1 -Stage prep -Config video_config.json
```

输出 `sentences_final.json`，进入并行翻译。

### 3. 翻译阶段（Claude Code 内执行）

挂载 `SKILL.md` 作为 Claude Code skill，由主 agent 并行 spawn 6-8 个 subagent 批译，输出 `translations.json`。

详见 `SKILL.md` Stage 5。

### 4. 生成最终文件

```powershell
pwsh pipeline.ps1 -Stage final -Config video_config.json
```

输出 `out.md`，自动复制到 `Clippings/`。

## 依赖

- Python 3.10+
- [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/)
- PowerShell 7+ (Windows) 或 pwsh (cross-platform)
- Obsidian + JumpVideo / Media Extended 插件（可选，仅用于视频跳转）

## 安装依赖

```bash
pip install youtube-transcript-api
```

## 协议

MIT
