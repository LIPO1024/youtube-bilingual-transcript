---
name: youtube-bilingual-transcript
description: >
  将 Obsidian Web Clipper 抓取的 YouTube 演讲/视频转录稿，整理为双语对照、
  句子级时间戳、自动内容分层、去欧化口语中文的 Obsidian 笔记。
  输出支持 JumpVideo 与 Media Extended 双协议跳转。
  触发条件：用户要求处理视频转录稿、整理演讲字幕、双语对照翻译、
  vibe-coding/技术演讲/学术讲座等 YouTube 内容整理。
---

# YouTube 双语字幕整理 Skill

> 本项目时间戳跳转功能依赖 [JumpVideo](https://www.thegodofking.com/) —— 一款支持几乎所有视频平台和笔记软件的免费视频笔记工具，独创时间戳链接技术，两个快捷键即可获取精确时间戳和截图。

## !!! 核心军规（执行前必读，绝不可遗漏）

以下 12 条是**最低不可违反要求**。无论流程多复杂，最终输出**必须**满足全部 12 条，否则视为失败：

1. **每个句子必须有双版本时间戳链接**：`[▶JV](jv://...);[▶ME](https://...&t=XXs)`，两者用 `;` 分隔，无空格
2. **JV 时间格式严格为 `HH:MM:SS.mmm`**（含前导零，如 `00:00:02.000`），绝不省略小时位
3. **句子合并算法不得用 min(starts)/max(ends)**：必须按"有效语音窗口"（`eff_end = min(start+duration, next_frag.start)`）+ 字符比例插值定位每个词的真实时刻，再以词为单位定位句界。详见 Stage 0 §句子合并算法。
4. **每个句末时间戳必须含 0.45 秒尾部 buffer**：避免 JV 因句末重音/拖音/气口被切，详见 Stage 6 §尾部 buffer。
5. **删除**所有 `<!-- JumpVideo -->` / `<!-- Media Extended -->` 注释、`**EN:**` 标识、`> [!中译]` Callout
6. **每个 `##` 大章节下方必须有 Mermaid 流程图 + `> [!tip] 学习借鉴`**，两者缺一不可
7. **严格一句对一句**：英文一句、中文一句，1:1 对应，不可多句合并；纯中文内容不保留英文行
8. **标题层级自动生成**：`##` 大章节 + `###` 细分主题 + `####` 子议题，命名凝练，禁止"引言/正文/结论"等泛泛标题
9. **文件顶部必须有 `# 内容总览` 目录区块，目录条目必须用 Obsidian wikilink 格式 `[[#完整标题|显示文本]]`**，禁用 GitHub-slug `[text](#slug)`（中文锚点 slug 化与 Obsidian 不兼容，会导致点击失效）。只显示到 `###` 层级。
10. **保留原始 frontmatter**，补充 `video-id` 字段；URL 净化后只保留 `watch?v=VIDEO_ID`
11. **中文译文去欧化**：根除"进行/加以/予以"空转、"被"字滥用、"基于...的"长定语链、"对于...而言"框架；输出前必须逐条对照下方「强制自检清单」
12. **翻译必须并行 subagent 批译**：`sentences_final.json` 拆为 6-8 批，主 agent 在**同一条消息**内并列发起 subagent，**禁止主 agent 串行逐句翻译**。Subagent 输出 JSON 必须用中文弯引号 `""` `''`，**禁用** ASCII `"` `'`，避免下游 JSON 转义错误。

---

## 触发条件

以下任一情形时调用本 skill：

- 用户要求处理/整理/翻译 YouTube 视频转录稿或字幕
- 用户提到 "双语对照"、"时间戳"、"视频跳转"、"演讲整理"
- 输入文件位于 `Clippings/` 或包含 YouTube URL 及原始转录文本
- 用户要求对抓取的视频内容进行内容分层、标题生成、去欧化翻译

## 输入规范

**来源**：`Clippings/文件名.md`（由 Obsidian Web Clipper 抓取）

**输入文件必须包含**：
- YouTube 视频 URL（原始，可能含污染参数）
- 原文转录（Web Clipper 已抓取，无需额外获取）
- 可能已有的中文译文（如没有，由本 skill 生成）

**语言检测与翻译策略**（自动执行，无需询问）：

| 原文语言占比 | 处理方式 |
|-------------|---------|
| > 80% 英文 | 执行完整双语对照翻译 |
| > 80% 中文 | **不翻译**，仅做时间戳格式化与内容分层，输出单语中文+时间戳 |
| 混合 | 逐句判断：英文句翻译，中文句保留原句 |

**前置确认**（每次执行前必须向用户确认）：
- 是否需要覆盖原文件，还是输出到新路径？
- 是否已安装 Media Extended / JumpVideo？
- 原文语言判断结果是否正确（尤其混合语言时）。

---

## 处理流程

### Stage 0：获取精确句子级时间戳

**核心问题**：Web Clipper 抓取的转录稿只有段落级秒级时间戳，无法满足句子级精确跳转需求。

**解决方案**：使用 `youtube_transcript_api` 获取 YouTube 原始自动字幕的片段级时间戳（精确到 10-100 毫秒），再合并为完整句子。

**执行步骤**：

1. 从净化后的 URL 提取 `VIDEO_ID`
2. 调用 `YouTubeTranscriptApi().fetch(VIDEO_ID)` 获取片段列表
3. 每个片段包含：`text`（文本）、`start`（起始秒数，float）、`duration`（持续时间，float）

**ASR 滑动窗口本质**（必须先理解）：
YouTube 自动字幕片段是**滑动窗口**生成的：窗口长约 4-5s、步进约 2s，相邻片段在显示文本上**高度重叠**（比如 `prev = "A B C D E"`，`next = "C D E F G"`）。

**致命陷阱**：直接用 `min(starts) ... max(ends)` 框住句子会把每个词的时刻拉宽 2-4 秒。这是早期版本翻车的根因，**严禁再犯**。

4. **句子合并算法**（基于"有效语音窗口" + 字符比例插值，**不得偷懒用 min/max**）：

   **a. 计算每个片段的有效语音窗口 `eff_end`**

   ```python
   for i in range(len(fragments) - 1):
       eff_end = min(fragments[i]["start"] + fragments[i]["duration"],
                     fragments[i + 1]["start"])
       if eff_end <= fragments[i]["start"]:
           eff_end = fragments[i]["start"] + fragments[i]["duration"]
       fragments[i]["eff_end"] = eff_end
   fragments[-1]["eff_end"] = fragments[-1]["start"] + fragments[-1]["duration"]
   ```

   含义：片段 N 真正的"新词被说出来"的时间窗 = `[start_N, start_{N+1}]`，因为下一片段开始时窗口已经滑走。

   **b. 在每个 `eff_end` 内按字符比例插值定位每个词的时刻**

   ```python
   span = fr["eff_end"] - fr["start"]
   total_chars = sum(len(t) for t in tokens)
   cur = fr["start"]
   for t in tokens:
       share = (len(t) / total_chars) * span
       word_times.append((t, cur, cur + share))
       cur += share
   ```

   **c. 跨片段去重**：用"前片段后缀 = 当前片段前缀"的最长匹配长度作为 overlap，跳过当前片段前 overlap 个 token，仅追加新词到全局时间轴

   ```python
   overlap = 0
   for k in range(min(len(tokens), len(prev_tokens)), 0, -1):
       if prev_tokens[-k:] == tokens[:k]:
           overlap = k
           break
   for j in range(overlap, len(tokens)):
       deduped.append(word_times[j])
   ```

   **d. 在去重后的全局词时间轴上识别句界**：

   - 用正则 `(?<=[.?!])\s+(?=[A-Z"\[]|>>)` 识别句子边界
   - 排除缩写误拆：`Mr. Mrs. Ms. Dr. Prof. Sr. Jr. vs. etc. i.e. e.g. Inc. Ltd. Corp. U.S. U.K. Ph.D.`
   - 句子起始时间 = 该句**第一个词**的 `start`；结束时间 = **下一句的 start**（最末一句用末词的 `end`）

5. **完整性自检**（写入脚本日志，必须为 0）：
   - `non-monotonic transitions: 0`：相邻词时间不得倒退
   - `final sentences = N`：N 与原始片段数量级吻合（一般 1.5-2 倍片段数）

6. **后处理**：
   - 合并长度 < 3 词的过短句到下一句
   - 修复相邻句时间重叠（后句 start = 前句 end）
   - 清理口语重复：`let's let's` → `let's`，`um um` → `um`

**Stage 0 检查点**：
- [ ] 已使用 `eff_end = min(start+duration, next.start)` 截断窗口，**禁止**直接 `start + duration`
- [ ] 跨片段去重生效（典型 5000 词以上量级被压到 3000-5000 词，不是简单拼接）
- [ ] 词时间轴 monotonic（脚本日志 `non-monotonic transitions: 0`）
- [ ] 每个句子有 `text`、`start`、`end`（均为 float）
- [ ] 句子总数与原文内容量匹配

**时间精度承诺**（执行此算法后）：句子起始 ±0.3 秒以内，结束误差由 Stage 6 §尾部 buffer 进一步补偿。

---

### Stage 1：URL 净化与元数据提取

1. 提取文件中的 YouTube URL。
2. **净化参数**：无情剥离 `index=`、`list=`、`yu26`、`si=`、`ab_channel=` 等污染参数，只保留干净的视频根链接：
   ```
   https://www.youtube.com/watch?v=VIDEO_ID
   ```
3. 从 URL 提取 `VIDEO_ID`。
4. 保留原始 frontmatter（title, source, author, published, tags 等），补充 `video-id` 字段。

**Stage 1 检查点**：
- [ ] URL 已净化，无 `index=`/`list=`/`yu26` 等参数
- [ ] frontmatter 保留并补充 `video-id`

---

### Stage 2：句子级拆分与标点重构

#### 2.1 句子拆分

基于 Stage 0 获取的精确句子列表，进一步微调：

- 单句长度 > 40 词或持续时间 > 15 秒时，检查是否可在从句边界（`, but` `, and` `, so`）处拆分
- 口语填充词（`um`, `uh`, `like`, `you know`, `I mean`, `sort of`, `kind of`）合理省略或融入句子，不单独成句
- 重复、自我修正压缩为一次表达
- 打断与重叠说话保留核心信息，省略礼貌赘语

#### 2.2 标点符号重构

基于完整内容上下文，统一修订标点：

**英文原文**：
- 引号统一为直引号 `"` 与 `'`（原文弯引号 `“”` `‘’` 修正）
- 省略号统一为 `...`（三个半角句点），去除 `..` 或 `……` 混用
- 破折号统一为 `--` 或 `—`（两端空格）
- 去除无意义的多余空格与连续逗号

**中文译文**：
- 引号统一为 `""`（双引号）与 `''`（单引号），符合现代汉语排版规范
- 省略号统一为 `……`（两个全角省略号字符）
- 破折号统一为 `——`（两个全角破折号）
- 顿号 `、` 与逗号 `，` 区分使用：并列词语用顿号，分句间用逗号
- 去除行首悬挂虚词（的/了/和/而）
- 删除无意义的空格与半角标点混用

**Stage 2 检查点**：
- [ ] 句子已按语义单元拆分，无 >40 词超长句
- [ ] 英文标点已统一为 `"` `'` `...`
- [ ] 中文标点已统一为 `""` `''` `……` `——`

---

### Stage 3：内容分层与标题生成

**全自动分析全文论证结构**，生成层级标题：

| 层级 | 用途 | 命名要求 |
|------|------|----------|
| `##` | 大章节 | 凝练概括 3-8 分钟内容区块，如 "三、为什么必须关注 Vibe Coding：指数级增长" |
| `###` | 细分主题 | 提取核心论点或方法论节点，如 "3.1 METR 数据：AI 任务长度每七个月翻倍" |
| `####` | 子议题 | 用于复杂节点下的展开，如 "4.4.2 叶节点（leaf nodes） vs 核心架构" |

**标题命名铁律**：
- 必须有总结性，不能是泛泛的"引言""正文""结论"
- 包含核心概念关键词（中英文对照首次出现）
- 字数控制在 25 字以内
- 禁止废话："关于……的介绍" → 直接写 "……"

**Stage 3 检查点**：
- [ ] `##` 标题覆盖全文主要论证区块
- [ ] `###` 标题提取核心论点，非泛泛描述
- [ ] 标题字数均 ≤25 字

---

### Stage 4：章节内容概览与学习借鉴

**每个 `##` 大章节标题下方**必须包含两个区块：

#### 4.1 内容概览（流程图形式）

使用 Mermaid 流程图概括该章节的论证脉络或操作步骤：

```markdown
```mermaid
flowchart LR
    A[论点/起点] --> B[展开/证据]
    B --> C[结论/行动]
```
```

- 流程图节点用中文，必要时附英文术语
- 节点数 3-6 个，反映核心逻辑链
- 复杂章节可用 `flowchart TD` 纵向展开

#### 4.2 学习借鉴（知识卡片）

使用 Obsidian Callout 提炼可迁移的方法论或洞见：

```markdown
> [!tip] 学习借鉴
> - 核心洞见 1：一句话概括
> - 核心洞见 2：一句话概括
> - 可行动作：具体建议
```

- 每条不超过 30 字
- 聚焦"可迁移"——读者能直接用在其他场景
- 不重复原文，是提炼后的升华

**Stage 4 检查点**：
- [ ] 每个 `##` 下方都有 Mermaid 流程图
- [ ] 每个 `##` 下方都有 `> [!tip] 学习借鉴`
- [ ] 两者缺一不可

---

### Stage 5：去欧化口语翻译（**并行 subagent 批译**）

逐句翻译为**自然口语中文**，同时**保留原讲稿人的语言特色**（语气节奏、用词习惯、修辞风格）。

> **执行铁律**：必须用并行 subagent 批译，**禁止主 agent 串行逐句翻译**。串行 503 句要 30+ 分钟，并行 6-8 批 5 分钟内完成。

#### 5.0 执行计划（必须严格按此执行）

**输入**：`sentences_final.json`（Stage 0-2 处理后的句子数组）

**步骤**：
1. 加载 `sentences_final.json`，统计句子总数 `N`
2. 计算批次：`batch_size = ceil(N / 7)`，目标 6-8 批，每批 60-90 句
3. 同时（并行）spawn 多个 `general-purpose` subagent，每个负责一段连续区间 `[start, end)`
4. 每个 subagent 收到：
   - 完整的 Stage 5 翻译规则（结构性规则、翻译腔清零、口语学术平衡、术语规范）
   - 该批次的句子数组（含 index 与 text）
   - 输出格式硬要求（见 §5.1）
5. 主 agent 收齐所有 subagent 返回的 JSON 片段，按 index 顺序拼接为完整数组
6. 写入 `translations.json`，验证 `len == N`
7. 验证无 ASCII 双引号 `"`、无空字符串、无英文残留

**关键**：所有 subagent 在**同一条主 agent 消息**中并行 spawn（多个 Agent 工具调用并列），不要串行等待。

**spawn 模板**（主 agent 在一条消息内并行发起所有批次）：

```python
# 伪代码示意，主 agent 在单条消息内并列调用：
batch_1: Agent(prompt="翻译规则+句子[0:75]+输出规范", run_in_background=False)
batch_2: Agent(prompt="翻译规则+句子[75:150]+输出规范", run_in_background=False)
...
batch_7: Agent(prompt="翻译规则+句子[450:503]+输出规范", run_in_background=False)
```

#### 5.1 Subagent 输出规范（强制）

每个 subagent **必须**返回纯 JSON 数组，格式如下：

```json
[
  {"i": 0, "cn": "中文译文一。"},
  {"i": 1, "cn": "中文译文二。"},
  ...
]
```

**硬要求**（违反任意一条则该 subagent 输出作废，需重译）：
- `i` 字段为该句在全局数组的 index（int）
- `cn` 字段为中文译文（string）
- **绝不**在 `cn` 中使用 ASCII 双引号 `"` 或单引号 `'`，必须用中文弯引号 `""` `''`
- 内层引号需嵌套时，外层 `""`，内层 `''`，避免 JSON 字符串转义错误
- 译文末尾保留中文句号 `。`、问号 `？`、感叹号 `！`，不留英文标点
- 无空字符串、无 placeholder、无 "（待译）" 等占位
- 输出严格为 JSON，前后不加 markdown 代码块、不加解释文字

**count 校验**：subagent 返回数组长度必须 == 该批次输入句数；否则主 agent 必须重新派发该批次。

#### 5.2 主 agent 合并与写入

主 agent 收到所有 subagent 输出后：

```python
all_translations = []
for batch_result in batches:
    all_translations.extend(batch_result)  # 已按 index 排序
all_translations.sort(key=lambda x: x["i"])
final_list = [item["cn"] for item in all_translations]
assert len(final_list) == N
# 写入 translations.json
```

`translations.json` 仅保存中文字符串数组（不带 index 字段），与 `sentences_final.json` 一一对应。

#### 5.3 翻译规则（subagent 必须严格执行）

**结构性规则**：
- 单句 > 50 字必拆
- 修饰链 > 7-8 字必拆
- "的"字三层嵌套（X 的 Y 的 Z 的 W）必拆
- 英文被动 → 中文主动 / 使动 / 无主句
- "被"字带不如意色彩，中性被动可省"被"
- "对 X 的分析" → "分析 X"；"X 的重新配置" → "重新配置 X"

**翻译腔清零**：
- 根除："的"字泛滥、"被"字滥用、"进行"/"加以"/"予以"空转
- 根除："关于……"前置、"作为……的"框架、"基于……的"长定语
- 不用欧化框架："对于……而言""被认为……的""在……条件下" → 改为汉语原生句式

**口语与学术平衡**：
- 日常叙述用**口语节奏**，字幕按语义单元 / 呼吸单元断行
- 学术内容专业术语必须精确，保留"可理解的陌生感"
- 口语填充词合理省略，重复、自我修正压缩为一次表达
- 每字必须必要：删除它，意思是否受损？不受损则删

**讲稿人语言特色保留**：
- 若讲者喜欢用反问，中文保留反问语气
- 若讲者喜欢用类比，中文保留类比结构
- 若讲者语气轻松/严肃/激昂，中文用相应语气词和句式体现
- 不把所有讲者都翻译成同一种"标准 AI 中译腔"

**连接与语气**：
- 连词克制："因此、但是、和、同时、所以、由于"每段不超过 1 次
- 段首无套式：不用"首先/其次/最后/综上所述/总而言之"作段首过渡，直接进入论点
- 动词强（主张/指出/反驳，非"作出主张"）、判断明（是/不是/未必）、指称清（用具体名词不用"它"）
- 程度副词不丢：very, quite, rather, slightly, deeply 等必须译出

**术语与人名规范**：
- **专业术语**：首次出现必须中译并附英文原文，格式：`中文译名（English Term）`。后续出现用中文。
  - 例：`氛围编程（vibe coding）`、`编程智能体（coding agents）`、`叶节点（leaf nodes）`
- **英文人名**：参照新华社译名室标准，首次出现附标准中译。
  - 例：`埃里克·施伦茨（Erik Schluntz）`、`安德烈·卡帕蒂（Andre Karpathy）`、`巴里·曾（Barry Zeng）`
  - 常见名可保留原文习惯用法，但须附标准译名至少一次
- **作品/书名**：首次出现附英文原名。
  - 例：《构建高效智能体》（Building Effective Agents）

**Stage 5 检查点**：
- [ ] 已用并行 subagent 批译，单条主 agent 消息内并列发起所有批次
- [ ] 译文 JSON 无 ASCII 双引号 `"` 或单引号 `'`，引号一律为 `""` `''`
- [ ] 译文长度 == 句子数 N，**禁用 fix_align.py 救火**（首次就要对齐）
- [ ] 译文无"进行/加以/予以"空转
- [ ] 首次出现的术语和人名已附英文原文
- [ ] 单句未超过 50 字

---

### Stage 6：时间戳生成（双版本紧凑格式）

**每句时间戳格式**（删除冗余注释，一行搞定）：

```markdown
- 【MM:SS-MM:SS】[▶JV](jv://?url=https://www.youtube.com/watch?v=VIDEO_ID&time=HH:MM:SS.mmm-HH:MM:SS.mmm&app=jump-video-extension);[▶ME](https://www.youtube.com/watch?v=VIDEO_ID&t=XXs)
```

**格式细节**：
- `【MM:SS-MM:SS】`：人类可读的时间范围，起始 → 结束
- `[▶JV](jv://...)`：JumpVideo 浏览器扩展跳转链接，时间精确到毫秒
- `[▶ME](https://...&t=XXs)`：Media Extended 插件跳转链接，`t` 为起始秒数（向下取整）
- 两个链接用 `;` 分隔，无空格
- **删除** `<!-- JumpVideo -->` 和 `<!-- Media Extended -->` 注释标识

#### §尾部 buffer（强制）

**问题来源**：JV 在点击时间戳后**自动停止**于 `end` 时刻。字符比例插值天然**低估**句末时刻——讲者在句尾会减速、加重音、换气，最后 1-2 个词所占的实际时间比按字符比例分得的多 200-500 ms。结果是听起来"最后一个词被切了"。

**强制规则**（不可省略）：
- **每个句子的 `end` 都加 0.45 秒尾部 buffer**
- buffer 上限 clamp 到下一句 `end - 0.05s`（不可吞掉整句下一句，但与下一句首词轻微重叠是可接受的）
- 最后一句的 buffer clamp 到视频最末时刻 + 0.5s

**实现模板**（参考 `split_long_sentences.py`）：

```python
END_BUFFER = 0.45
VIDEO_END = max(s["end"] for s in result) + 0.5

for i, s in enumerate(result):
    raw_end = s["end"] + END_BUFFER
    if i + 1 < len(result):
        cap = result[i + 1]["end"] - 0.05  # 不超过下一句末
    else:
        cap = VIDEO_END
    s["end"] = round(min(raw_end, cap), 3)
```

**为什么是 0.45s**（不是 0.3 也不是 1.0）：
- 0.3s 以下：仍然能听到末词被切（特别是辅音收尾如 `that`、`fix`、`cut`）
- 0.5s 以上：在快速短句段落（演讲高潮）会盖住下一句开头
- 0.45s 是经验校准的折中值；如果某视频普遍仍切，可调到 0.55-0.6s 重新生成

**Stage 6 检查点**：
- [ ] 每个句子都有 `[▶JV]` + `[▶ME]` 双版本链接
- [ ] JV 时间格式为 `HH:MM:SS.mmm`，含前导零
- [ ] 无 `<!-- -->` 注释残留
- [ ] **每个句末 `end` 已加 0.45s buffer，clamp 至 `next.end - 0.05`**

---

### Stage 7：双语对照格式化（严格一句对一句）

**每句呈现结构**（删除冗余标识，干净列表缩进）：

```markdown
---
- 【MM:SS-MM:SS】[▶JV](jv://...);[▶ME](https://...)
	- English original sentence here.
		- 中文译文在这里。
---
```

**纯中文内容时每句呈现结构**（不保留英文行）：

```markdown
---
- 【MM:SS-MM:SS】[▶JV](jv://...);[▶ME](https://...)
	- 中文原文句子在这里。
---
```

**格式铁律**：
- **删除** `**EN:**` 标识，英文直接以列表项呈现
- **删除** `> [!中译]` Callout，中文直接以二级缩进列表呈现
- 英文缩进一级（tab），中文缩进两级（tab）
- 句间用 `---` 水平分隔线隔开
- 一句英文严格对照一句中文，1:1 对应，不可多句合并
- 若英文一句过长（> 40 词），拆分为两句英文，中文也对应拆分为两句
- 若英文包含多个并列短句（如 "A, B, and C"），视为一句整体翻译
- 中文译文必须在语义、语气、信息上与该句英文完全对等，不可跨句补偿信息
- **纯中文内容时**：不保留英文行，直接以时间戳 + 中文呈现

**Stage 7 检查点**：
- [ ] 无 `**EN:**` 标识
- [ ] 无 `> [!中译]` Callout
- [ ] 英文一句、中文一句，1:1 对应
- [ ] 纯中文内容不保留英文行

---

## 输出文件结构

```markdown
---
title: "原始标题"
source: https://www.youtube.com/watch?v=VIDEO_ID
video-id: VIDEO_ID
author:
  - "[[作者名]]"
published: YYYY-MM-DD
clips-source: "[[Clippings/原始文件名.md]]"
tags:
  - "#翻译"
  - "#双语字幕"
  - 视频主题标签
---

# 原始标题

> **演讲信息**
> - 演讲者：Name（职位）
> - 活动：Event Name
> - 视频地址：[YouTube](净化后的URL)
> - 核心论点：（一句话概括）

---

# 内容总览

> **阅读提示**：
> - 点击 `[▶JV]` 使用 JumpVideo 浏览器扩展跳转
> - 点击 `[▶ME]` 使用 Media Extended 插件在 Obsidian 内跳转
> - 点击下方目录标题可跳转到对应章节

## 目录

- [[#一、大章节标题|一、大章节标题]]
  - [[#1.1 细分主题|1.1 细分主题]]
  - [[#1.2 细分主题|1.2 细分主题]]
- [[#二、大章节标题|二、大章节标题]]
  - [[#2.1 细分主题|2.1 细分主题]]
- ...

---

# 正文

## 一、凝练的大章节标题

```mermaid
flowchart LR
  A[节点1] --> B[节点2]
  B --> C[节点3]
```

> [!tip] 学习借鉴
> - 洞见 1
> - 洞见 2

### 1.1 细分主题标题

---
- 【0:00-0:03】[▶JV](jv://...);[▶ME](https://...)
	- Welcome.
		- 欢迎。
---
- 【0:03-0:12】[▶JV](jv://...);[▶ME](https://...)
	- Today I'm going to talk about vibe coding.
		- 今天我要聊的是氛围编程（vibe coding）。
---

### 1.2 下一个细分主题

...

## 二、下一大章节

...
```

**目录生成规范**：
- 目录位于正文前独立区块，标题为 `# 内容总览`
- 目录条目用 **Obsidian wikilink** 格式：`[[#完整标题|显示文本]]`，例如 `- [[#一、上线—掉线—再上线|一、上线—掉线—再上线]]`
- **禁用** GitHub-slug `[标题](#slug)`：Obsidian 对中文/标点的 slug 化与 GitHub 不一致，会导致点击失效
- 目录只显示到 `###` 层级，`####` 子议题不出现在目录中
- 目录中 wikilink 内的标题文本必须与正文 `##/###` 标题 1:1 完全一致（包括序号、空格、标点）

---

## !!! 强制自检清单（输出前必须逐条勾选，未勾选完不得提交）

**格式与链接**：
- [ ] 每个句子都有 `[▶JV]` + `[▶ME]` 双版本紧凑链接
- [ ] JV 时间格式为 `HH:MM:SS.mmm`（含前导零）
- [ ] **Stage 0 算法采用 `eff_end = min(start+duration, next.start)` 截断窗口**（脚本日志 `non-monotonic transitions: 0`）
- [ ] **每个句末时间戳含 0.45s 尾部 buffer，clamp 至下一句末 -0.05s**
- [ ] 无 `<!-- JumpVideo -->` / `<!-- Media Extended -->` 注释
- [ ] 无 `**EN:**` 标识、无 `> [!中译]` Callout
- [ ] URL 已净化，无 `index=`/`list=`/`yu26` 等参数
- [ ] 文件顶部保留原始 frontmatter 并补充 `video-id`

**结构与标题**：
- [ ] 标题层级已自动生成：`##` 大章节 + `###` 细分主题
- [ ] 每个 `##` 章节下都有 Mermaid 流程图 + `> [!tip] 学习借鉴`
- [ ] 文件顶部包含 `# 内容总览` 目录，**目录条目用 Obsidian wikilink `[[#完整标题|显示文本]]`**（禁用 GitHub-slug `(#slug)`）
- [ ] 目录中的标题与正文 `##/###` 标题完全一致（wikilink 内文字必须 1:1 匹配）

**内容对照**：
- [ ] 原文语言判断正确：英文则翻译，中文则不翻译仅格式化
- [ ] 严格一句对一句：英文一句、中文一句，1:1 对应
- [ ] 纯中文内容不保留英文行
- [ ] 翻译去欧化：无"进行"/"加以"/"予以"空转，无滥用"被"字
- [ ] 标点符号已重构：中文用 `……` `——` `""`，英文用 `"` `'` `...`
- [ ] 单句未超过 50 字，修饰链未超过 7-8 字
- [ ] 首次出现的术语附英文原文：中文（English）
- [ ] 首次出现的人名附新华社标准译名：标准译名（English）
- [ ] 段首无"首先/其次/综上所述"套式
- [ ] 连词每段不超过 1 次

**执行效率**：
- [ ] **翻译用并行 subagent 批译**（同一条主 agent 消息内并列发起 6-8 批，禁串行）
- [ ] Subagent JSON 输出无 ASCII `"` `'`，仅用中文 `""` `''`（避免 `fix_quotes.py` 救火）
- [ ] 翻译数组 `len == sentences_final.json` 长度（禁用 `fix_align.py` 救火）
- [ ] 全流程已通过 `pipeline.ps1` 一键执行，未中途人工干预

---

## 时间戳精度与 ASR 偏差校准

**问题来源**：YouTube 自动字幕（ASR）使用滑动窗口生成片段。窗口大小约 4-5s，步长约 2s，相邻片段在显示文本上高度重叠（同一时刻的语音被相邻 2-3 个片段重复包含）。如果直接用片段的 `start + duration` 框句子，每个词的时刻会被拉宽到相邻片段共同覆盖的范围（2-4 秒），与实际 speech onset 错位严重。

**默认策略**（已固化在 Stage 0 算法中，不要回退）：
1. 使用"有效语音窗口"`eff_end = min(start+duration, next_frag.start)` 截断每个片段
2. 在 `eff_end` 内做字符比例插值，定位每个词的真实时刻
3. 跨片段做"前后缀去重"，避免同一个词被两个片段都计入
4. 句子起始 = 该句首词时刻；句子结束 = 下一句起始（最后一句用末词时刻）
5. 句末统一加 0.45s buffer（Stage 6 §尾部 buffer），clamp 到下一句末 -0.05s
6. 强制 `fmt_time_full()` 始终返回 `HH:MM:SS.mmm` 格式（含前导零），确保 JumpVideo 协议正确解析

**用户校准流程**（仅当上述算法仍有可见偏差时才需要，多数情况下不必启用）：
1. 用户在视频中找到 3-5 个清晰可辨的句子，记录实际视频时间（精确到秒）
2. 用户提供 `(笔记时间, 实际时间)` 对照组
3. 使用分段线性插值（piecewise linear interpolation）重新计算所有时间戳
4. 更新 `offset` 为插值函数，重新生成文件

**校准脚本模板**（供参考）：
```python
# 用户提供的对照点：(sentence_index, actual_seconds)
calibration_points = [
    (0, 2.5),      # 第一句实际在 2.5s 开始
    (100, 65.0),   # 第101句实际在 65s 开始
    (269, 1865.0), # 最后一句实际在 1865s 开始
]

# 分段线性插值
from bisect import bisect_left
idxs, actuals = zip(*calibration_points)
def calibrated_start(sentence_idx, raw_start):
    pos = bisect_left(idxs, sentence_idx)
    if pos == 0:
        return actuals[0] + (raw_start - sentences[idxs[0]]['start'])
    if pos >= len(idxs):
        return actuals[-1] + (raw_start - sentences[idxs[-1]]['start'])
    i1, i2 = idxs[pos-1], idxs[pos]
    a1, a2 = actuals[pos-1], actuals[pos]
    ratio = (sentence_idx - i1) / (i2 - i1)
    return a1 + (a2 - a1) * ratio
```

**精度预期**：
- 旧算法（min/max 框句）：±1-3 秒，最后 1-2 词常被切——**已弃用**
- 新算法（eff_end + 字符插值 + 0.45s buffer）：句子起始 ±0.3s，句子结束发音完整无切音
- 用户 3-5 点校准后：±0.1-0.2s（接近实用极限，仅在罕见 ASR 异常视频需要）
