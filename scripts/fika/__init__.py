"""Fika 联机功能模块。

提供 Fika 联机功能的安装、配置和管理。
"""

from .installer import is_fika_installed
from .operations import (
    be_host,
    join_host,
    restore_solo,
    get_fika_status,
    # 兼容旧接口
    start_fika,
    create_server,
    join_server,
    close_fika,
)

__all__ = [
    "is_fika_installed",
    "be_host",
    "join_host",
    "restore_solo",
    "get_fika_status",
    # 兼容旧接口
    "start_fika",
    "create_server",
    "join_server",
    "close_fika",
]
