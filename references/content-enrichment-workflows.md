# Content Enrichment Workflows for Obsidian

Use this reference when an Obsidian note needs translation, generated visuals, diagrams, or slides. The final artifact must remain Obsidian-friendly: saved inside the vault, linked with vault-relative paths, and traceable from the note.

## General Rules

1. Keep the source note unchanged unless the user asks for in-place rewriting.
2. Before saving generated visuals, run `scripts/obsidian_image_helper.py asset-plan --vault <vault> --note <note>` and use the returned paths plus `image_format`.
   - If the output type is explicit, pass `--asset-kind cover`, `illustration`, `infographic`, `diagram`, `slide`, `photo`, `card`, or `web-image`.
   - Use `image_format.aspect_ratio`, `image_format.file_format`, and `image_format.target_folder` as the generation/save plan.
3. Save generated files under the note-specific asset root:
   - Asset root: `<attachment-base>/<笔记标题>-封面-插图/`
   - Original note images copied or normalized during cleanup: `<asset-root>/原文图片/`
   - Web-sourced images: `<asset-root>/网页图片/`
   - AI image root: `<asset-root>/AI图/`
   - AI covers: `<asset-root>/AI图/封面/`
   - AI article illustrations: `<asset-root>/AI图/插图/`
   - AI infographics: `<asset-root>/AI图/信息图/`
   - AI diagrams: `<asset-root>/AI图/图解/`
   - AI slide assets: `<asset-root>/AI图/幻灯片/`
   - Slide outlines or decks: `Slides/<note-slug>/`
   - Use `config/defaults.json` `attachments_folder` as `<attachment-base>` when present.
4. Generated images should use Chinese for visible text by default: titles, labels, callouts, legends, and diagram wording.
5. Insert generated images with `scripts/obsidian_image_helper.py apply`.
6. Update frontmatter only for stable metadata such as `coverImage`, `translationOf`, `language`, `visualAssets`, or `slideDeck`.
7. Keep external API keys, cookies, platform credentials, and raw image prompts outside the note. Never paste secrets or prompts into Markdown.
8. If prompts must be preserved, save them under `<asset-root>/AI图/prompts/` as sidecars and do not link them from the note unless the user asks.
9. If image generation is not available, describe the missing generation step in the response or create an outline-only result in chat. Do not insert prompt text into the note.

## Translation

Use when the user asks to translate, localize, make a bilingual note, or turn captured source material into another language.

Workflow:

1. Decide output mode:
   - `sidecar`: create a sibling translated note, preferred for knowledge bases.
   - `replace`: rewrite the current note in target language, only when asked.
   - `bilingual`: keep original and translated sections in the same note.
2. Preserve Obsidian links:
   - Keep wikilink targets unchanged unless the user asks to translate note titles.
   - Translate link aliases when useful: `[[original-note|translated alias]]`.
3. Preserve images and embeds.
4. Add frontmatter to the translated note:

```yaml
language: <target-language>
translationOf: <source-note-path>
sourceLanguage: <source-language>
```

5. Translate directly with the requested audience, tone, and terminology. For publication-quality work, use a two-pass flow: translate, then review and polish.

## Article Illustrations

Use when the user asks for "add images", "illustrate this note", "section illustrations", or similar.

Workflow:

1. Analyze the note and choose 1-5 places where images add explanatory value.
2. Choose the image style before generation or search:
   - Default to `hand-drawn`.
   - Use the user's explicit style when provided.
   - Use automatic scene style when requested: `technical-schematic` for systems, `infographic` for dense summaries, `editorial` for essays, `minimal` for sparse references, and `photo` for real-world subjects.
3. Prefer visual explanations over decoration.
4. Generate AI images into `image_format.target_folder`, normally `<asset-root>/AI图/插图/`, using the returned aspect ratio and file format. Web-sourced section images stay in `<asset-root>/网页图片/`.
5. Insert each image near the section it supports:

```bash
python scripts/obsidian_image_helper.py apply --vault <vault> --note <note> --image <image> --position after-heading --heading "<heading>" --caption "<caption>"
```

6. Add a `visualAssets` list in frontmatter only when multiple generated assets are important to track.

## Cover Images

Use when the user asks for a cover, article header, preview image, or note hero image.

Workflow:

1. Summarize the note into one strong visual concept.
2. Use `hand-drawn` cover style by default unless the user specifies another style or asks for automatic scene styling.
3. Run `asset-plan --asset-kind cover` and generate a `16:9` PNG cover into `<asset-root>/AI图/封面/<note-slug>.png` unless config overrides the aspect ratio.
4. Update or add frontmatter:

```yaml
coverImage: <asset-root-relative-path>/AI图/封面/<note-slug>.png
```

5. Insert the cover as a hero image only if the user wants it visible in the note body. Otherwise keep it as frontmatter metadata.

## Infographics

Use when the user asks for a visual summary, dense knowledge image, process card, comparison image, or high-density infographic.

Workflow:

1. Identify the information structure: timeline, comparison, funnel, tree, mind map, pyramid, grid, or process.
2. Use `infographic` style for dense visual summaries, `hand-drawn` for softer learning notes, or automatic scene style when requested.
3. Run `asset-plan --asset-kind infographic` and generate one `3:4` PNG into `<asset-root>/AI图/信息图/<note-slug>-<topic>.png` unless config overrides the aspect ratio.
4. Insert the infographic after the note summary or after the section it visualizes.
5. Add a short caption explaining what the visual helps the reader understand.

## Diagrams

Use when the user asks for architecture diagrams, flowcharts, sequence diagrams, mind maps, timelines, data flow, state machines, or "draw a diagram".

Workflow:

1. Run `asset-plan --asset-kind diagram`.
2. Choose SVG for technical/conceptual diagrams when exact text and reusable markup matter. Choose generated raster images when the user wants illustration style.
3. Save the generated diagram to `<asset-root>/AI图/图解/<note-slug>-<diagram-type>.<ext>` using `image_format.file_format`.
4. Insert with a wiki embed:

```markdown
![[<asset-root-relative-path>/AI图/图解/<file>|<caption>]]
```

5. If the note already has Mermaid, PlantUML, or ASCII diagrams, decide whether to preserve them as source and add the visual diagram as a rendered companion.
6. For factual diagrams, keep the labels derived from note content. Do not add unverified architecture components or steps.

## Slide Decks

Use when the user asks to turn a note into slides, presentation, deck, PPT, lecture material, or talk outline.

Workflow:

1. Decide the output:
   - `outline-only`: create a slide outline note.
   - `images`: generate slide images.
   - `deck`: generate or assemble a deck if the runtime supports it.
2. Save outlines/deck material under `Slides/<note-slug>/`.
3. Run `asset-plan --asset-kind slide` and save `16:9` PNG slide images under `<asset-root>/AI图/幻灯片/` unless config overrides the aspect ratio.
4. Add a section near the end of the source note only if the user wants deck links in the note:

```markdown
## Related deck

- [[Slides/<note-slug>/outline|Slide outline]]
- ![[<asset-root-relative-path>/AI图/幻灯片/01-title.png|Title slide]]
```

5. Keep slide generation separate from note rewriting. Do not turn the original note into slide bullets unless the user asks.
