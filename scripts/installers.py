import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from . import config
from .config import GameVersion, ModPackage
from . import utils
from .utils import Colors, color_text


class InstallerState:
    """保存当前用户选择的安装路径，便于各功能共享。"""

    def __init__(self) -> None:
        self.install_path: Optional[Path] = None

    def spt_dir(self) -> Optional[Path]:
        """返回安装路径下的 SPT 子目录。"""
        if not self.install_path:
            return None
        return self.install_path / config.TARGET_SUBDIR


def _confirm(message: str) -> bool:
    """通用二次确认，输入 y 继续。"""
    reply = input(f"{message} (y/N): ").strip().lower()
    return reply == "y"


def select_install_path(state: InstallerState) -> None:
    """选取安装目录并校验：必须为空且目录名不含中文。"""
    while True:
        chosen = utils.pick_directory_with_dialog(state.install_path)
        if chosen is None:
            print("已取消选择。")
            return
        error = utils.ensure_empty_directory(chosen)
        if error:
            print(error)
            continue
        state.install_path = chosen
        print(f"安装路径已设置: {chosen}")
        return


def _require_install_path(state: InstallerState, enforce_empty: bool = False) -> Optional[Path]:
    """确保已选择安装路径，必要时再次校验为空。"""
    if not state.install_path:
        print("请先通过选项 1 选择安装路径。")
        return None
    if enforce_empty:
        error = utils.ensure_empty_directory(state.install_path)
        if error:
            print(error)
            return None
    return state.install_path


def _copy_required(target_root: Path) -> None:
    """复制 required 安装必备组件到目标路径。"""
    src = config.REQUIRED_DIR
    dst = target_root / "required"
    if not src.exists():
        print("未找到 resources/required，跳过该步骤。")
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def auto_install(state: InstallerState, versions: List[GameVersion]) -> None:
    """执行自动安装：解压客户端、服务端，并复制 required。"""
    install_path = _require_install_path(state, enforce_empty=True)
    if not install_path:
        return

    if not versions:
        print("没有可用的版本配置。")
        return

    print("可用版本：")
    for idx, version in enumerate(versions, start=1):
        print(f"{idx}. {version.label}")
    try:
        selection = int(input("请选择版本编号（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return
    if selection == 0:
        print("已取消。")
        return
    if selection < 1 or selection > len(versions):
        print("编号不存在。")
        return
    version = versions[selection - 1]

    if not _confirm(f"确认开始安装版本 {version.label} 吗？"):
        print("已取消。")
        return
    if not _confirm("安装过程中请不要关闭软件，是否继续？"):
        print("已取消。")
        return

    client_zip = config.CLIENT_DIR / version.client_zip
    server_zip = config.SERVER_DIR / version.server_zip
    if not client_zip.exists():
        print(f"找不到客户端压缩包: {client_zip}")
        return
    if not server_zip.exists():
        print(f"找不到服务端压缩包: {server_zip}")
        return

    try:
        print("[1/3] 解压客户端文件...")
        utils.extract_zip(client_zip, install_path, strip_common_root=False, show_progress=True)
        print("[2/3] 解压服务端/补丁文件...")
        utils.extract_zip(server_zip, install_path, strip_common_root=True, show_progress=True)
        print("[3/3] 复制 required 必备组件...")
        _copy_required(install_path)
    except Exception as exc:
        print(f"安装失败: {exc}")
        return

    print("安装完成，已将文件解压到:", install_path)
    required_target = install_path / "required"
    if required_target.exists():
        utils.open_in_explorer(required_target)
        print(color_text("请安装所需组件。", Colors.RED))


def install_mod(state: InstallerState, mods: List[ModPackage]) -> None:
    """安装内置 MOD：选择 zip 并覆盖到安装目录。"""
    install_path = _require_install_path(state, enforce_empty=False)
    if not install_path:
        return
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return
    expected_server = spt_dir / "SPT.Server.exe"
    if not expected_server.exists():
        print("未检测到 SPT.Server.exe，可能尚未安装完成。")
        return

    if not mods:
        print("未发现可用的 MOD 包。请将 zip 放入 resources/mods。")
        return

    print("可用 MOD：")
    for idx, mod in enumerate(mods, start=1):
        print(f"{idx}. {mod.display_name}")
    try:
        selection = int(input("请选择要安装的 MOD（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return
    if selection == 0:
        print("已取消。")
        return
    if selection < 1 or selection > len(mods):
        print("编号不存在。")
        return
    mod = mods[selection - 1]
    mod_zip = config.MODS_DIR / mod.zip_name
    if not mod_zip.exists():
        print(f"未找到 MOD 压缩包: {mod_zip}")
        return

    if not _confirm(f"即将安装 MOD: {mod.display_name}，并覆盖同名文件，确认吗？"):
        print("已取消。")
        return
    try:
        utils.extract_zip(mod_zip, install_path, strip_common_root=False, show_progress=True)
    except Exception as exc:
        print(f"安装 MOD 失败: {exc}")
        return
    print(f"MOD {mod.display_name} 安装完成。")


def launch_game(state: InstallerState) -> None:
    """启动服务端并延迟启动 Launcher。"""
    install_path = _require_install_path(state, enforce_empty=False)
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
        print("已启动 SPT.Server.exe，等待 5 秒后启动客户端...")
        time.sleep(5)
        subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
    except Exception as exc:
        print(f"启动失败: {exc}")
        return
    print("客户端已启动。")
