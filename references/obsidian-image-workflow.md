# Obsidian Image Workflow

## Supported image links

- Wiki embeds: `![[image.png]]`, `![[folder/image.png|caption]]`
- Markdown images: `![alt](folder/image.png)`
- HTML images: `<img src="folder/image.png">`

Prefer wiki embeds for Obsidian-native notes unless the note already consistently uses Markdown image links.

## Vision checklist

When analyzing an image, capture only useful note-level details:

- Subject: what the image depicts.
- Text/OCR: important visible words, labels, numbers, dates, and UI messages.
- Structure: diagram flow, chart axes, table headers, or layout.
- Evidence value: why this image belongs in the note.
- Caption: one short phrase or sentence.

Avoid long descriptions unless the image is the primary source.

## Automatic image selection

Selection order:

1. Existing embeds already in the note.
2. Local vault images with matching filename/path/title/heading keywords.
3. Local images in common folders: `Attachments`, `assets`, `images`, `media`, `resources`.
4. User-approved web-sourced images found through image search.
5. User-approved generated images.
6. Generated covers, illustrations, infographics, diagrams, or slide images created by a specialized workflow.

Reject images that are merely aesthetic when the note is factual or research-oriented.

## External images

If using external images, prefer:

- User-provided files.
- Public domain, Creative Commons, official product/organization assets, or generated images.
- Files saved into the vault with attribution in frontmatter or a nearby source line when required.

Do not hotlink external images unless the user explicitly wants that.

## Web image search

Use this workflow when local vault images do not match the note well enough and the user wants online image sourcing.

1. Generate a search plan from the note:

```bash
python scripts/obsidian_image_helper.py web-query --vault <vault> --note <note>
```

Pass `--style <style>` to force a visual style. Pass `--style auto` or `--style-mode auto` to let the model choose a scene-specific style. If no style is provided, the default is `hand-drawn` unless `config/defaults.json` overrides it.

Pass `--asset-kind <kind>` when the intended output type is known. This sets the recommended aspect ratio, file format, and target folder before search or generation.

2. Search with the runtime's web/image search tool using `primary_query`, then `style_queries`, then alternate `queries` if needed.
3. Collect 5-10 candidates with image URL, source page URL, title/alt text, visible license/source hints, and thumbnail preview when available.
4. Pick the best candidate using these criteria:
   - Semantic relevance to the note title, headings, entities, and claims.
   - Fit to the selected or auto-selected image style.
   - Fit to the selected or auto-routed image format plan.
   - Adds evidence or explanation; not just decoration.
   - Comes from a trustworthy source page.
   - Has usable rights: public domain, Creative Commons, official media, user-approved fair use, or another clearly acceptable source.
   - Has enough resolution and no distracting watermark.
   - Can be captioned honestly in one short sentence.
5. Download and insert the selected image:

```bash
python scripts/obsidian_image_helper.py download --vault <vault> --note <note> --url <image-url> --source-page <page-url> --source-title "<source title>" --caption "<caption>" --style <style> --insert
```

6. Re-run `inventory` and verify the embed resolves.

The `download` command stores web images under the routed note-specific asset folder by default and writes a `.source.md` sidecar with source metadata, style, asset kind, aspect ratio, and file format. Keep that sidecar unless the user explicitly asks not to preserve attribution.

Reject search results when licensing is unclear and the note is intended for publishing. For private research notes, still preserve source metadata so the user can revisit the origin later.

## Image style selection

Default style: `hand-drawn`.

Use a user-provided style exactly when the user specifies one. Use automatic scene selection only when the user asks for it, passes `--style auto`, or sets `image_style_mode` to `auto`.

| Style | Use for |
|-------|---------|
| `hand-drawn` | General learning notes, conceptual explanations, personal knowledge base entries |
| `technical-schematic` | Architecture, workflows, APIs, databases, engineering systems |
| `infographic` | Summaries, comparisons, metrics, timelines, high-density visual cards |
| `editorial` | Essays, opinions, culture, history, narrative concepts |
| `minimal` | Checklists, memos, reference notes, sparse executive summaries |
| `photo` | Real people, places, products, events, objects, field observations |

For generated images, put the chosen style directly in the generation prompt. For web images, prefer matching style but do not let style outrank truthfulness, source quality, or note relevance.

