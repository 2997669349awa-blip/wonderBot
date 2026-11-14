"""WonderBot 成本审查：记录每一次大模型调用的 token 用量与费用。

数据来源是上游已有的 ProviderStat 记录（每次 Agent 响应一条），本模块在其
写入时旁路记账，不改动上游 ORM 与迁移链。价格表为可编辑 JSON，默认给出
参考值；未匹配到模型时按 0 计费并在报表中单列，避免虚报成本。

数据库：<data>/wonderbot_cost.db，独立文件，可随时删除重建。
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

# 参考单价，单位：人民币元 / 百万 token。按模型名前缀匹配，越精确越优先。
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "deepseek-chat": {"input": 2.0, "cached_input": 0.5, "output": 8.0},
    "deepseek-reasoner": {"input": 4.0, "cached_input": 1.0, "output": 16.0},
    "gpt-4o-mini": {"input": 1.1, "cached_input": 0.55, "output": 4.4},
    "gpt-4o": {"input": 18.0, "cached_input": 9.0, "output": 72.0},
    "gpt-4.1-mini": {"input": 1.5, "cached_input": 0.4, "output": 6.0},
    "claude-sonnet-4": {"input": 22.0, "cached_input": 2.2, "output": 110.0},
    "claude-haiku": {"input": 6.0, "cached_input": 0.6, "output": 30.0},
    "qwen-plus": {"input": 4.0, "cached_input": 1.0, "output": 12.0},
    "qwen-turbo": {"input": 2.0, "cached_input": 0.5, "output": 6.0},
    "gemini-2.5-flash": {"input": 2.2, "cached_input": 0.55, "output": 8.8},
    "gemini-2.5-pro": {"input": 9.0, "cached_input": 2.25, "output": 36.0},
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cost_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              REAL    NOT NULL,
    umo             TEXT    NOT NULL DEFAULT '',
    sender_id       TEXT    NOT NULL DEFAULT '',
    provider_id     TEXT    NOT NULL DEFAULT '',
    model           TEXT    NOT NULL DEFAULT '',
    input_other     INTEGER NOT NULL DEFAULT 0,
    input_cached    INTEGER NOT NULL DEFAULT 0,
    output          INTEGER NOT NULL DEFAULT 0,
    latency_ms      REAL    NOT NULL DEFAULT 0,
    cost_cny        REAL    NOT NULL DEFAULT 0,
    price_matched   INTEGER NOT NULL DEFAULT 1,
    currency        TEXT    NOT NULL DEFAULT 'CNY'
);
CREATE INDEX IF NOT EXISTS idx_cost_ts    ON cost_records(ts);
CREATE INDEX IF NOT EXISTS idx_cost_model ON cost_records(model);
CREATE INDEX IF NOT EXISTS idx_cost_sender ON cost_records(sender_id);
"""


def _default_data_dir() -> Path:
    """优先用 WonderBot 自己的环境变量，其次回落到上游数据目录。"""
    import os

    override = os.environ.get("WONDERBOT_DATA_DIR")
    if override:
        return Path(override).expanduser()
    try:
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        return Path(get_astrbot_data_path())
    except Exception:
        return Path.cwd() / "data"


