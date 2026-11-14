# WonderBot beta0.1.0 安装说明

本文件随源码安装包一并提供。更完整的项目介绍见 [README.md](README.md)，配置细节见 [WONDERBOT.md](WONDERBOT.md)。

## 1. 环境要求

| 项 | 要求 |
|---|---|
| Python | 3.12 或更高（推荐 3.12 / 3.13） |
| 操作系统 | Linux / macOS / Windows（WSL） |
| 磁盘 | 建议 2 GB 以上可用空间 |
| 网络 | 安装依赖时需要访问 PyPI；运行时的模型与消息平台按所选服务而定 |
| 可选 | Docker 与 Docker Compose（容器部署时）；Node / pnpm（仅重新构建 WebUI 时） |

## 2. 获取安装包

从官方 Release 页下载，两种归档内容一致：

- `WonderBot-beta0.1.0-source.zip`
- `WonderBot-beta0.1.0-source.tar.gz`

地址：https://github.com/2997669349awa-blip/wonderBot/releases/tag/beta0.1.0

下载安装包与 Release 同页的 `SHA256SUMS` 校验文件到同一目录后校验完整性：

```bash
sha256sum -c SHA256SUMS
```

解压：

```bash
unzip WonderBot-beta0.1.0-source.zip && cd WonderBot-beta0.1.0
# 或
tar xzf WonderBot-beta0.1.0-source.tar.gz && cd WonderBot-beta0.1.0
```

## 3. 一键安装

```bash
chmod +x install.sh
./install.sh
```

脚本依次完成：检查 Python 版本 → 创建 `.venv` → 升级 pip → 安装 `requirements.txt` → 创建 `data/` → 运行 `compileall` 语法自检 → 打印后续步骤。

如果依赖下载缓慢，可手动指定镜像：

```bash
.venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 4. 手动安装

```bash
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
mkdir -p data
.venv/bin/python main.py
```

> 不建议直接 `pip install .`：`pyproject.toml` 带自定义 hatchling 构建钩子，安装时会尝试构建 Vue 仪表盘（需要 Node / pnpm）。使用 `requirements.txt` + 直接运行 `main.py` 不需要前端构建链。

## 5. 首次配置（必做）

编辑 `data/cmd_config.json`，在 `platform_settings` 下加入白名单：

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

**默认 `qq_ids` 为空数组 = 拒绝所有 QQ 用户命令**，这是刻意的安全默认值。填入自己的 QQ 号后生效，被拒绝的事件不会进入大模型，不产生 token 消耗。

然后在 WebUI（默认 `http://127.0.0.1:6185`）配置消息平台与模型服务。

## 6. 验证安装

```bash
# 语法自检
.venv/bin/python -m compileall -q astrbot

# 品牌与更新源常量
.venv/bin/python -c "from astrbot.core.wonderbot import brand; print(brand.REPO_URL); print('更新检查启用:', brand.updates_enabled())"
# 期望输出官方仓库地址，以及「更新检查启用: False」

# 生成一次成本审查报表（无数据时也会生成空报表）
.venv/bin/python scripts/wonderbot_report.py
```

## 7. 故障排查

| 现象 | 原因与处理 |
|---|---|
| `未找到 Python 3.12+` | 安装 Python 3.12 或更高版本；确认 `python3.12` 在 PATH 中 |
| 创建虚拟环境失败 | 安装 `python3.12-venv`（Debian/Ubuntu）或对应包 |
| 依赖安装失败 | 换国内 PyPI 镜像；检查网络与磁盘空间 |
| QQ 命令无响应 | 检查 `qq_ids` 是否已填；确认 `enabled` 为 true；查看拒绝日志 |
| WebUI 打不开 | 确认进程已监听 6185 端口；检查防火墙与容器端口映射 |
| 成本报表无数据 | 账本在首次真实大模型调用后才写入；`cost-report-demo.html` 是演示数据 |
| 沙盒功能不可用 | 沙盒镜像为占位名，需要自行构建推送；不使用沙盒不影响主程序 |

## 8. 目录说明

```
main.py                       程序入口
requirements.txt              依赖清单
install.sh                    一键安装脚本
WONDERBOT.md                  完整配置文档
NOTICE.md                     版权与衍生声明
EULA.md                       最终用户许可协议
VERSION                       产品版本号
astrbot/core/wonderbot/       新增能力模块（品牌 / 成本 / 记忆）
website/                      官网静态源码
dashboard/                    WebUI 前端源码
data/                         运行时数据（安装后生成）
```

## 9. 卸载

```bash
rm -rf .venv        # 虚拟环境
# data/ 目录含成本账本与记忆，按需自行备份或删除
```

## 10. 许可证

AGPL-3.0-or-later。`LICENSE` 为上游 AGPL 全文（原样保留），`NOTICE.md` 列明上游来源、原始版权与修改清单。以网络服务形式对外提供时，须依 AGPLv3 第 13 条主动向使用者提供对应源码的获取途径。
