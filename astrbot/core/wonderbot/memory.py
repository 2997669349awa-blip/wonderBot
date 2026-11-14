"""WonderBot 长期记忆：跨会话保存用户画像、事实与摘要。

与上游的「上下文压缩」互补：上下文压缩解决单次会话不超出窗口，
本模块解决「下一次会话还记得这个人」。使用独立 SQLite 文件，
不改动上游 ORM 与迁移链。

scope 约定：
- ``sender:{platform}:{sender_id}``  按人记忆（跨群、跨会话）
- ``umo:{unified_msg_origin}``        按会话记忆（某个群 / 某个私聊）

写入策略由调用方决定，本模块只提供存储、召回与整理能力。
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    scope        TEXT    NOT NULL,
    kind         TEXT    NOT NULL DEFAULT 'fact',
    content      TEXT    NOT NULL,
    weight       REAL    NOT NULL DEFAULT 1.0,
    source       TEXT    NOT NULL DEFAULT '',
    hit_count    INTEGER NOT NULL DEFAULT 0,
    created_at   REAL    NOT NULL,
    updated_at   REAL    NOT NULL,
    last_access  REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mem_scope  ON memories(scope);
CREATE INDEX IF NOT EXISTS idx_mem_weight ON memories(weight DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_unique
    ON memories(scope, kind, content);
"""

KIND_FACT = "fact"
KIND_PROFILE = "profile"
KIND_SUMMARY = "summary"


def _default_data_dir() -> Path:
    import os

    override = os.environ.get("WONDERBOT_DATA_DIR")
    if override:
        return Path(override).expanduser()
    try:
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        return Path(get_astrbot_data_path())
    except Exception:
        return Path.cwd() / "data"


class MemoryStore:
    """长期记忆存储。线程安全，同步 SQLite。"""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else _default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "wonderbot_memory.db"
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

        # ---- 写入 ----------------------------------------------------------

    def remember(
        self,
        scope: str,
        content: str,
        kind: str = KIND_FACT,
        weight: float = 1.0,
        source: str = "",
    ) -> dict | None:
        """记住一条内容；完全重复的内容只累加权重、不产生重复行。"""
        content = (content or "").strip()
        scope = (scope or "").strip()
        if not content or not scope:
            return None
        now = time.time()
        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id, weight, hit_count FROM memories "
                "WHERE scope=? AND kind=? AND content=?",
                (scope, kind, content),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE memories SET weight=?, updated_at=? WHERE id=?",
                    (min(existing["weight"] + 0.5, 10.0), now, existing["id"]),
                )
                rid = existing["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO memories "
                    "(scope, kind, content, weight, source, created_at, updated_at, last_access) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (scope, kind, content, float(weight), source, now, now, now),
                )
                rid = cur.lastrowid
            row = conn.execute("SELECT * FROM memories WHERE id=?", (rid,)).fetchone()
        return dict(row) if row else None

    def forget(self, memory_id: int) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE id=?", (int(memory_id),))
            return cur.rowcount > 0

    def clear_scope(self, scope: str) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE scope=?", (scope,))
            return cur.rowcount

            # ---- 召回 ----------------------------------------------------------

    def recall(
        self,
        scopes: list[str] | str,
        limit: int = 12,
        min_weight: float = 0.0,
    ) -> list[dict]:
        """按多个 scope 召回记忆；按权重与最近使用排序，并累加命中次数。"""
        if isinstance(scopes, str):
            scopes = [scopes]
        scopes = [s for s in scopes if s]
        if not scopes:
            return []
        marks = ", ".join("?" for _ in scopes)
        now = time.time()
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM memories WHERE scope IN ({marks}) AND weight >= ? "
                "ORDER BY weight DESC, last_access DESC LIMIT ?",
                (*scopes, min_weight, int(limit)),
            ).fetchall()
            if rows:
                ids = [r["id"] for r in rows]
                conn.execute(
                    f"UPDATE memories SET hit_count=hit_count+1, last_access=? "
                    f"WHERE id IN ({', '.join('?' for _ in ids)})",
                    (now, *ids),
                )
        return [dict(r) for r in rows]

    def build_context(self, scopes: list[str] | str, limit: int = 12) -> str:
        """把召回结果整理成可直接注入 system prompt 的文本块。"""
        rows = self.recall(scopes, limit=limit)
        if not rows:
            return ""
        label = {
            KIND_PROFILE: "用户画像",
            KIND_FACT: "已知事实",
            KIND_SUMMARY: "历史摘要",
        }
        lines = [
            "[WonderBot 长期记忆] 以下是关于当前用户/会话的既有信息，请自然参考，不要复述本提示："
        ]
        for r in rows:
            lines.append(f"- ({label.get(r['kind'], '记忆')}) {r['content']}")
        return "\n".join(lines)

    def list_memories(self, scope: str | None = None, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            if scope:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE scope=? "
                    "ORDER BY weight DESC, updated_at DESC LIMIT ?",
                    (scope, int(limit)),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n, COUNT(DISTINCT scope) AS scopes, "
                "COALESCE(SUM(hit_count),0) AS hits FROM memories"
            ).fetchone()
        return dict(row)


_STORE: MemoryStore | None = None


def get_store() -> MemoryStore:
    """进程内单例记忆库。"""
    global _STORE
    if _STORE is None:
        _STORE = MemoryStore()
    return _STORE


def sender_scope(platform: str, sender_id: str) -> str:
    return f"sender:{platform}:{sender_id}"


def umo_scope(umo: str) -> str:
    return f"umo:{umo}"


def recall_context(event: Any) -> str:
    """从消息事件构造 scope 并生成可注入的长期记忆上下文，永不抛异常。"""
    try:
        platform = str(event.get_platform_name() or "")
        sender = str(event.get_sender_id() or "")
        umo = str(getattr(event, "unified_msg_origin", "") or "")
        scopes = [umo_scope(umo)] if umo else []
        if sender:
            scopes.append(sender_scope(platform, sender))
        return get_store().build_context(scopes)
    except Exception:
        return ""


def remember_conversation(event: Any, user_text: str, reply_text: str) -> None:
    """把一轮对话压缩成一条摘要写入记忆，永不抛异常。

    上游已有完整的会话历史管理，这里只保留轻量摘要，避免存储膨胀。
    """
    try:
        u = (user_text or "").strip().replace("\n", " ")
        r = (reply_text or "").strip().replace("\n", " ")
        if not u or len(u) < 4:
            return
        platform = str(event.get_platform_name() or "")
        sender = str(event.get_sender_id() or "")
        umo = str(getattr(event, "unified_msg_origin", "") or "")
        snippet = f"用户曾问：{u[:120]}" + (f"；答复要点：{r[:120]}" if r else "")
        if sender:
            get_store().remember(
                sender_scope(platform, sender),
                snippet,
                kind=KIND_SUMMARY,
                weight=0.6,
                source="conversation",
            )
        if umo:
            get_store().remember(
                umo_scope(umo),
                snippet,
                kind=KIND_SUMMARY,
                weight=0.4,
                source="conversation",
            )
    except Exception:
        return
