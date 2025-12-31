# Project Context

## Purpose
This repo is an Anki 2.1 add-on (ID `1098514784`) that provides an in-Anki EPUB/text “reader” to support language learning while reading:
- Open an EPUB (and/or paste text), read in a dedicated window.
- Click/select words to get AI-powered explanations (and optional translation/examples depending on client/prompting).
- Add the result to Anki as a new note using user-configurable deck/model/field mappings.
- Persist imported books/chapters/progress in Anki’s collection database.

## Tech Stack
- Language/runtime: Python (runs inside Anki’s embedded Python; not a standalone app)
- UI: Anki `aqt` + PyQt6 widgets (`QMainWindow`, dialogs, signals/slots)
- Async/network: `asyncio` + `aiohttp` for OpenAI-compatible chat completion APIs
- EPUB parsing: `zipfile`, `xml.etree.ElementTree`, BeautifulSoup4 (`bs4`), `lxml`
- Storage: Anki collection DB via `mw.col.db` (SQLite under the hood)
- Packaging/deps: vendored dependencies in `vendor/` (added to `sys.path` at runtime)
- Config: JSON files under `config/` plus runtime config written to `config.json` in the add-on folder

## Project Conventions

### Code Style
- Python modules use explicit classes for “handlers” and “clients” (e.g., `EPUBHandler`, `DBHandler`, `AnkiHandler`, `OpenAIClient`).
- Type hints are used in many places, but not enforced by tooling.
- Docstrings and UI strings are a mix of Chinese and English; keep new UI text consistent with the surrounding file.
- Prefer small, focused helper classes in `utils/` rather than monolithic GUI logic.
- Avoid introducing new third-party dependencies unless they can be vendored (Anki add-ons run in a constrained environment).

### Architecture Patterns
- Entry point: `__init__.py` registers a Tools menu action and opens `gui/reader_window.py:ReaderWindow`.
- UI layer: `gui/` contains Qt windows/dialogs and generated UI wrappers (e.g., `gui/ui_reader_window.py`).
- Domain/services:
  - `utils/epub_handler.py` loads EPUBs, extracts metadata/chapters, and cleans HTML for display.
  - `utils/db_handler.py` creates/reads/writes tables in `mw.col.db` for books/chapters/bookmarks.
  - `utils/anki_handler.py` creates notes in the configured deck/model with field mapping and tags.
  - `utils/ai_factory.py` selects an AI client; clients call OpenAI-compatible `/chat/completions` endpoints.
- Async in GUI: async work is typically executed by grabbing/creating an event loop and running `run_until_complete()`; keep UI responsive and avoid long blocking calls on the main thread.
- Cross-platform: `event_loop_handler.py` configures/cleans up event loop policy (notably for Windows) to reduce shutdown warnings.

### Testing Strategy
- No automated test suite is currently present; verification is primarily manual inside Anki.
- When changing behavior, prefer adding a small, deterministic helper function (e.g., in `utils/`) that can be sanity-checked independently, and then validate the UI flow in Anki.

### Git Workflow
- No repo-enforced workflow is defined here.
- Suggested: use small, focused commits; keep changes scoped to one concern; avoid formatting-only diffs unless required.

## Domain Context
- This is an Anki add-on: code runs inside Anki and uses `aqt.mw` (main window) and `mw.col` (collection).
- “Adding a note” means creating an `anki.notes.Note` and inserting it into `mw.col` in the selected deck.
- Persistent storage should use `mw.col.db` (Anki-managed SQLite), not external DB files.
- User configuration locations:
  - AI service + context settings: `CONFIG_PATH` in `gui/settings_dialog.py` writes `config.json` under the add-on folder.
  - Note settings: `config/note_config.json` (deck/model/field mapping/tags).
  - Prompt templates: `config/templates.json` (`{word}` placeholder; a “current template” id is stored).
  - Reader styling: `config/reader_style.json`.

## Important Constraints
- Must remain compatible with Anki versions declared in `manifest.json` (min `2.1.50`, max tested `24.06.3`).
- Dependency management: assume end-users do not have system-wide Python packages available; prefer vendoring into `vendor/` and adding it to `sys.path`.
- Network access is required for AI features; the add-on must handle offline/failing API calls gracefully.
- UI responsiveness matters: avoid blocking Anki’s UI thread on slow IO/network operations.

## External Dependencies
- OpenAI Chat Completions API: `https://api.openai.com/v1/chat/completions`
- “Custom Service” API: user-provided base URL implementing an OpenAI-compatible `/chat/completions` endpoint
- Anki runtime APIs: `aqt`, `anki`, and the collection database exposed via `mw.col.db`
