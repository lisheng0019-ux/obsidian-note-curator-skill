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
- 可选集成 `JimLiu/baoyu-skills`
  - `baoyu-translate`
  - `baoyu-article-illustrator`
  - `baoyu-cover-image`
  - `baoyu-infographic`
  - `baoyu-diagram`
  - `baoyu-slide-deck`

## 目录结构

```text
obsidian-note-curator-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── config/
│   └── defaults.json
├── references/
│   ├── baoyu-content-workflows.md
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
  "attachments_folder": "D:\\path\\to\\your\\vault\\图片"
}
```

脚本读取笔记时，如果没有显式传入 `--vault`，会优先使用 `vault_root`。保存或下载图片时，如果没有显式传入 `--attachments-folder`，会优先使用 `attachments_folder`。这能避免 Windows 命令行传递中文路径时出现编码问题。

网上搜索下载的图片默认会放到：

```text
<attachments_folder>\web-images\<note-slug>\
```

## 依赖

基础功能只需要：

- Claude Code / Claudian
- Python 3
- 一个 Obsidian vault

可选增强：

- `JimLiu/baoyu-skills`
- 支持图片生成的运行环境或 API key

## 推荐搭配 baoyu-skills

如果你希望启用翻译、配图、封面、信息图、幻灯片等更完整的内容生产能力，可以安装：

```bash
/plugin marketplace add JimLiu/baoyu-skills
/plugin install baoyu-skills@baoyu-skills
```

或按你的 Claude / Claudian 环境支持的方式安装对应 skills。

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

### 下载并插入网上图片

```bash
python scripts/obsidian_image_helper.py download --vault <vault> --note <note> --url <image-url> --source-page <page-url> --caption "<caption>" --insert
```

默认会保存到：

```text
Attachments/web-images/<note-slug>/
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
Attachments/covers/
Attachments/illustrations/<note-slug>/
图片/web-images/<note-slug>/
Attachments/infographics/
Attachments/diagrams/
Attachments/slides/<note-slug>/
Slides/<note-slug>/
```

## 设计原则

- Obsidian 笔记是 source of truth。
- 保留 wikilinks，尽量不破坏原有 vault 结构。
- 优先使用 vault 内已有图片，再考虑网上搜索、生成或外部来源。
- 网上图片必须保存来源记录，发布用途需要优先选择许可清晰的图片。
- 视觉资产必须保存到 vault 内，并使用相对路径引用。
- 不把 API key、cookie、平台凭据写进笔记。
- 没有安装 baoyu-skills 时，仍能降级完成基础整理、翻译、SVG 图解或生成提示词。

## 许可证

按你的仓库策略补充许可证文件。
