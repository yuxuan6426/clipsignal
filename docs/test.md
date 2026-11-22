---
type: "Guide"
title: "验收"
description: "复现顺序与证据口径。"
tags: ["ClipSignal"]
---

# 验收

## 冠英首发案例的已验证结果

| 环节 | 验证结果 |
| --- | --- |
| 剪映 | 冠英 22 秒双语草稿通过原生读回与素材引用核对，完成本机登记并在剪映首页人工确认 |
| 海外企业核验 | Chrome 读 X 和 Facebook 的两个公开入口，回查官网后合并为同一重型配件渠道候选，进口能力、采购意向与到场单列待核 |
| 销售接手 | 合成维修厂询盘通过企业、意图和授权分流，交接卡包含车桥或件号、数量与报价依据等补问 |
| Gmail 与云蝠 | Gmail 自验覆盖发送回执，云蝠自验覆盖测试知识库读回 |
| 微信视频号 | 本机 MCP 读取作品详情和可见评论，账号关联覆盖按实际记录 |

展会实跑分别验成片发布、邮件收件、实际通话、预约与到访。接收端按自己的环境、业务账户和真实回执验收。闲时持续巡看、展馆周边定向推广与视频号自动获客全链列为后续扩展。

## 在接收设备复跑

运行 `node tools/check-okf.mjs`、`node tools/leads.mjs --self-test` 和 `node --test tests/core.mjs`。使用可用 Python 跑 `python -m unittest discover -s tests -p test_status.py`。运行 `node tools/release.mjs check` 核对清单与文件边界。`node tools/release.mjs export <new-directory>` 生成同机重定位副本。

使用本机 FFmpeg 生成 3 秒测试图形到 .local/prep/sample.mp4，再运行 node tools/draft-plan.mjs examples/draft.json examples/media.json。将 UTF-8 JSON 写入私有运行目录，调用上游 draft create 和 draft validate 生成并原生验收隔离草稿。对真实剪映首页登记保留单独回执。状态栏单独检查 MCP 协议与实际 TUI 选择。换机需要在新 Windows、非作者账号和不同路径上从首次配置开始运行。实盘的剪映首页、平台发布、邮件送达、实际通话和到访分别采证。

首次装载验收使用发布清单导出的独立副本，运行 install.ps1 -Flow core，读回 entry，执行合成候选。用新会话的项目 Skill 列表核对 clipsignal 是否可发现。
