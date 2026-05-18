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

2. Search with the runtime's web/image search tool using `primary_query`, then `style_queries`, then alternate `queries` if needed.
3. Collect 5-10 candidates with image URL, source page URL, title/alt text, visible license/source hints, and thumbnail preview when available.
4. Pick the best candidate using these criteria:
   - Semantic relevance to the note title, headings, entities, and claims.
   - Fit to the selected or auto-selected image style.
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

The `download` command stores web images under `Attachments/web-images/<note-slug>/` by default and writes a `.source.md` sidecar with source metadata. Keep that sidecar unless the user explicitly asks not to preserve attribution.

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

## Generated asset folders

Use stable folders so future runs can find and reuse generated assets. If `config/defaults.json` defines `attachments_folder`, place these folders under that configured attachment base; otherwise place them under `Attachments/`.

- Covers: `covers/`
- Article illustrations: `illustrations/<note-slug>/`
- Web-sourced images: `web-images/<note-slug>/`
- Infographics: `infographics/`
- Diagrams: `diagrams/`
- Slide images: `slides/<note-slug>/`

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
