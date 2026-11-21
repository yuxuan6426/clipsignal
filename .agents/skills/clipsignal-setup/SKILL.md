---
name: clipsignal-setup
description: "首次使用或换 Windows 设备时配置和验证 ClipSignal。"
---

# clipsignal-setup

从仓库根执行 `setup.ps1 -Check -Flow <flow>`，解释缺失、已安装但出错、需要授权和待实测的区别。依照[配置指引](../../../docs/setup.md)准备模块。对工作区受管组件可运行 `setup.ps1 -Apply`，再运行原 `-Check`。复用兼容依赖与已有回执；浏览器、原生读回和账号用实际产物确认。运行错误转交 `clipsignal-repair`。
