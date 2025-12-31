# Design: Reader UI Deduplication & Modularization

## Goals
- Reduce copy/paste logic and keep UI tokens consistent across surfaces.
- Make `ReaderWindow` easier to navigate by splitting clearly-scoped modules.
- Preserve existing behavior and UI as much as possible (refactor-first; QSS/theme changes must be visually equivalent).

## Proposed Module Boundaries

### Shared utilities
- `utils/paths.py` (or similar): defines canonical locations for:
  - add-on base dir (`.../anki_reader/`)
  - `config.json`
  - `config/` JSONs (note config, reader style, templates)
- `utils/async_utils.py`: single `run_async()` (or equivalent) used by GUI code; documented relationship with `event_loop_handler.py`.
- `utils/config_utils.py` (optional): thin helpers for reading/writing JSON config with consistent encoding/error handling (keep scope narrow; no broad utils refactor).

### Shared UI tokens
- `gui/ui_tokens.py` (or similar):
  - `DIALOG_QSS` base string (reused by dialogs)
  - reader theme tokens (theme → (bg, text, selection) and derived palette)
  - word label sizing helper based on word length

### Reader window split
Keep `gui/reader_window.py` as a thin composition root:
- `gui/reader/widgets.py`: `WordClickableTextEdit` and any reader-specific widgets.
- `gui/reader/epub_manager_dialog.py`: `EPUBManagerDialog` (and future EPUB-related dialogs).
- `gui/reader/reader_window.py`: optionally move `ReaderWindow` here if keeping the public import stable is easy; otherwise keep the class in `gui/reader_window.py` and import helpers from the new modules.

## Migration Strategy (Low Risk)
1. Extract shared helpers first and update imports, with no file moves.
2. Move `EPUBManagerDialog` out next (purely internal references).
3. Move `WordClickableTextEdit` out next.
4. If desired, move `ReaderWindow` into a subpackage only after internal refactors are stable; keep `from .gui.reader_window import ReaderWindow` behavior intact for `__init__.py`.

## Risks and Mitigations
- **Import stability**: `__init__.py` imports `from .gui.reader_window import ReaderWindow`.
  - Mitigation: keep that import path stable; if moving, add a small re-export shim module.
- **Event loop handling**: unify `run_async` without changing runtime semantics.
  - Mitigation: keep the exact current behavior initially; only align with `event_loop_handler.py` if manual QA confirms no regressions.
- **QSS diffs**: centralization can inadvertently change whitespace or selector ordering.
  - Mitigation: treat QSS as behavior; prefer moving the literal string unchanged.