class CostLedger:
    """成本账本。线程安全，同步 SQLite，写入耗时在微秒级。"""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else _default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "wonderbot_cost.db"
        self.pricing_path = self.data_dir / "wonderbot_pricing.json"
        self._lock = threading.Lock()
        self._init_db()
        self._init_pricing()

        # ---- 初始化 --------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _init_pricing(self) -> None:
        if not self.pricing_path.exists():
            self.pricing_path.write_text(
                json.dumps(DEFAULT_PRICING, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def load_pricing(self) -> dict[str, dict[str, float]]:
        try:
            data = json.loads(self.pricing_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return dict(DEFAULT_PRICING)

        # ---- 计价 ----------------------------------------------------------

    def price_for(self, model: str) -> dict[str, float] | None:
        """按模型名前缀匹配单价表；未匹配返回 None。"""
        if not model:
            return None
        pricing = self.load_pricing()
        key = model.strip().lower()
        for name in sorted(pricing, key=len, reverse=True):
            if key.startswith(name.lower()) or name.lower() in key:
                p = pricing[name]
                return {
                    "input": float(p.get("input", 0)),
                    "cached_input": float(p.get("cached_input", p.get("input", 0))),
                    "output": float(p.get("output", 0)),
                }
        return None

    def compute(
        self,
        model: str,
        input_other: int,
        input_cached: int,
        output: int,
    ) -> tuple[float, bool, dict[str, float]]:
        """返回 (费用元, 是否匹配到单价, 分项费用)。单位：元 / 百万 token。"""
        price = self.price_for(model)
        if price is None:
            return 0.0, False, {"input": 0.0, "cached": 0.0, "output": 0.0}
        parts = {
            "input": input_other * price["input"] / 1_000_000,
            "cached": input_cached * price["cached_input"] / 1_000_000,
            "output": output * price["output"] / 1_000_000,
        }
        return round(sum(parts.values()), 8), True, parts

        # ---- 记录 ----------------------------------------------------------

    def record(
        self,
        *,
        model: str = "",
        provider_id: str = "",
        umo: str = "",
        sender_id: str = "",
        input_other: int = 0,
        input_cached: int = 0,
        output: int = 0,
        start_time: float = 0.0,
        end_time: float = 0.0,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """写入一条调用成本记录，返回含 cost_cny 的结果字典。"""
        cost, matched, _ = self.compute(model, input_other, input_cached, output)
        latency_ms = (
            max(0.0, (end_time - start_time) * 1000) if end_time > start_time else 0.0
        )
        row = {
            "ts": ts if ts is not None else time.time(),
            "umo": str(umo or ""),
            "sender_id": str(sender_id or ""),
            "provider_id": str(provider_id or ""),
            "model": str(model or ""),
            "input_other": int(input_other or 0),
            "input_cached": int(input_cached or 0),
            "output": int(output or 0),
            "latency_ms": round(latency_ms, 2),
            "cost_cny": cost,
            "price_matched": 1 if matched else 0,
        }
        cols = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                f"INSERT INTO cost_records ({cols}) VALUES ({marks})",
                tuple(row.values()),
            )
            row["id"] = cur.lastrowid
        return row

    def record_from_provider_stat(self, stat: Any, sender_id: str = "") -> dict | None:
        """从上游 ProviderStat 对象旁路记账；任何异常都不影响主流程。"""
        try:
            return self.record(
                model=getattr(stat, "provider_model", "") or "",
                provider_id=getattr(stat, "provider_id", "") or "",
                umo=getattr(stat, "umo", "") or "",
                sender_id=sender_id,
                input_other=getattr(stat, "token_input_other", 0) or 0,
                input_cached=getattr(stat, "token_input_cached", 0) or 0,
                output=getattr(stat, "token_output", 0) or 0,
                start_time=getattr(stat, "start_time", 0.0) or 0.0,
                end_time=getattr(stat, "end_time", 0.0) or 0.0,
            )
        except Exception:
            return None

            # ---- 查询 ----------------------------------------------------------

    def recent(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM cost_records ORDER BY ts DESC, id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]

    def summary(self, since_ts: float | None = None) -> dict:
        since = since_ts if since_ts is not None else 0.0
        with self._connect() as conn:
            total = conn.execute(
                """SELECT COUNT(*) AS n,
                          COALESCE(SUM(input_other + input_cached),0) AS tin,
                          COALESCE(SUM(output),0) AS tout,
                          COALESCE(SUM(cost_cny),0) AS cost,
                          COALESCE(SUM(CASE WHEN price_matched=0 THEN 1 ELSE 0 END),0)
                              AS unpriced
                   FROM cost_records WHERE ts >= ?""",
                (since,),
            ).fetchone()
            by_model = conn.execute(
                """SELECT model, COUNT(*) AS n,
                          COALESCE(SUM(input_other + input_cached),0) AS tin,
                          COALESCE(SUM(output),0) AS tout,
                          ROUND(SUM(cost_cny), 6) AS cost
                   FROM cost_records WHERE ts >= ?
                   GROUP BY model ORDER BY cost DESC""",
                (since,),
            ).fetchall()
            by_sender = conn.execute(
                """SELECT sender_id, COUNT(*) AS n,
                          ROUND(SUM(cost_cny), 6) AS cost
                   FROM cost_records WHERE ts >= ?
                   GROUP BY sender_id ORDER BY cost DESC LIMIT 20""",
                (since,),
            ).fetchall()
        return {
            "calls": total["n"],
            "input_tokens": total["tin"],
            "output_tokens": total["tout"],
            "total_cny": round(total["cost"], 6),
            "unpriced_calls": total["unpriced"],
            "by_model": [dict(r) for r in by_model],
            "by_sender": [dict(r) for r in by_sender],
        }

    def render_html(self, limit: int = 100) -> str:
        """生成深黑主题的成本审查报表，逐条列出每次调用的消耗。"""
        import html
        from datetime import datetime

        s = self.summary()
        rows = self.recent(limit)
        esc = lambda v: html.escape(str(v))
        tr = (
            "\n".join(
                "<tr>"
                f"<td>{datetime.fromtimestamp(r['ts']).strftime('%Y-%m-%d %H:%M:%S')}</td>"
                f"<td>{esc(r['sender_id'] or '-')}</td>"
                f"<td>{esc(r['model'] or '-')}</td>"
                f"<td>{r['input_other']:,}</td><td>{r['input_cached']:,}</td>"
                f"<td>{r['output']:,}</td>"
                f"<td>{r['latency_ms']:,.0f}</td>"
                f"<td class=\"cost\">¥{r['cost_cny']:.6f}</td>"
                f"<td>{'' if r['price_matched'] else '<span class=warn>未配置单价</span>'}</td>"
                "</tr>"
                for r in rows
            )
            or '<tr><td colspan="9" class="empty">暂无记录</td></tr>'
        )
        model_rows = (
            "\n".join(
                f"<tr><td>{esc(m['model'] or '-')}</td><td>{m['n']}</td>"
                f"<td>{m['tin']:,}</td><td>{m['tout']:,}</td>"
                f"<td class=\"cost\">¥{m['cost']:.6f}</td></tr>"
                for m in s["by_model"]
            )
            or '<tr><td colspan="5" class="empty">暂无记录</td></tr>'
        )
        return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>WonderBot 成本审查</title><style>
:root{{color-scheme:dark}}body{{margin:0;padding:32px;background:#08080a;color:#e8e8ec;
font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:16px;margin:32px 0 12px;color:#9aa0aa}}
.sub{{color:#7b808a;margin-bottom:24px}}.cards{{display:flex;gap:14px;flex-wrap:wrap}}
.card{{background:#121216;border:1px solid #26262e;border-radius:12px;padding:16px 22px;min-width:150px}}
.card b{{display:block;font-size:24px;color:#5ee0c8;margin-top:6px}}
.card span{{color:#8b909a;font-size:12px}}
table{{width:100%;border-collapse:collapse;background:#101014;border:1px solid #26262e;border-radius:12px;overflow:hidden}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid #1e1e26;font-size:13px}}
th{{background:#18181e;color:#9aa0aa;font-weight:500}}tr:last-child td{{border-bottom:0}}
.cost{{color:#5ee0c8;font-variant-numeric:tabular-nums}}.warn{{color:#ffb454}}
.empty{{text-align:center;color:#6b707a;padding:28px}}code{{color:#8ab4f8}}
</style></head><body>
<h1>WonderBot · 成本审查</h1>
<div class="sub">逐次记录每次大模型调用的 token 与费用 · 单价表 <code>wonderbot_pricing.json</code> 可自行修改</div>
<div class="cards">
<div class="card"><span>累计调用</span><b>{s['calls']:,}</b></div>
<div class="card"><span>输入 token</span><b>{s['input_tokens']:,}</b></div>
<div class="card"><span>输出 token</span><b>{s['output_tokens']:,}</b></div>
<div class="card"><span>累计费用</span><b>¥{s['total_cny']:.4f}</b></div>
<div class="card"><span>未匹配单价</span><b>{s['unpriced_calls']}</b></div>
</div>
<h2>按模型汇总</h2><table><thead><tr><th>模型</th><th>调用数</th><th>输入</th><th>输出</th><th>费用</th></tr></thead><tbody>{model_rows}</tbody></table>
<h2>逐次调用明细（最近 {limit} 条）</h2><table><thead><tr><th>时间</th><th>用户</th><th>模型</th><th>输入</th><th>缓存命中</th><th>输出</th><th>耗时 ms</th><th>本次费用</th><th>备注</th></tr></thead><tbody>{tr}</tbody></table>
</body></html>"""


_LEDGER: CostLedger | None = None


def get_ledger() -> CostLedger:
    """进程内单例账本。"""
    global _LEDGER
    if _LEDGER is None:
        _LEDGER = CostLedger()
    return _LEDGER


def record_provider_stat(
    stat: Any,
    *,
    sender_id: str = "",
    umo: str = "",
    provider_id: str = "",
    model: str = "",
) -> dict | None:
    """供上游 record_agent_stats 调用的旁路入口。

    ``stat`` 既可以是 AgentRunner.stats.to_dict() 的字典，也可以是
    ProviderStat ORM 对象；任何异常都被吞掉，绝不影响主响应流程。
    """
    try:
        ledger = get_ledger()
        if isinstance(stat, dict):
            usage = stat.get("token_usage", {}) or {}
            return ledger.record(
                model=model or "",
                provider_id=provider_id or "",
                umo=umo or "",
                sender_id=sender_id,
                input_other=int(usage.get("input_other", 0) or 0),
                input_cached=int(usage.get("input_cached", 0) or 0),
                output=int(usage.get("output", 0) or 0),
                start_time=float(stat.get("start_time", 0.0) or 0.0),
                end_time=float(stat.get("end_time", 0.0) or 0.0),
            )
        return ledger.record_from_provider_stat(stat, sender_id=sender_id)
    except Exception:
        return None
