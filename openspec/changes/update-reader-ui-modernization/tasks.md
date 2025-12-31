## 1. Implementation
- [ ] 1.1 Audit current reader UI components and styles (`gui/ui_reader_window.py`, `gui/reader_window.py`)
- [ ] 1.2 Define a small set of UI design tokens (colors, spacing, font sizes) and a QSS strategy (single stylesheet vs component-level)
- [ ] 1.3 Update reader window styling for reading comfort (text area typography, margins, selection color, scrollbars)
- [ ] 1.4 Update word panel styling and layout (hierarchy, spacing, loading/empty states, readability of rich text)
- [ ] 1.5 Make toolbar controls visually consistent (button sizes, labels, spacing; optional icons if available)
- [ ] 1.6 Apply the same styling conventions to settings dialogs for consistency
- [ ] 1.7 UI 文案统一中文（ReaderWindow、菜单、按钮、对话框）
- [ ] 1.8 Persist window geometry and splitter position across sessions
- [ ] 1.9 Ensure UI preferences persist and reload correctly (align with `config/reader_style.json` and existing config files)

## 2. Validation
- [ ] 2.1 Manual QA in Anki: open EPUB, navigate chapters, lookup word, add note, switch themes, adjust typography controls
- [ ] 2.2 Cross-platform sanity checks (at minimum: macOS + one of Windows/Linux if available)
- [ ] 2.3 No performance regression when rendering chapters (no noticeable UI lag during scrolling/selection)
