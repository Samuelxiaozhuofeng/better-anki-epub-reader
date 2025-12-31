from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LookupResult:
    word: str
    basic_meaning: List[str]
    contextual_meaning: str
    optional: Dict[str, Any]


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            return "\n".join(lines[1:-1]).strip()
    return s


def _extract_first_json_object(text: str) -> Optional[str]:
    s = _strip_code_fences(text)
    start = s.find("{")
    if start < 0:
        return None

    in_string = False
    escape = False
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def _coerce_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(x).strip() for x in value if str(x).strip()]
    else:
        items = [str(value).strip()]
    return [x for x in items if x]


def parse_lookup_result(text: str, *, max_basic_meanings: int = 3) -> LookupResult:
    candidate = _extract_first_json_object(text)
    if not candidate:
        raise ValueError("未找到 JSON 对象")

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("JSON 根对象必须是 object")

    word = str(data.get("word", "")).strip()
    contextual = str(data.get("contextual_meaning", "")).strip()
    basic = _coerce_str_list(data.get("basic_meaning"))

    if not word:
        raise ValueError("缺少必选字段: word")
    if not contextual:
        raise ValueError("缺少必选字段: contextual_meaning")
    if not basic:
        raise ValueError("缺少必选字段: basic_meaning")

    basic = basic[:max_basic_meanings]

    optional: Dict[str, Any] = {
        k: v
        for k, v in data.items()
        if k not in {"word", "basic_meaning", "contextual_meaning"}
    }
    return LookupResult(word=word, basic_meaning=basic, contextual_meaning=contextual, optional=optional)


def build_lookup_prompt(
    *,
    template_text: str,
    word: str,
    context: str,
    enabled_optional_fields: Dict[str, bool],
    max_basic_meanings: int = 3,
) -> str:
    optional_fields = [k for k, enabled in enabled_optional_fields.items() if enabled]
    optional_clause = ""
    if optional_fields:
        optional_clause = ", ".join(optional_fields)

    schema = (
        "{\n"
        '  "word": string,\n'
        f'  "basic_meaning": [string]  # 最多 {max_basic_meanings} 条\n'
        '  "contextual_meaning": string\n'
        "}"
    )

    template_rendered = (template_text or "").strip()
    template_rendered = template_rendered.replace("{word}", word)
    template_rendered = template_rendered.replace("{optional_fields}", optional_clause)
    if "{context}" in template_rendered:
        template_rendered = template_rendered.replace("{context}", context or "")
    if "{json_schema}" in template_rendered:
        template_rendered = template_rendered.replace("{json_schema}", schema)

    needs_schema = "{json_schema}" not in (template_text or "")
    needs_word = "{word}" not in (template_text or "")
    needs_context = "{context}" not in (template_text or "")

    parts: List[str] = []
    if template_rendered:
        parts.append(template_rendered)

    parts.append("请严格只输出 JSON（不要 Markdown/代码块/解释性文字）。")
    if needs_schema:
        parts.append("JSON schema:")
        parts.append(schema)
    if optional_fields:
        parts.append(
            "可选字段（如果你能提供）："
            + ", ".join(optional_fields)
            + "（仅在有把握时输出；没有就省略字段）"
        )
    if needs_word:
        parts.append(f"目标词汇：{word}")
    parts.append(
        "要求：\n"
        f"- basic_meaning：不超过 {max_basic_meanings} 条，给出词汇常见核心义（简明）。\n"
        "- contextual_meaning：必须结合下面上下文（当前句/邻句），并明确对应本次上下文。"
    )
    if needs_context:
        parts.append(f"上下文：\n{context}")
    return "\n\n".join([p for p in parts if p.strip()]).strip()


def build_json_repair_prompt(*, invalid_output: str) -> str:
    return (
        "你将把下面内容修复为严格 JSON，并且只输出 JSON（不要 Markdown/代码块/多余文字）。\n"
        "必选字段：word、basic_meaning（数组，最多3条）、contextual_meaning。\n\n"
        "待修复内容：\n"
        f"{invalid_output}\n"
    ).strip()


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def lookup_template_for_preferences(*, style: str, language: str) -> str:
    style = (style or "friendly").strip().lower()
    language = (language or "zh").strip().lower()

    if language == "en":
        lang_line = "Write the meanings in English (JSON keys stay as specified)."
    elif language == "es":
        lang_line = "Escribe los significados en español (las claves JSON se mantienen)."
    else:
        lang_line = "释义内容请使用中文（JSON 键保持为系统指定）。"

    if style == "formal":
        style_lines = (
            "Style: formal, academic, precise; avoid jokes and avoid fluff.",
            "Prefer clear definitions over paraphrase.",
        )
    elif style == "humorous":
        style_lines = (
            "Style: light and humorous but still accurate; keep it tasteful and brief.",
            "No emojis unless absolutely necessary.",
        )
    else:
        style_lines = (
            "Style: friendly teacher; simple and clear; brief.",
            "Use easy wording suitable for learners.",
        )

    return "\n".join(
        [
            "You are a language teacher.",
            lang_line,
            *style_lines,
        ]
    ).strip()


def render_lookup_result_html(result: LookupResult, *, enabled_optional_fields: Dict[str, bool]) -> str:
    label_map = {"pos": "词性", "ipa": "音标", "examples": "例句"}
    parts: List[str] = []
    parts.append("<div>")
    parts.append("<h3 style='margin:0 0 8px 0;'>基本义</h3>")
    parts.append("<ul style='margin:0 0 12px 18px; padding:0;'>")
    for item in result.basic_meaning:
        parts.append(f"<li style='margin:4px 0;'>{escape_html(item)}</li>")
    parts.append("</ul>")

    parts.append("<h3 style='margin:0 0 8px 0;'>语境义</h3>")
    parts.append(f"<p style='margin:0 0 12px 0;'>{escape_html(result.contextual_meaning)}</p>")

    for key, enabled in enabled_optional_fields.items():
        if not enabled:
            continue
        if key not in result.optional:
            continue
        value = result.optional.get(key)
        if value is None:
            continue
        title = label_map.get(key, str(key))
        parts.append(f"<h3 style='margin:0 0 8px 0;'>{escape_html(title)}</h3>")
        if isinstance(value, list):
            if key == "examples":
                parts.append("<ul style='margin:0 0 12px 18px; padding:0;'>")
                for item in value:
                    if isinstance(item, dict):
                        en = str(item.get("en", "")).strip()
                        zh = str(item.get("zh", "")).strip()
                        line = en if not zh else f"{en} — {zh}"
                    else:
                        line = str(item).strip()
                    if line:
                        parts.append(f"<li style='margin:4px 0;'>{escape_html(line)}</li>")
                parts.append("</ul>")
                continue
            parts.append("<ul style='margin:0 0 12px 18px; padding:0;'>")
            for v in value:
                s = str(v).strip()
                if s:
                    parts.append(f"<li style='margin:4px 0;'>{escape_html(s)}</li>")
            parts.append("</ul>")
        else:
            parts.append(f"<p style='margin:0 0 12px 0;'>{escape_html(str(value))}</p>")

    parts.append("</div>")
    return "".join(parts)


def render_streaming_html(accumulated_text: str) -> str:
    safe = escape_html(accumulated_text)
    return (
        "<div>"
        "<p style='margin:0 0 8px 0; color:#86868B;'>正在生成（流式）…</p>"
        f"<pre style='white-space:pre-wrap; margin:0;'>{safe}</pre>"
        "</div>"
    )
