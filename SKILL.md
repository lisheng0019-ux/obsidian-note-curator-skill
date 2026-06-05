---
name: obsidian-note-curator
description: Organize and enrich Obsidian Markdown notes in Claude Code/Claudian. Use for note cleanup, structure rewriting, frontmatter/tags/backlinks, image understanding/OCR/captions, automatic note images from local vault or web image search, translation, article illustrations, cover images, infographics, SVG diagrams, slide decks, Chinese or multilingual note curation, Obsidian vault work, .md notes, or Claudian workflows.
---

# Obsidian Note Curator

## Goal

Turn rough Obsidian notes into clean, linked, visually useful knowledge assets while preserving the user's voice and vault conventions.

Use Claude's vision capability for image understanding. Use the bundled helper script for deterministic vault scanning, image link resolution, candidate image matching, and safe Markdown insertion.

This skill also supports native content enrichment workflows for translation, illustrations, cover images, infographics, diagrams, and slide material. The Obsidian note remains the source of truth; generated or transformed assets must be saved into the vault and linked back from the note.

## Local Configuration

Read `config/defaults.json` before saving or downloading images. This installation can set:

```json
{
  "vault_root": "<absolute path to the Obsidian vault>",
  "attachments_folder": "<absolute path inside the vault>",
  "default_image_style": "hand-drawn",
  "image_style_mode": "default",
  "image_format_mode": "auto",
  "default_cover_aspect": "16:9",
  "default_illustration_aspect": "4:3",
  "default_infographic_aspect": "3:4",
  "default_diagram_aspect": "auto",
  "default_slide_aspect": "16:9",
  "default_photo_aspect": "4:3",
  "default_card_aspect": "3:4",
  "default_web_image_aspect": "auto",
  "prefer_svg_for_diagrams": true,
  "generated_asset_folder_pattern": "{note-title}-\u5c01\u9762-\u63d2\u56fe",
  "generated_image_text_language": "zh-CN",
  "write_generation_prompts_to_note": false
}
```

When present, use `vault_root` as the default vault if `--vault` is omitted, and use `attachments_folder` as the default Obsidian image attachment base. The attachment folder must stay inside the target vault. Web-sourced and generated images should be saved under the note-specific asset folder inside that base folder unless the user passes an explicit `--attachments-folder`.

Use `default_image_style` as the default style for inserted or generated images. The default is `hand-drawn`. When `image_style_mode` is `auto`, choose a scene-appropriate style from the note context unless the user explicitly names a style.

Use `image_format_mode` to route generated or sourced images by purpose. The default is `auto`, which returns an `image_format` plan with `asset_kind`, `aspect_ratio`, `file_format`, `folder_key`, `target_folder`, and `reason`. Respect explicit user intent over the auto router. Use `prefer_svg_for_diagrams` to choose SVG for technical diagrams when exact labels and reusable markup matter.

Use `generated_asset_folder_pattern` for note-specific visual asset folders. The default pattern names the folder from the analyzed note title plus the Chinese words for cover and illustration. Use `generated_image_text_language` for visible text inside generated images; default to Chinese. Keep `write_generation_prompts_to_note` false unless the user explicitly asks to put prompts in the note.

## Capability Router

Choose the narrowest workflow that satisfies the user's request:

| Request intent | Preferred workflow |
|----------------|--------------------|
| Clean up, structure, tag, summarize, link notes | Core note curation workflow |
| Understand screenshots, diagrams, photos, or scanned text | Vision + image inventory workflow |
| Add existing local images | Image suggestion + insertion workflow |
| Search the web for matching images and insert the best result | Web image search workflow |
| Choose or auto-select image style | Image style workflow |
| Translate a note or source material | Translation workflow |
| Add section illustrations | Article illustration workflow |
| Create a note cover | Cover image workflow |
| Make a visual summary or dense knowledge image | Infographic workflow |
| Draw architecture/process/concept diagrams | Diagram workflow |
| Turn a note into presentation material | Slide deck workflow |

No external skill package is required for these workflows. Use native Claude/Codex capabilities, configured image-generation tools, web/image search tools, and the bundled helper script to save Obsidian-shaped outputs.

## Workflow

1. Determine the vault root and target note.
   - Prefer the current working directory when it contains `.obsidian/`.
   - If a target note path is provided, use it directly.
   - If Claudian passes selected text only, improve that text and ask for the note path before editing files.

2. Inspect the note and image inventory.
   - Run:

