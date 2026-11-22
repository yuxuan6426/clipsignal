---
type: "Guide"
title: "验收"
description: "复现顺序与证据口径。"
tags: ["ClipSignal"]
---

# 验收

## 七项能力的实证与待验

| 模块 | 已验证 | 待复跑或现场验收 |
| --- | --- | --- |
| [总控与首次配置](workflow.md#首次配置修复与复用) | 总控和配置指引已落地。本机 GCC 已编译并运行 Win64 测试程序，发布副本已在同机换路径复跑。 | 在接收方的 Windows 与账号环境完成首次配置和各模块验证。 |
| [内容理解与拍摄说明](workflow.md#内容制作与发布) | Agent Plan 已处理冠英授权原片和访谈录音。一条展会参考片的结构拆解已串入剪映草稿。 | 从自动选择行业参考样片到盘点素材、经 Gmail 发送补拍说明和回传续剪的完整复跑。 |
| [剪映制片](workflow.md#内容制作与发布) | 冠英 22 秒双语草稿通过原生读回和素材引用核对，在剪映首页人工确认。 | 编辑器内播放、正式导出及旁白、配乐、过渡页合成整链。Codex ImageGen 备选需接入资产来源校验。 |
| [海外线索发现与核验](workflow.md#买家发现与核验) | X 与 Facebook 的记录回查官网，合并成一条已核品类和角色的重型配件渠道候选。YouTube 已做回放，销售交接以合成询盘验过。 | 实际候选的进口能力、采购需求和到场意向核实。 |
| [展会发布与触达](workflow.md#邀约与销售接手) | Gmail 自验有发送回执。云蝠测试知识库可经 MCP 读回，Windows Codex 接入已有握手与工具发现记录。 | 自动私信与商务联系方式回收待验。Gmail 接收端、云蝠语音智能体绑定与线路、实际外呼、企业账号发片、预约与到访各自验收。 |
| [自研视频号扩展](../modules/wechat/README.md) | 已验证公开作品入库、微信窗口读取可见评论，以及 Codex MCP 读取作品和评论。 | 按买家画像定向发现、作者主页核验到企业候选的自动全链。 |
| [自进化与自修复](workflow.md#首次配置修复与复用) | 隔离演练完成修复、复验、续跑与项目记忆入库。另一次独立启动命中该经验，模拟邮件保留为待核。 | 接收设备用对应版本复跑关键环节，并用服务端回执复核真实外部动作。 |

展会实跑在接收方的设备、账号与授权范围内验收。闲时持续巡看、展馆周边定向推广与视频号自动获客全链列为后续扩展。

## 在接收设备复跑

运行 `node tools/check-okf.mjs`、`node tools/leads.mjs --self-test` 和 `node --test tests/core.mjs`。使用可用 Python 跑 `python -m unittest discover -s tests -p test_status.py`。运行 `node tools/release.mjs check` 核对清单与文件边界。`node tools/release.mjs export <new-directory>` 生成同机重定位副本。

使用本机 FFmpeg 生成 3 秒测试图形到 .local/prep/sample.mp4，再运行 node tools/draft-plan.mjs examples/draft.json examples/media.json。将 UTF-8 JSON 写入私有运行目录，调用上游 draft create 和 draft validate 生成并原生验收隔离草稿。对真实剪映首页登记保留单独回执。状态栏单独检查 MCP 协议与实际 TUI 选择。换机需要在新 Windows、非作者账号和不同路径上从首次配置开始运行。实盘的剪映首页、平台发布、邮件送达、实际通话和到访分别采证。

首次装载验收使用发布清单导出的独立副本，运行 install.ps1 -Flow core，读回 entry，执行合成候选。用新会话的项目 Skill 列表核对 clipsignal 是否可发现。
