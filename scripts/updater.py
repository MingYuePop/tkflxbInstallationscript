"""版本检查和自动更新功能模块。"""

import subprocess
from typing import Optional

from . import config
from . import utils
from . import announcement


def get_latest_version_info() -> Optional[dict]:
    """
    从公告 JSON 获取最新版本信息。
    
    Returns:
        包含 latest_version 和 download_url 的字典，获取失败返回 None
    """
    ann = announcement.get_announcement()
    if not ann["success"]:
        print(f"无法获取版本信息: {ann['error']}")
        return None
    
    data = ann.get("data", {})
    latest_version = data.get("latest_version")
    download_url = data.get("download_url")
    
    if not latest_version or not download_url:
        print("公告中缺少版本或下载链接信息。")
        return None
    
    return {
        "latest_version": latest_version,
        "download_url": download_url,
    }


def check_update() -> Optional[dict]:
    """
    检查是否有新版本。
    
    Returns:
        如果有新版本，返回 {"has_update": True, "latest_version": "...", "download_url": "..."}
        如果已是最新版本，返回 {"has_update": False, "current_version": "..."}
        获取信息失败返回 None
    """
    version_info = get_latest_version_info()
    if not version_info:
        return None
    
    latest_version = version_info["latest_version"]
    download_url = version_info["download_url"]
    
    # 获取当前软件版本
    current_version = config.SOFTWARE_VERSION
    
    if latest_version > current_version:
        return {
            "has_update": True,
            "latest_version": latest_version,
            "current_version": current_version,
            "download_url": download_url,
        }
    else:
        return {
            "has_update": False,
            "current_version": current_version,
        }


def _confirm(message: str) -> bool:
    """通用二次确认，输入 y 继续。"""
    reply = input(f"{message} (y/N): ").strip().lower()
    return reply == "y"


def auto_update() -> None:
    """
    自动更新流程：检查版本，如有新版本则下载。
    """
    update_info = check_update()
    if not update_info:
        print("无法检查更新，请稍后重试。")
        return
    
    if not update_info["has_update"]:
        print(f"当前已是最新版本（{update_info['current_version']}），无需更新。")
        return
    
    latest_version = update_info["latest_version"]
    download_url = update_info["download_url"]
    
    print(f"发现新版本: {latest_version}")
    print(f"当前版本: {update_info['current_version']}")
    print(f"下载链接: {download_url}")
    
    if not _confirm("是否立即下载更新？"):
        print("已取消更新。")
        return
    
    # # 下载到 BASE_DIR
    # filename = download_url.split("/")[-1]
    # if not filename or filename.endswith("/"):
    #     filename = f"SPT-Installer-{latest_version}.exe"
    
    dest_path = config.BASE_DIR / f"SPT-Installer-{latest_version}.exe"
    
    print(f"正在下载到: {dest_path}")
    if utils.download_file(download_url, dest_path, show_progress=True):
        print(f"下载完成！已保存到: {dest_path}")
        print('请你关闭软件，启动新版本')
        # if _confirm("是否立即运行更新程序？"):
        #     try:
        #         subprocess.Popen([str(dest_path)])
        #         print("已启动更新程序。")
        #     except Exception as exc:
        #         print(f"启动更新程序失败: {exc}")
        #         print(f"请手动运行: {dest_path}")
    else:
        print("下载失败，请检查网络连接。")
