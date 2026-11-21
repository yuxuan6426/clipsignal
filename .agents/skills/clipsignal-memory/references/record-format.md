# 项目记忆文件格式

记忆保存在 Git 忽略的 `.local/memory`。创建首条记录时建立 OKF v0.3 根索引和更新记录。每个条目用 UTF-8 Markdown，文件名采用模块和场景的稳定短名。同场景存在并行有效的版本时，在文件名中注明版本以区分。

## 根索引

```markdown
---
okf_version: "0.3"
title: "ClipSignal 项目记忆"
---

# ClipSignal 项目记忆

- [剪映草稿素材登记](jianying-draft-media.md) - 剪映草稿登记前验证素材引用。
```

## 条目

以下为格式示例。填写实际验证者、环境版本、时间、适用条件和回执。由 Codex 执行的验证记为 `agent:codex`，实际进行了人工核对时再记相应人工的验证。

```markdown
---
type: "Practice"
title: "剪映草稿素材登记"
description: "剪映草稿登记前验证素材引用的有效步骤。"
tags: ["ClipSignal", "剪映", "草稿"]
module: "jianying"
scenario: "草稿登记"
applicability: {"os":"Windows x64", "version":"本次验收所用版本", "conditions":"可访问剪映草稿目录"}
status: "active"
generated: {"by":"agent:codex","at":"2026-11-21T12:00:00+08:00"}
verified: [{"by":"agent:codex","at":"2026-11-21T12:00:00+08:00"}]
stale_after: "2026-12-21T12:00:00+08:00"
sources:
  - {"id":"receipt","title":"已脱敏的草稿验证回执","resource":"jianying-draft-media.receipt.json"}
---

# 剪映草稿素材登记

填写现象、使用步骤、已观察的结果和复验方法。[^receipt]

[^receipt]: [已脱敏的草稿验证回执](jianying-draft-media.receipt.json)
```

来源采用实际使用的官方文档 URL 或本包内的最小验收回执。回执示例字段为工作区相对位置、运行版本、可核验的时间及验收结果。采用精简 JSON 或文本文件，避免在复制回执时带入运行环境、请求头或实际客户数据。标记 `superseded` 时添加 `superseded_by`，填同一知识包内替代条目的相对路径，并更新索引的条目状态。

## 更新记录

```markdown
# 更新记录

## 2026-11-21

- 收录剪映草稿登记经验。
```

按日期倒序维护，每日只用一个标题。记录相同知识反复通过验收时，经核对可更新该条目，保留其可追溯的来源和状态。
