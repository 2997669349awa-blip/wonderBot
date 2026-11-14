# WonderBot 版权与衍生声明

## 本作品

**WonderBot** — 面向 QQ 群与私域场景的智能助手发行版
版权所有 © 2026 WonderBot 团队
许可证：**AGPL-3.0-or-later**（见 `LICENSE`）
官方仓库：https://github.com/2997669349awa-blip/wonderBot

## 上游作品与原始版权

WonderBot 是以下作品的**衍生作品**（依据 AGPLv3 第 0 条与第 5 条）：

- 上游项目：**AstrBot** — https://github.com/AstrBotDevs/AstrBot
- 上游版权：Copyright (C) AstrBotDevs / AstrBot contributors
- 上游许可证：GNU Affero General Public License v3.0 or later（AGPL-3.0-or-later）
- 采用基线版本：`v4.29.4`，上游 `master` 分支提交 `630d5ce`

上游 `LICENSE` 全文及全部原始版权声明在本仓库中**原样保留，未作删改**；
上列上游名称与版权行不随本衍生版的品牌替换而改变。
本作品整体继续以 AGPL-3.0-or-later 发布，未对下游附加任何额外限制。

## 本作品所做的修改

依据 AGPLv3 第 5 条要求，列明主要修改：

1. **品牌与标识**：产品名、图标、首次运行声明、EULA、文档、WebUI 文案、配色
   （深黑主题）全部替换为 WonderBot 自有标识；更新源与公告地址改为自有服务。
2. **更新机制**：更新检查、核心包与 WebUI 包下载地址改由
   `astrbot/core/wonderbot/brand.py` 集中配置；未配置自有发布源时**禁用更新检查**，
   不会连接上游官方发布服务。
3. **遥测**：默认关闭匿名统计外发（`WONDERBOT_DISABLE_METRICS` 默认值为 `1`）。
4. **成本审查**：新增 `astrbot/core/wonderbot/cost.py`，逐次记录每次大模型调用的
   token、耗时与费用，单价表可编辑，并可生成 HTML 审查报表。
5. **长期记忆**：新增 `astrbot/core/wonderbot/memory.py`，按用户与会话维度持久化
   画像、事实与摘要，并在系统提示词组装时注入。
6. **QQ 发送者白名单**：新增 `SenderAllowlistStage` 流水线阶段，
   仅放行白名单内 QQ 号，其余用户的事件在进入插件与大模型前终止。
7. **兼容性保留**：Python 包目录 `astrbot/`、导入路径与 `astrbot.api` 公共接口
   **未改动**，以保持对既有插件生态的兼容；其中的类名标识符不属于产品品牌，
   故未重命名。

## 获取对应源码

本作品以网络服务形式提供时，依据 AGPLv3 第 13 条，使用者可从上述官方仓库
获取与所运行版本完整对应的源码。

## 商标

「WonderBot」名称与图标为本作品自有标识。本声明中对上游名称的引用仅用于
说明版权归属与衍生关系，不构成隶属、背书或商标授权。
