---
type: "Guide"
title: "Install ClipSignal in Codex"
description: "一句话装载、可重跑安装与验收入口。"
tags: ["ClipSignal"]
sources: [{"id":"codex","title":"OpenAI CLI installation and Codex skill locations","resource":"https://developers.openai.com/api/reference/cli"}]
---

# Install ClipSignal in Codex


## 给 Codex 的一句话

> 请从 https://github.com/yuxuan6426/clipsignal 安装并装载 ClipSignal，按仓库的 INSTALL.md 运行环境自检和合成候选验收，告诉我当前可用的模块和配置缺项。

## Codex 执行顺序

1. 检查当前工作区是否已包含来源明确的 ClipSignal。若仓库访问受限，使用现有 GitHub 登录并核对读取权限。需要新克隆时用现有认证的 `gh repo clone yuxuan6426/clipsignal <目标目录>` 或 `git clone https://github.com/yuxuan6426/clipsignal.git <目标目录>`。未指定目录时用 Windows 用户目录下的 `clipsignal`，已有交付目录就复用。
2. 在实际 checkout 根运行 `powershell.exe -NoProfile -File install.ps1 -Flow core`。它校验发布清单和项目入口，调用只读环境检查，并将本地回执写到 `.local/config/install.json`。选定业务后可用 `-Flow media|edit|leads|wechat|publish|outreach` 复查对应依赖。
3. **在本次会话直接读取安装回执的 `entry`，并按其中的 ClipSignal 总控执行。** 每次工具调用以回执中的 `workspace` 为工作目录。此步骤适用于技能发现列表还未刷新的会话。下次打开该工作区可使用 `$clipsignal`。[^codex]
4. Node.js 可用时运行 `node tools/leads.mjs examples/leads.json`。验收应得到一家合成经销商，两条平台证据，状态为「待核」。报告入口路径、检查结果、合成验收和还需配置的组件。此次安装只使用合成输入。

## 可选的用户级入口

希望在其他 Codex 项目中也能使用时，运行 `powershell.exe -NoProfile -File install.ps1 -UserSkill`。它在用户的 `.agents/skills/clipsignal` 写入轻量入口，完整套件、依赖和私有状态仍位于 checkout。已存在同一入口时可直接复跑，已有不同入口时使用项目入口。下个 Codex 会话按用户级 Skill 发现规则加载，移动 checkout 后需更新该入口。[^codex]

Chrome、Gmail、Agent Plan、云蝠、博查和剪映分别按[首次配置](docs/setup.md)接入。只有该服务的真实验收通过后才标记可运行。

[^codex]: [OpenAI Codex Skill 安装路径与新会话](<https://developers.openai.com/api/reference/cli>)
