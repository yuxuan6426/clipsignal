---
type: "Guide"
title: "ClipSignal 技术图册"
description: "系统架构、展会和任务链路可维护图解。"
tags: ["ClipSignal"]
---

# ClipSignal 技术图册

## 系统架构

```mermaid
flowchart LR
  Codex --> Skills
  Skills --> Media["Media"]
  Skills --> Browser["Browser"]
  Skills --> MCP
  Media --> Outputs
  Browser --> Outputs
  MCP --> Outputs
```

## 展会全景

```mermaid
flowchart LR
  Plan --> Show --> Followup["Follow-up"]
```

## 拍摄素材结构

原片、时码和素材清单归在同一份任务记录里。

```mermaid
flowchart LR
  Media --> Footage
  Media --> Timecodes
  Media --> Map["Asset map"]
```

## 剪映制作链

```mermaid
flowchart LR
  Source --> Timeline --> Draft --> Review
```

## 海外企业核验链

```mermaid
flowchart LR
  Bocha --> Chrome --> Website["Official site"] --> Shortlist
```

## 视频号 MCP 链

```mermaid
flowchart LR
  Import --> Workbench --> SQLite --> MCP
```

## 候选证据结构

每条候选证据包含来源、企业、角色和状态。

| 来源 | 企业 | 角色 | 状态 |
| --- | --- | --- | --- |
| Source | Company | Role | Status |

## 发布与触达回执

```mermaid
flowchart LR
  Authorize --> Action["Send / Call"] --> Receipt --> Handoff
```

## 首次装载与依赖

```mermaid
flowchart LR
  Clone["Git clone"] --> Install --> Preflight --> Test
```

## 修复与项目记忆

```mermaid
flowchart LR
  Failure --> Repair --> Verify --> Memory
```

发送、发布、计费或外呼状态未知时，先查服务回执。用各阶段验收时的实际状态判断接手和续跑。[工作流](workflow.md)