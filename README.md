# Anki Reader

一个帮助你在阅读时学习英语的Anki插件。

## 功能特点

- 支持文本选择和翻译
- 自动生成单词释义和例句
- 一键添加到Anki卡片
- 支持OpenAI和自定义API服务

## 安装说明

1. 确保你的Anki版本在2.1.50以上
2. 下载插件文件
3. 将插件文件夹放入Anki的插件目录：
   - Windows: `%APPDATA%\Anki2\addons21\`
   - Mac: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`
4. 安装依赖（两种方法）：

   方法一：使用Anki的Python环境安装
   ```bash
   cd {插件目录}/anki_reader
   "C:\Program Files\Anki\python\python.exe" -m pip install aiohttp yarl multidict attrs charset-normalizer async-timeout frozenlist aiosignal idna --target=vendor
   ```

   方法二：使用系统Python环境安装
   ```bash
   cd {插件目录}/anki_reader
   python -m pip install -r requirements.txt --target=vendor
   ```

5. 重启Anki

## 配置说明

1. 在Anki菜单中选择"工具" -> "Anki Reader"
2. 点击"设置"按钮
3. 选择AI服务类型：
   - OpenAI：需要填写API Key和可选的API地址
   - 自定义API：需要填写API地址和相关端点

## 使用方法

1. 在Anki菜单中选择"工具" -> "Anki Reader"
2. 在打开的窗口中粘贴或输入英文文本
3. 选择单词或段落：
   - 单词：自动获取释义和例句
   - 段落：自动翻译
4. 点击"添加到Anki"将内容添加到卡片中

## 常见问题

1. 如果遇到依赖安装问题：
   - 确保使用了正确的Python版本（与Anki使用的版本相同）
   - 尝试使用Anki自带的Python环境安装
   - 检查vendor目录是否存在并包含所有依赖包

2. 如果遇到API连接问题：
   - 检查网络连接
   - 确认API Key是否正确
   - 确认API地址是否可访问

## 支持与反馈

如果你遇到任何问题或有建议，请在GitHub上提交issue。 