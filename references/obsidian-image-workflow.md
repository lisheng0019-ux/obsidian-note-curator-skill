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
4. User-approved generated or externally sourced images.
5. Generated covers, illustrations, infographics, diagrams, or slide images created by a specialized workflow.

Reject images that are merely aesthetic when the note is factual or research-oriented.

## External images

If using external images, prefer:

- User-provided files.
- Public domain, Creative Commons, official product/organization assets, or generated images.
- Files saved into the vault with attribution in frontmatter or a nearby source line when required.

Do not hotlink external images unless the user explicitly wants that.

## Generated asset folders

Use stable folders so future runs can find and reuse generated assets:

- Covers: `Attachments/covers/`
- Article illustrations: `Attachments/illustrations/<note-slug>/`
- Infographics: `Attachments/infographics/`
- Diagrams: `Attachments/diagrams/`
- Slide images: `Attachments/slides/<note-slug>/`

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
