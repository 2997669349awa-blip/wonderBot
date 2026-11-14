"""WonderBot 发送者白名单：拒绝执行白名单之外任何 QQ 用户的命令。

与上游 WhitelistCheckStage 的区别：
- 上游按「会话 ID / 群 ID」过滤，管的是「在哪些会话里响应」；
- 本阶段按「发送者 QQ 号」过滤，管的是「谁有资格下命令」。

放在 ProcessStage 之前，非白名单用户的事件在进入插件与大模型调用前
就被终止，因此不会产生任何 token 消耗。
"""

from collections.abc import AsyncGenerator

from astrbot.core import logger
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from ..context import PipelineContext
from ..stage import Stage, register_stage

# QQ 生态常见的平台标识（aiocqhttp = OneBot 协议，qqofficial = 官方平台）
DEFAULT_QQ_PLATFORMS = ("aiocqhttp", "qqofficial", "onebot", "qq")


@register_stage
class SenderAllowlistStage(Stage):
    """仅放行白名单内的 QQ 用户；其余发送者的事件一律终止。"""

    async def initialize(self, ctx: PipelineContext) -> None:
        settings = ctx.astrbot_config.get("platform_settings", {}) or {}
        cfg = settings.get("wonderbot_sender_allowlist", {}) or {}

        self.enabled = bool(cfg.get("enabled", True))
        self.allowed_ids = {
            str(i).strip() for i in cfg.get("qq_ids", []) if str(i).strip()
        }
        self.platforms = tuple(
            str(p).strip().lower()
            for p in cfg.get("platforms", DEFAULT_QQ_PLATFORMS)
            if str(p).strip()
        )
        # True 时仅拦截命令/唤醒类消息，普通闲聊仍可响应
        self.only_commands = bool(cfg.get("only_commands", False))
        self.log_rejected = bool(cfg.get("log_rejected", True))
        self.allow_webchat = bool(cfg.get("allow_webchat", True))

        if self.enabled and not self.allowed_ids:
            logger.warning(
                "WonderBot 发送者白名单已启用但 qq_ids 为空："
                "所有 QQ 用户的命令都会被拒绝。请在 配置文件 -> 访问控制 "
                "-> WonderBot 发送者白名单 中填入允许的 QQ 号。"
            )

    def _is_qq_platform(self, platform: str) -> bool:
        return any(platform == p or platform.startswith(p) for p in self.platforms)

    async def process(
        self,
        event: AstrMessageEvent,
    ) -> None | AsyncGenerator[None, None]:
        if not self.enabled:
            return

        platform = str(event.get_platform_name() or "").strip().lower()

        # WebChat 是本地管理会话，默认不受 QQ 白名单约束
        if platform == "webchat" and self.allow_webchat:
            return
        if not self._is_qq_platform(platform):
            return

        sender_id = str(event.get_sender_id() or "").strip()
        if sender_id and sender_id in self.allowed_ids:
            return

            # 仅命令模式：普通闲聊放行，只拦截唤醒/指令类消息
        if self.only_commands and not (
            getattr(event, "is_at_or_wake_command", False)
            or getattr(event, "call_llm", False)
        ):
            return

        if self.log_rejected:
            logger.info(
                "WonderBot 拒绝执行：QQ 用户 %s（平台 %s）不在发送者白名单中，"
                "事件已在调用大模型前终止。",
                sender_id or "未知",
                platform,
            )
        event.stop_event()
