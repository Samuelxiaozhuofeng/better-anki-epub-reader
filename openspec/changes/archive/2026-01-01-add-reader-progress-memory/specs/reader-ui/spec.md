## ADDED Requirements
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
