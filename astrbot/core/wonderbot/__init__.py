"""WonderBot 能力扩展包。

包含三项独立能力，均使用独立 SQLite 数据库，不侵入上游表结构与迁移链：
- brand    : 品牌与更新源集中配置
- cost     : 每次 LLM 调用的成本审查
- memory   : 跨会话长期记忆
"""

from . import brand

__all__ = ["brand"]
