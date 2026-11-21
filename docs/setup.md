---
type: "Guide"
title: "首次配置"
description: "在接收方 Windows 设备配置 ClipSignal。"
tags: ["ClipSignal"]
---

# 首次配置

使用 Git for Windows、PowerShell 7、Miniconda 和具备 `node:util.parseEnv` 的 Node.js。运行 `powershell -NoProfile -File setup.ps1 -Check -Flow core`，再选 `media|edit|leads|wechat|publish|outreach`。`-Apply -Flow wechat` 使用 Conda 创建项目 Python 3.13 环境，便于独立运行视频号。`-Conda`、`-Python`、`-JianyingRoot`、`-Gcc` 可指向现有安装。工作区内的配置和回执写入 `.local/`。

剪辑按[依赖说明](deps.md)装好 Agent Plan 和剪映运行时。剪映专业版由接收端安装，Dev-C++ 配套 x64 MinGW GCC。媒体理解用 `CLIPSIGNAL_MEDIA_ROOT` 指定已安装的 Skill 目录。FFmpeg、FFprobe、FluidSynth、音源和 core／music 环境由剪映上游安装入口管理。

在当前 Codex 安装、连接 Chrome 和 Gmail。用小型文件验 Chrome 的读取和下载，用自己的服务账户验 Agent Plan、博查和云蝠。可复制 [.env.example](../.env.example) 为 `.local/config/services.env`。云蝠 helper 的同名进程变量优先；博查与 Agent Plan 在各自的运行环境设置相应变量。密钥存在、网页已连接和实际业务成功分别留回执。

可选 CLI 状态栏运行 `node tools/mcp-config.mjs --statusline --python <absolute-python>`，将输出合并进工作区的 `.codex/config.toml`。新 TUI 会话通过 `/statusline` 选择 ClipSignal。云蝠用 `node tools/mcp-config.mjs --cloudbat` 生成同工作区的 MCP 配置，视频号见[模块说明](../modules/wechat/README.md)。
