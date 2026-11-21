---
type: "Guide"
title: "依赖与许可"
description: "分发、重建、宿主及配置依赖。"
tags: ["ClipSignal"]
---

# 依赖与许可

| 依赖 | 处理方式 | 来源与验收 |
| --- | --- | --- |
| ClipSignal 与视频号工作台 | 随包 | 自研源码 Apache-2.0，视频号 Python 3.13 与固定依赖见[模块](../modules/wechat/README.md)。 |
| No Negative Echo | 随包 | 2.1.1，原 MIT [许可证](../.agents/skills/no-negative-echo/LICENSE)与交付清单随附。 |
| Windows、Git Bash、PowerShell、Node.js、Miniconda、Dev-C++／MinGW、剪映专业版 | 宿主 | Windows x64，`setup.ps1 -Check` 探测对应命令及剪映适配。系统应用从[Git for Windows](https://git-scm.com/install/windows)、[PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows)、[Miniconda](https://docs.anaconda.com/miniconda/)、[Node.js](https://nodejs.org/)及各应用官方渠道获取。 |
| douyin-agent、jianying-draft-collab | 重建 | 使用接收方已有的官方项目发行目录和其交付清单及锁文件；加载其 Skill，执行其只读自检与剪映原生探测。 |
| music-production | 重建 | 使用剪映工作流所固定的版本和音源，验渲染及混音。各上游保留原有许可。 |
| Agent Plan、博查、云蝠、Chrome、Gmail | 配置 | 接收端账号、额度与权限。Bocha Web Search 使用 `https://api.bocha.cn/v1/web-search` 和 `BOCHA_API_KEY`。业务完成需要实际服务回执。 |
| 参考视频、授权实拍、买家画像 | 输入 | 由任务提供或通过接收端获准入口取得。
