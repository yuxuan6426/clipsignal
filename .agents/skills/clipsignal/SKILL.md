---
name: clipsignal
description: "ClipSignal 总控，配置 Windows 工作区并编排内容制作、外贸找客与渠道触达。"
---

# clipsignal

先执行 sibling `no-negative-echo` 的相关规范和 `clipsignal-memory` 的查阅。确定任务 ID、目标市场、企业和产品资料、授权素材、活动目标与渠道权限。使用当前工作区 [setup](../../../docs/setup.md)，运行 `setup.ps1 -Check -Flow <flow>`。将结果存为任务 JSON 后可用 `node tools/route.mjs <json>` 分类。缺依赖转安装，已装报错转修复，权限待核时继续能独立执行的分支。安装或修复后重跑原入口并逐项验收。

- 参考作品、媒体理解、录制说明转 `clipsignal-media`，剪辑转 `clipsignal-edit`。
- 海外企业核验转 `clipsignal-leads`，微信视频号转 `clipsignal-wechat`。
- 正式成片发布转 `clipsignal-publish`，邮件和电话转 `clipsignal-outreach`。
- 预检、运行或验收故障转 `clipsignal-repair`。通过验收后转 `clipsignal-memory` 收录经验。

阶段以回执推进。已授权的例行恢复完成后直接交付成果。结果待核的外部动作先查询原回执。状态写入可选 `node tools/progress.mjs THREAD MODULE PHASE STATE [PENDING]`，仅使用宿主已提供的当前 thread ID。输入、素材和含业务数据的回执留在 `.local/`。本工作区业务入口共享这些阶段规则。
