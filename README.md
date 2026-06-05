# Obsidian Note Curator Skill

一个面向 Obsidian + Claudian / Claude Code 的笔记整理 skill，用于把粗糙笔记整理成结构清晰、可检索、可链接、带视觉资产的知识库条目。

它的核心定位不是单纯“润色 Markdown”，而是作为 Obsidian 工作流中枢：负责识别 vault、解析图片引用、理解图片内容、整理笔记结构，并在需要时协调翻译、配图、封面、信息图、图解和幻灯片生成。

## 功能

- 整理 Obsidian Markdown 笔记
  - 标题层级
  - 摘要
  - frontmatter
  - tags
  - backlinks / wikilinks
  - 行动项
- 识图与图片理解
  - 解析 `![[image.png]]`
  - 解析 Markdown 图片
  - 解析 HTML `<img>`
  - 支持 OCR、截图理解、图表/流程图解读
- 自动为笔记添加图片
  - 扫描 vault 内已有图片
  - 根据标题、标签、正文关键词推荐匹配图片
  - 自动插入 Obsidian wiki embed
  - 支持选择插图风格，默认手绘风格，也可让大模型按场景自动选择
- 网上搜索相关图片
  - 根据笔记分析结果生成图片搜索查询
  - 对候选图片进行语义匹配、来源可信度、清晰度和可用授权判断
  - 下载最匹配图片到 vault，并写入来源记录
- 生成或协调视觉资产
  - 文章配图
  - 封面图
  - 信息图
  - SVG 图解
  - 幻灯片素材
- 原生内容增强工作流
  - 翻译
  - 文章配图
  - 封面图
  - 信息图
  - SVG 图解
  - 幻灯片素材

## 目录结构

```text
obsidian-note-curator-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── config/
│   └── defaults.json
├── references/
│   ├── content-enrichment-workflows.md
│   └── obsidian-image-workflow.md
└── scripts/
    └── obsidian_image_helper.py
```

## 安装

### 安装到单个 Obsidian vault

把本仓库放到你的 vault：

```text
<your-vault>/.claude/skills/obsidian-note-curator/
```

### 安装为全局 Claude Code skill

放到用户级 skills 目录：

```text
~/.claude/skills/obsidian-note-curator/
```

Windows 示例：

```powershell
git clone https://github.com/lisheng0019-ux/obsidian-note-curator-skill.git "$HOME\.claude\skills\obsidian-note-curator"
```

## 默认路径配置

可以创建本机配置文件：

```text
config/defaults.json
```

内容示例：

```json
{
  "vault_root": "D:\\path\\to\\your\\vault",
  "attachments_folder": "D:\\path\\to\\your\\vault\\图片",
  "default_image_style": "hand-drawn",
  "image_style_mode": "default",
  "generated_asset_folder_pattern": "{note-title}-封面-插图",
  "generated_image_text_language": "zh-CN",
  "write_generation_prompts_to_note": false
}
```

脚本读取笔记时，如果没有显式传入 `--vault`，会优先使用 `vault_root`。保存或下载图片时，如果没有显式传入 `--attachments-folder`，会优先使用 `attachments_folder`。这能避免 Windows 命令行传递中文路径时出现编码问题。

`default_image_style` 控制默认插图/生成图风格，默认值为 `hand-drawn`。`image_style_mode` 设为 `auto` 时，会让 Claude 根据笔记场景自动选择更合适的图片风格。

`generated_asset_folder_pattern` 控制生成资产目录，默认会按“笔记标题-封面-插图”创建笔记专属图片文件夹。`generated_image_text_language` 默认 `zh-CN`，表示生成图片里的标题、标签、说明文字优先使用中文。`write_generation_prompts_to_note` 默认为 `false`，避免把提示词写进笔记正文，污染 Obsidian 关系图谱。

网上搜索下载的图片默认会放到：

```text
<attachments_folder>\<笔记标题>-封面-插图\网页图片\
```

## 依赖

基础功能只需要：

- Claude Code / Claudian
- Python 3
- 一个 Obsidian vault

可选增强：

- 支持图片生成的运行环境或 API key

## 使用示例

在 Claudian / Claude Code 中对当前笔记说：

```text
整理这篇 Obsidian 笔记，补充摘要、标签和双链，并分析里面的图片。
```

```text
帮我把这篇笔记翻译成中文，保留原有 Obsidian 链接和图片。
```

```text
为这篇笔记生成一张封面图，并写入 frontmatter。
```

