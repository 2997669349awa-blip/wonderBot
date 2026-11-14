"""WonderBot 品牌与更新源集中配置。

所有对外可见的名称、链接、更新地址都只在本文件定义。
更换自己的官方仓库 / 域名 / 发布服务时，改这里或设置对应环境变量即可，
不需要全仓库搜索替换。

安全默认值：RELEASE_API 为空时更新检查被完全禁用，不会向任何上游
（包括 WonderBot 官方）发起版本探测请求。
"""

from __future__ import annotations

import os
from typing import Final

BRAND_NAME: Final[str] = "WonderBot"
BRAND_NAME_CN: Final[str] = "WonderBot 智能助手"
ORGANIZATION: Final[str] = "2997669349awa-blip"
PRODUCT_SUFFIX: Final[str] = "WonderBot for Ops"


def _env(key: str, default: str) -> str:
    """读取环境变量；空字符串一律回落到默认值（除非默认本身为空）。"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip() or default

    # ---- 对外身份 ----------------------------------------------------------


REPO_URL: Final[str] = _env(
    "WONDERBOT_REPO_URL", "https://github.com/2997669349awa-blip/wonderBot"
)
WEBSITE_URL: Final[str] = _env("WONDERBOT_WEBSITE_URL", "https://2997669349awa-blip.github.io/wonderBot")
DOCS_URL: Final[str] = _env("WONDERBOT_DOCS_URL", "https://github.com/2997669349awa-blip/wonderBot/tree/main/docs")
CONTACT_EMAIL: Final[str] = _env("WONDERBOT_CONTACT_EMAIL", "team@wonderbot.dev")
NOTICE_URL: Final[str] = _env("WONDERBOT_NOTICE_URL", f"{WEBSITE_URL}/notice.json")

# ---- 更新源（全部默认关闭，绝不回退到上游官方源）------------------------
RELEASE_API: Final[str] = os.environ.get("WONDERBOT_RELEASE_API", "").strip()
CORE_PACKAGE_BASE_URL: Final[str] = os.environ.get(
    "WONDERBOT_CORE_PACKAGE_BASE_URL", ""
).strip()
DASHBOARD_PACKAGE_BASE_URL: Final[str] = os.environ.get(
    "WONDERBOT_DASHBOARD_PACKAGE_BASE_URL", ""
).strip()
DASHBOARD_RELEASE_FALLBACK: Final[str] = os.environ.get(
    "WONDERBOT_DASHBOARD_RELEASE_FALLBACK", ""
).strip()


def updates_enabled() -> bool:
    """是否允许检查更新。默认为 False，避免检测到上游官方版本。"""
    return bool(RELEASE_API)


def require_release_api() -> str:
    """返回发布源；未配置时抛出明确错误，绝不静默回退。"""
    if not RELEASE_API:
        raise RuntimeError(
            "WonderBot 更新源未配置。请设置 WONDERBOT_RELEASE_API 指向你自己的"
            "发布服务后再检查更新；本项目不会连接上游官方更新服务。"
        )
    return RELEASE_API


def core_package_url(version: str) -> str | None:
    """按版本构造自己的核心更新包地址；未配置发布源时返回 None。"""
    if not CORE_PACKAGE_BASE_URL or not version.startswith("v"):
        return None
    return f"{CORE_PACKAGE_BASE_URL.rstrip('/')}/{version}/source.zip"


def dashboard_package_url(version: str) -> str | None:
    """按版本构造自己的 WebUI 更新包地址；未配置发布源时返回 None。"""
    if not DASHBOARD_PACKAGE_BASE_URL:
        return None
    return f"{DASHBOARD_PACKAGE_BASE_URL.rstrip('/')}/{version}/dist.zip"


__all__ = [
    "BRAND_NAME",
    "BRAND_NAME_CN",
    "ORGANIZATION",
    "PRODUCT_SUFFIX",
    "REPO_URL",
    "WEBSITE_URL",
    "DOCS_URL",
    "CONTACT_EMAIL",
    "NOTICE_URL",
    "RELEASE_API",
    "CORE_PACKAGE_BASE_URL",
    "DASHBOARD_PACKAGE_BASE_URL",
    "DASHBOARD_RELEASE_FALLBACK",
    "updates_enabled",
    "require_release_api",
    "core_package_url",
    "dashboard_package_url",
]
