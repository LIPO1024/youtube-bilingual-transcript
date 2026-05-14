# 完整依赖安装与配置指南

本 skill 涉及多个软件/插件的协同工作。以下是每项的安装方式和最小配置。

---

## 1. Obsidian（笔记本体）

**用途**：存储和阅读生成的双语笔记。

**安装**：
- 官网下载：[obsidian.md](https://obsidian.md/)
- Windows / macOS / Linux / iOS / Android 均支持

**最小配置**：
1. 创建或打开一个 vault
2. 在 vault 根目录创建 `Clippings/` 文件夹（用于存放 Web Clipper 抓取的文件）

---

## 2. Obsidian Web Clipper（浏览器扩展）

**用途**：在浏览器中一键抓取 YouTube 页面内容（包括字幕转录）。

**安装**：
- Chrome / Edge：[Chrome Web Store 搜索 "Obsidian Web Clipper"](https://chromewebstore.google.com/)
- Firefox：[Firefox Add-ons](https://addons.mozilla.org/)

**最小配置**：
1. 安装扩展后，点击图标进入设置
2. 连接到 Obsidian（选择你的 vault）
3. 确保抓取模板包含 `transcript` 或页面正文内容
4. 设置默认保存路径为 `Clippings/`

---

## 3. JumpVideo（视频时间戳跳转，强烈推荐）

**用途**：点击笔记中的 `[▶JV]` 链接，精确跳转至视频的对应时间点。

**安装**：
- 官网下载：[https://www.thegodofking.com/](https://www.thegodofking.com/)
- Windows / macOS 均支持
- 同时安装对应的浏览器扩展

**最小配置**：
1. 安装主程序 + 浏览器扩展
2. 在 JumpVideo 设置中配置默认播放器（浏览器 / PotPlayer / MPV / VLC）
3. 浏览器扩展授权访问 YouTube 等视频网站

> JumpVideo 独创的时间戳链接技术让时间戳永不失效，支持几乎所有视频平台和网盘。

---

## 4. Media Extended（Obsidian 社区插件）

**用途**：在 Obsidian 内部直接播放 YouTube 视频，点击 `[▶ME]` 链接时无需离开 Obsidian。

**安装**：
1. Obsidian 中打开 **设置 → 社区插件 → 浏览**
2. 搜索 "Media Extended"，安装并启用

**最小配置**：
- 安装后无需额外配置，插件自动处理 YouTube 链接

---

## 5. Claude Code（AI 处理引擎）

**用途**：读取 skill 定义，执行完整的 7 阶段处理流程。

**安装**：
- 官网：[claude.ai/code](https://claude.ai/code)
- 或 VS Code 扩展市场搜索 "Claude Code"

**最小配置**：
1. 安装 Claude Code CLI 或 VS Code 扩展
2. 登录 Anthropic 账号
3. 打开 Obsidian vault 目录作为工作目录
4. 将本 skill 安装到 `~/.claude/skills/youtube-bilingual-transcript/`（见 README 快速安装）

---

## 6. Python 3.10+（字幕获取与处理）

**用途**：执行 `fetch_and_split.py` 等脚本，获取 YouTube 原始字幕并做精确句子拆分。

**安装**：
- 官网：[python.org](https://www.python.org/downloads/)
- 安装时勾选 "Add Python to PATH"

**依赖包**：
```bash
pip install youtube-transcript-api
```

**验证**：
```bash
python --version  # 应显示 3.10 或更高
python -c "from youtube_transcript_api import YouTubeTranscriptApi; print('OK')"
```

---

## 7. PowerShell 7+ / pwsh（流水线执行）

**用途**：运行 `pipeline.ps1` 一键流水线。

**安装**：
- Windows：PowerShell 7 已随 Windows 11 预装，或从 [GitHub](https://github.com/PowerShell/PowerShell/releases) 下载
- macOS / Linux：`brew install powershell` 或 [官方安装指南](https://learn.microsoft.com/powershell/scripting/install/installing-powershell)

**验证**：
```powershell
pwsh --version
```

---

## 8. Git（一键安装脚本需要）

**用途**：`install.ps1` / `install.sh` 脚本使用 git clone 安装 skill。

**安装**：
- 官网：[git-scm.com](https://git-scm.com/)

**验证**：
```bash
git --version
```

---

## 配置检查清单

开始处理第一个视频前，逐项确认：

- [ ] Obsidian 已安装，vault 中存在 `Clippings/` 文件夹
- [ ] Web Clipper 已安装，能正常抓取网页到 Obsidian
- [ ] JumpVideo 已安装，浏览器扩展已启用
- [ ] Media Extended 已在 Obsidian 社区插件中启用
- [ ] Claude Code 已安装，能在 vault 目录正常启动
- [ ] Python 3.10+ 已安装，`youtube-transcript-api` 已 pip 安装
- [ ] PowerShell 7+ 可用，`pwsh --version` 有输出
- [ ] 本 skill 已安装到 `~/.claude/skills/youtube-bilingual-transcript/`

全部勾选后，即可按 README "完整使用流程" 开始处理第一个视频。
