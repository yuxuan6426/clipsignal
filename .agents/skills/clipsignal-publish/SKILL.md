---
name: clipsignal-publish
description: "用授权平台账号上传成片并返回真实发布回执。"
---

# clipsignal-publish

先用 `clipsignal-edit` 取得并验收正式导出文件、字幕与封面。按任务授权在连接的 Chrome 中打开目标平台，核对账号、上传文件、标题与发布时间后执行授权发布。保存作品链接、实际可见性和时间。保留失败时的上传／草稿／发布阶段，使用 `clipsignal-repair` 查现有状态，避免重复提交。
