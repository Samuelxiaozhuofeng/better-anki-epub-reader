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
The system SHALL display clear word panel states for empty, loading, and loaded content, and render explanation content in a readable layout.

#### Scenario: No word selected
- **WHEN** the reader window is open and the user has not selected/clicked a word
- **THEN** the word panel shows an empty state that explains how to look up a word

#### Scenario: Lookup in progress
- **WHEN** the user triggers a word lookup
- **THEN** the word panel shows a loading state until results are available or an error occurs

#### Scenario: Lookup result displayed
- **WHEN** the lookup completes successfully
- **THEN** the word and explanation are displayed with readable typography and spacing

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

