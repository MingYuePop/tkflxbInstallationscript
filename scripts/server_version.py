from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from . import config, utils
from .manifest import load_manifest, update_manifest_server_version

if TYPE_CHECKING:
    from .installers import InstallerState


def _confirm(message: str) -> bool:
    """通用二次确认，输入 y 继续。"""
    reply = input(f"{message} (y/N): ").strip().lower()
    return reply == "y"


def _require_install_path(state: "InstallerState") -> Optional[Path]:
    """确保已选择安装路径。"""
    if not state.install_path:
        print("请先通过选项 1 选择安装路径。")
        return None
    return state.install_path


def download_server_version(state: "InstallerState") -> None:
    """下载指定的服务端版本到 server 文件夹。"""
    install_path = _require_install_path(state)
    if not install_path:
        return

    manifest = load_manifest(install_path)
    if not manifest:
        print("未检测到已安装的游戏，请先完成自动安装。")
        return

    server_versions = config.discover_server_versions_from_announcement()
    if not server_versions:
        print("无法获取服务端版本列表，请检查网络连接。")
        return

    print("\n可用的服务端版本：")
    for idx, sv in enumerate(server_versions, start=1):
        print(f"{idx}. {sv.version}")

    try:
        selection = int(input("请选择要下载的版本编号（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return

    if selection == 0:
        print("已取消。")
        return

    if selection < 1 or selection > len(server_versions):
        print("编号不存在。")
        return

    selected_version = server_versions[selection - 1]

    server_zip_path = config.SERVER_DIR / selected_version.server_zip
    if server_zip_path.exists():
        print(f"版本 {selected_version.version} 已存在于本地，无需下载。")
        return

    if not _confirm(f"确认下载版本 {selected_version.version} 吗？"):
        print("已取消。")
        return

    print(f"正在下载服务端版本 {selected_version.version}...")
    success = utils.download_file(selected_version.download_url, server_zip_path, show_progress=True)

    if success:
        print(f"版本 {selected_version.version} 下载完成。")
    else:
        print(f"版本 {selected_version.version} 下载失败。")
        try:
            server_zip_path.unlink()
        except Exception:
            pass


def switch_server_version(state: "InstallerState") -> None:
    """切换服务端版本。"""
    install_path = _require_install_path(state)
    if not install_path:
        return

    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return

    manifest = load_manifest(install_path)
    if not manifest:
        print("未检测到已安装的游戏。")
        return

    current_version = manifest.get("version", "未知")
    current_server_zip = manifest.get("server_zip", "")
    print(f"当前服务端版本：{current_version}")

    available_zips: List[Path] = list(config.SERVER_DIR.glob("*.zip"))
    if not available_zips:
        print("未找到任何服务端版本文件，请先下载。")
        return

    print("\n可用的本地服务端版本：")
    sorted_zips = sorted(available_zips)
    for idx, zip_file in enumerate(sorted_zips, start=1):
        print(f"{idx}. {zip_file.stem}")

    try:
        selection = int(input("请选择要切换的版本编号（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return

    if selection == 0:
        print("已取消。")
        return

    if selection < 1 or selection > len(sorted_zips):
        print("编号不存在。")
        return

    selected_zip = sorted_zips[selection - 1]
    if selected_zip.name == current_server_zip:
        print(f"已经是版本 {current_version}，无需切换。")
        return

    new_version = selected_zip.stem
    if not _confirm(f"确认切换到版本 {new_version} 吗？"):
        print("已取消。")
        return

    print(f"正在切换到版本 {new_version}...")
    try:
        utils.extract_zip(selected_zip, install_path, strip_common_root=True, show_progress=True)
        update_manifest_server_version(install_path, new_version, selected_zip.name)
        print(f"成功切换到版本 {new_version}。")
    except PermissionError:
        print("\n切换版本失败。")
        print("可能原因：游戏服务端仍在运行。")
        print("解决方案：请关闭 SPT.Server.exe 后再试。")
    except Exception as exc:
        print(f"切换版本失败: {exc}")
