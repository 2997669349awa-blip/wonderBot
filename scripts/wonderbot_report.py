#!/usr/bin/env python3
"""生成 WonderBot 成本审查报表（深黑主题，逐次列出每次调用的费用）。"""

import argparse, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("WONDERBOT_DATA_DIR", str(ROOT / "data"))

from astrbot.core.wonderbot.cost import CostLedger  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200, help="明细条数")
    ap.add_argument("--out", type=str, default="", help="输出 HTML 路径")
    args = ap.parse_args()

    ledger = CostLedger()
    out = Path(args.out) if args.out else ledger.data_dir / "cost-report.html"
    out.write_text(ledger.render_html(limit=args.limit), encoding="utf-8")
    s = ledger.summary()
    print(f"报表: {out}")
    print(
        f"累计 {s['calls']} 次调用, {s['input_tokens']:,} 输入 / "
        f"{s['output_tokens']:,} 输出 token, 合计 ¥{s['total_cny']:.6f}"
    )
    if s["unpriced_calls"]:
        print(
            f"提示: {s['unpriced_calls']} 次调用未匹配到单价，请补充 wonderbot_pricing.json"
        )


if __name__ == "__main__":
    main()