```text
根据这篇笔记生成一张信息图，放到摘要后面。
```

```text
把这篇技术笔记画成 SVG 架构图，并插入到相关小节。
```

```text
把这篇笔记整理成幻灯片大纲，并生成相关 slide images。
```

## 图片辅助脚本

本 skill 内置 `scripts/obsidian_image_helper.py`，用于稳定处理 Obsidian 图片引用。

### 查看笔记图片和 vault 图片库存

```bash
python scripts/obsidian_image_helper.py inventory --vault <vault> --note <note>
```

### 推荐本地图片

```bash
python scripts/obsidian_image_helper.py suggest --vault <vault> --note <note> --limit 8
```

### 根据笔记生成网上搜图查询

```bash
python scripts/obsidian_image_helper.py web-query --vault <vault> --note <note>
```

Claude / Claudian 会用输出的 `primary_query` 和 `queries` 去搜索图片，并根据 `match_criteria` 选择最匹配的候选图。

### 查看当前笔记的视觉资产目录规划

```bash
python scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note>
```

默认返回的目录结构类似：

```text
图片/<笔记标题>-封面-插图/
图片/<笔记标题>-封面-插图/封面/
图片/<笔记标题>-封面-插图/插图/
图片/<笔记标题>-封面-插图/网页图片/
图片/<笔记标题>-封面-插图/信息图/
图片/<笔记标题>-封面-插图/图解/
图片/<笔记标题>-封面-插图/幻灯片/
图片/<笔记标题>-封面-插图/prompts/
```

`prompts/` 只用于必要时保存旁路提示词文件，不会自动插入到笔记结构中。

指定图片风格：

```bash
python scripts/obsidian_image_helper.py web-query --vault <vault> --note <note> --style hand-drawn
```

让大模型按笔记场景自动选择风格：

```bash
python scripts/obsidian_image_helper.py web-query --vault <vault> --note <note> --style auto
```

内置风格包括：

- `hand-drawn`：默认手绘风格，适合知识笔记、学习笔记和概念解释。
- `technical-schematic`：适合架构、流程、API、数据库、工程系统。
- `infographic`：适合总结、对比、指标、时间线和高密度知识卡片。
- `editorial`：适合随笔、观点、文化、历史和叙事概念。
- `minimal`：适合清单、备忘、参考笔记和简洁摘要。
- `photo`：适合真实人物、地点、产品、事件、物体和现场记录。

### 下载并插入网上图片

```bash
python scripts/obsidian_image_helper.py download --vault <vault> --note <note> --url <image-url> --source-page <page-url> --caption "<caption>" --style hand-drawn --insert
```

默认会保存到：

```text
图片/<笔记标题>-封面-插图/网页图片/
```

同时生成 `.source.md` 文件记录来源，方便之后追溯。

### 插入图片

```bash
python scripts/obsidian_image_helper.py apply --vault <vault> --note <note> --image <image-path> --position hero --caption "<caption>"
```

插入到指定标题下：

```bash
python scripts/obsidian_image_helper.py apply --vault <vault> --note <note> --image <image-path> --position after-heading --heading "<heading>" --caption "<caption>"
```

## 生成资产的默认保存位置

为方便 Obsidian 后续管理，建议生成资产放在这些目录：

```text
图片/<笔记标题>-封面-插图/封面/
图片/<笔记标题>-封面-插图/插图/
图片/<笔记标题>-封面-插图/网页图片/
图片/<笔记标题>-封面-插图/信息图/
图片/<笔记标题>-封面-插图/图解/
图片/<笔记标题>-封面-插图/幻灯片/
图片/<笔记标题>-封面-插图/prompts/
Slides/<note-slug>/
```

## 设计原则

- Obsidian 笔记是 source of truth。
- 保留 wikilinks，尽量不破坏原有 vault 结构。
- 优先使用 vault 内已有图片，再考虑网上搜索、生成或外部来源。
- 网上图片必须保存来源记录，发布用途需要优先选择许可清晰的图片。
- 视觉资产必须保存到 vault 内，并使用相对路径引用。
- 生成图片内的可见文字默认使用中文。
- 提示词不写入笔记正文；需要留档时只保存到 `prompts/` 旁路目录。
- 不把 API key、cookie、平台凭据写进笔记。
- 即使没有额外第三方 skill，也能完成基础整理、翻译、SVG 图解或生成提示词。

## 许可证

按你的仓库策略补充许可证文件。
