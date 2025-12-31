from __future__ import annotations

from typing import Dict, Tuple

ThemeColors = Tuple[str, str, str]


THEME_COLORS: Dict[str, ThemeColors] = {
    "Default": ("#FFFFFF", "#1D1D1F", "#CFE4FF"),
    "Eye Care": ("#F6F5F1", "#1D1D1F", "#E8E7E3"),
    "Dark": ("#1C1C1E", "#E5E5E7", "#3A3A3C"),
    "Brown": ("#FAF6F1", "#2C2C2E", "#EFE6D8"),
}


def get_theme_colors(theme_id: str) -> ThemeColors:
    return THEME_COLORS.get(theme_id, ("#FFFFFF", "#000000", "#F7F7F7"))


def get_reader_palette(theme_id: str) -> Dict[str, str]:
    bg_color, text_color, selection_color = get_theme_colors(theme_id)
    is_dark = theme_id == "Dark"

    return {
        "bg_color": bg_color,
        "text_color": text_color,
        "selection_color": selection_color,
        "is_dark": is_dark,
        "panel_bg": "#2C2C2E" if is_dark else "#F5F5F7",
        "card_bg": "#3A3A3C" if is_dark else "#FFFFFF",
        "border_color": "#3A3A3C" if is_dark else "#E5E5EA",
        "control_bg": "#3A3A3C" if is_dark else "#FFFFFF",
        "control_hover_bg": "#48484A" if is_dark else "#F5F5F7",
    }


def word_label_font_size(word: str) -> int:
    word_length = len(word.split())
    if word_length <= 3:
        return 28
    if word_length <= 6:
        return 24
    if word_length <= 10:
        return 20
    return 16


def word_label_font_size_compact(word: str) -> int:
    word_length = len(word.split())
    if word_length <= 3:
        return 24
    if word_length <= 6:
        return 20
    if word_length <= 10:
        return 18
    return 16
