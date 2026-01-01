## ADDED Requirements
### Requirement: 图片搜索来源稳定并提供失败退路
The system SHALL retrieve images from a stable public source by default and provide a usable fallback when images cannot be loaded.

#### Scenario: Prefer stable JSON API sources
- **WHEN** the user requests images for a word
- **THEN** the system fetches image candidates from a stable JSON API source (e.g., Wikimedia/Wikipedia)
- **AND THEN** the system avoids relying solely on brittle HTML scraping

#### Scenario: Fallback link when no images
- **WHEN** no images can be retrieved or decoded
- **THEN** the image panel shows a clear message and a link to search images in the browser
