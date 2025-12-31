# Change: Update Reader 查词面板（流式 + JSON结构化 + 不阻塞）

## Why
当前查词流程会在点击词汇后阻塞 UI（同步等待网络请求），并且释义返回为非结构化富文本，难以稳定渲染“基本义 / 语境义”等固定信息层级，也不利于后续扩展字段（词性/音标/例句等）。

## What Changes
- 将查词请求改为 **SSE 流式响应**（OpenAI-compatible `/chat/completions` + `stream=true`），查词面板逐步渲染结果。
- 统一 AI 返回为 **JSON**（必含 `word`、`basic_meaning`、`contextual_meaning`），并在返回不合法时进行“修复/重试”以保证结构化输出。
- 重构查词面板内容组织：以结构化区块展示词汇、最多 3 条基本义、以及与“当前句/邻句”绑定的语境义；可选字段（如 `pos` 等）作为可配置开关。
- 查词流程改为 **不阻塞 UI**，并支持 **取消/中断上一次查词**（例如用户连续点击多个词时）。

## Impact
- Affected specs:
  - `reader-ui`
- Affected code (expected):
  - `gui/reader_window.py`（查词调度、取消、面板渲染）
  - `gui/ui_reader_window.py`（面板布局/组件，为结构化展示做准备）
  - `utils/openai_client.py`、`utils/custom_ai_client.py`、`utils/ai_client.py`（增加流式能力与结构化 JSON 返回）
  - `gui/settings_dialog.py` 或相关配置读取逻辑（可选字段开关的配置项）

## Non-Goals
- 不改变 EPUB 导入/章节导航/书签/图片搜索等功能行为。
- 不改变“添加到 Anki”的字段映射机制；仅确保在结构化结果下仍可按既有方式写入。
- 不引入新的第三方依赖（除非可 vendoring 且确有必要）。

