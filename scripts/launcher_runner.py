import subprocess
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from .installers import InstallerState


def _require_install_path(state: "InstallerState") -> Optional[Path]:
    """确保已选择安装路径。"""
    if not state.install_path:
        print("请先通过选项 1 选择安装路径。")
        return None
    return state.install_path


def launch_game(state: "InstallerState") -> None:
    """启动服务端并延迟启动 Launcher。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return

    server_exe = spt_dir / "SPT.Server.exe"
    launcher_exe = spt_dir / "patched_SPT.Launcher.exe"
    if not server_exe.exists():
        print(f"缺少 {server_exe.name}，请确认安装无误。")
        return
    if not launcher_exe.exists():
        fallback = spt_dir / "SPT.Launcher.exe"
        if fallback.exists():
            launcher_exe = fallback
        else:
            print("缺少 patched_SPT.Launcher.exe，无法启动。")
            return

    creation_flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
    try:
        subprocess.Popen([str(server_exe)], cwd=spt_dir, creationflags=creation_flags)
        print("已启动 SPT.Server.exe，等待 6 秒后启动客户端...")
        time.sleep(6)
        subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
    except Exception as exc:
        print(f"启动失败: {exc}")
        return
    print("客户端已启动。")


def launch_client_only(state: "InstallerState") -> None:
    """仅启动客户端（不启动服务端）。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return

    launcher_exe = spt_dir / "patched_SPT.Launcher.exe"
    if not launcher_exe.exists():
        fallback = spt_dir / "SPT.Launcher.exe"
        if fallback.exists():
            launcher_exe = fallback
        else:
            print("缺少启动器文件，无法启动。")
            return

    creation_flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
    try:
        subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
        print("客户端已启动。")
    except Exception as exc:
        print(f"启动失败: {exc}")
