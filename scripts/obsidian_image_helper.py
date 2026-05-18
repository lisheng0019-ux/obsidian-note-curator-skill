#!/usr/bin/env python3
"""Resolve, suggest, and insert Obsidian note images."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".svg", ".avif"}
EXCLUDED_DIRS = {".git", ".obsidian", ".trash", ".claude", ".claudian", ".codex", "node_modules"}
COMMON_IMAGE_DIRS = ("Attachments", "attachments", "assets", "Assets", "images", "Images", "media", "Media", "resources", "Resources")


@dataclass
class ImageLink:
    kind: str
    raw: str
    target: str
    resolved: str | None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def normalize_rel(path: Path, vault: Path) -> str:
    try:
        rel = path.resolve().relative_to(vault.resolve())
        return rel.as_posix()
    except ValueError:
        return path.as_posix()


def find_vault(start: Path | None) -> Path:
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".obsidian").exists():
            return candidate
    return current


def resolve_note(vault: Path, note_arg: str) -> Path:
    note = Path(note_arg)
    candidates = []
    if note.is_absolute():
        candidates.append(note)
    else:
        candidates.extend([Path.cwd() / note, vault / note])
    if note.suffix.lower() != ".md":
        candidates.append(vault / f"{note_arg}.md")
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"Note not found: {note_arg}")


def iter_images(vault: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        root_path = Path(root)
        for name in files:
            path = root_path / name
            if path.suffix.lower() in IMAGE_EXTS:
                yield path.resolve()


def image_index(vault: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in iter_images(vault):
        keys = {
            path.name.lower(),
            path.stem.lower(),
            normalize_rel(path, vault).lower(),
        }
        for key in keys:
            index.setdefault(key, []).append(path)
    return index


def clean_link_target(target: str) -> str:
    target = target.strip().strip("<>").strip()
    target = target.split("#", 1)[0].split("|", 1)[0].strip()
    return unquote(target)


def parse_image_links(text: str, vault: Path, note: Path) -> list[ImageLink]:
    links: list[ImageLink] = []
    idx = image_index(vault)

    def resolve(target: str) -> str | None:
        clean = clean_link_target(target).replace("\\", "/")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", clean):
            return None
        direct = Path(clean)
        candidates = []
        if direct.is_absolute():
            candidates.append(direct)
        else:
            candidates.extend([note.parent / direct, vault / direct])
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())
        key = Path(clean).name.lower()
        if key in idx:
            return str(idx[key][0])
        stem = Path(clean).stem.lower()
        if stem in idx:
            return str(idx[stem][0])
        return None

    for match in re.finditer(r"!\[\[([^\]]+)\]\]", text):
        raw = match.group(0)
        target = clean_link_target(match.group(1))
        links.append(ImageLink("wiki", raw, target, resolve(target)))

    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        raw = match.group(0)
        target = clean_link_target(match.group(1))
        links.append(ImageLink("markdown", raw, target, resolve(target)))

    for match in re.finditer(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", text, flags=re.IGNORECASE):
        raw = match.group(0)
        target = clean_link_target(match.group(1))
        links.append(ImageLink("html", raw, target, resolve(target)))

    return links


def strip_markdown_noise(text: str) -> str:
    text = re.sub(r"^---\s.*?^---\s", " ", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[\[[^\]]+\]\]", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    return text


def extract_terms(text: str) -> list[str]:
    clean = strip_markdown_noise(text).lower()
    terms: list[str] = []
    for heading in re.findall(r"^#{1,3}\s+(.+)$", clean, flags=re.MULTILINE):
        terms.extend(re.findall(r"[\w\u4e00-\u9fff]{2,}", heading))
        if len(heading) >= 2:
            terms.append(heading.strip())
    terms.extend(re.findall(r"#([\w\u4e00-\u9fff/-]{2,})", clean))
    terms.extend(re.findall(r"[\w\u4e00-\u9fff]{3,}", clean))
    seen: set[str] = set()
    output: list[str] = []
    stop = {"the", "and", "with", "from", "this", "that", "note", "image", "obsidian", "http", "https"}
    for term in terms:
        term = term.strip("_- /")
        if not term or term in stop or term in seen:
            continue
        seen.add(term)
        output.append(term)
    return output[:80]


def score_image(path: Path, vault: Path, terms: list[str]) -> tuple[int, list[str]]:
    rel = normalize_rel(path, vault).lower()
    searchable = re.sub(r"[_\-\.]+", " ", rel)
    score = 0
    reasons: list[str] = []
    common_bonus = 2 if any(part in rel for part in [d.lower() for d in COMMON_IMAGE_DIRS]) else 0
    score += common_bonus
    for term in terms:
        if len(term) < 2:
            continue
        if term in searchable:
            inc = min(12, max(3, len(term) // 2))
            score += inc
            if len(reasons) < 4:
                reasons.append(term)
    return score, reasons


def build_inventory(vault: Path, note: Path) -> dict:
    text = read_text(note)
    links = parse_image_links(text, vault, note)
    images = list(iter_images(vault))
    return {
        "vault": str(vault),
        "note": str(note),
        "embedded_images": [
            {
                "kind": link.kind,
                "raw": link.raw,
                "target": link.target,
                "resolved": link.resolved,
                "exists": bool(link.resolved),
            }
            for link in links
        ],
        "image_count": len(images),
        "candidate_images": [normalize_rel(path, vault) for path in images[:500]],
    }


def suggest_images(vault: Path, note: Path, limit: int) -> dict:
    text = read_text(note)
    existing = {Path(link.resolved).resolve() for link in parse_image_links(text, vault, note) if link.resolved}
    terms = extract_terms(text)
    scored = []
    for path in iter_images(vault):
        if path.resolve() in existing:
            continue
        score, reasons = score_image(path, vault, terms)
        if score > 0:
            scored.append((score, path, reasons))
    scored.sort(key=lambda item: (-item[0], normalize_rel(item[1], vault)))
    return {
        "vault": str(vault),
        "note": str(note),
        "terms_used": terms[:25],
        "suggestions": [
            {
                "score": score,
                "path": normalize_rel(path, vault),
                "absolute_path": str(path),
                "matched_terms": reasons,
            }
            for score, path, reasons in scored[:limit]
        ],
    }


def frontmatter_bounds(lines: list[str]) -> tuple[int, int] | None:
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return 0, idx
    return None


def insertion_index(lines: list[str], position: str, heading: str | None) -> int:
    fm = frontmatter_bounds(lines)
    start = fm[1] + 1 if fm else 0
    if position == "end":
        return len(lines)
    if position == "after-heading" and heading:
        wanted = heading.strip().lstrip("#").strip().lower()
        for idx, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                current = line.lstrip("#").strip().lower()
                if current == wanted or wanted in current:
                    return idx + 1
    for idx in range(start, len(lines)):
        if re.match(r"^#\s+", lines[idx]):
            return idx + 1
    return start


def ensure_inside_vault(vault: Path, image: Path, attachment_folder: str | None, copy: bool) -> Path:
    image = image.resolve()
    try:
        image.relative_to(vault.resolve())
        return image
    except ValueError:
        if not copy:
            raise ValueError(f"Image is outside the vault; pass --copy to copy it in: {image}")
    folder = vault / (attachment_folder or "Attachments")
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / image.name
    counter = 1
    while destination.exists() and destination.resolve() != image:
        destination = folder / f"{image.stem}-{counter}{image.suffix}"
        counter += 1
    if destination.resolve() != image:
        shutil.copy2(image, destination)
    return destination.resolve()


def make_embed(rel_path: str, caption: str | None) -> str:
    rel_path = rel_path.replace("\\", "/")
    if caption:
        return f"![[{rel_path}|{caption.strip()}]]"
    return f"![[{rel_path}]]"


def apply_images(args: argparse.Namespace) -> dict:
    vault = find_vault(Path(args.vault).resolve() if args.vault else None)
    note = resolve_note(vault, args.note)
    text = read_text(note)
    lines = text.splitlines()
    embeds = []
    existing_text = text.lower()
    for image_arg in args.image:
        image = Path(image_arg)
        if not image.is_absolute():
            image = (vault / image_arg)
        image = ensure_inside_vault(vault, image, args.attachments_folder, args.copy)
        rel = normalize_rel(image, vault)
        if rel.lower() in existing_text or image.name.lower() in existing_text:
            continue
        embeds.append(make_embed(rel, args.caption))
    if not embeds:
        return {"changed": False, "note": str(note), "inserted": []}
    idx = insertion_index(lines, args.position, args.heading)
    block = ["", *embeds, ""]
    updated_lines = lines[:idx] + block + lines[idx:]
    updated = "\n".join(updated_lines).rstrip() + "\n"
    if not args.dry_run:
        write_text(note, updated)
    return {
        "changed": not args.dry_run,
        "dry_run": args.dry_run,
        "note": str(note),
        "inserted": embeds,
        "position": args.position,
        "heading": args.heading,
    }


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve, suggest, and insert Obsidian note images.")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory")
    inv.add_argument("--vault")
    inv.add_argument("--note", required=True)

    sug = sub.add_parser("suggest")
    sug.add_argument("--vault")
    sug.add_argument("--note", required=True)
    sug.add_argument("--limit", type=int, default=8)

    app = sub.add_parser("apply")
    app.add_argument("--vault")
    app.add_argument("--note", required=True)
    app.add_argument("--image", action="append", required=True)
    app.add_argument("--position", choices=["hero", "after-heading", "end"], default="hero")
    app.add_argument("--heading")
    app.add_argument("--caption")
    app.add_argument("--attachments-folder")
    app.add_argument("--copy", action="store_true")
    app.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    try:
        vault = find_vault(Path(args.vault).resolve() if getattr(args, "vault", None) else None)
        if args.command == "inventory":
            print_json(build_inventory(vault, resolve_note(vault, args.note)))
        elif args.command == "suggest":
            print_json(suggest_images(vault, resolve_note(vault, args.note), args.limit))
        elif args.command == "apply":
            print_json(apply_images(args))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
