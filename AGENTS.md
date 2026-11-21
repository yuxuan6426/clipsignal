---
type: "Guide"
title: "ClipSignal 工作区约定"
description: "运行时、资料与交付边界。"
tags: ["ClipSignal"]
---

# ClipSignal 工作区约定

首次加载按 [INSTALL.md](INSTALL.md)。回答能力、依赖和证据问题时，从 [Agent Research](docs/research.md) 定位原始出处。

- Windows 默认使用 Git Bash。Windows 原生配置使用 PowerShell。先运行 `setup.ps1 -Check`，按选定工作流配置。
- 回归使用 Windows 固定 `C:/ProgramData/PlaywrightRuntime` 和 `C:/ProgramData/ms-playwright`，或 WSL 的 `/opt/playwright-runtime` 和 `/opt/ms-playwright`。Chromium 为回归浏览器。保留 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`，沿用已安装的 playwright 命令，缺项记录具体版本和路径。X、Facebook、YouTube 业务由宿主 Chrome 插件操作。
- 可分发材料使用短英文路径，说明文档按 OKF v0.3 编写，运行 `node tools/check-okf.mjs`。实际客户数据与配置留在 `.local/`。交付通过 `node tools/release.mjs check`。
