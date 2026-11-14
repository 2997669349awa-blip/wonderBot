"""Centralized WonderBot path helpers.

Project path:
- Fixed to the source tree location.

Root path:
- Defaults to the current working directory.
- Can be overridden with the ``ASTRBOT_ROOT`` environment variable.

Data subdirectories:
- Most runtime data lives under ``<root>/data``.
- A few tool-runtime files intentionally live under the system temporary
  directory as ``.wonderbot``.
"""

import os
import tempfile
from pathlib import Path

from astrbot.core.utils.runtime_env import is_packaged_desktop_runtime


def get_astrbot_path() -> str:
    """Return the WonderBot project source path."""
    return os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../"),
    )


def get_astrbot_root() -> str:
    """Return the WonderBot root directory."""
    if path := (os.environ.get("WONDERBOT_ROOT") or os.environ.get("ASTRBOT_ROOT")):
        return os.path.realpath(path)
    if is_packaged_desktop_runtime():
        return os.path.realpath(os.path.join(os.path.expanduser("~"), ".wonderbot"))
    return os.path.realpath(os.getcwd())


def get_astrbot_data_path() -> str:
    """Return the WonderBot data directory path."""
    return os.path.realpath(os.path.join(get_astrbot_root(), "data"))


def get_astrbot_config_path() -> str:
    """Return the WonderBot config directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "config"))


def get_astrbot_plugin_path() -> str:
    """Return the WonderBot plugin directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "plugins"))


def get_astrbot_builtin_plugin_path() -> str:
    """Return the WonderBot built-in plugin directory path."""
    return os.path.realpath(
        os.path.join(get_astrbot_path(), "astrbot", "builtin_stars")
    )


def get_astrbot_plugin_data_path() -> str:
    """Return the WonderBot plugin data directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "plugin_data"))


def get_astrbot_t2i_templates_path() -> str:
    """Return the WonderBot T2I templates directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "t2i_templates"))


def get_astrbot_webchat_path() -> str:
    """Return the WonderBot WebChat data directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "webchat"))


def get_astrbot_temp_path() -> str:
    """Return the WonderBot temporary data directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "temp"))


def get_astrbot_skills_path() -> str:
    """Return the WonderBot skills directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "skills"))


def get_astrbot_workspaces_path() -> str:
    """Return the WonderBot workspaces directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "workspaces"))


def get_astrbot_system_tmp_path() -> str:
    """Return the shared system temporary directory used by local tools.

    The directory is the ``.wonderbot`` entry of the system temporary
    directory. When the system temporary directory is unusable, Python falls
    back to the current working directory, which is where ``astrbot init``
    leaves the ``.wonderbot`` marker file. In that case a sibling directory is
    used so the marker file is never shadowed by a directory.

    Returns:
        Absolute path of the shared system temporary directory.
    """
    system_tmp = Path(tempfile.gettempdir())
    candidate = system_tmp / ".wonderbot"
    if candidate.is_file():
        candidate = system_tmp / ".wonderbot-tmp"
    return os.path.realpath(str(candidate))


def get_astrbot_site_packages_path() -> str:
    """Return the WonderBot third-party site-packages directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "site-packages"))


def get_astrbot_knowledge_base_path() -> str:
    """Return the WonderBot knowledge base root path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "knowledge_base"))


def get_astrbot_backups_path() -> str:
    """Return the WonderBot backups directory path."""
    return os.path.realpath(os.path.join(get_astrbot_data_path(), "backups"))
