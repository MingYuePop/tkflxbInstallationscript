from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from . import config, utils
from .config import ModPackage
from .manifest import load_manifest, record_mod_installation, remove_mod_record

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


def install_mod(state: "InstallerState", mods: List[ModPackage]) -> None:
    """安装内置 MOD：选择 zip 并覆盖到安装目录。"""
    install_path = _require_install_path(state)
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
        print(f"未找到 MOD 压缩包 {mod_zip}")
        return

    if not _confirm(f"即将安装 MOD: {mod.display_name}，并覆盖同名文件，确认吗？"):
        print("已取消。")
        return
    try:
        extracted_files = utils.extract_zip(mod_zip, install_path, strip_common_root=False, show_progress=True)
        record_mod_installation(install_path, mod.display_name, extracted_files)
    except Exception as exc:
        print(f"安装 MOD 失败: {exc}")
        return
    print(f"MOD {mod.display_name} 安装完成。")


def uninstall_mod(state: "InstallerState") -> None:
    """卸载已安装的 MOD：根据标记文件删除 MOD 文件。"""
    install_path = _require_install_path(state)
    if not install_path:
        return

    manifest = load_manifest(install_path)
    if not manifest:
        print("未检测到已安装的游戏。")
        return

    mods = manifest.get("mods", {})
    if not mods:
        print("未找到已安装的 MOD。")
        return

    print("已安装的 MOD：")
    mod_names = list(mods.keys())
    for idx, mod_name in enumerate(mod_names, start=1):
        mod_info = mods[mod_name]
        file_count = len(mod_info.get("files", []))
        print(f"{idx}. {mod_name} ({file_count} 个文件)")

    try:
        selection = int(input("请选择要卸载的 MOD（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return

    if selection == 0:
        print("已取消。")
        return

    if selection < 1 or selection > len(mod_names):
        print("编号不存在。")
        return

    mod_name = mod_names[selection - 1]
    mod_info = mods[mod_name]
    files_to_delete = mod_info.get("files", [])

    if not _confirm(f"确认卸载 MOD: {mod_name}（将删除 {len(files_to_delete)} 个文件）吗？"):
        print("已取消。")
        return

    deleted_count = 0
    skipped_count = 0
    for file_path in files_to_delete:
        full_path = install_path / file_path
        try:
            if full_path.exists():
                full_path.unlink()
                deleted_count += 1
            else:
                skipped_count += 1
        except Exception as exc:
            print(f"删除文件失败 {file_path}: {exc}")
            skipped_count += 1

    # 删除 MOD 的文件夹（如果为空）
    directories = mod_info.get("directories", [])
    deleted_dirs_count = 0
    for dir_path in sorted(directories, reverse=True):  # 从深层目录开始删除
        full_dir_path = install_path / dir_path
        try:
            if full_dir_path.exists() and full_dir_path.is_dir():
                # 检查目录是否为空
                if not any(full_dir_path.iterdir()):
                    full_dir_path.rmdir()
                    deleted_dirs_count += 1
        except Exception as exc:
            # 目录不为空或删除失败，跳过
            pass

    remove_mod_record(install_path, mod_name)

    print(f"MOD {mod_name} 卸载完成。")
    print(f"已删除 {deleted_count} 个文件，跳过 {skipped_count} 个文件。")
    if deleted_dirs_count > 0:
        print(f"已删除 {deleted_dirs_count} 个空文件夹。")
