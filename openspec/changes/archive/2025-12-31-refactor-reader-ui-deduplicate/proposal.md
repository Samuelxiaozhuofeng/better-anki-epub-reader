# Change: Refactor Reader UI to Reduce Duplication

## Why
The current Reader UI code has noticeable duplication and mixed responsibilities (UI styling, async helpers, config paths, EPUB management, word lookup, image search) concentrated in a few large modules. This makes changes riskier and slows iteration.

## What Changes
- Extract repeated constants/utilities (e.g., dialog QSS, theme tokens, async runner, config path helpers) into shared modules.
- Split `gui/reader_window.py` into smaller focused modules (reader window wiring vs widgets vs dialogs).
- Keep behavior and UI output the same by default; refactor is primarily structural and deduplication-focused.

## Impact
- Affected specs:
  - `reader-ui` (internal consistency requirements; no user-facing feature change intended)
- Affected code (expected):
  - `gui/reader_window.py` (split)
  - `gui/settings_dialog.py`, `gui/note_settings_dialog.py`, `gui/template_dialog.py` (reuse shared QSS/utilities)
  - `utils/*` (shared helpers for paths/async/config access)

## Current Findings (Duplication / Redundancy Hotspots)
- Duplicated async helper: `run_async()` exists in both `gui/reader_window.py` and `gui/settings_dialog.py`.
- Duplicated dialog styling: `DIALOG_QSS` is defined separately in multiple dialogs (`gui/settings_dialog.py`, `gui/note_settings_dialog.py`, `gui/template_dialog.py`).
- Duplicated theme token maps and word-label sizing logic: `theme_colors` dict and related derived colors appear multiple times in `gui/reader_window.py`.
- Repeated config path construction: multiple modules build `mw.pm.addonFolder()/anki_reader/...` paths independently.
- Mixed responsibilities in a single file: `gui/reader_window.py` contains `WordClickableTextEdit`, `ReaderWindow`, and `EPUBManagerDialog` plus image navigation and style persistence.

## Non-Goals
- No feature additions (annotations, highlights, sync, etc.).
- No behavioral change to EPUB parsing, AI prompting, or note creation flows unless required to preserve current behavior after refactor.
- No new third-party dependencies.

## Confirmed Decisions
- Scope: Reader UI refactor plus limited `utils/*` cleanup for shared small helpers only (`paths` / `async` / `config`).
- Styling constraint: “视觉等价即可” (visually equivalent is acceptable; no intentional UX/behavior changes).
