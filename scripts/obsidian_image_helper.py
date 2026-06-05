#!/usr/bin/env python3
"""Resolve, suggest, download, and insert Obsidian note images."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".svg", ".avif"}
EXCLUDED_DIRS = {".git", ".obsidian", ".trash", ".claude", ".claudian", ".codex", "node_modules"}
COMMON_IMAGE_DIRS = ("Attachments", "attachments", "assets", "Assets", "images", "Images", "media", "Media", "resources", "Resources")
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config" / "defaults.json"
DEFAULT_IMAGE_STYLE = "hand-drawn"
DEFAULT_ASSET_FOLDER_PATTERN = "{note-title}-封面-插图"
DEFAULT_GENERATED_IMAGE_TEXT_LANGUAGE = "zh-CN"
DEFAULT_IMAGE_FORMAT_MODE = "auto"
DEFAULT_PREFER_SVG_FOR_DIAGRAMS = True
DEFAULT_IMAGE_ASPECTS = {
    "cover": "16:9",
    "illustration": "4:3",
    "infographic": "3:4",
    "diagram": "auto",
    "slide": "16:9",
    "photo": "4:3",
    "card": "3:4",
    "web-image": "auto",
}
STYLE_PRESETS = {
    "hand-drawn": {
        "label": "hand-drawn",
        "search_terms": ["hand drawn illustration", "sketch notes", "hand drawn diagram"],
        "prompt_modifier": "hand-drawn educational illustration, clean sketch lines, warm paper texture, minimal visual noise",
        "best_for": "default knowledge notes, learning notes, conceptual explanations",
    },
    "technical-schematic": {
        "label": "technical-schematic",
        "search_terms": ["technical schematic", "architecture diagram", "blueprint diagram"],
        "prompt_modifier": "technical schematic, precise labels, blueprint-inspired layout, clean lines",
        "best_for": "architecture, systems, workflows, engineering notes",
    },
    "infographic": {
        "label": "infographic",
        "search_terms": ["infographic", "visual summary", "knowledge card"],
        "prompt_modifier": "high-clarity infographic, structured modules, concise labels, strong hierarchy",
        "best_for": "summaries, comparisons, processes, data-heavy notes",
    },
    "editorial": {
        "label": "editorial",
        "search_terms": ["editorial illustration", "conceptual illustration", "magazine illustration"],
        "prompt_modifier": "editorial conceptual illustration, polished composition, restrained colors",
        "best_for": "essays, opinions, narrative notes",
    },
    "minimal": {
        "label": "minimal",
        "search_terms": ["minimal illustration", "simple line art", "clean vector"],
        "prompt_modifier": "minimal clean illustration, generous whitespace, simple shapes, low distraction",
        "best_for": "reference notes, executive summaries, sparse notes",
    },
    "photo": {
        "label": "photo",
        "search_terms": ["photo", "realistic photo", "documentary image"],
        "prompt_modifier": "realistic documentary photo style, natural lighting, authentic scene",
        "best_for": "people, places, objects, events, product or field notes",
    },
}
FORMAT_PRESETS = {
    "cover": {
        "label": "cover",
        "folder_key": "cover_folder",
        "file_format": "png",
        "aspect_config": "default_cover_aspect",
        "best_for": "note covers, visual anchors, hero images",
    },
    "illustration": {
        "label": "illustration",
        "folder_key": "illustration_folder",
        "file_format": "png",
        "aspect_config": "default_illustration_aspect",
        "best_for": "section illustrations and conceptual explanations",
    },
    "infographic": {
        "label": "infographic",
        "folder_key": "infographic_folder",
        "file_format": "png",
        "aspect_config": "default_infographic_aspect",
        "best_for": "summaries, comparisons, metrics, timelines, dense knowledge cards",
    },
    "diagram": {
        "label": "diagram",
        "folder_key": "diagram_folder",
        "file_format": "png",
        "aspect_config": "default_diagram_aspect",
        "best_for": "architecture, process, relationship, and concept maps",
    },
    "slide": {
        "label": "slide",
        "folder_key": "slide_image_folder",
        "file_format": "png",
        "aspect_config": "default_slide_aspect",
        "best_for": "presentation slides and 16:9 teaching material",
    },
    "photo": {
        "label": "photo",
        "folder_key": "illustration_folder",
        "file_format": "jpg",
        "aspect_config": "default_photo_aspect",
        "best_for": "real people, places, products, events, objects, and field scenes",
    },
    "card": {
        "label": "card",
        "folder_key": "infographic_folder",
        "file_format": "png",
        "aspect_config": "default_card_aspect",
        "best_for": "social cards, knowledge cards, and compact shareable visuals",
    },
    "web-image": {
        "label": "web-image",
        "folder_key": "web_image_folder",
        "file_format": "source",
        "aspect_config": "default_web_image_aspect",
        "best_for": "downloaded web images where the original format should usually be preserved",
    },
}
ASSET_SUBFOLDERS = {
    "cover_folder": "封面",
    "illustration_folder": "插图",
    "web_image_folder": "网页图片",
    "infographic_folder": "信息图",
    "diagram_folder": "图解",
    "slide_image_folder": "幻灯片",
}


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


def load_config() -> dict:
    if not DEFAULT_CONFIG.exists():
        return {}
    try:
        data = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid config JSON: {DEFAULT_CONFIG}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a JSON object: {DEFAULT_CONFIG}")
    return data


def configured_attachment_folder() -> str | None:
    config = load_config()
    value = config.get("attachments_folder")
    if value is None:
        value = config.get("attachment_folder")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("attachments_folder in config/defaults.json must be a string")
    return value.strip() or None


def configured_image_style() -> str:
    config = load_config()
    value = config.get("default_image_style") or config.get("image_style") or DEFAULT_IMAGE_STYLE
    if not isinstance(value, str):
        raise ValueError("default_image_style in config/defaults.json must be a string")
    value = value.strip().lower()
    return value or DEFAULT_IMAGE_STYLE


def configured_style_mode() -> str:
    config = load_config()
    value = config.get("image_style_mode") or "default"
    if not isinstance(value, str):
        raise ValueError("image_style_mode in config/defaults.json must be a string")
    value = value.strip().lower()
    if value not in {"default", "auto"}:
        raise ValueError("image_style_mode must be 'default' or 'auto'")
    return value


def configured_asset_folder_pattern() -> str:
    config = load_config()
    value = config.get("generated_asset_folder_pattern") or config.get("asset_folder_pattern") or DEFAULT_ASSET_FOLDER_PATTERN
    if not isinstance(value, str):
        raise ValueError("generated_asset_folder_pattern in config/defaults.json must be a string")
    return value.strip() or DEFAULT_ASSET_FOLDER_PATTERN


def configured_generated_image_text_language() -> str:
    config = load_config()
    value = config.get("generated_image_text_language") or DEFAULT_GENERATED_IMAGE_TEXT_LANGUAGE
    if not isinstance(value, str):
        raise ValueError("generated_image_text_language in config/defaults.json must be a string")
    return value.strip() or DEFAULT_GENERATED_IMAGE_TEXT_LANGUAGE


def configured_write_generation_prompts_to_note() -> bool:
    config = load_config()
    value = config.get("write_generation_prompts_to_note")
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValueError("write_generation_prompts_to_note in config/defaults.json must be a boolean")
    return value


def configured_image_format_mode() -> str:
    config = load_config()
    value = config.get("image_format_mode") or DEFAULT_IMAGE_FORMAT_MODE
    if not isinstance(value, str):
        raise ValueError("image_format_mode in config/defaults.json must be a string")
    value = value.strip().lower()
    if value not in {"auto", "default"}:
        raise ValueError("image_format_mode must be 'auto' or 'default'")
    return value


def configured_default_aspect(asset_kind: str, fallback: str) -> str:
    config = load_config()
    config_key = FORMAT_PRESETS.get(asset_kind, {}).get("aspect_config")
    value = config.get(config_key) if config_key else None
    if value is None:
        value = DEFAULT_IMAGE_ASPECTS.get(asset_kind, fallback)
    if not isinstance(value, str):
        raise ValueError(f"{config_key} in config/defaults.json must be a string")
    return value.strip() or fallback


def configured_prefer_svg_for_diagrams() -> bool:
    config = load_config()
    value = config.get("prefer_svg_for_diagrams")
    if value is None:
        return DEFAULT_PREFER_SVG_FOR_DIAGRAMS
    if not isinstance(value, bool):
        raise ValueError("prefer_svg_for_diagrams in config/defaults.json must be a boolean")
    return value


def configured_vault_root() -> Path | None:
    config = load_config()
    value = config.get("vault_root") or config.get("vault")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("vault_root in config/defaults.json must be a string")
    value = value.strip()
    if not value:
        return None
    return Path(value).resolve()


def normalize_rel(path: Path, vault: Path) -> str:
    try:
        rel = path.resolve().relative_to(vault.resolve())
        return rel.as_posix()
    except ValueError:
        return path.as_posix()


def find_vault(start: Path | None) -> Path:
    if start is None:
        configured = configured_vault_root()
        if configured:
            return configured
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


def recommend_style(text: str, terms: list[str]) -> tuple[str, str]:
    haystack = " ".join([text.lower(), *terms])
    technical = ("architecture", "system", "workflow", "api", "database", "server", "模型", "架构", "流程", "系统", "工程")
    data = ("metric", "data", "comparison", "table", "summary", "dashboard", "指标", "数据", "对比", "总结", "信息图")
    narrative = ("story", "essay", "reflection", "history", "culture", "故事", "随笔", "历史", "文化")
    tangible = ("photo", "person", "place", "product", "event", "人物", "地点", "产品", "现场", "照片")
    sparse = ("memo", "brief", "checklist", "reference", "清单", "备忘", "参考")
    if any(token in haystack for token in technical):
        return "technical-schematic", "technical or process-oriented note"
    if any(token in haystack for token in data):
        return "infographic", "summary, comparison, or data-heavy note"
    if any(token in haystack for token in tangible):
        return "photo", "note appears to need a real-world subject"
    if any(token in haystack for token in narrative):
        return "editorial", "essay or narrative note"
    if any(token in haystack for token in sparse):
        return "minimal", "compact reference-style note"
    return DEFAULT_IMAGE_STYLE, "general knowledge note"


def style_details(style: str) -> dict:
    normalized = style.strip().lower() or DEFAULT_IMAGE_STYLE
    preset = STYLE_PRESETS.get(normalized)
    if preset:
        return {"name": normalized, **preset}
    return {
        "name": normalized,
        "label": normalized,
        "search_terms": [normalized, f"{normalized} illustration"],
        "prompt_modifier": f"{normalized} visual style, coherent with the note context",
        "best_for": "user-specified custom style",
    }


def build_style_plan(text: str, terms: list[str], style_arg: str | None, style_mode_arg: str | None) -> dict:
    configured_style = configured_image_style()
    configured_mode = configured_style_mode()
    requested_style = (style_arg or "").strip().lower()
    requested_mode = (style_mode_arg or "").strip().lower()
    if requested_mode and requested_mode not in {"default", "auto"}:
        raise ValueError("--style-mode must be 'default' or 'auto'")
    mode = requested_mode or configured_mode
    if requested_style == "auto":
        mode = "auto"
    if requested_style and requested_style != "auto":
        selected = requested_style
        reason = "user-specified style"
        mode = "custom"
    elif mode == "auto":
        selected, reason = recommend_style(text, terms)
    else:
        selected = configured_style
        reason = "configured default style"
    details = style_details(selected)
    alternatives = [
        {"name": name, "best_for": preset["best_for"]}
        for name, preset in STYLE_PRESETS.items()
        if name != selected
    ]
    return {
        "mode": mode,
        "selected": details["name"],
        "label": details["label"],
        "reason": reason,
        "search_terms": details["search_terms"],
        "prompt_modifier": details["prompt_modifier"],
        "alternatives": alternatives[:6],
    }


def normalize_asset_kind(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "auto": None,
        "hero": "cover",
        "cover-image": "cover",
        "section": "illustration",
        "article-illustration": "illustration",
        "info-graphic": "infographic",
        "information-graphic": "infographic",
        "svg-diagram": "diagram",
        "process-diagram": "diagram",
        "slide-image": "slide",
        "deck": "slide",
        "presentation": "slide",
        "knowledge-card": "card",
        "social-card": "card",
        "web": "web-image",
        "webimage": "web-image",
        "封面": "cover",
        "插图": "illustration",
        "配图": "illustration",
        "信息图": "infographic",
        "图解": "diagram",
        "图表": "diagram",
        "幻灯片": "slide",
        "照片": "photo",
        "摄影": "photo",
        "知识卡片": "card",
        "网页图片": "web-image",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized is None:
        return None
    if normalized not in FORMAT_PRESETS:
        allowed = ", ".join(FORMAT_PRESETS)
        raise ValueError(f"Unknown asset kind '{value}'. Expected one of: {allowed}")
    return normalized


def recommend_asset_kind(text: str, terms: list[str]) -> tuple[str, str]:
    haystack = " ".join([text.lower(), *terms])
    checks = [
        (
            "cover",
            ("cover", "hero", "title image", "封面", "题图", "头图"),
            "note explicitly asks for a cover or hero image",
        ),
        (
            "slide",
            ("slide", "slides", "deck", "presentation", "ppt", "powerpoint", "幻灯片", "演示", "汇报", "课件"),
            "note is presentation-oriented",
        ),
        (
            "diagram",
            (
                "architecture",
                "workflow",
                "system",
                "process",
                "pipeline",
                "relationship",
                "topology",
                "api",
                "database",
                "架构",
                "流程",
                "系统",
                "过程",
                "关系",
                "链路",
                "拓扑",
                "接口",
                "数据库",
                "图解",
            ),
            "note contains process, system, or relationship structure",
        ),
        (
            "infographic",
            (
                "metric",
                "data",
                "comparison",
                "compare",
                "summary",
                "dashboard",
                "timeline",
                "table",
                "chart",
                "指标",
                "数据",
                "对比",
                "总结",
                "时间线",
                "表格",
                "信息图",
                "可视化",
            ),
            "note contains comparison, summary, data, or timeline structure",
        ),
        (
            "card",
            ("card", "social", "xiaohongshu", "xhs", "knowledge card", "小红书", "知识卡片", "卡片", "社媒"),
            "note is suited to compact shareable knowledge cards",
        ),
        (
            "photo",
            (
                "photo",
                "person",
                "place",
                "product",
                "event",
                "object",
                "scene",
                "field",
                "人物",
                "地点",
                "产品",
                "事件",
                "物品",
                "现场",
                "照片",
            ),
            "note appears to need a real-world subject or scene",
        ),
    ]
    for asset_kind, tokens, reason in checks:
        if any(token in haystack for token in tokens):
            return asset_kind, reason
    return "illustration", "general knowledge note benefits from a section illustration"


def format_details(asset_kind: str) -> dict:
    normalized = normalize_asset_kind(asset_kind) or "illustration"
    preset = FORMAT_PRESETS[normalized]
    fallback_aspect = DEFAULT_IMAGE_ASPECTS.get(normalized, "4:3")
    file_format = preset["file_format"]
    if normalized == "diagram" and configured_prefer_svg_for_diagrams():
        file_format = "svg"
    return {
        "asset_kind": normalized,
        "label": preset["label"],
        "aspect_ratio": configured_default_aspect(normalized, fallback_aspect),
        "file_format": file_format,
        "folder_key": preset["folder_key"],
        "best_for": preset["best_for"],
    }


def asset_subfolder_for_folder_key(folder_key: str | None) -> str:
    return ASSET_SUBFOLDERS.get(folder_key or "", "插图")


def build_format_plan(text: str, terms: list[str], asset_kind_arg: str | None = None) -> dict:
    requested_kind = normalize_asset_kind(asset_kind_arg)
    configured_mode = configured_image_format_mode()
    if requested_kind:
        selected = requested_kind
        mode = "custom"
        reason = "user-specified asset kind"
    elif configured_mode == "auto":
        selected, reason = recommend_asset_kind(text, terms)
        mode = "auto"
    else:
        selected = "illustration"
        reason = "configured default format routing"
        mode = "default"
    details = format_details(selected)
    alternatives = [
        {
            "asset_kind": name,
            "aspect_ratio": configured_default_aspect(name, DEFAULT_IMAGE_ASPECTS.get(name, "auto")),
            "file_format": "svg" if name == "diagram" and configured_prefer_svg_for_diagrams() else preset["file_format"],
            "best_for": preset["best_for"],
        }
        for name, preset in FORMAT_PRESETS.items()
        if name != selected
    ]
    return {
        "mode": mode,
        "reason": reason,
        **details,
        "alternatives": alternatives,
    }


def first_heading_or_stem(text: str, note: Path) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return note.stem


def slugify(value: str, fallback: str = "image") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-{2,}", "-", value).strip("-_")
    return value[:80] or fallback


def note_asset_folder_name(note: Path, text: str) -> str:
    title = first_heading_or_stem(text, note)
    title_slug = slugify(title, slugify(note.stem, "note"))
    stem_slug = slugify(note.stem, title_slug)
    pattern = configured_asset_folder_pattern()
    folder_name = (
        pattern.replace("{note-title}", title_slug)
        .replace("{note-slug}", title_slug)
        .replace("{note-stem}", stem_slug)
    )
    return slugify(folder_name, f"{title_slug}-封面-插图")


def note_asset_folder(vault: Path, note: Path, subfolder: str | None = None, create: bool = True) -> Path:
    text = read_text(note)
    root = resolve_attachment_base(vault, None, create=create) / note_asset_folder_name(note, text)
    folder = root / subfolder if subfolder else root
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


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


def build_web_query_plan(
    vault: Path,
    note: Path,
    style_arg: str | None = None,
    style_mode_arg: str | None = None,
    asset_kind_arg: str | None = None,
) -> dict:
    text = read_text(note)
    title = first_heading_or_stem(text, note)
    terms = extract_terms(text)
    style_plan = build_style_plan(text, terms, style_arg, style_mode_arg)
    format_plan = build_format_plan(text, terms, asset_kind_arg)
    headings = [
        heading.strip()
        for heading in re.findall(r"^#{2,3}\s+(.+)$", text, flags=re.MULTILINE)
        if heading.strip()
    ][:6]
    core_terms = [term for term in terms if len(term) >= 2][:10]
    topic = " ".join([title, *core_terms[:4]]).strip()
    if not topic:
        topic = note.stem
    queries = []
    kind_suffixes = {
        "cover": ("cover image", "hero image", "editorial cover"),
        "illustration": ("illustration", "concept illustration", "educational illustration"),
        "infographic": ("infographic", "visual summary", "knowledge infographic"),
        "diagram": ("diagram", "process diagram", "architecture diagram"),
        "slide": ("presentation slide", "slide background", "teaching slide"),
        "photo": ("photo", "documentary image", "realistic photo"),
        "card": ("knowledge card", "social media card", "visual card"),
        "web-image": ("image", "illustration", "photo"),
    }
    preferred_suffixes = kind_suffixes.get(format_plan["asset_kind"], kind_suffixes["illustration"])
    for suffix in (*preferred_suffixes, "illustration", "diagram", "infographic", "photo"):
        queries.append(f"{topic} {suffix}".strip())
    for style_term in style_plan["search_terms"]:
        queries.append(f"{topic} {style_term}".strip())
    if re.search(r"[\u4e00-\u9fff]", text):
        queries.insert(0, f"{topic} 配图")
        queries.insert(1, f"{topic} 信息图")
    seen: set[str] = set()
    unique_queries: list[str] = []
    for query in queries:
        key = query.lower()
        if key not in seen:
            seen.add(key)
            unique_queries.append(query)
    target_folder = note_asset_folder(vault, note, asset_subfolder_for_folder_key(format_plan["folder_key"]), create=False)
    style_queries = [f"{topic} {term}".strip() for term in style_plan["search_terms"]]
    return {
        "vault": str(vault),
        "note": str(note),
        "title": title,
        "headings": headings,
        "terms_used": core_terms,
        "target_folder": normalize_rel(target_folder, vault),
        "asset_plan": build_asset_plan(vault, note, create=False, asset_kind_arg=asset_kind_arg),
        "image_style": style_plan,
        "image_format": format_plan,
        "primary_query": unique_queries[0],
        "queries": unique_queries[:6],
        "style_queries": style_queries[:5],
        "match_criteria": [
            "semantic match with the note title, headings, and core entities",
            f"visual style should match '{style_plan['selected']}' unless the model selects a better scene-specific style",
            f"asset kind should fit '{format_plan['asset_kind']}' with aspect ratio '{format_plan['aspect_ratio']}'",
            f"prefer final file format '{format_plan['file_format']}' unless preserving a web source format is better",
            "clear subject matter that adds evidence or explanation, not decoration only",
            "trustworthy source page and usable image license or user-approved use",
            "sufficient resolution, no heavy watermark, no misleading crop",
            "caption can honestly state what the image contributes to the note",
        ],
    }


def extension_from_response(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    path_ext = Path(unquote(parsed.path)).suffix.lower()
    if path_ext in IMAGE_EXTS:
        return ".jpg" if path_ext == ".jpeg" else path_ext
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            guessed = ".jpg" if guessed == ".jpe" else guessed.lower()
            if guessed in IMAGE_EXTS:
                return guessed
    return ".jpg"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_attachment_base(vault: Path, folder_arg: str | None, create: bool = True) -> Path:
    folder_value = folder_arg or configured_attachment_folder()
    if folder_value:
        folder_path = Path(folder_value)
        folder = folder_path if folder_path.is_absolute() else vault / folder_path
    else:
        folder = vault / "Attachments"
    folder = folder.resolve()
    try:
        folder.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Attachment folder must stay inside the vault: {folder}") from exc
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def build_asset_plan(vault: Path, note: Path, create: bool = False, asset_kind_arg: str | None = None) -> dict:
    text = read_text(note)
    terms = extract_terms(text)
    format_plan = build_format_plan(text, terms, asset_kind_arg)
    root = note_asset_folder(vault, note, None, create=create)
    folders = {
        "asset_root": root,
        "cover_folder": root / ASSET_SUBFOLDERS["cover_folder"],
        "illustration_folder": root / ASSET_SUBFOLDERS["illustration_folder"],
        "web_image_folder": root / ASSET_SUBFOLDERS["web_image_folder"],
        "infographic_folder": root / ASSET_SUBFOLDERS["infographic_folder"],
        "diagram_folder": root / ASSET_SUBFOLDERS["diagram_folder"],
        "slide_image_folder": root / ASSET_SUBFOLDERS["slide_image_folder"],
        "prompt_sidecar_folder": root / "prompts",
    }
    if create:
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)
    normalized_folders = {key: normalize_rel(path, vault) for key, path in folders.items()}
    format_plan["target_folder"] = normalized_folders.get(format_plan["folder_key"])
    return {
        "note": str(note),
        "generated_image_text_language": configured_generated_image_text_language(),
        "write_generation_prompts_to_note": configured_write_generation_prompts_to_note(),
        "image_format": format_plan,
        "folder_pattern": configured_asset_folder_pattern(),
        "folders": normalized_folders,
        "prompt_policy": "Do not insert generation prompts into the note body. Save prompt sidecars only when needed.",
    }


def safe_attachment_folder(
    vault: Path,
    folder_arg: str | None,
    note: Path,
    asset_kind_arg: str | None = None,
    create: bool = True,
) -> Path:
    if folder_arg:
        folder = resolve_attachment_base(vault, folder_arg, create=create)
    else:
        text = read_text(note)
        format_plan = build_format_plan(text, extract_terms(text), asset_kind_arg)
        folder = note_asset_folder(vault, note, asset_subfolder_for_folder_key(format_plan["folder_key"]), create=create)
    return folder


def download_url(url: str) -> tuple[bytes, str | None]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https image URLs are supported")
    request = Request(url, headers={"User-Agent": "obsidian-note-curator/1.0"})
    with urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type")
        chunks = []
        total = 0
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError("Image download exceeds 20 MB limit")
            chunks.append(chunk)
    return b"".join(chunks), content_type


def write_source_note(image_path: Path, vault: Path, note: Path, args: argparse.Namespace) -> Path:
    source_path = image_path.with_suffix(f"{image_path.suffix}.source.md")
    note_text = read_text(note)
    terms = extract_terms(note_text)
    style_plan = build_style_plan(note_text, terms, args.style, getattr(args, "style_mode", None))
    format_plan = build_format_plan(note_text, terms, getattr(args, "asset_kind", None))
    lines = [
        "---",
        f"sourceUrl: {json.dumps(args.url, ensure_ascii=False)}",
        f"sourcePage: {json.dumps(args.source_page or '', ensure_ascii=False)}",
        f"sourceTitle: {json.dumps(args.source_title or '', ensure_ascii=False)}",
        f"imageStyle: {json.dumps(style_plan['selected'], ensure_ascii=False)}",
        f"imageStyleMode: {json.dumps(style_plan['mode'], ensure_ascii=False)}",
        f"imageStyleReason: {json.dumps(style_plan['reason'], ensure_ascii=False)}",
        f"imageAssetKind: {json.dumps(format_plan['asset_kind'], ensure_ascii=False)}",
        f"imageAspectRatio: {json.dumps(format_plan['aspect_ratio'], ensure_ascii=False)}",
        f"imageFileFormat: {json.dumps(format_plan['file_format'], ensure_ascii=False)}",
        f"imageFormatReason: {json.dumps(format_plan['reason'], ensure_ascii=False)}",
        f"downloadedAt: {datetime.now(timezone.utc).isoformat()}",
        f"usedIn: {json.dumps(normalize_rel(note, vault), ensure_ascii=False)}",
        "---",
        "",
        "Source metadata for a web image saved by obsidian-note-curator.",
        "",
    ]
    write_text(source_path, "\n".join(lines))
    return source_path


def download_web_image(args: argparse.Namespace) -> dict:
    vault = find_vault(Path(args.vault).resolve() if args.vault else None)
    note = resolve_note(vault, args.note)
    folder = safe_attachment_folder(vault, args.attachments_folder, note, args.asset_kind, create=not args.dry_run)
    note_text = read_text(note)
    terms = extract_terms(note_text)
    style_plan = build_style_plan(note_text, terms, args.style, args.style_mode)
    format_plan = build_format_plan(note_text, terms, args.asset_kind)
    if args.dry_run:
        return {
            "changed": False,
            "dry_run": True,
            "note": str(note),
            "target_folder": normalize_rel(folder, vault),
            "url": args.url,
            "image_style": style_plan,
            "image_format": format_plan,
            "insert": args.insert,
        }
    data, content_type = download_url(args.url)
    if content_type and not content_type.lower().startswith("image/"):
        parsed_ext = Path(unquote(urlparse(args.url).path)).suffix.lower()
        if parsed_ext not in IMAGE_EXTS:
            raise ValueError(f"URL did not return an image content type: {content_type}")
    ext = extension_from_response(args.url, content_type)
    base_name = slugify(args.filename or Path(unquote(urlparse(args.url).path)).stem or note.stem, "web-image")
    destination = unique_path(folder / f"{base_name}{ext}")
    destination.write_bytes(data)
    source_note = None
    if not args.no_source_note:
        source_note = write_source_note(destination, vault, note, args)
    insert_result = None
    if args.insert:
        insert_args = argparse.Namespace(
            vault=str(vault),
            note=str(note),
            image=[str(destination)],
            position=args.position,
            heading=args.heading,
            caption=args.caption,
            attachments_folder=None,
            copy=False,
            dry_run=False,
        )
        insert_result = apply_images(insert_args)
    return {
        "changed": True,
        "note": str(note),
        "image": normalize_rel(destination, vault),
        "absolute_path": str(destination),
        "source_note": normalize_rel(source_note, vault) if source_note else None,
        "content_type": content_type,
        "image_style": style_plan,
        "image_format": format_plan,
        "insert_result": insert_result,
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
    folder = resolve_attachment_base(vault, attachment_folder, create=True)
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


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Resolve, suggest, download, and insert Obsidian note images.")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory")
    inv.add_argument("--vault")
    inv.add_argument("--note", required=True)

    sug = sub.add_parser("suggest")
    sug.add_argument("--vault")
    sug.add_argument("--note", required=True)
    sug.add_argument("--limit", type=int, default=8)

    asset = sub.add_parser("asset-plan")
    asset.add_argument("--vault")
    asset.add_argument("--note", required=True)
    asset.add_argument("--create", action="store_true")
    asset.add_argument("--asset-kind", help="Optional asset kind override: cover, illustration, infographic, diagram, slide, photo, card, or web-image")

    webq = sub.add_parser("web-query")
    webq.add_argument("--vault")
    webq.add_argument("--note", required=True)
    webq.add_argument("--style", help="Image style name, or 'auto' for scene-specific style selection")
    webq.add_argument("--style-mode", choices=["default", "auto"], help="Use configured default style or auto-select by note context")
    webq.add_argument("--asset-kind", help="Optional asset kind override for format, aspect ratio, and target folder")

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

    dl = sub.add_parser("download")
    dl.add_argument("--vault")
    dl.add_argument("--note", required=True)
    dl.add_argument("--url", required=True)
    dl.add_argument("--filename")
    dl.add_argument("--source-page")
    dl.add_argument("--source-title")
    dl.add_argument("--caption")
    dl.add_argument("--style")
    dl.add_argument("--style-mode", choices=["default", "auto"])
    dl.add_argument("--asset-kind", help="Optional asset kind override for target folder and source metadata")
    dl.add_argument("--position", choices=["hero", "after-heading", "end"], default="hero")
    dl.add_argument("--heading")
    dl.add_argument("--attachments-folder")
    dl.add_argument("--insert", action="store_true")
    dl.add_argument("--no-source-note", action="store_true")
    dl.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    try:
        vault = find_vault(Path(args.vault).resolve() if getattr(args, "vault", None) else None)
        if args.command == "inventory":
            print_json(build_inventory(vault, resolve_note(vault, args.note)))
        elif args.command == "suggest":
            print_json(suggest_images(vault, resolve_note(vault, args.note), args.limit))
        elif args.command == "asset-plan":
            print_json(build_asset_plan(vault, resolve_note(vault, args.note), args.create, args.asset_kind))
        elif args.command == "web-query":
            print_json(build_web_query_plan(vault, resolve_note(vault, args.note), args.style, args.style_mode, args.asset_kind))
        elif args.command == "apply":
            print_json(apply_images(args))
        elif args.command == "download":
            print_json(download_web_image(args))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
