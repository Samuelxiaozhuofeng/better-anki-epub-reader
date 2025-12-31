## Context
The add-on UI is implemented with Anki `aqt` (PyQt). The main window uses a generated UI class (`gui/ui_reader_window.py`) with extensive inline QSS, and `gui/reader_window.py` adds additional widgets and style updates at runtime (theme switching, typography controls).

## Goals / Non-Goals
- Goals:
  - Improve readability and visual hierarchy for long-form reading.
  - Make styling consistent and maintainable (avoid scattered, conflicting QSS).
  - Keep UX snappy; avoid heavy redraws or expensive HTML reprocessing on small UI changes.
  - Standardize UI labels to Chinese to reduce cognitive load.
  - Persist UI state (window geometry and splitter position) across sessions.
- Non-Goals:
  - No change in feature set or data model unless needed for UI persistence.
  - No new external UI dependencies; stay within PyQt/Anki.

## Decisions
- Decision: Consolidate styling into a small number of QSS “themes” with shared tokens.
  - Why: Current styles are split between generated UI and runtime overrides, increasing inconsistency.
- Decision: Keep existing user-adjustable controls (font size, line spacing, paragraph spacing, alignment, theme) and ensure they visibly affect the reading area in real time.
  - Why: These controls already exist and are central to reading comfort.
- Decision: Standardize reader UI labels to Chinese.
  - Why: Mixed CN/EN labels reduce scanability and feel less polished.
- Decision: Persist window geometry and splitter position.
  - Why: Readers expect the window layout to remain stable across sessions.

## Approach
- Define a minimal “design token” mapping per theme (background, foreground, selection, panel background, accent).
- Apply QSS consistently:
  - Base QSS applied at the window/root level.
  - Component QSS limited to special cases (e.g., word header card).
- Add missing UI states where needed:
  - Empty state (no word selected) in the word panel.
  - Loading state during AI requests that is visually distinct and accessible.
- Implement persistence:
  - Save/restore window geometry and splitter sizes via `QSettings` (preferred) or a small JSON config in the add-on folder.
  - Keep persistence isolated to UI concerns; avoid coupling to EPUB/AI logic.

## Risks / Trade-offs
- QSS differences between Qt versions / platforms can cause visual drift.
  - Mitigation: prefer simple QSS, avoid platform-specific assets; verify on multiple OSes when possible.
- Over-styling can reduce Anki-native feel.
  - Mitigation: keep changes minimal; prioritize readability and consistent spacing over novelty.

## Open Questions
- Confirm typography defaults (font stack, default sizes).
- Confirm whether to include icons (would require bundling assets and ensuring paths work in add-on packaging).
