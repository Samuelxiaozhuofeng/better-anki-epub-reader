# Change: Modernize Reader UI

## Why
The current reader UI feels visually inconsistent and “rough”, which reduces reading comfort and makes controls harder to scan while reading and looking up words.

## What Changes
- Refresh the visual design of the reader window (typography, spacing, colors, component styling) to a more modern, comfortable reading experience.
- Make styling consistent across the reader window and related dialogs (toolbars, buttons, text areas, panels).
- Improve UI ergonomics without changing core behaviors (EPUB loading, AI lookups, note creation).
- Persist additional UI state for a smoother reading workflow (window size/position and splitter position).

## Impact
- Affected specs:
  - `reader-ui` (new capability spec introduced via this change)
- Affected code (expected):
  - `gui/reader_window.py`
  - `gui/ui_reader_window.py`
  - `gui/settings_dialog.py`, `gui/ui_settings_dialog.py`
  - `config/reader_style.json` (persisted UI preferences)

## Non-Goals
- No changes to EPUB parsing logic, AI prompting logic, or Anki note creation behavior (unless required for UI wiring).
- No new third-party UI frameworks; remain within Anki `aqt`/PyQt.
- No major feature additions beyond UI/UX polish (e.g., annotations, highlights, syncing).

## Confirmed Decisions
- UI 文案：统一中文
- 视觉方向：macOS 极简（克制、低对比、强调阅读舒适度）
- UI 状态持久化：需要（窗口大小/位置、分割条位置）
