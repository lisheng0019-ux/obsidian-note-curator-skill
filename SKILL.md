---
name: obsidian-note-curator
description: Organize and enrich Obsidian Markdown notes in Claude Code/Claudian. Use for note cleanup, structure rewriting, frontmatter/tags/backlinks, image understanding/OCR/captions, automatic note images from local vault or web image search, translation, article illustrations, cover images, infographics, SVG diagrams, slide decks, Chinese or multilingual note curation, Obsidian vault work, .md notes, or Claudian workflows.
---

# Obsidian Note Curator

## Goal

Turn rough Obsidian notes into clean, linked, visually useful knowledge assets while preserving the user's voice and vault conventions.

Use Claude's vision capability for image understanding. Use the bundled helper script for deterministic vault scanning, image link resolution, candidate image matching, and safe Markdown insertion.

This skill can also coordinate optional content-production skills such as `baoyu-translate`, `baoyu-article-illustrator`, `baoyu-cover-image`, `baoyu-infographic`, `baoyu-diagram`, and `baoyu-slide-deck` when they are installed. The Obsidian note remains the source of truth; generated or transformed assets must be saved into the vault and linked back from the note.

## Capability Router

Choose the narrowest workflow that satisfies the user's request:

| Request intent | Preferred workflow |
|----------------|--------------------|
| Clean up, structure, tag, summarize, link notes | Core note curation workflow |
| Understand screenshots, diagrams, photos, or scanned text | Vision + image inventory workflow |
| Add existing local images | Image suggestion + insertion workflow |
| Search the web for matching images and insert the best result | Web image search workflow |
| Translate a note or source material | Translation workflow |
| Add section illustrations | Article illustration workflow |
| Create a note cover | Cover image workflow |
| Make a visual summary or dense knowledge image | Infographic workflow |
| Draw architecture/process/concept diagrams | Diagram workflow |
| Turn a note into presentation material | Slide deck workflow |

If a matching baoyu skill is installed and available in the runtime, prefer it for that specialized task. If it is not installed, use native Claude/Codex capabilities and save the same Obsidian-shaped outputs.

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
   - Translation: see [content enrichment workflows](references/baoyu-content-workflows.md#translation).
   - Illustrations: see [content enrichment workflows](references/baoyu-content-workflows.md#article-illustrations).
   - Cover images: see [content enrichment workflows](references/baoyu-content-workflows.md#cover-images).
   - Infographics: see [content enrichment workflows](references/baoyu-content-workflows.md#infographics).
   - Diagrams: see [content enrichment workflows](references/baoyu-content-workflows.md#diagrams).
   - Slide decks: see [content enrichment workflows](references/baoyu-content-workflows.md#slide-decks).

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
   - Compare candidates by semantic match, source trust, image clarity, license/usability, and caption fit.
   - Download and insert the best approved image with:

```bash
python scripts/obsidian_image_helper.py download --vault <vault> --note <note> --url <image-url> --source-page <page-url> --caption "<short caption>" --insert
```

7. If no suitable local image exists.
   - If web/image-generation tools are available and the user allowed external sourcing, create or source a copyright-safe image, place it under the vault attachment folder, then insert it.
   - Otherwise add a short "image_needed" note or provide a generation prompt instead of fabricating a file.

8. Validate.
   - Re-run `inventory` and confirm all inserted images resolve.
   - Check that image captions are short, useful, and do not repeat nearby prose.
   - Avoid duplicate embeds and avoid putting decorative images between tightly related paragraphs.
   - For generated assets, confirm the output file exists inside the vault and the note uses a vault-relative link.
   - For web-sourced images, confirm a `.source.md` sidecar or equivalent attribution record exists unless the user explicitly disabled it.

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
- Use stable asset subfolders when creating new files:
  - `Attachments/covers/`
  - `Attachments/illustrations/<note-slug>/`
  - `Attachments/web-images/<note-slug>/`
  - `Attachments/infographics/`
  - `Attachments/diagrams/`
  - `Attachments/slides/<note-slug>/`
- Do not edit `.obsidian/`, plugin settings, or hidden provider folders unless explicitly asked.
- Do not rename existing notes or images unless the user asks.
- Do not overwrite generated assets unless the user asks; append a short suffix or timestamp on conflict.

## Helper Script

The script supports:

- `inventory`: resolve embedded images and scan vault image candidates.
- `suggest`: rank local images by note title, headings, tags, and filename/path overlap.
- `web-query`: create web image search queries and match criteria from the note.
- `apply`: insert one or more image embeds without duplicating existing links.
- `download`: save a selected web image into the vault, write source metadata, and optionally insert it.

Read `references/obsidian-image-workflow.md` when the task involves complex image sourcing, captions, or vault conventions.

Read `references/baoyu-content-workflows.md` when the task involves translation, generated illustrations, covers, infographics, diagrams, or slides.