```bash
python scripts/obsidian_image_helper.py inventory --vault <vault> --note <note>
```

   - Read the output to find existing image embeds, unresolved links, and candidate local images.

3. Understand existing images.
   - For each resolved image relevant to the task, inspect it with available multimodal/vision support.
   - Extract visible text, subject, entities, diagram structure, screenshot UI state, date-like details, and quality issues.
   - Do not invent unseen details. Mark uncertainty explicitly.

4. Restructure the note.
   - Preserve the user's language unless asked to translate.
   - Keep Obsidian wikilinks intact.
   - Prefer clear H1/H2/H3 hierarchy, concise summary, useful tags, source/provenance fields, and action items when present.
   - Add or update frontmatter only when it improves retrieval.
   - Keep original claims traceable; do not silently discard important information.

5. Run specialized enrichment when requested.
   - Before generating visual assets, run:

```bash
python scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note>
```

   - Use the returned folders for covers, illustrations, infographics, diagrams, slide images, and prompt sidecars.
   - Use the returned `image_format` plan for image purpose, aspect ratio, file format, and target folder.
   - If the requested output type is explicit, pass `--asset-kind cover`, `illustration`, `infographic`, `diagram`, `slide`, `photo`, `card`, or `web-image`.
   - Make visible text inside generated images Chinese by default.
   - Do not insert image-generation prompts into the note body.
   - Translation: see [content enrichment workflows](references/content-enrichment-workflows.md#translation).
   - Illustrations: see [content enrichment workflows](references/content-enrichment-workflows.md#article-illustrations).
   - Cover images: see [content enrichment workflows](references/content-enrichment-workflows.md#cover-images).
   - Infographics: see [content enrichment workflows](references/content-enrichment-workflows.md#infographics).
   - Diagrams: see [content enrichment workflows](references/content-enrichment-workflows.md#diagrams).
   - Slide decks: see [content enrichment workflows](references/content-enrichment-workflows.md#slide-decks).

6. Add images automatically when useful.
   - Prefer existing vault images first. Run:

```bash
python scripts/obsidian_image_helper.py suggest --vault <vault> --note <note> --limit 8
```

   - Pick images whose content and filename/path actually match the note.
   - If a chosen image has not been visually inspected, inspect it before inserting.
   - Insert with:

```bash
python scripts/obsidian_image_helper.py apply --vault <vault> --note <note> --image <image-path> --position hero --caption "<short caption>"
```

   - Use `--position after-heading --heading "<heading text>"` for section-specific images.
   - If local candidates are weak and the user wants web sourcing, run:

```bash
python scripts/obsidian_image_helper.py web-query --vault <vault> --note <note>
```

   - Use the returned query plan with the runtime's web/image search tool.
   - Pass `--style <style>` to force a style, or `--style auto` / `--style-mode auto` to let the model choose a scene-specific style.
   - Pass `--asset-kind <kind>` when searching for a cover, infographic, diagram, slide image, photo, card, or web image with a specific output shape.
   - Compare candidates by semantic match, source trust, image clarity, license/usability, and caption fit.
   - Download and insert the best approved image with:

```bash
python scripts/obsidian_image_helper.py download --vault <vault> --note <note> --url <image-url> --source-page <page-url> --caption "<short caption>" --style <style> --insert
```

7. If no suitable local image exists.
   - If web/image-generation tools are available and the user allowed external sourcing, create or source a copyright-safe image, place it under the note-specific asset folder, then insert it.
   - Otherwise report the missing image need in the response. Do not add prompt text or "image_needed" notes into the Markdown file unless the user asks.

8. Validate.
   - Re-run `inventory` and confirm all inserted images resolve.
   - Check that image captions are short, useful, and do not repeat nearby prose.
   - Avoid duplicate embeds and avoid putting decorative images between tightly related paragraphs.
   - For generated assets, confirm the output file exists inside the vault and the note uses a vault-relative link.
   - For web-sourced images, confirm a `.source.md` sidecar or equivalent attribution record exists unless the user explicitly disabled it.

## Image Style Rules

- Default inserted or generated images to `hand-drawn`: clean educational sketch, warm paper texture, low visual noise.
- Let an explicit user style override all defaults. Accept built-in or custom style names.
- If the user asks for automatic scene style, or `image_style_mode` is `auto`, select the style that best fits the note:
  - `hand-drawn`: general knowledge, learning notes, conceptual explanations.
  - `technical-schematic`: systems, architecture, workflows, engineering, APIs, databases.
  - `infographic`: comparisons, summaries, metrics, timelines, dense knowledge cards.
  - `editorial`: essays, opinions, culture, history, narrative concepts.
  - `minimal`: checklists, memos, reference notes, sparse executive summaries.
  - `photo`: real people, places, products, events, objects, field notes.
- For generated images, include the selected style and the helper script's `prompt_modifier` in the image prompt.
- For generated images, require visible text, labels, titles, callouts, and diagram wording to be Chinese unless the user explicitly asks for another language.
- For web image search, prefer candidates that match the selected style, but never choose a weaker or misleading image only for style.
- For existing local images, treat style as a preference. Relevance and accuracy come first.

## Image Format Rules

- Always check `asset-plan` before saving generated or web-sourced visual assets.
- Use explicit user intent first. If the user says cover, infographic, diagram, slide, photo, or card, pass that value as `--asset-kind`.
- If the user does not specify a kind, let the helper's auto router choose from note content.
- Respect the returned `image_format`:
  - `cover`: `16:9`, `png`, save in `cover_folder`.
  - `illustration`: `4:3`, `png`, save in `illustration_folder`.
  - `infographic`: `3:4`, `png`, save in `infographic_folder`.
  - `diagram`: `auto`, `svg` when `prefer_svg_for_diagrams` is true, save in `diagram_folder`.
  - `slide`: `16:9`, `png`, save in `slide_image_folder`.
  - `photo`: `4:3`, `jpg`, save in `illustration_folder` unless a web source format should be preserved.
  - `card`: `3:4`, `png`, save in `infographic_folder`.
  - `web-image`: preserve source format when useful, save in `web_image_folder`.
- For generated raster images, set the image model aspect ratio from `image_format.aspect_ratio` when the model supports it.
- For SVG diagrams, keep labels short, Chinese by default, and derived from the note content.
- If the selected model cannot produce the preferred format, generate the closest supported format and record the final file extension in the source sidecar or response.

## Prompt And Graph Hygiene

- Never insert raw image prompts, prompt drafts, negative prompts, model settings, or generation logs into the note body.
- Do not add prompt-only sections, prompt backlinks, or prompt tags to the note. This keeps Obsidian graph view clean.
- If prompts must be preserved, save them as sidecar files under the asset plan's `prompt_sidecar_folder`, not as linked notes.
- Insert only final assets, concise captions, and stable metadata such as `coverImage` or `visualAssets`.

## Image Placement Rules

- Hero image: after frontmatter and the first H1, only when the note benefits from a visual anchor.
- Section image: after the heading it supports, before the first paragraph or immediately after a short intro sentence.
- Evidence image: near the claim it supports, with a caption that states what the image contributes.
- Screenshot/diagram: include OCR or a brief interpretation below the image when useful.
- Long notes: prefer one hero image plus at most one image per major section.

## Obsidian Conventions

- Use `![[path/to/image.png|caption]]` for vault-local embeds.
- Use relative paths from the vault root, with forward slashes.
- Keep attachments inside the user's existing attachment folder when obvious; otherwise use `Attachments/`.
- If `config/defaults.json` defines `attachments_folder`, treat it as the default attachment folder.
- Use the stable asset subfolders returned by `asset-plan` when creating new image files.
- The default `<note-asset-folder>` is the analyzed note title plus the Chinese words for cover and illustration.
- Use the prompt sidecar folder only for prompt files that are not inserted into the note.
- Do not edit `.obsidian/`, plugin settings, or hidden provider folders unless explicitly asked.
- Do not rename existing notes or images unless the user asks.
- Do not overwrite generated assets unless the user asks; append a short suffix or timestamp on conflict.

## Helper Script

The script supports:

- `inventory`: resolve embedded images and scan vault image candidates.
- `suggest`: rank local images by note title, headings, tags, and filename/path overlap.
- `web-query`: create web image search queries, style guidance, format routing, and match criteria from the note.
- `asset-plan`: return the note-specific visual asset folders, image format plan, and prompt policy.
- `apply`: insert one or more image embeds without duplicating existing links.
- `download`: save a selected web image into the routed vault folder, write source metadata, and optionally insert it.

Read `references/obsidian-image-workflow.md` when the task involves complex image sourcing, captions, or vault conventions.

Read `references/content-enrichment-workflows.md` when the task involves translation, generated illustrations, covers, infographics, diagrams, or slides.
