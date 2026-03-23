from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from .paths import addon_data_root, config_json_path, templates_path


PRESET_STYLE_OPTIONS: List[Tuple[str, str]] = [
    ("friendly", "友好讲解"),
    ("formal", "正式学术"),
    ("humorous", "轻松幽默"),
    ("custom", "自定义"),
]

LANGUAGE_OPTIONS: List[Tuple[str, str]] = [
    ("zh", "中文"),
    ("en", "English"),
    ("es", "Español"),
]

PRESET_STYLE_IDS = {item[0] for item in PRESET_STYLE_OPTIONS if item[0] != "custom"}
DEFAULT_PRESET_STYLE = "friendly"
DEFAULT_LANGUAGE = "zh"


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_json(path: str, data: Dict) -> None:
    os.makedirs(addon_data_root(), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _normalize_custom_styles(raw_styles) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    seen_ids = set()
    if isinstance(raw_styles, dict):
        raw_styles = list(raw_styles.values())
    if not isinstance(raw_styles, list):
        return normalized

    for index, item in enumerate(raw_styles, start=1):
        if not isinstance(item, dict):
            continue
        style_id = str(item.get("id", "")).strip() or f"custom_{index}"
        if style_id in seen_ids:
            continue
        name = str(item.get("name", "")).strip() or f"自定义风格 {index}"
        instruction = str(item.get("instruction", "")).strip() or str(item.get("template", "")).strip()
        if not instruction:
            continue
        normalized.append(
            {
                "id": style_id,
                "name": name,
                "instruction": instruction,
            }
        )
        seen_ids.add(style_id)
    return normalized


def _migrate_legacy_custom_styles() -> List[Dict[str, str]]:
    legacy = _load_json(templates_path())
    word_definition = legacy.get("word_definition", {})
    if not isinstance(word_definition, dict):
        return []

    styles: List[Dict[str, str]] = []
    for template_id, item in word_definition.items():
        if template_id in {"default", "example_json_guided"}:
            continue
        if isinstance(item, str):
            instruction = item.strip()
            name = template_id
        elif isinstance(item, dict):
            instruction = str(item.get("template", "")).strip()
            name = str(item.get("name", "")).strip() or template_id
        else:
            continue
        if not instruction:
            continue
        styles.append(
            {
                "id": str(template_id).strip() or f"custom_{len(styles) + 1}",
                "name": name,
                "instruction": instruction,
            }
        )
    return styles


def load_lookup_preferences() -> Dict:
    config = _load_json(config_json_path())

    language = str(config.get("lookup_language", DEFAULT_LANGUAGE)).strip().lower() or DEFAULT_LANGUAGE

    lookup_style_mode = str(config.get("lookup_style_mode", "")).strip().lower()
    lookup_style_preset = str(config.get("lookup_style_preset", "")).strip().lower()
    legacy_style = str(config.get("lookup_style", "")).strip().lower()

    if lookup_style_preset not in PRESET_STYLE_IDS:
        if legacy_style in PRESET_STYLE_IDS:
            lookup_style_preset = legacy_style
        else:
            lookup_style_preset = DEFAULT_PRESET_STYLE

    if lookup_style_mode not in {"preset", "custom"}:
        lookup_style_mode = "custom" if legacy_style == "custom" else "preset"

    custom_styles = _normalize_custom_styles(config.get("lookup_custom_styles"))
    if not custom_styles:
        custom_styles = _migrate_legacy_custom_styles()

    active_custom_style_id = str(config.get("lookup_active_custom_style_id", "")).strip()
    custom_ids = {item["id"] for item in custom_styles}
    if active_custom_style_id not in custom_ids:
        active_custom_style_id = custom_styles[0]["id"] if custom_styles else ""

    optional_fields = config.get("lookup_optional_fields", {})
    if not isinstance(optional_fields, dict):
        optional_fields = {}

    if lookup_style_mode == "custom" and not active_custom_style_id:
        lookup_style_mode = "preset"

    return {
        "lookup_language": language,
        "lookup_style_mode": lookup_style_mode,
        "lookup_style_preset": lookup_style_preset,
        "lookup_custom_styles": custom_styles,
        "lookup_active_custom_style_id": active_custom_style_id,
        "lookup_optional_fields": {
            "pos": bool(optional_fields.get("pos", False)),
            "ipa": bool(optional_fields.get("ipa", False)),
            "examples": bool(optional_fields.get("examples", False)),
        },
    }


def save_lookup_preferences(preferences: Dict) -> None:
    config = _load_json(config_json_path())
    normalized = load_lookup_preferences()
    normalized.update(preferences)

    custom_styles = _normalize_custom_styles(normalized.get("lookup_custom_styles", []))
    custom_ids = {item["id"] for item in custom_styles}
    active_custom_style_id = str(normalized.get("lookup_active_custom_style_id", "")).strip()
    if active_custom_style_id not in custom_ids:
        active_custom_style_id = custom_styles[0]["id"] if custom_styles else ""

    lookup_style_mode = str(normalized.get("lookup_style_mode", "preset")).strip().lower()
    if lookup_style_mode == "custom" and not active_custom_style_id:
        lookup_style_mode = "preset"

    lookup_style_preset = str(normalized.get("lookup_style_preset", DEFAULT_PRESET_STYLE)).strip().lower()
    if lookup_style_preset not in PRESET_STYLE_IDS:
        lookup_style_preset = DEFAULT_PRESET_STYLE

    config["lookup_language"] = str(normalized.get("lookup_language", DEFAULT_LANGUAGE)).strip().lower() or DEFAULT_LANGUAGE
    config["lookup_style_mode"] = lookup_style_mode
    config["lookup_style_preset"] = lookup_style_preset
    config["lookup_style"] = "custom" if lookup_style_mode == "custom" else lookup_style_preset
    config["lookup_custom_styles"] = custom_styles
    config["lookup_active_custom_style_id"] = active_custom_style_id
    config["lookup_optional_fields"] = {
        "pos": bool(normalized.get("lookup_optional_fields", {}).get("pos", False)),
        "ipa": bool(normalized.get("lookup_optional_fields", {}).get("ipa", False)),
        "examples": bool(normalized.get("lookup_optional_fields", {}).get("examples", False)),
    }

    _save_json(config_json_path(), config)


def find_active_custom_style(preferences: Dict) -> Dict[str, str] | None:
    active_id = str(preferences.get("lookup_active_custom_style_id", "")).strip()
    for item in preferences.get("lookup_custom_styles", []):
        if isinstance(item, dict) and item.get("id") == active_id:
            return item
    return None
