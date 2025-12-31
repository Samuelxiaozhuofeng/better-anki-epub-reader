## 1. Implementation
- [x] 1.1 Audit duplication hotspots and define extraction list (async runner, config paths, QSS, theme tokens)
- [x] 1.2 Introduce shared helpers:
  - [x] 1.2.1 Centralize add-on config/data paths (single source of truth)
  - [x] 1.2.2 Centralize `run_async` (and align with `event_loop_handler.py` usage)
  - [x] 1.2.3 Centralize dialog base QSS and reader theme tokens (允许视觉等价调整)
- [x] 1.3 Split `gui/reader_window.py` into focused modules (no behavior change):
  - [x] 1.3.1 Move `WordClickableTextEdit` into a widget module
  - [x] 1.3.2 Move `EPUBManagerDialog` into its own dialog module
  - [x] 1.3.3 Keep `ReaderWindow` as the composition root and update imports
- [x] 1.4 Replace in-file duplicates with shared modules (theme map, word label sizing, path building)
- [x] 1.5 Tighten lifecycle ownership (avoid repeated `TemplateManager()` creation, clarify single instance ownership)
- [x] 1.6 Keep `utils/*` scope limited to shared helpers only (paths/async/config); defer unrelated `utils` refactors

## 2. Validation
- [x] 2.1 Manual QA in Anki:
  - [x] 2.1.1 Open reader, open EPUB, navigate chapters, verify progress/bookmark behavior
  - [x] 2.1.2 Click/select word → meaning loads → add to Anki still works
  - [x] 2.1.3 Theme/typography controls still apply immediately and persist as before
  - [x] 2.1.4 Open settings dialogs (AI/context/note/template) and verify styling remains consistent
- [x] 2.2 Smoke-check startup/shutdown: no new event loop warnings/exceptions on Anki exit
