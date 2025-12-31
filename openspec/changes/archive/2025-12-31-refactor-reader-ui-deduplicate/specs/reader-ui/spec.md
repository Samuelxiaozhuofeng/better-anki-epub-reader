# reader-ui Spec Delta

## ADDED Requirements
### Requirement: Shared UI tokens remain consistent
The system SHALL define reader UI theme tokens and base dialog styling in a single shared source of truth so that the reader window and related dialogs remain visually consistent.

#### Scenario: Open reader and dialogs
- **WHEN** the user opens the reader window and any related settings dialog
- **THEN** the surfaces use the same base styling and compatible theme palette (no diverging “near-duplicate” definitions)

