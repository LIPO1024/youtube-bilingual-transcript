# YouTube Bilingual Transcript

将 YouTube 演讲/视频自动字幕整理为**双语对照、句子级时间戳、自动内容分层**的 Obsidian 笔记。

支持 [JumpVideo](https://www.thegodofking.com/) 与 [Media Extended](https://github.com/aidenlx/media-extended) 双协议视频跳转。

---

## 特性

- **精确句子级时间戳**：基于 YouTube ASR 滑动窗口算法（`eff_end` + 字符比例插值 + 跨片段去重），起始误差 ±0.3 秒
- **0.45 秒尾部 buffer**：避免句末重音/拖音被 JV 切掉
- **双版本时间戳链接**：`[▶JV](jv://...);[▶ME](https://...)` 单行紧凑格式
- **去欧化口语翻译**：根除"进行/加以/予以"空转、"被"字滥用、"基于...的"长定语链
- **内容自动分层**：`##` 大章节 + `###` 细分主题 + `####` 子议题，每章含 Mermaid 流程图与 `[!tip] 学习借鉴` 知识卡片
- **并行批译**：sentences_final.json 拆为 6-8 批，Claude Code subagent 并行翻译，5 分钟内完成

---

## 快速开始（30 秒安装到 Claude Code）

**Windows (PowerShell)**：
```powershell
irm https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.ps1 | iex
```

**macOS / Linux**：
```bash
curl -fsSL https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.sh | bash
```

脚本自动安装到 `~/.claude/skills/youtube-bilingual-transcript/`。

> 无脚本权限？手动安装见下方 [手动安装](#手动安装)。

---

## 完整使用流程

### 前置条件

| 软件 | 用途 | 安装方式 |
|------|------|---------|
| [Obsidian](https://obsidian.md/) | 笔记存储与阅读 | 官网下载 |
| [Obsidian Web Clipper](https://obsidian.md/clipper) | 浏览器抓取 YouTube 字幕 | 浏览器扩展商店 |
| [JumpVideo](https://www.thegodofking.com/) | 视频时间戳跳转（强烈推荐） | 官网下载 |
| [Media Extended](https://github.com/aidenlx/media-extended) | Obsidian 内嵌视频播放 | Obsidian 社区插件 |
| Claude Code | AI 翻译与整理 | [claude.ai/code](https://claude.ai/code) |
| Python 3.10+ | 字幕获取与处理 | [python.org](https://www.python.org/) |

完整配置指南：[DEPENDENCIES.md](DEPENDENCIES.md)

### 步骤 1：用 Obsidian Web Clipper 抓取字幕

1. 打开 YouTube 视频页面，点击浏览器工具栏 **Obsidian Web Clipper** 图标
2. 确认转录文本（transcript）已被捕获
3. 保存到 `Clippings/视频标题.md`

> 抓取文件须包含：YouTube URL、原文转录。中文译文可有可无。

### 步骤 2：在 Claude Code 中调用 skill 处理

```
/youtube-bilingual-transcript
```

或描述需求：
```
处理 Clippings/xxx.md，生成双语对照笔记
```

Claude Code 自动执行 7 阶段流程：获取时间戳 → 净化 URL → 句子拆分 → 内容分层 → 并行翻译 → 生成链接 → 输出 Markdown。

### 步骤 3：在 Obsidian 中查看

生成的 `.md` 文件自动放入 `Clippings/`，直接在 Obsidian 打开：
- 点击 `[▶JV]` 用 JumpVideo 跳转至精确句首
- 点击 `[▶ME]` 用 Media Extended 在 Obsidian 内播放
- 目录用 `[[#标题|显示文本]]` wikilink，Obsidian 原生跳转

---

## 特别致谢：JumpVideo

本项目的时间戳跳转功能深度依赖 **JumpVideo**。

JumpVideo 是一款专为"边看视频边做笔记"设计的免费软件，独创的时间戳链接技术可以搭配浏览器、PotPlayer、MPV、VLC 等播放器，为几乎所有格式的视频做笔记。

**为什么推荐 JumpVideo**：
- **独创时间戳链接技术**：仅需两个快捷键即可获取时间戳链接和截图，时间戳链接永不失效，任何时间、任何地点、任何设备都能回到视频的对应时间点
- **支持所有笔记软件**：Obsidian、思源笔记、Logseq、Flomo、Notion、XMind、RoamEdit、RemNote、BookxNote、ithoughts、幕布、葫芦笔记、TheBrain 等
- **支持所有在线视频和网盘**：哔哩哔哩、百度网盘、阿里云盘、天翼云盘、夸克网盘、迅雷网盘、腾讯微云、115 网盘、Alist、CloudDrive2、MOOC、YouTube、TED、网易公开课、微信视频号、知乎、抖音、快手、小红书、微博、西瓜视频、今日头条、搜狐视频、腾讯视频、优酷视频、爱奇艺、芒果 TV、咪咕视频、PP 视频等
- **傻瓜式操作，数据可迁移**：做好的笔记可以迁移到另一台电脑或另一款笔记软件，小白入门无难度
- **完全免费**

官网：[https://www.thegodofking.com/](https://www.thegodofking.com/)

> 本项目与 JumpVideo 无商业关联，仅因其实用价值而真诚推荐。

---

## 文件结构

| 文件 | 用途 |
|------|------|
| `skill.md` | Claude Code skill 定义（7 阶段流程 + 12 条军规） |
| `fetch_and_split.py` | Stage 0：YouTube 字幕获取 + 精确句子拆分 |
| `apply_buffer.py` | Stage 2：句末 0.45s buffer |
| `split_long.py` | Stage 2.1：长句拆分 |
| `generate_final.py` | Stage 7：Markdown 生成器 |
| `pipeline.ps1` | 一键流水线：prep → 翻译 → final |
| `fix_quotes.py` / `fix_align.py` | 应急修复脚本 |
| `DEPENDENCIES.md` | 完整依赖安装与配置指南 |
| `SUPPORT.md` | 打赏、入群、定制服务 |

---

## 打赏与支持

如果你喜欢这个 skill，可以扫码支持，或加入交流群获取更多定制服务。

<p align="center">
  <img src="assets/wechat-qr.jpg" width="280" alt="微信二维码">
  <br>
  <sub>扫码添加好友 — 入群交流 / 打赏支持 / 定制笔记服务</sub>
</p>

详情：[SUPPORT.md](SUPPORT.md)

---

## 协议

MIT
