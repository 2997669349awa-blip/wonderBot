# WonderBot 使用与配置

官方仓库：https://github.com/2997669349awa-blip/wonderBot · 文档：https://github.com/2997669349awa-blip/wonderBot/tree/main/docs

## 1. 填自己的官方仓库与发布源

所有对外地址集中在 `astrbot/core/wonderbot/brand.py`，改这一处即可，
也可以用环境变量覆盖（推荐，改完不用改代码）：

| 环境变量 | 作用 | 默认值 |
|---|---|---|
| `WONDERBOT_REPO_URL` | 官方仓库地址 | `https://github.com/2997669349awa-blip/wonderBot` |
| `WONDERBOT_WEBSITE_URL` / `WONDERBOT_DOCS_URL` | 官网 / 文档站 | `https://2997669349awa-blip.github.io/wonderBot` / `https://github.com/2997669349awa-blip/wonderBot/tree/main/docs` |
| `WONDERBOT_RELEASE_API` | 版本检查接口 | **空 = 禁用更新检查** |
| `WONDERBOT_CORE_PACKAGE_BASE_URL` | 核心更新包地址前缀 | 空 |
| `WONDERBOT_DASHBOARD_PACKAGE_BASE_URL` | WebUI 更新包地址前缀 | 空 |
| `WONDERBOT_NOTICE_URL` | 公告 JSON 地址 | `<官网>/notice.json` |
| `WONDERBOT_DATA_DIR` | 成本与记忆数据库目录 | 上游 `data/` |

**默认不检查更新**：`WONDERBOT_RELEASE_API` 为空时，`check_update()` 直接返回 `None`、
`get_releases()` 返回空列表，不会向任何上游官方服务发请求。WebUI 也只会使用随源码
自带的 `dist`，不会从上游仓库下载。把自己的发布服务地址填进上表后，更新链路才会启用。

## 2. QQ 发送者白名单

配置文件 `data/cmd_config.json` → `platform_settings.wonderbot_sender_allowlist`：

```json
{
  "enabled": true,
  "qq_ids": ["123456789", "987654321"],
  "platforms": ["aiocqhttp", "qqofficial", "onebot", "qq"],
  "only_commands": false,
  "log_rejected": true,
  "allow_webchat": true
}
```

- 按**发送者 QQ 号**判断，不是按群号或会话 ID；非白名单用户的事件在进入插件和
  大模型之前就被终止，因此**不会产生任何 token 消耗**。
- 默认 `enabled=true` 且 `qq_ids` 为空 → 拒绝所有 QQ 用户命令（安全默认）。
  填入自己的 QQ 号后生效。
- `only_commands=true` 时只拦截 @ / 唤醒类指令，普通闲聊仍可响应。
- 日志会记录每次拒绝，便于审查。

## 3. 成本审查

每次大模型调用的 token（普通输入 / 缓存命中 / 输出）、耗时与费用写入
`data/wonderbot_cost.db`。单价表 `data/wonderbot_pricing.json` 首次运行自动生成，
单位为**元 / 百万 token**，可直接编辑；未匹配到单价的调用按 0 计费并在报表中标注
「未配置单价」，不会虚报成本。

生成审查报表（逐次明细 + 按模型汇总，深黑主题）：

```bash
python3 scripts/wonderbot_report.py            # 输出 data/cost-report.html
python3 scripts/wonderbot_report.py --limit 500
```

## 4. 长期记忆

`data/wonderbot_memory.db`，按 `sender:{平台}:{QQ号}` 与 `umo:{会话}` 两个维度存储：
- 每轮对话自动沉淀一条轻量摘要（用户问题 + 答复要点）；
- 系统提示词组装时自动召回权重最高的若干条并注入；
- 重复内容只累加权重，不产生重复行；可通过 `MemoryStore.forget(id)` /
  `clear_scope(scope)` 删除。

## 5. 开发与运行

要求 Python ≥ 3.12。源码目录 `astrbot/` 与 `astrbot.api` 公共接口**刻意保留原名**，
用于兼容既有插件生态；产品名、界面、文档、图标与对外地址均为 WonderBot。

```bash
pip install -r requirements.txt
python3 main.py
```

## 6. 许可证与署名

AGPL-3.0-or-later。`LICENSE` 为上游 AGPL 全文，原样保留；版权归属、上游来源与
完整修改清单见 `NOTICE.md`。以网络服务形式对外提供时，须依 AGPLv3 第 13 条
向使用者提供对应源码的获取途径。

## 7. 沙盒与部署镜像

Docker Compose、K8s 清单与 Agent 沙盒里原先指向上游作者的镜像
（`soulter/shipyard-bay`、`soulter/shipyard-ship`）已统一改为
`wonderbotdevs/shipyard-bay`、`wonderbotdevs/shipyard-ship` 占位名。
**这些镜像需要由你自行构建并推送到自己的镜像仓库**，否则 Agent 沙盒功能不可用；
不使用沙盒时不影响主程序运行。若已有自己的镜像仓库，把上述名称全局替换即可。
