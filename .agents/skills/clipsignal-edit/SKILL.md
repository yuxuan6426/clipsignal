---
name: clipsignal-edit
description: "把参考拆解和企业授权原片制作成剪映首页可见的独立草稿。"
---

# clipsignal-edit

输入授权原片、拆解、受众和时长。通过 `clipsignal-media` 理解原片后，调用已安装的 jianying-draft-collab 的原生自检和草稿工具。旁白用 Agent Plan 豆包 TTS 2.0 默认女声，独立保存旁白、字幕和本地原创纯音乐轨。过渡页优先 Chrome 的 ChatGPT 网页，只有当前资产审核支持内置 ImageGen 来源时才走备选。用 `tools/draft-plan.mjs` 将媒体标识映射为接收端绝对路径。原生读回通过后，应用自然退出时用隔离副本登记到实际草稿根。分别记录首页、编辑、导出和发布。
