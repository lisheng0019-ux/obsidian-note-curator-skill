# Baoyu Content Workflows for Obsidian

Use this reference when an Obsidian note needs translation, generated visuals, diagrams, or slides. Treat baoyu skills as optional specialized engines. The final artifact must remain Obsidian-friendly: saved inside the vault, linked with vault-relative paths, and traceable from the note.

## General Rules

1. Keep the source note unchanged unless the user asks for in-place rewriting.
2. Save generated files under the vault, preferably:
   - Covers: `Attachments/covers/`
   - Article illustrations: `Attachments/illustrations/<note-slug>/`
   - Infographics: `Attachments/infographics/`
   - Diagrams: `Attachments/diagrams/`
   - Slide assets: `Attachments/slides/<note-slug>/`
   - Slide outlines or decks: `Slides/<note-slug>/`
3. Insert generated images with `scripts/obsidian_image_helper.py apply`.
4. Update frontmatter only for stable metadata such as `coverImage`, `translationOf`, `language`, `visualAssets`, or `slideDeck`.
5. Keep external API keys, cookies, and platform credentials outside the note. Never paste secrets into Markdown.
6. If a baoyu skill asks for first-time setup, complete that setup before generation. If setup is not possible, fall back to a prompt-only or outline-only result.

## Translation

Use when the user asks to translate, localize, make a bilingual note, or turn captured source material into another language.

Preferred engine: `baoyu-translate`.

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

5. If `baoyu-translate` is available, use normal mode for articles and refined mode for publication-quality notes. If not available, translate directly while following the same output rules.

## Article Illustrations

Use when the user asks for "add images", "illustrate this note", "section illustrations", or similar.

Preferred engine: `baoyu-article-illustrator`.

Workflow:

1. Analyze the note and choose 1-5 places where images add explanatory value.
2. Prefer visual explanations over decoration.
3. Generate or collect images into `Attachments/illustrations/<note-slug>/`.
4. Insert each image near the section it supports:

```bash
python scripts/obsidian_image_helper.py apply --vault <vault> --note <note> --image <image> --position after-heading --heading "<heading>" --caption "<caption>"
```

5. Add a `visualAssets` list in frontmatter only when multiple generated assets are important to track.

## Cover Images

Use when the user asks for a cover, article header, preview image, or note hero image.

Preferred engine: `baoyu-cover-image`; fallback: native image generation.

Workflow:

1. Summarize the note into one strong visual concept.
2. Generate a cover into `Attachments/covers/<note-slug>.png`.
3. Update or add frontmatter:

```yaml
coverImage: Attachments/covers/<note-slug>.png
```

4. Insert the cover as a hero image only if the user wants it visible in the note body. Otherwise keep it as frontmatter metadata.

## Infographics

Use when the user asks for a visual summary, dense knowledge image, process card, comparison image, or high-density infographic.

Preferred engine: `baoyu-infographic`.

Workflow:

1. Identify the information structure: timeline, comparison, funnel, tree, mind map, pyramid, grid, or process.
2. Generate one image into `Attachments/infographics/<note-slug>-<topic>.png`.
3. Insert the infographic after the note summary or after the section it visualizes.
4. Add a short caption explaining what the visual helps the reader understand.

## Diagrams

Use when the user asks for architecture diagrams, flowcharts, sequence diagrams, mind maps, timelines, data flow, state machines, or "draw a diagram".

Preferred engine: `baoyu-diagram`.

Workflow:

1. Choose SVG for technical/conceptual diagrams.
2. Save the generated diagram to `Attachments/diagrams/<note-slug>-<diagram-type>.svg`.
3. Insert with a wiki embed:

```markdown
![[Attachments/diagrams/<file>.svg|<caption>]]
```

4. If the note already has Mermaid, PlantUML, or ASCII diagrams, decide whether to preserve them as source and add the SVG as a rendered companion.
5. For factual diagrams, keep the diagram labels derived from note content. Do not add unverified architecture components or steps.

## Slide Decks

Use when the user asks to turn a note into slides, presentation, deck, PPT, lecture material, or talk outline.

Preferred engine: `baoyu-slide-deck`.

Workflow:

1. Decide the output:
   - `outline-only`: add a slide outline note.
   - `images`: generate slide images.
   - `deck`: generate or assemble a deck if the runtime supports it.
2. Save outlines/deck material under `Slides/<note-slug>/`.
3. Save slide images under `Attachments/slides/<note-slug>/`.
4. Add a section near the end of the source note:

```markdown
## Related deck

- [[Slides/<note-slug>/outline|Slide outline]]
- ![[Attachments/slides/<note-slug>/01-title.png|Title slide]]
```

5. Keep slide generation separate from note rewriting. Do not turn the original note into slide bullets unless the user asks.

## Fallback Without Baoyu Skills

If the relevant baoyu skill is not installed:

- Translation: perform translation directly and save sidecar notes.
- Illustrations/covers/infographics: generate a prompt file next to the note or use the runtime-native image tool if available.
- Diagrams: create a standalone SVG directly when appropriate.
- Slides: create a Markdown slide outline and, if possible, render images later.

Always tell the user which path was used.
