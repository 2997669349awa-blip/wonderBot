#!/usr/bin/env bash
# WonderBot beta0.1.0 一键安装脚本
# 用法: chmod +x install.sh && ./install.sh
set -euo pipefail

APP_NAME="WonderBot"
APP_VERSION="beta0.1.0"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

log()  { printf '[%s] %s\n' "$APP_NAME" "$*"; }
warn() { printf '[%s] 警告: %s\n' "$APP_NAME" "$*" >&2; }
die()  { printf '[%s] 错误: %s\n' "$APP_NAME" "$*" >&2; exit 1; }

log "安装版本 $APP_VERSION"
log "安装目录 $ROOT"

# ---------- 1. 检查 Python ----------
PYTHON=""
for c in python3.12 python3.13 python3.14 python3 python; do
  command -v "$c" >/dev/null 2>&1 || continue
  if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    PYTHON="$(command -v "$c")"
    break
  fi
done
[ -n "$PYTHON" ] || die "未找到 Python 3.12 或更高版本，请先安装后重试"
log "Python: $($PYTHON --version 2>&1)  ($PYTHON)"

# ---------- 2. 虚拟环境 ----------
VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  log "创建虚拟环境 .venv"
  "$PYTHON" -m venv "$VENV" || die "创建虚拟环境失败（请确认已安装 python3-venv）"
else
  log "复用已有虚拟环境 .venv"
fi
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

# ---------- 3. 依赖 ----------
[ -f "$ROOT/requirements.txt" ] || die "缺少 requirements.txt，安装包可能不完整"
log "升级 pip"
"$PIP" install --quiet --upgrade pip || warn "pip 升级失败，继续尝试安装依赖"
log "安装依赖（首次可能需要几分钟）"
if ! "$PIP" install --quiet -r "$ROOT/requirements.txt"; then
  die "依赖安装失败。可尝试国内镜像: $PIP install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
fi
log "依赖安装完成"

# ---------- 4. 数据目录 ----------
mkdir -p "$ROOT/data"
log "数据目录: $ROOT/data"

# ---------- 5. 语法自检 ----------
log "运行 Python 语法自检（compileall）"
if "$PY" -m compileall -q "$ROOT/astrbot" >/dev/null 2>&1; then
  log "语法自检通过"
else
  warn "语法自检发现问题，请人工检查后再启动"
fi
find "$ROOT" -name '*.pyc' -delete 2>/dev/null || true
find "$ROOT" -type d -name '__pycache__' -empty -delete 2>/dev/null || true

# ---------- 6. 脚本权限 ----------
chmod +x "$ROOT/scripts/wonderbot_report.py" 2>/dev/null || true

# ---------- 7. 完成提示 ----------
cat <<EOF

================================================================
[$APP_NAME] $APP_VERSION 安装完成
================================================================

下一步：

  1) 编辑配置文件
     $ROOT/data/cmd_config.json

     在 platform_settings.wonderbot_sender_allowlist.qq_ids
     填入允许的 QQ 号。默认名单为空，即拒绝所有 QQ 命令，
     这是刻意的安全默认值，不填就收不到机器人回复。

  2) 启动
     $PY main.py

  3) 打开 WebUI
     http://127.0.0.1:6185
     在界面里配置消息平台（QQ / 飞书 / 钉钉等）与模型服务。

  4) 成本审查报表
     $PY scripts/wonderbot_report.py

本地数据：
     成本账本   $ROOT/data/wonderbot_cost.db
     记忆库     $ROOT/data/wonderbot_memory.db
     单价表     $ROOT/data/wonderbot_pricing.json（首次运行自动生成）

文档：       $ROOT/WONDERBOT.md
许可证：     AGPL-3.0-or-later（见 LICENSE 与 NOTICE.md）
================================================================
EOF
