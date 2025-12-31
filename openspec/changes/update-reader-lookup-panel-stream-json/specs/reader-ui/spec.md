## MODIFIED Requirements
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

## ADDED Requirements
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
