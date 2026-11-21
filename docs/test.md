---
type: "Guide"
title: "验收"
description: "复现顺序与证据口径。"
tags: ["ClipSignal"]
---

# 验收

运行 `node tools/check-okf.mjs`、`node tools/leads.mjs --self-test` 和 `node --test tests/core.mjs`。使用可用 Python 跑 `python -m unittest discover -s tests -p test_status.py`。运行 `node tools/release.mjs check` 核对清单与文件边界。`node tools/release.mjs export <new-directory>` 生成同机重定位副本。

使用本机 FFmpeg 生成 3 秒测试图形到 .local/prep/sample.mp4，再运行 node tools/draft-plan.mjs examples/draft.json examples/media.json。将 UTF-8 JSON 写入私有运行目录，调用上游 draft create 和 draft validate 生成并原生验收隔离草稿。对真实剪映首页登记保留单独回执。状态栏单独检查 MCP 协议与实际 TUI 选择。换机需要在新 Windows、非作者账号和不同路径上从首次配置开始运行。实盘的剪映首页、平台发布、邮件送达、实际通话和到访分别采证。

首次装载验收使用发布清单导出的独立副本，运行 install.ps1 -Flow core，读回 entry，执行合成候选。用新会话的项目 Skill 列表核对 clipsignal 是否可发现。
