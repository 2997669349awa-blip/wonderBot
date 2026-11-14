![WonderBot](wonderbot-icon.png)

# WonderBot

> 面向 QQ 群与私域场景的开源智能助手发行版。
> 把「每一次调用花多少钱、每个用户说过什么、谁有资格下命令」三件事全部落到本地、可查、可审计。

| 项目 | 内容 |
|---|---|
| 当前版本 | **beta0.1.0**（预发布，对应 Python 包版本 `0.1.0b0`） |
| 官方网站 | https://2997669349awa-blip.github.io/wonderBot/ |
| 官方仓库 | https://github.com/2997669349awa-blip/wonderBot |
| 发行下载 | https://github.com/2997669349awa-blip/wonderBot/releases/tag/beta0.1.0 |
| 许可证 | **AGPL-3.0-or-later** |
| 运行环境 | Python 3.12+ |
| 上游基线 | AstrBot v4.29.4（`master` 提交 `630d5ce`） |
| 项目性质 | 独立衍生发行版，与上游官方团队无隶属、背书或代理关系 |

---

## 目录

- [一、这是什么](#一这是什么)
- [二、版本与状态](#二版本与状态)
- [三、九项核心能力](#三九项核心能力)
- [四、快速开始](#四快速开始)
- [五、配置详解](#五配置详解)
- [六、改动清单与目录结构](#六改动清单与目录结构)
- [七、工作原理](#七工作原理)
- [八、路线图](#八路线图)
- [九、常见问题](#九常见问题)
- [十、许可证与衍生声明](#十许可证与衍生声明)
- [十一、致谢与社区](#十一致谢与社区)
- [附录：校验与源码构建](#附录校验与源码构建)

---

## 一、这是什么

WonderBot 是一个**独立衍生发行版**，基于开源项目 [AstrBot](https://github.com/AstrBotDevs/AstrBot)（AGPL-3.0-or-later）做能力 fork。

上游是「全平台 × 全模型 × 上千插件」的通用框架，覆盖面极广、迭代很快：QQ、微信、企业微信、飞书、钉钉、Telegram、Discord、Slack 等消息平台，以及 OpenAI 兼容服务、Anthropic、Gemini、DeepSeek、通义、智谱、Ollama、Dify、Coze 等模型服务都能接。但通用框架解决的是「能不能接进来」，长期在真实社群里跑，还有三件事绕不开：

1. **钱**：每次大模型调用到底花了多少，哪些群、哪些人、哪个插件在烧钱，原始框架只记录 token 计数，且这些计数默认被匿名外发。
2. **人**：机器人是否记得某个用户上周说过什么，而不是每次对话都从零开始。上游的「自动上下文压缩」解决会话内不爆窗，不是跨会话记住人。
3. **权限**：谁能对机器人下命令。上游默认是内容安全（健康模式），不是按身份的访问控制。

WonderBot 的选择是**收窄、不拓宽**：不动核心架构，只在官方还浅的地方补齐能力，做成面向中文社群 / 私域运营的开箱即用发行版，并保持能持续合并上游。这是 B 路线（能力 fork），不是简单换皮。

---

## 二、版本与状态

`beta0.1.0` 是首个预发布版本，功能完整、可部署，但按预发布口径管理：

- Python 包版本写作 `0.1.0b0`，这是 PEP 440 对 beta 预发布的标准写法；两者指同一个版本。
- 基线锁定上游 `v4.29.4`，不追 `master` HEAD，按周期合并上游改动。
- 包含完整源码、安装脚本、中文文档、官网源文件与合规声明；不含编译产物与 `.git` 提交历史（源码快照发布）。
- 沙盒（Agent 代码执行）相关镜像为占位名，需要自行构建推送；不使用沙盒不影响主程序。

---

## 三、九项核心能力

| # | 能力 | 实现位置 | 说明 |
|---|---|---|---|
| 1 | 逐次成本审查 | `astrbot/core/wonderbot/cost.py` | 每次调用记录模型、普通输入 / 缓存命中 / 输出 token、耗时、费用、发送者与会话 |
| 2 | 长期记忆 | `astrbot/core/wonderbot/memory.py` | 按 QQ 号与会话两维度持久化画像、事实、摘要，系统提示词自动召回注入 |
| 3 | QQ 发送者白名单 | `astrbot/core/pipeline/sender_allowlist_check/stage.py` | 按发送者 QQ 号放行，非白名单事件在进入插件与大模型前终止 |
| 4 | 深黑主题 WebUI | `dashboard/src/theme/`、`dashboard/src/main.ts` | 深浅两套配色统一纯黑系，强制默认深色，不跟随系统 |
| 5 | 自有更新源 | `astrbot/core/wonderbot/brand.py` | 版本检查 / 核心包 / WebUI 包 / 公告地址集中配置，未配置即禁用 |
| 6 | 默认零遥测 | `astrbot/core/utils/metrics.py` | 匿名统计默认关闭，不生成持久安装 ID，不外发使用数据 |
| 7 | 独立品牌 | `dashboard/public/`、`favicon.svg`、`FIRST_NOTICE*`、`EULA.md` | 名称、图标、首次声明、协议、文档、镜像名与对外链接全部自有化 |
| 8 | 插件生态兼容 | `astrbot/api/`、`astrbot/` 包目录 | 公共接口与导入路径刻意保留，既有插件无需改动 |
| 9 | 合规开源 | `LICENSE`、`NOTICE.md` | AGPL 全文与上游版权声明原样保留，修改清单公开 |

### 3.1 逐次成本审查

上游的 `ProviderStat` 只记录 token 计数且默认匿名外发。WonderBot 在写入官方统计的同一挂点旁路记录一份本地账本：

- 数据落在 `data/wonderbot_cost.db`（SQLite），字段包含时间、模型、provider、输入 / 缓存 / 输出 token、耗时毫秒、费用、是否匹配单价、发送者 ID、会话标识。
- 单价表 `data/wonderbot_pricing.json` 首次运行自动生成，单位为**元 / 百万 token**，可直接按实际合同价编辑。
- 未匹配到单价的调用按 0 计费，并在报表里标注「未配置单价」，**不虚报成本**。
- 生成审查报表：

  ```bash
  .venv/bin/python scripts/wonderbot_report.py --limit 500
  # 输出 data/cost-report.html：逐次明细 + 按模型汇总，深黑主题
  ```

### 3.2 长期记忆

- 作用域分两级：`sender:{平台}:{QQ号}`（跟人走）与 `umo:{会话}`（跟群 / 会话走）。
- 每轮对话自动沉淀一条轻量摘要（用户问题 + 答复要点）；也可写入显式画像与事实。
- 系统提示词组装时（`main_agent/builder.py`）召回权重最高的若干条注入。
- 重复内容只累加权重、不产生重复行；支持 `forget(id)` 与 `clear_scope(scope)` 删除。
- 数据落在 `data/wonderbot_memory.db`。

### 3.3 QQ 发送者白名单

- 判断依据是**发送者 QQ 号**，不是群号或会话 ID。
- 被拒绝的事件在流水线最前端 `WakingCheckStage` 之后、`WhitelistCheckStage` 之前终止，因此**不产生任何 token 消耗**。
- 默认 `enabled=true` 且 `qq_ids=[]`，即拒绝所有 QQ 用户命令（安全默认），填入自己的 QQ 号后生效。
- `only_commands=true` 时只拦截 @ / 唤醒类指令，普通闲聊仍可响应；`allow_webchat=true` 放行 WebUI 内的对话。
- 每次拒绝写日志，便于审计。

### 3.4 更新源与「不会检测到官方更新」

所有对外地址集中在 `astrbot/core/wonderbot/brand.py`，也可以全部用环境变量覆盖：

| 环境变量 | 作用 | 默认值 |
|---|---|---|
| `WONDERBOT_REPO_URL` | 官方仓库 | `https://github.com/2997669349awa-blip/wonderBot` |
| `WONDERBOT_WEBSITE_URL` | 官网 | `https://2997669349awa-blip.github.io/wonderBot` |
| `WONDERBOT_DOCS_URL` | 文档 | 仓库 `docs/` 目录 |
| `WONDERBOT_NOTICE_URL` | 公告 JSON | `<官网>/notice.json` |
| `WONDERBOT_RELEASE_API` | 版本检查接口 | **空 = 禁用更新检查** |
| `WONDERBOT_CORE_PACKAGE_BASE_URL` | 核心更新包前缀 | 空 |
| `WONDERBOT_DASHBOARD_PACKAGE_BASE_URL` | WebUI 更新包前缀 | 空 |
| `WONDERBOT_DISABLE_METRICS` | 关闭匿名统计 | `1`（默认关闭） |
| `WONDERBOT_ROOT` / `WONDERBOT_DATA_DIR` | 根目录 / 账本目录 | 上游默认 / `data/` |

`RELEASE_API` 为空时，`check_update()` 直接返回 `None`、`get_releases()` 返回空列表，**不发起任何网络请求**；WebUI 只使用随源码自带的资源，不会从上游官方仓库下载。把自己的发布服务地址填进上表后，更新链路才会启用。

---

## 四、快速开始

### 4.1 从安装包安装（推荐）

```bash
curl -L -o wonderbot.zip \
  https://github.com/2997669349awa-blip/wonderBot/releases/download/beta0.1.0/WonderBot-beta0.1.0-source.zip
unzip wonderbot.zip && cd WonderBot-beta0.1.0
chmod +x install.sh && ./install.sh
```

`install.sh` 会检查 Python 版本、创建 `.venv` 虚拟环境、安装 `requirements.txt`、准备 `data/` 目录与配置，并打印后续步骤。

### 4.2 从源码运行

```bash
git clone https://github.com/2997669349awa-blip/wonderBot.git
cd wonderBot
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

> 说明：本仓库 `pyproject.toml` 带有自定义 hatchling 构建钩子，会在安装时尝试构建 Vue 仪表盘（需要 Node / pnpm）。因此**推荐用 `requirements.txt` + 直接运行 `main.py`** 的方式，不依赖前端构建链。

### 4.3 Docker Compose

```bash
docker compose -f compose.yml up -d
```

`compose.yml`、`Dockerfile`、K8s 清单中的镜像名已改为 `wonderbotdevs/*` 占位名，部署前请替换成自己镜像仓库的地址并自行构建推送。

### 4.4 首次必做

编辑 `data/cmd_config.json`：

```json
{
  "platform_settings": {
    "wonderbot_sender_allowlist": {
      "enabled": true,
      "qq_ids": ["123456789"],
      "platforms": ["aiocqhttp", "qqofficial", "onebot", "qq"],
      "only_commands": false,
      "log_rejected": true,
      "allow_webchat": true
    }
  }
}
```

填入自己的 QQ 号，然后在 WebUI（默认 `http://127.0.0.1:6185`）里配置消息平台与模型服务。完整配置见 [WONDERBOT.md](WONDERBOT.md)。

---

## 五、配置详解

### 5.1 白名单字段

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `enabled` | bool | `true` | 是否启用发送者白名单 |
| `qq_ids` | string[] | `[]` | 允许的 QQ 号；空数组即拒绝全部 QQ 命令 |
| `platforms` | string[] | 4 种 QQ 平台 | 仅对这些平台生效，其他平台不受影响 |
| `only_commands` | bool | `false` | 为 true 时只拦截指令，闲聊仍可响应 |
| `log_rejected` | bool | `true` | 记录每次拒绝 |
| `allow_webchat` | bool | `true` | 放行 WebUI 内对话 |

### 5.2 成本单价表

`data/wonderbot_pricing.json` 首次运行自动生成，形如：

```json
{
  "deepseek-chat": { "input": 2.0, "cached_input": 0.5, "output": 8.0 },
  "gpt-4o-mini": { "input": 1.1, "cached_input": 0.55, "output": 4.4 }
}
```

单位为元 / 百万 token。修改后新调用即按新单价计费，历史记录不变。

### 5.3 数据与隐私

- 成本账本 `data/wonderbot_cost.db`、记忆库 `data/wonderbot_memory.db` 均为本地 SQLite。
- 默认不向任何外部服务上报遥测；聊天内容不会离开自己的服务器。
- 若接入第三方大模型服务，提示词按该服务商条款处理，请自行评估。
- 上游 EULA 中「不收集对话内容」的承诺已被本衍生版 EULA 第 5 条重写，因为长期记忆确实会在本地保存内容。

### 5.4 沙盒镜像

`compose.yml`、K8s 清单与 Agent 沙盒里原先指向上游作者的镜像已改为 `wonderbotdevs/shipyard-bay`、`wonderbotdevs/shipyard-ship` 占位名，**需要自行构建并推送到自己的镜像仓库**，否则沙盒功能不可用；不使用沙盒不影响主程序。

---

## 六、改动清单与目录结构

### 6.1 新增文件

```
astrbot/core/wonderbot/
├── __init__.py          模块导出
├── brand.py             品牌、官网地址、更新源集中配置（默认禁用更新检查）
├── cost.py              SQLite 成本账本、单价表、HTML 审查报表
└── memory.py            长期记忆存取、去重加权、上下文注入

astrbot/core/pipeline/sender_allowlist_check/
├── __init__.py
└── stage.py             SenderAllowlistStage 白名单流水线阶段

website/                 官网静态源码（GitHub Pages 部署到 gh-pages 分支）
├── index.html          单页官网
├── assets/style.css    深黑主题样式
├── assets/app.js       交互脚本
├── favicon.svg
├── notice.json         公告数据
└── .nojekyll

scripts/wonderbot_report.py   成本审查报表生成脚本
install.sh                    一键安装脚本（随安装包提供）
INSTALL.md                    安装与验证说明
VERSION                       产品版本号 beta0.1.0
WONDERBOT.md                  完整使用与配置文档
NOTICE.md                     版权、衍生关系与修改清单
EULA.md                       本衍生版最终用户许可协议
wonderbot-icon.png            产品图标
cost-report-demo.html         成本报表示例（演示数据）
```

### 6.2 修改的上游文件

| 文件 | 改动 |
|---|---|
| `astrbot/core/updater.py` | 更新源改用 `brand`；未配置时禁用检查；类名兼容别名保留 |
| `astrbot/core/dashboard_assets.py` | WebUI 包只从自有发布源下载，未配置时明确报错，不回退上游 |
| `astrbot/builtin_stars/builtin_commands/commands/help.py` | 公告地址改用 `brand.NOTICE_URL` |
| `astrbot/core/utils/metrics.py` | 匿名统计默认关闭 |
| `astrbot/core/utils/astrbot_path.py` | 支持 `WONDERBOT_ROOT` 环境变量 |
| `astrbot/core/config/default.py` | 新增 `wonderbot_sender_allowlist` 配置块 |
| `astrbot/core/astr_agent_runtime/history.py` | 旁路写入成本账本与对话记忆 |
| `astrbot/core/astr_agent_runtime/main_agent/builder.py` | 系统提示词注入召回的记忆 |
| `astrbot/core/pipeline/{bootstrap,stage_order,__init__}.py` | 注册 `SenderAllowlistStage` |
| `dashboard/src/theme/*`、`main.ts`、`config.ts` | 深黑配色、强制默认深色 |
| `dashboard/public/*`、`dashboard/index.html` | 图标与页面标题 |
| `FIRST_NOTICE*`（5 个语言） | 整份重写为 WonderBot 声明 |
| `README*`、`EULA.md`、部署配置 | 品牌与地址全量替换 |
| `pyproject.toml` | 项目名、版本 `0.1.0b0`、描述、仓库地址 |

### 6.3 刻意保留

- `LICENSE`：上游 AGPL-3.0-or-later 全文与原始版权声明，原样保留（法律要求）。
- `astrbot/` 包目录与 `astrbot.api` 公共接口：插件契约层，改动会与上千个第三方插件断链。
- Python 类名如 `AstrBotConfig`、`AstrBotMessage`：属于代码标识符，不是产品品牌；AGPL 不要求重命名。
- `NOTICE.md` 中对上游名称的引用：仅用于说明版权归属与衍生关系。

---

## 七、工作原理

消息进入后的流水线顺序（节选）：

```
WakingCheckStage          是否需要唤醒
  ↓
SenderAllowlistStage     [新增] 按发送者 QQ 号放行 / 拒绝
  ↓
WhitelistCheckStage      上游的会话白名单
  ↓
SessionStatusCheckStage  会话是否启用
  ↓
... 插件处理 ...
  ↓
ProcessStage / Agent     组装系统提示词时注入长期记忆
  ↓
history.py               一次写入：官方 ProviderStat + 成本账本 + 对话记忆
  ↓
RespondStage             回复
```

三个新增模块都是**挂载式**的：独立文件 + 少量接线点，不重写核心逻辑。这样合并上游时只需按 [NOTICE.md](NOTICE.md) 的修改清单逐项核对，不会把 fork 变成永久分叉。

---

## 八、路线图

| 版本 | 目标 |
|---|---|
| **beta0.1.0**（当前） | 品牌与更新源自有化、深黑主题、成本审查、长期记忆、QQ 白名单、完整文档与合规声明 |
| 0.2.0 | 向量检索、记忆过期与权重衰减、按群共享记忆、WebUI 记忆管理 |
| 0.3.0 | 多 Agent 编排与预算上限、工具调用白名单、敏感操作二次确认、审计导出 |
| 1.0.0 | 成套社群运营模板、prompt 版本管理与评测、多群汇总看板 |

0.2.0 之后为规划方向，会随上游合并节奏调整。

---

## 九、常见问题

**和 AstrBot 官方是什么关系？**
独立衍生作品，AGPL-3.0-or-later，基线 v4.29.4。原始版权与许可证全文原样保留，修改清单在 `NOTICE.md`。与上游官方团队无隶属、背书或代理关系，也不使用其更新服务。

**装好后所有 QQ 命令都没反应？**
这是刻意的安全默认值：白名单默认开启且名单为空。把 QQ 号填进 `wonderbot_sender_allowlist.qq_ids` 即可。

**会不会偷偷上报数据或检测到官方更新？**
不会。匿名统计默认关闭；更新检查、核心包、WebUI 包与公告地址全部指向自有配置，未配置发布源时更新检查直接禁用、不发起任何网络请求。

**为什么代码里还有 `astrbot` 包目录和类名？**
那是插件契约层。全仓库数百个标识符与上千个插件依赖这些名字，字面全替换会让项目跑不起来。产品可见层已全部为 WonderBot，AGPL 只要求保留版权声明并标明修改。

**可以商用或收费吗？**
AGPLv3 允许商业化与收费（部署托管、企业定制、技术支持），但衍生作品必须继续以 AGPL-3.0-or-later 开源，不能改成 MIT / Apache / 闭源，也不能对下游附加「禁止商用」等额外限制。以网络服务形式提供时须依第 13 条主动提供对应源码获取途径。

**「卖闭源授权」可行吗？**
不可行。双授权需全体版权方同意，衍生版做不到。可行收入是部署托管、企业定制、技术支持与培训。

---

## 十、许可证与衍生声明

- 本作品以 **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)** 发布。
- `LICENSE` 为上游 AGPL 全文，原样保留，未作删改；`NOTICE.md` 列明上游来源、原始版权、基线版本与全部修改项。
- 依据 AGPLv3 第 5 条，分发修改版本须保留版权声明、标明修改之处，并以同一许可证发布整个衍生作品。
- 依据 AGPLv3 第 13 条，以网络服务形式提供时，须向使用者主动提供与所运行版本完整对应的源码获取途径；「先上线、以后再开源」在服务上线那一刻即已违约。
- 不得对下游附加额外限制（如「禁止商用」「禁止二次分发」）。
- `EULA.md` 是本衍生版自己的最终用户许可协议，明确不增补、不减损 AGPLv3 授予的权利；两者冲突时以 AGPLv3 为准。
- 「WonderBot」名称与图标为本作品自有标识。对上游名称的引用仅用于说明版权归属与衍生关系，不构成商标授权。

完整声明见 [NOTICE.md](NOTICE.md) 与 [EULA.md](EULA.md)。

---

## 十一、致谢与社区

感谢 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 及所有贡献者提供的优秀开源底座。

- 问题反馈与功能建议：https://github.com/2997669349awa-blip/wonderBot/issues
- 版本下载：https://github.com/2997669349awa-blip/wonderBot/releases
- 官网：https://2997669349awa-blip.github.io/wonderBot/
- 配置文档：[WONDERBOT.md](WONDERBOT.md)
- 上游文档源：`docs/` 目录（VitePress）

---

## 附录：校验与源码构建

### 校验安装包

```bash
sha256sum -c SHA256SUMS
```

`SHA256SUMS` 与安装包一并发在 Release 中。

### 语法校验

```bash
python3.12 -m compileall -q astrbot
```

### 官网本地预览

官网是纯静态站点，无外部依赖，直接打开 `website/index.html` 即可，或：

```bash
cd website && python3 -m http.server 8080
```

### 从源码重新打包

```bash
VERSION=beta0.1.0
zip -qr WonderBot-$VERSION-source.zip WonderBot -x '*.pyc' '*__pycache__*'
tar czf WonderBot-$VERSION-source.tar.gz --exclude='*.pyc' --exclude='__pycache__' WonderBot
```

---

© 2026 WonderBot · AGPL-3.0-or-later · 独立衍生项目，与上游官方无隶属关系
