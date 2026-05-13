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

---

## 快速开始（一键安装到 Claude Code）

### 方式一：安装脚本（推荐）

**Windows (PowerShell)**：
```powershell
irm https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.ps1 | iex
```

**macOS / Linux**：
```bash
curl -fsSL https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.sh | bash
```

脚本会自动将本 skill 安装到 `~/.claude/skills/youtube-bilingual-transcript/`。

### 方式二：手动安装

1. 点击 GitHub 页面右上角 **Code → Download ZIP**，下载并解压。
2. 将解压后的文件夹重命名为 `youtube-bilingual-transcript`。
3. 移动到 Claude Code skills 目录：
   - Windows：`C:\Users\<你的用户名>\.claude\skills\`
   - macOS / Linux：`~/.claude/skills/`

### 方式三：Git Clone

```bash
git clone https://github.com/LIPO1024/youtube-bilingual-transcript.git \
  ~/.claude/skills/youtube-bilingual-transcript
```

---

## 使用流程（Obsidian Web Clipper → Claude Code → 双语笔记）

### 前置条件

- 已安装 [Obsidian](https://obsidian.md/) + [Web Clipper](https://obsidian.md/clipper) 浏览器扩展
- 已安装 Claude Code，且本 skill 已放入 `.claude/skills/` 目录
- Python 3.10+ 与 `youtube-transcript-api`：
  ```bash
  pip install youtube-transcript-api
  ```

### 步骤 1：用 Obsidian Web Clipper 抓取 YouTube 字幕

1. 打开任意 YouTube 视频页面。
2. 点击浏览器工具栏的 **Obsidian Web Clipper** 图标。
3. 选择抓取模板，确保转录文本（transcript）被捕获。
4. 保存到 Obsidian vault 的 `Clippings/` 文件夹，例如：
   ```
   Clippings/How To Completely Reinvent Yourself In 6-12 Months.md
   ```

> 抓取文件必须包含：YouTube URL（原始，可能带污染参数）、原文转录文本。中文译文可有可无。

### 步骤 2：在 Claude Code 中调用 skill 处理

1. 打开 Claude Code，进入你的 Obsidian vault 工作目录。
2. 直接输入：
   ```
   /youtube-bilingual-transcript
   ```
3. 或描述你的需求：
   ```
   处理这个 YouTube 视频转录稿，生成双语对照笔记。
   文件在 Clippings/xxx.md
   ```

Claude Code 会自动读取 `SKILL.md`，执行完整 7 阶段流程：
- **Stage 0**：获取精确句子级时间戳
- **Stage 1**：URL 净化与元数据提取
- **Stage 2**：句子拆分与标点重构
- **Stage 3**：内容分层与标题生成
- **Stage 4**：Mermaid 流程图 + 学习借鉴卡片
- **Stage 5**：并行 subagent 批译
- **Stage 6**：双版本时间戳链接生成
- **Stage 7**：双语对照格式化输出

### 步骤 3：在 Obsidian 中查看

生成的 `.md` 文件会自动放入 `Clippings/`（或你指定的路径），直接在 Obsidian 中打开即可：

- 点击 `[▶JV]` 用 JumpVideo 浏览器扩展跳转
- 点击 `[▶ME]` 用 Media Extended 在 Obsidian 内跳转
- 目录用 `[[#标题|显示文本]]` wikilink，支持 Obsidian 内部跳转

---

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

---

## 协议

MIT
