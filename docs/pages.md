---
type: "Guide"
title: "产品站与发布"
description: "双页静态站、素材来源和 Pages 上线。"
tags: ["ClipSignal"]
sources: [{"id":"kooying","title":"浙江冠英官网与展会邀请","resource":"https://cn.kooying.com/"},{"id":"github-pages","title":"GitHub Pages 项目站地址","resource":"https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages"}]
generated: {"by":"agent:codex","at":"2026-11-22T10:41:21+08:00"}
---

# 产品站与发布

首页面向浙江冠英团队，从工厂或展台实拍讲到买家核验、展位见面和湖州访厂。工作流页说明交付、授权、回执及销售补问，通用能力与验收见[工作流](workflow.md)和[验收](test.md)。展位与日期源自冠英官网。[^kooying]

产品站使用 GitHub Pages 项目站地址，工作流位于同一站点的 `guide/`。[^github-pages] [产品首页](https://yuxuan6426.github.io/clipsignal/) · [工作流](https://yuxuan6426.github.io/clipsignal/guide/)

- 用 `node tools/build-pages.mjs .local/pages-preview` 构建到一个新目录。以该目录作为站点根，首页与 `guide/` 使用可移植的相对路径。
- 站点获准上线且仓库已经公开后，由拥有 Pages 管理权限的 Windows 用户运行 `powershell.exe -NoProfile -File tools/publish-pages.ps1`。脚本核对仓库可见性，选择 GitHub Actions 来源并启动部署。已有本机 GitHub CLI 包装器时可用 `-Gh` 指定。
- 部署工作流由手动触发，在公开仓库的 `main` 上检查可见性并构建。首次上线由脚本完成 Pages 配置。上线后查看 GitHub Actions 和匿名访问结果，核对首页、`guide/` 与图片加载。
- 技术图保留[可维护源](diagrams.md)。场景图为 AI 生成示意，站点按审核过的图片清单和 SHA-256 构建。
[^kooying]: [浙江冠英官网首页](https://cn.kooying.com/)

[^github-pages]: [GitHub Pages 项目站默认地址](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
