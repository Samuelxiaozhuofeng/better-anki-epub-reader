## Why
 / no images found”。根因是 Bing 图片搜索页面对爬虫/脚本请求不稳定（限流、当前“必应图片”功能经常出现“图片加载失败反爬、验证码、返回不同页面结构），导致图片 URL 提取失败，从而影响阅读体验。

## What Changes
- 使用稳定的公开数据源作为默认图片来源：优先从 Wikimedia Commons / Wikipedia（MediaWiki API）获取缩略图/图片链接。
- 维持现有逻辑作为补充：若 Wikimedia 结果不足，再尝试 Bing 解析作为补充来源（可选）。
- 失败时的可用退路：若仍无法获取图片，图片区域提供“在浏览器中搜索图片”的链接，避免死路。

## Non-Goals
- 配置付费/需要 Key 的第三方图片 API（如 Bing 官方 API、SerpAPI）
- 图片版权/来源标注体系（本次仅保证“有图可看”和稳定性）

## Impact
- 图片搜索的可用性显著提升，减少“no images found”。
- 网络请求从 HTML 解析转为 JSON API 为主，结构更稳定。
