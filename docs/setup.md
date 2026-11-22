---
type: "Guide"
title: "首次配置"
description: "在接收方 Windows 设备配置 ClipSignal。"
tags: ["ClipSignal"]
sources: [{"id":"yunfu-voiceagent","title":"云蝠智能 VoiceAgent 产品页","resource":"https://www.ccgpt.net/aicc/"},{"id":"yunfu-windows","title":"yuxuan6426 的 Windows Codex MCP 接入仓库","resource":"https://github.com/yuxuan6426/yunfu-mcp-windows"}]
---

# 首次配置

使用 Git for Windows、PowerShell 7、Miniconda 和具备 `node:util.parseEnv` 的 Node.js。运行 `powershell -NoProfile -File setup.ps1 -Check -Flow core`，再选 `media|edit|leads|wechat|publish|outreach`。`-Apply -Flow wechat` 使用 Conda 创建项目 Python 3.13 环境，便于独立运行视频号。`-Conda`、`-Python`、`-JianyingRoot`、`-Gcc` 可指向现有安装。工作区内的配置和回执写入 `.local/`。

剪辑按[依赖说明](deps.md)装好 Agent Plan 和剪映运行时。剪映专业版由接收端安装，Dev-C++ 配套 x64 MinGW GCC。媒体理解用 `CLIPSIGNAL_MEDIA_ROOT` 指定已安装的 Skill 目录。FFmpeg、FFprobe、FluidSynth、音源和 core／music 环境由剪映上游安装入口管理。

在当前 Codex 安装、连接 Chrome 和 Gmail。用小型文件验 Chrome 的读取和下载，用自己的服务账户验 Agent Plan、博查和云蝠。可复制 [.env.example](../.env.example) 为 `.local/config/services.env`。云蝠 helper 的同名进程变量优先；博查与 Agent Plan 在各自的运行环境设置相应变量。密钥存在、网页已连接和实际业务成功分别留回执。

可选 CLI 状态栏运行 `node tools/mcp-config.mjs --statusline --python <absolute-python>`，将输出合并进工作区的 `.codex/config.toml`。新 TUI 会话通过 `/statusline` 选择 ClipSignal。视频号见[模块说明](../modules/wechat/README.md)。

## 云蝠智能外呼接入

云蝠智能 VoiceAgent 提供语音智能体和电话外呼。[^yunfu-voiceagent] Windows 上的 Codex MCP 接入由 yuxuan6426 构建并提供接入支持，公开仓库收录 [Codex 接入指引](https://github.com/yuxuan6426/yunfu-mcp-windows/blob/main/codex-windows.md)与[握手和工具发现验收](https://github.com/yuxuan6426/yunfu-mcp-windows/blob/main/verification.md)。[^yunfu-windows]

在 ClipSignal 工作区运行 `node tools/mcp-config.mjs --cloudbat` 可生成项目内的 MCP 配置。按所用账号核对工具可见性与知识库读回。正式外呼按既有业务授权、已配置语音智能体和线路另行验收。

[^yunfu-voiceagent]: [云蝠智能官网](https://www.ccgpt.net/) · [VoiceAgent 产品页](https://www.ccgpt.net/aicc/)
[^yunfu-windows]: [yunfu-mcp-windows 接入仓库](https://github.com/yuxuan6426/yunfu-mcp-windows)
