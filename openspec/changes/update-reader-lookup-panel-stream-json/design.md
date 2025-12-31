# Design: 查词流式响应 + JSON结构化 + 可取消的 UI 方案

## Overview
本变更将“查词”从 UI 线程同步等待网络请求，调整为后台执行并通过信号/回调逐步更新查词面板；同时将 AI 输出规范为 JSON，保证查词面板以固定层级渲染（词汇 / 基本义 / 语境义），并为可选字段扩展预留开关。

## Key Decisions
- **Streaming transport**: 使用 OpenAI-compatible `/chat/completions` 的 `stream=true`（SSE）获取增量内容。
- **UI responsiveness**: 所有网络与 JSON 修复/重试逻辑在后台执行，UI 线程仅做轻量渲染更新。
- **Cancellation**: 每次查词生成递增的 `lookup_request_id`；新请求发起时取消旧请求，并忽略旧请求的后续流式片段。
- **Structured output**: AI 最终产出为 JSON：
  - 必选字段：`word`、`basic_meaning`、`contextual_meaning`
  - 可选字段（第一期仅“可承载”，不强制全部实现）：如 `pos`、`ipa`、`examples` 等，是否展示由配置开关控制。
- **Repair policy**: 如果模型返回不合法 JSON 或缺字段，执行“修复/重试”以得到可解析 JSON（保证面板渲染稳定）。

## Data Contract (JSON)
### Required
- `word`: string（标准化后的词汇本体）
- `basic_meaning`: array[string]（最多 3 条，按常见度/与词汇核心义排序）
- `contextual_meaning`: string（必须结合“当前句/邻句”，明确对应本次上下文）

### Optional (gated by toggles)
- `pos`: string | array[string]
- `ipa`: string
- `examples`: array[{en: string, zh?: string}]
- `notes`: string

## UI Rendering Model
- 面板应具备明确状态：
  - Empty：提示“点击单词/选中文本查词”
  - Loading：显示“正在加载…”并允许取消
  - Streaming：逐步更新显示内容（至少能看到生成进度/增量文本）
  - Success：以区块显示 `word`、`basic_meaning`（列表）、`contextual_meaning`（段落）
  - Error：展示错误并允许重试
- 当用户连续点击时：
  - 立即更新 `word` 标题并进入 Loading/Streaming
  - 旧请求被取消或结果被忽略，不得覆盖新请求面板内容

## Implementation Notes (Non-code)
- 建议将“流式网络读取 + JSON 聚合/修复 + 取消”封装为独立服务层（例如 `utils/lookup_service.py`），UI 层只订阅进度事件与最终结果。
- SSE 解析需兼容 OpenAI 风格增量（`data: {...}`），并支持将增量内容累积为最终 JSON 字符串（或在流式阶段展示“当前累积文本”，最终再结构化渲染）。
- “修复/重试”应有上限与可观测错误信息，避免无限循环与静默失败。

## Risks / Trade-offs
- Streaming + JSON 的张力：流式阶段可能只能展示“未完成 JSON”文本。
  - 方案：流式阶段展示“生成中（结构化）”的累积文本或分区占位，最终解析成功后切换到结构化视图。
- 取消语义：不同后端对取消连接的支持不同。
  - 方案：优先关闭 session/response；若无法强制中止，则通过 `lookup_request_id` 忽略旧片段，保证 UI 正确。

