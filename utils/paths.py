from __future__ import annotations

import os

from aqt import mw


def addon_install_root() -> str:
    return os.path.dirname(os.path.dirname(__file__))


def addon_data_root() -> str:
    return os.path.join(mw.pm.addonFolder(), "anki_reader")


def config_json_path() -> str:
    return os.path.join(addon_data_root(), "config.json")


def config_dir() -> str:
    return os.path.join(addon_data_root(), "config")


def note_config_path() -> str:
    return os.path.join(config_dir(), "note_config.json")


def reader_style_path() -> str:
    return os.path.join(config_dir(), "reader_style.json")


def templates_path() -> str:
    return os.path.join(addon_install_root(), "config", "templates.json")

