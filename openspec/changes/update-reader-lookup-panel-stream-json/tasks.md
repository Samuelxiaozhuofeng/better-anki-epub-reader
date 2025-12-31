## 1. Implementation
- [ ] 1.1 盘点现有查词调用链（`WordClickableTextEdit` → `ReaderWindow.on_word_clicked` → AI client），确认阻塞点与 UI 更新点
- [ ] 1.2 为 AI client 增加流式接口（SSE），并定义“增量片段 + 最终 JSON”输出形态（包含取消能力）
- [ ] 1.3 定义并实现 JSON schema 校验与“修复/重试”策略（必含 `word/basic_meaning/contextual_meaning`，basic_meaning ≤ 3）
- [ ] 1.4 重构查词面板渲染：结构化区块（词汇/基本义列表/语境义），并支持 Loading/Streaming/Success/Error 状态切换
- [ ] 1.5 将查词执行移出 UI 线程（不冻结），并支持用户连续点击时取消/中断上一次查词
- [ ] 1.6 增加可选字段显示开关的配置项（默认关闭），并确保开关影响渲染/提示词（按需请求字段）
- [ ] 1.7 保持“添加到 Anki”流程可用：在结构化结果下生成用于写入的 `meaning/context` 字段内容（与现有字段映射兼容）

## 2. Validation
- [ ] 2.1 手动 QA（Anki 内）：连续快速点击不同词汇，确认 UI 不冻结且旧请求不会覆盖新结果
- [ ] 2.2 手动 QA：观察流式输出更新频率/可读性，确认最终结构化渲染正确（basic_meaning ≤ 3，contextual_meaning 与上下文匹配）
- [ ] 2.3 手动 QA：断网/后端报错/返回非 JSON 时，确认“修复/重试/错误展示”路径可用且不会卡死
- [ ] 2.4 手动 QA：取消行为（新点击触发取消旧请求或显式取消），确认面板状态与最终结果一致

