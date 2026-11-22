---
type: "Guide"
title: "ClipSignal — 面向外贸团队的融媒体获客技能套件"
description: "在 Codex 中为外贸团队制作展会内容、核验企业、交接线索。"
tags: ["ClipSignal"]
---

# ClipSignal — 面向外贸团队的融媒体获客技能套件


**从展会内容，到可核验的海外买家。** ClipSignal 将参考拆解、实拍剪映制作、海外企业核验和渠道触达组织在同一个任务里，分别交付素材与可复查的线索。

[一句话装载](INSTALL.md) · [双页产品站](docs/pages.md) · [工作流](docs/workflow.md) · [技术图册](docs/diagrams.md) · [English](docs/readme-en.md)

<!-- hero:start -->
![用摄像机记录展会、展台洽谈和青色信息轨迹](assets/showcase/scene-01.webp)

*ClipSignal 产品场景插画，经本地 New API 生成。*
<!-- hero:end -->

## 在 Codex 发一句话

> 请从 https://github.com/yuxuan6426/clipsignal 安装并装载 ClipSignal，按仓库的 INSTALL.md 运行环境自检和合成候选验收，告诉我当前可用的模块和配置缺项。

Windows 上的 Codex 会话可直接读取装载入口。首次运行用自己的剪映安装、浏览器权限和业务服务凭据。[安装与配置](INSTALL.md) · [合成样例](examples/index.md)

## 两条链路，面向两类交接

```mermaid
flowchart LR
    Task["展会任务 · Codex"] --> Media["参考拆解与实拍"]
    Task --> Market["海外与视频号线索"]
    Media --> Draft["可编辑剪映草稿"]
    Market --> Verify["企业与来源核验"]
    Verify --> Sales["候选表与交接卡"]
```

| 工作阶段 | 内容人员 | 获客与销售 |
| --- | --- | --- |
| 展前 | 参考拆解、录制说明、素材采集 | 买家画像、企业角色与品类筛选 |
| 展中 | 草稿、字幕、预览，按账号验证发布 | 复核公开商务联系方式，准备展位或工厂邀约 |
| 展后 | 整理作品与素材来源 | 分别记录回复、接通、预约和销售接手 |

### 内容制作

参考作品解析为时码和镜头说明。用授权原片编排时间轴、字幕及旁白；独立草稿经原生读回后再做首页登记与成片验收。[剪辑 Skill](.agents/skills/clipsignal-edit/SKILL.md)

### 海外企业核验

博查用于发现入口。Chrome 读取可见帖子、评论和企业主页，官网或官方名录用于核对企业角色和品类。候选表保留原始来源、观察时间和待核项。[候选输入](examples/leads.json) · [分流 Skill](.agents/skills/clipsignal-leads/SKILL.md)

### 微信视频号与渠道触达

本地工作台、SQLite 和 MCP 承接可见作品与评论。Gmail 邮件、云蝠电话和内容发布各自核对授权与回执，状态不明先核查服务端。[视频号模块](modules/wechat/README.md) · [触达 Skill](.agents/skills/clipsignal-outreach/SKILL.md)

<!-- showcase:start -->
## 展会场景图册

<details open>
<summary>从展前准备到展后接手 · AI 场景插画</summary>

| | |
| --- | --- |
| ![展前选题用的分镜卡和产品样件](assets/showcase/scene-02.webp) | ![展会现场的授权拍摄场景](assets/showcase/scene-03.webp) |
| ![媒体原片与时码整理](assets/showcase/scene-04.webp) | ![剪辑素材按时间分层的概念图](assets/showcase/scene-05.webp) |
| ![展会企业线索与来源核验](assets/showcase/scene-06.webp) | ![视频号作品和评论关系示意](assets/showcase/scene-07.webp) |
| ![给海外采购商准备展会邀约](assets/showcase/scene-08.webp) | ![销售按证据交接候选](assets/showcase/scene-09.webp) |
| ![展后回访记录与阶段归档](assets/showcase/scene-10.webp) |  |

</details>
<!-- showcase:end -->

## 系统与链路图册

| 技术关系 | 查看图解 |
| --- | --- |
| 总控、流程与素材 | [总体架构](docs/diagrams.md#系统架构) · [展会全景](docs/diagrams.md#展会全景) · [拍摄素材](docs/diagrams.md#拍摄素材结构) · [剪映链](docs/diagrams.md#剪映制作链) |
| 场景、证据与回执 | [海外核验](docs/diagrams.md#海外企业核验链) · [视频号 MCP](docs/diagrams.md#视频号-mcp-链) · [候选证据](docs/diagrams.md#候选证据结构) · [触达回执](docs/diagrams.md#发布与触达回执) |
| 装载与维护 | [首次装载](docs/diagrams.md#首次装载与依赖) · [故障恢复和记忆](docs/diagrams.md#修复与项目记忆) |

<details>
<summary>展开 · 故障恢复与项目记忆</summary>

```mermaid
flowchart LR
    A["任务阶段失败"] --> B["查现有回执"]
    B --> C["修复与复验"]
    C --> D["从检查点续跑"]
    D --> E["收录已验证经验"]
```

</details>

<!-- tech:start -->
<details open>
<summary>技术图示 · 节点与箭头已逐图核对</summary>

| | |
| --- | --- |
| ![系统架构](assets/showcase/diagram-system.webp) | ![展会全景](assets/showcase/diagram-event.webp) |
| ![拍摄素材结构](assets/showcase/diagram-media.webp) | ![剪映制作链](assets/showcase/diagram-edit.webp) |
| ![海外企业核验链](assets/showcase/diagram-leads.webp) | ![视频号 MCP 链](assets/showcase/diagram-wechat.webp) |
| ![候选证据结构](assets/showcase/diagram-evidence.webp) | ![发布与触达回执](assets/showcase/diagram-outreach.webp) |
| ![首次装载与依赖](assets/showcase/diagram-setup.webp) | ![修复与项目记忆](assets/showcase/diagram-repair.webp) |

</details>
<!-- tech:end -->

## 实测与复跑

合成候选分流、剪映草稿原生读回、视频号作品与评论的本地 MCP 调用、同机换路径复跑均有独立验收办法。剪映首页登记、正式成片发布、邮件送达、外呼接通和到访单独核对。[验收步骤](docs/test.md) · [Agent Research](docs/research.md) · [分发清单](delivery.json)

[依赖](docs/deps.md) · [Apache-2.0](LICENSE) · [Agent 检索入口](llms.txt)