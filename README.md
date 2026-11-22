---
type: "Guide"
title: "ClipSignal — 面向外贸团队的融媒体获客技能套件"
description: "在 Codex 中为外贸团队制作展会内容、核验企业、交接线索。"
tags: ["ClipSignal"]
---

# ClipSignal — 面向外贸团队的融媒体获客技能套件

**ClipSignal 帮外贸团队把工厂或展台实拍做成可编辑的剪映草稿，也能从公开社媒发现并核验买家，交给销售跟进。** 首发场景是冠英商用车汽配展，销售可据此安排展位会面和湖州访厂。

[产品站（GitHub Pages）](https://yuxuan6426.github.io/clipsignal/) · [B1X 赛事页](https://b1x.work/events/competitions/cmp_d76ad4530fe1447d8707d3247ce5c7ad) · [安装指引](INSTALL.md) · [English](docs/readme-en.md)

## 在 Codex 发一句话

在 Windows 打开 Codex，将下面这句话粘贴到会话。

> 请从 https://github.com/yuxuan6426/clipsignal 安装并装载 ClipSignal，按仓库的 INSTALL.md 运行环境自检和合成候选验收，告诉我当前可用的模块和配置缺项。

Codex 会加载套件、预检环境并运行合成候选验收，告诉你哪些模块可用、还缺什么配置。[首次配置](docs/setup.md) · [合成样例](examples/index.md)

## 团队能接手什么

| 交付或结果 | 怎么用 |
| --- | --- |
| **录制说明与剪映草稿** | 用对标作品的镜头与时码生成 Markdown 录制说明，指导团队在工厂或展台实拍。交付可编辑的剪映草稿、字幕、预览与素材来源。 |
| **有证据的海外买家候选** | 用博查和 Chrome 发现线索并回查官网。把品类匹配、企业角色、进口能力和采购需求分别记证据。候选表、Markdown 报告和 JSON 保留来源、时间及待核项。 |
| **邀约与销售交接** | 对获准跟进的对象发送 Gmail 邮件或使用云蝠智能外呼。将发送、接通、回复、预约及到访分别入账，销售据此确认下一步。 |

自研的**微信视频号工作台与 MCP**随套件按 Apache-2.0 发布。Codex 可读取作品、可见评论和已关联账号，再接入同一套企业核验字段。[工作台源码与配置](modules/wechat/README.md)

<!-- hero:start -->
![企业工程师在自家工厂面对摄像机讲解制动件](assets/showcase/scene-01.webp)

*ClipSignal 产品场景插画，经本地 New API 生成。*
<!-- hero:end -->

## 两条链路，面向两类交接

两条链共用企业资料、买家画像和展会目标。可单独运行，也可在同一个任务里并行。

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 22, "rankSpacing": 32, "padding": 10, "subGraphTitleMargin": {"top": 7, "bottom": 12}}}}%%
flowchart TD
    accTitle: ClipSignal 展会内容制作与买家核验
    accDescr: Codex 预检后选择内容制作、买家核验或两者并行。内容链交付录制说明和剪映草稿，获客链交付有来源的候选表与销售交接卡。授权后的发布和邀约另核回执。

    Task["展会任务 · Codex<br/>企业资料、活动目标与目标买家"] --> Preflight{"环境预检通过？"}
    Preflight -->|已就绪| Route["选择内容链、获客链或并行"]
    Preflight -->|缺项或故障| Repair["补装依赖或定位报错<br/>核对回执，从检查点复检"]
    Repair -->|复检通过| Route

    subgraph Media["内容制作"]
        direction TB
        Reference["可选 · 拆解参考作品<br/>开头、证明镜头、节奏、时码"] --> ShotList["录制说明<br/>镜头清单、话术与补拍<br/>Markdown 或邮件"]
        ShotList --> Shoot["自家工厂或展台录制<br/>收集企业授权原片"]
        Shoot --> Analyze["Agent Plan 理解原片<br/>转写、画面与时码"]
        Analyze --> Timeline["编排剪映时间轴<br/>字幕与豆包旁白<br/>本地配乐与过渡页"]
        Timeline --> Draft["交付可编辑剪映草稿<br/>验原生读回与首页可见性"]
        Draft --> Publish["可选 · 导出与获准发布<br/>留存成片、来源和发布回执"]
    end

    subgraph Leads["买家核验与交接"]
        direction TB
        Profile["定义买家画像<br/>地区、品类、角色、关键词"] --> Find["按渠道发现候选<br/>海外 · 博查与 Chrome<br/>视频号 · 工作台与 MCP"]
        Find --> Read["读内容、评论和账号主页<br/>记录来源与观察时间"]
        Read --> Evidence["回查官网或官方名录<br/>核对角色、品类与进口证据"]
        Evidence --> Pack["去重与分级<br/>候选表与销售交接卡<br/>来源、时间与待核项"]
        Pack --> Approval{"触达已获授权？"}
        Approval -->|已获准| Invite["Gmail 邮件或云蝠电话<br/>邀约到展位或工厂"]
        Invite --> Receipt["核对送达、接通<br/>回复与预约"]
        Receipt --> Handoff["销售接手及展后跟进"]
        Approval -->|待授权或补证| Handoff
    end

    Route --> Reference
    Route --> Profile
    Publish --> Close["归档交付物与已核回执<br/>沉淀已验证做法，买家问题回到选题"]
    Handoff --> Close

    classDef default fill:#fff,stroke:#9babc2,color:#122445
    style Media fill:#f8faff,stroke:#c5d3e9
    style Leads fill:#f8faff,stroke:#c5d3e9
    classDef deliver fill:#eff4ff,stroke:#2457d6,color:#122445
    classDef check fill:#fff,stroke:#2457d6,color:#122445
    class ShotList,Draft,Pack,Handoff,Close deliver
    class Preflight,Approval check
```

[完整工作流](docs/workflow.md) · [技术图解](docs/diagrams.md) · [自修复与项目记忆](docs/workflow.md#首次配置修复与复用)

## 冠英首发验证

22 秒双语剪映草稿已原生读回并人工确认首页可见。X 与 Facebook 的公开记录经官网核验后合为一个渠道候选，销售交接使用合成询盘验收。视频号 MCP 读取、Gmail 自验发送和云蝠知识库读回分别有记录。成片发布、邮件收件、实际外呼及到访以现场回执验收。

[查看七项能力的实证与待验](docs/test.md#七项能力的实证与待验)

## 服务来源与发布

电话销售与外呼由云蝠智能 VoiceAgent 提供。Windows Codex MCP 接入由 **yuxuan6426** 构建并提供接入支持。[云蝠智能官网](https://www.ccgpt.net/) · [yunfu-mcp-windows 仓库](https://github.com/yuxuan6426/yunfu-mcp-windows)

[Pages 部署指引](docs/pages.md) · [依赖与许可](docs/deps.md) · [Apache-2.0](LICENSE) · [Agent 检索入口](llms.txt)
