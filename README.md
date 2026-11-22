---
type: "Guide"
title: "ClipSignal — 面向外贸团队的融媒体获客技能套件"
description: "在 Codex 中为外贸团队制作展会内容、核验企业、交接线索。"
tags: ["ClipSignal"]
---

# ClipSignal — 面向外贸团队的融媒体获客技能套件

**ClipSignal 为外贸团队提供全自动剪辑和自主获客工作流。** 用工作区授权素材制作可编辑的剪映草稿，从公开社媒发现并核验买家，交给销售跟进。 首发场景是冠英商用车汽配展，销售可据此安排展位会面和湖州访厂。

[产品站（GitHub Pages）](https://yuxuan6426.github.io/clipsignal/) · [B1X 赛事页](https://b1x.work/events/competitions/cmp_d76ad4530fe1447d8707d3247ce5c7ad) · [安装指引](INSTALL.md) · [English](docs/readme-en.md)

[54 秒展台循环](https://yuxuan6426.github.io/clipsignal/demo/) · [4 分钟现场路演](https://yuxuan6426.github.io/clipsignal/demo/?mode=pitch)

## 在 Codex 发一句话

在 Windows 打开 Codex，将下面这句话粘贴到会话。

> 请从 https://github.com/yuxuan6426/clipsignal 安装并装载 ClipSignal，按仓库的 INSTALL.md 运行环境自检和合成候选验收，告诉我当前可用的模块和配置缺项。

Codex 会加载套件、预检环境并运行合成候选验收，告诉你哪些模块可用、还缺什么配置。[首次配置](docs/setup.md) · [合成样例](examples/index.md)

## 团队能接手什么

| 交付或结果 | 怎么用 |
| --- | --- |
| **全自动剪辑** | 参考可由用户提供或由 Agent 查找。用工作区已有素材制作可编辑草稿、字幕和预览。缺镜头时，按授权通过 Gmail 发送补拍清单，收到新素材后继续剪辑。 |
| **自主获客** | 用博查、Chrome 和视频号 MCP，从作品、评论与主页查找可能的买家。回查企业官网，分别核对品类、角色、进口能力和采购需求。交付候选表、Markdown 报告和 JSON，保留来源、观察时间与待核项。 |
| **邀约与销售交接** | 在获准场景中验证站内私信与商务联系方式确认。后续用 Gmail 邮件或云蝠智能外呼安排邀约，向销售交接回复、预约与到访记录。 |

自研的**微信视频号工作台与 MCP**随套件按 Apache-2.0 发布。Codex 可读取作品、可见评论和已关联账号，再接入同一套企业核验字段。[工作台源码与配置](modules/wechat/README.md)

<!-- hero:start -->
![企业工程师在自家工厂面对摄像机讲解制动件](assets/showcase/scene-01.webp)

*AI 生成的产品场景示意。*
<!-- hero:end -->

## 两条链路，面向两类交接

两条链共用企业资料、买家画像和展会目标。可单独运行，也可在同一个任务里并行。

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 22, "rankSpacing": 32, "padding": 10, "subGraphTitleMargin": {"top": 7, "bottom": 12}}}}%%
flowchart TD
    accTitle: ClipSignal 展会内容制作与买家核验
    accDescr: Codex 可运行全自动剪辑、自主获客或两者并行。剪辑复用工作区素材并按需请求补拍。获客从作品、评论到候选核验与授权跟进。

    Task["展会任务 · Codex<br/>企业资料、活动目标与目标买家"] --> Preflight{"环境预检通过？"}
    Preflight -->|已就绪| Route["选择内容链、获客链或并行"]
    Preflight -->|缺项或故障| Repair["补装依赖或定位报错<br/>核对回执，从检查点复检"]
    Repair -->|复检通过| Route

    subgraph Media["全自动剪辑"]
        direction TB
        Reference["指定或搜索参考视频<br/>拆解开场、镜头与节奏"] --> Footage{"已有授权素材齐全？"}
        Footage -->|缺镜头| ShotList["生成补拍清单<br/>按授权发邮件"]
        ShotList -->|素材回传| Analyze["Agent Plan 理解原片<br/>转写、画面与时码"]
        Footage -->|齐全| Analyze
        Analyze --> Timeline["编排剪映时间轴<br/>字幕与豆包旁白<br/>本地配乐与过渡页"]
        Timeline --> Draft["交付可编辑剪映草稿<br/>验原生读回与首页可见性"]
        Draft --> Publish["可选 · 导出与获准发布<br/>留存成片、来源和发布回执"]
    end

    subgraph Leads["自主获客"]
        direction TB
        Profile["定义买家画像<br/>地区、品类、角色、关键词"] --> Find["按渠道发现候选<br/>海外 · 博查与 Chrome<br/>视频号 · 工作台与 MCP"]
        Find --> Read["读内容、评论和账号主页<br/>记录来源与观察时间"]
        Read --> Evidence["回查官网或官方名录<br/>核对角色、品类与进口证据"]
        Evidence --> Pack["去重与分级<br/>候选表与销售交接卡<br/>来源、时间与待核项"]
        Pack --> Approval{"触达已获授权？"}
        Approval -->|已获准| Contact["私信并确认商务联系方式<br/>自动链路待验证"]
        Contact --> Invite["Gmail 邮件或云蝠电话<br/>邀约到展位或工厂"]
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

22 秒双语剪映草稿已原生读回并人工确认首页可见。X 与 Facebook 的公开记录经官网核验后合为一个渠道候选，销售交接使用合成询盘验收。已验证视频号 MCP 读取、Gmail 测试邮件发送及通过 MCP 读取云蝠测试知识库。自动私信与联系方式确认、正式发布、邮件送达、实际外呼及到访在展会场景分别验证。

[查看七项能力的实证与待验](docs/test.md#七项能力的实证与待验)

## 服务来源与发布

电话销售与外呼由云蝠智能 VoiceAgent 提供。Windows Codex MCP 接入由 **yuxuan6426** 构建并提供接入支持。[云蝠智能官网](https://www.ccgpt.net/) · [yunfu-mcp-windows 仓库](https://github.com/yuxuan6426/yunfu-mcp-windows)

[Pages 部署指引](docs/pages.md) · [依赖与许可](docs/deps.md) · [Apache-2.0](LICENSE) · [Agent 检索入口](llms.txt)