## Image format selection

Run `asset-plan` before saving generated or web-sourced images:

```bash
python scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note>
```

Use `--asset-kind` to override auto-routing when the user names the intended output:

```bash
python scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note> --asset-kind diagram
```

The returned `image_format` object is the source of truth for AI generation and saving. Web downloads keep their own source folder.

| Asset kind | Typical use | Aspect ratio | File format | Folder |
|------------|-------------|--------------|-------------|--------|
| `cover` | Note cover, article header, hero image | `16:9` | `png` | `AI图/封面/` |
| `illustration` | Section image, conceptual visual | `4:3` | `png` | `AI图/插图/` |
| `infographic` | Visual summary, comparison, timeline, metric card | `3:4` | `png` | `AI图/信息图/` |
| `diagram` | Architecture, process, relationship, mind map | `auto` | `svg` when enabled, otherwise `png` | `AI图/图解/` |
| `slide` | Slide image, teaching page, presentation visual | `16:9` | `png` | `AI图/幻灯片/` |
| `photo` | Real people, places, products, events, objects | `4:3` | `jpg` | `AI图/插图/` |
| `card` | Knowledge card, social card, compact summary | `3:4` | `png` | `AI图/信息图/` |
| `web-image` | Downloaded source image | `auto` | preserve source format | `网页图片/` |

For generated raster images, pass the recommended aspect ratio to the image model when supported. For diagrams, prefer SVG when labels, arrows, hierarchy, or exact Chinese text matter. If the selected model cannot produce the preferred format, generate the closest supported format and keep the final extension honest.

Source-first placement:

- Original note images copied or normalized during cleanup: `<asset-root>/原文图片/`
- Web-sourced images downloaded from search: `<asset-root>/网页图片/`
- AI-generated images: `<asset-root>/AI图/<kind>/`
- AI prompt sidecars: `<asset-root>/AI图/prompts/`

## Generated image language and prompt hygiene

- Generated images should use Chinese for visible text by default: titles, labels, callouts, diagram nodes, legends, and captions rendered inside the image.
- Use another language only when the user explicitly asks or the source note requires preserving a proper noun, brand, code symbol, or original quote.
- Do not insert generation prompts into the Obsidian note body.
- Do not add prompt sections, prompt backlinks, prompt tags, or prompt-only notes that would clutter graph view.
- If a prompt must be saved for reproducibility, save it under the prompt sidecar folder returned by `asset-plan` (`AI图/prompts/`), and do not link it from the note unless the user asks.

## Generated asset folders

Use stable folders so future runs can find and reuse assets. If `config/defaults.json` defines `attachments_folder`, place these folders under that configured attachment base; otherwise place them under `Attachments/`.

Before saving generated or web-sourced visual assets, run:

```bash
python scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note>
```

Use `image_format.target_folder` as the preferred folder for AI-generated output. Web downloads use `web_image_folder` even when `--asset-kind` describes the visual purpose.

The default asset root is:

```text
<attachment-base>/<笔记标题>-封面-插图/
```

Use these subfolders:

- Original note images: `<笔记标题>-封面-插图/原文图片/`
- Web-sourced images: `<笔记标题>-封面-插图/网页图片/`
- AI image root: `<笔记标题>-封面-插图/AI图/`
- AI covers: `<笔记标题>-封面-插图/AI图/封面/`
- AI article illustrations: `<笔记标题>-封面-插图/AI图/插图/`
- AI infographics: `<笔记标题>-封面-插图/AI图/信息图/`
- AI diagrams: `<笔记标题>-封面-插图/AI图/图解/`
- AI slide images: `<笔记标题>-封面-插图/AI图/幻灯片/`
- AI prompt sidecars, only when needed: `<笔记标题>-封面-插图/AI图/prompts/`

Prefer descriptive filenames such as `retrieval-augmented-generation-flow.svg` over generic names such as `image1.png`.

## Caption style

- Keep captions under 18 words.
- State what the image adds, not just what it is.
- Use the note's language.
- For screenshots, mention the app/page/state.
- For diagrams, mention the relationship or process shown.

Good:

`![[Attachments/zettelkasten-flow.png|Zettelkasten links from fleeting notes to permanent notes]]`

Weak:

`![[Attachments/zettelkasten-flow.png|Nice image]]`
