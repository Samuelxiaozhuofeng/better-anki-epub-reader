# reader-ui Specification

## Purpose
TBD - created by archiving change update-reader-ui-modernization. Update Purpose after archive.
## Requirements
### Requirement: UI 文案统一中文
The system SHALL present reader UI labels and actions in Chinese consistently.

#### Scenario: Reader controls are Chinese
- **WHEN** the user opens the reader window
- **THEN** primary controls (toolbars, buttons, menus, dialogs) display Chinese labels

### Requirement: Modern, consistent reader appearance
The system SHALL present a visually consistent and modern reader UI (reading area, toolbars, and word panel) that prioritizes long-form reading comfort.

#### Scenario: Open reader window
- **WHEN** the user opens the reader window
- **THEN** the reading area, toolbars, and word panel share consistent spacing, typography, and component styling

### Requirement: Readability-focused typography controls
The system SHALL allow the user to adjust typography settings (font size, line spacing, paragraph spacing, and alignment) and apply changes immediately to the reading area.

#### Scenario: Adjust typography
- **WHEN** the user changes font size, line spacing, paragraph spacing, or alignment
- **THEN** the reading area updates immediately to reflect the new settings

### Requirement: Theme support with accessible contrast
The system SHALL provide themes (including a dark theme) with sufficient contrast for text and controls.

#### Scenario: Switch theme
- **WHEN** the user selects a different theme
- **THEN** text, selection highlight, and controls remain readable and visually consistent across the reader window

### Requirement: Word panel states are clear and readable
The system SHALL display clear word panel states for empty, loading, streaming, and loaded content, and render structured lookup content in a readable layout.

#### Scenario: No word selected
- **WHEN** the reader window is open and the user has not selected/clicked a word
- **THEN** the word panel shows an empty state that explains how to look up a word

#### Scenario: Lookup in progress (non-blocking)
- **WHEN** the user triggers a word lookup
- **THEN** the word panel shows a loading/streaming state until results are available or an error occurs
- **AND THEN** the reader UI remains responsive (no UI freeze) while the lookup runs

#### Scenario: Lookup result displayed (structured)
- **WHEN** the lookup completes successfully
- **THEN** the word panel renders content in structured sections:
  - word header
  - basic meanings (up to 3 items)
  - contextual meaning bound to the current sentence/adjacent sentence context

#### Scenario: Rapid successive lookups
- **WHEN** the user clicks multiple words in quick succession
- **THEN** the latest lookup becomes the active one and older lookups are cancelled or ignored
- **AND THEN** older results MUST NOT overwrite the latest word panel content

### Requirement: Lookup results are returned as JSON and repaired if needed
The system SHALL obtain lookup results as JSON with required fields and apply a bounded repair/retry strategy when the model output is invalid or missing required fields.

#### Scenario: Valid JSON result
- **WHEN** a lookup completes successfully
- **THEN** the system produces a JSON object containing `word`, `basic_meaning`, and `contextual_meaning`
- **AND THEN** `basic_meaning` contains at most 3 meanings

#### Scenario: Invalid model output
- **WHEN** the model output is not valid JSON or is missing required fields
- **THEN** the system attempts repair/retry to produce valid JSON
- **AND THEN** if repair/retry fails, the word panel shows an error state with a clear message

### Requirement: Optional lookup fields are user-configurable
The system SHALL allow optional lookup fields (e.g., part of speech) to be enabled/disabled via configuration, without affecting required fields.

#### Scenario: Optional fields disabled
- **WHEN** optional lookup fields are disabled in configuration
- **THEN** the word panel only displays required fields (`word`, `basic_meaning`, `contextual_meaning`)

#### Scenario: Optional fields enabled
- **WHEN** a user enables one or more optional fields
- **THEN** the system requests and renders those fields in the word panel alongside required fields

### Requirement: Persist reader layout and window state
The system SHALL persist and restore reader window geometry and splitter position across sessions.

#### Scenario: Restore layout after restart
- **WHEN** the user closes and reopens Anki and opens the reader window again
- **THEN** the reader window restores the last window size/position and splitter layout

### Requirement: UI changes do not break existing workflows
The system SHALL preserve existing reader workflows (open content, navigate chapters, lookup words, add to Anki) while applying UI improvements.

#### Scenario: Add note after UI refresh
- **WHEN** the user looks up a word and clicks “add to Anki”
- **THEN** a note is created using the configured deck/model/field mapping as before

### Requirement: Shared UI tokens remain consistent
The system SHALL define reader UI theme tokens and base dialog styling in a single shared source of truth so that the reader window and related dialogs remain visually consistent.

#### Scenario: Open reader and dialogs
- **WHEN** the user opens the reader window and any related settings dialog
- **THEN** the surfaces use the same base styling and compatible theme palette (no diverging “near-duplicate” definitions)

### Requirement: 阅读进度记忆与自动恢复
The system SHALL persist the user’s last reading location per book (chapter + in-chapter position) and restore it automatically when the same book is opened again.

#### Scenario: 自动保存阅读进度（滚动阅读）
- **WHEN** the user scrolls in the reading area of a book
- **THEN** the system saves the current chapter and in-chapter position automatically (without requiring a manual “mark” action)
- **AND THEN** progress updates are throttled/debounced to avoid excessive writes

#### Scenario: 自动恢复到上次阅读点
- **WHEN** the user opens a previously-read book
- **THEN** the reader jumps to the last saved chapter for that book
- **AND THEN** the reader restores the in-chapter position so the user can continue reading where they left off

#### Scenario: Re-opening an already-imported EPUB does not reset progress by default
- **WHEN** the user opens an EPUB file that has already been imported
- **THEN** the system preserves the existing reading progress by default

### Requirement: 打开阅读器时提供书籍选择入口
The system SHALL present a book selection entry point when the reader window is opened so the user can quickly continue reading.

#### Scenario: Open reader shows book manager
- **WHEN** the user opens the reader window
- **THEN** the system shows the “book manager” dialog by default

