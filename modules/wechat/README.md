---
type: "Guide"
title: "微信视频号工作台"
description: "本机 SQLite、Web 工作台及 Codex MCP。"
tags: ["ClipSignal"]
---

# 微信视频号工作台

在项目根运行 `.\setup.ps1 -Apply -Flow wechat`，或在独立 Python 3.13 Conda 环境进入本目录运行 `bash project.sh setup`。将 `CHANNELS_DATA_DIR` 指向接收端私有目录，例如项目 `.local/wechat` 的绝对路径。再运行 `bash project.sh start --no-browser` 和 `bash project.sh mcp-config`。使用项目受管环境时，可将 `CHANNELS_CONDA_EXE` 指向 Conda，或在同一 Python 下直接运行 `python -m channels.server --no-browser` 与 `python -m channels.mcp_server --codex-config`。

公开分享预览和授权导入可入库。微信桌面 UIA 路径读取用户打开的独立视频号窗口。SocialDataX 是可选补充入口，配置键留在接收端，启用前核对额度和权限。MCP 可读取候选作品、评论及已关联账号和作品。关联状态和评论覆盖须按实际记录。

测试按项目固定 Playwright 运行时执行。扫码、微信评论、浏览器和授权业务线索分别验收。
