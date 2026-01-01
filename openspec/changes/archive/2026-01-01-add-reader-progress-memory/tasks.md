## 1. Implementation
- [x] 1.1 在 `ReaderWindow` 中增加滚动保存进度的防抖定时器，并在滚动停止后静默调用 `save_current_position()`
- [x] 1.2 在 `ReaderWindow.closeEvent()` 中确保退出前保存当前进度
- [x] 1.3 调整 `ReaderWindow.open_epub()`：若该文件已导入，则直接打开数据库中的书籍与章节并恢复进度（不重新导入、不重置进度）
- [ ] 1.4 校验“从书籍管理器打开书籍”和“从文件打开书籍”两条路径都能恢复章节 + 章节内位置
- [x] 1.5 打开阅读器窗口时自动弹出“书籍管理”对话框

## 2. Spec
- [x] 2.1 为 `reader-ui` 增加“阅读进度记忆与恢复”需求与场景
