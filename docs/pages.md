---
type: "Guide"
title: "产品站与发布"
description: "双页静态站、素材来源和 Pages 上线。"
tags: ["ClipSignal"]
---

# 产品站与发布


- 用 `node tools/build-pages.mjs .local/pages-preview` 构建到一个新目录。以该目录作为站点根，首页与 `guide/` 使用可移植的相对路径。
- 仅在仓库公开后，由拥有 Pages 管理权限的 Windows 用户运行 `powershell.exe -NoProfile -File tools/publish-pages.ps1`。脚本核对仓库可见性，选择 GitHub Actions 来源并启动部署。已有本机 GitHub CLI 包装器时可用 `-Gh` 指定。
- 工作流收到仓库公开事件或手动触发时检查可见性。GitHub 第一次还没有启用 Pages 时，以上脚本完成首次设置。上线后查看 GitHub Actions 和实际匿名页面，核对首页、`guide/` 与图片加载。
- 技术图保留[可维护源](diagrams.md)。展示图只纳入通过逐图审阅的文件和相应 SHA-256。本版展示图由本地 New API 的 gpt-image-2.5 生成。生成请求、凭据和候选保存在本机忽略目录。