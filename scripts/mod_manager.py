import json
import shutil
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from . import config, utils
from .config import ModPackage, ModVersion
from .manifest import load_manifest, record_mod_installation, remove_mod_record
from .process import close_spt_processes

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


def _extract_mod_version(display_name: str) -> str:
    """从 display_name 中提取 MOD 版本号。
    
    假设格式为 'ModName-1.2.3' 或 'ModName_1.2.3'，
    通过最后一个分隔符分割获取版本号。
    """
    # 尝试用 '-' 分割
    if '-' in display_name:
        parts = display_name.rsplit('-', 1)
        if len(parts) == 2:
            return parts[1]
    # 尝试用 '_' 分割
    if '_' in display_name:
        parts = display_name.rsplit('_', 1)
        if len(parts) == 2:
            return parts[1]
    # 无法提取版本号
    return ""


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
    
    # 检测并关闭 SPT 进程
    if not close_spt_processes():
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
    
    # 提取 MOD 版本号（从 display_name 分割）
    mod_version = _extract_mod_version(mod.display_name)
    
    # 获取当前安装的服务端版本（从标记文件读取）
    manifest = load_manifest(install_path)
    mod_supported_versions = manifest.get("version", "") if manifest else ""
    
    try:
        extracted_files = utils.extract_zip(mod_zip, install_path, strip_common_root=False, show_progress=True)
        # 写入标记文件,传入当前路径和mod名字,和安装 MOD 时返回并记录解压出的文件列表
        record_mod_installation(mod_version, mod_supported_versions, install_path, mod.display_name, extracted_files)
    except Exception as exc:
        print(f"安装 MOD 失败: {exc}")
        return
    print(f"MOD {mod.display_name} 安装完成。")


def uninstall_mod(state: "InstallerState") -> None:
    """卸载已安装的 MOD：根据标记文件删除 MOD 文件。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    # 检测并关闭 SPT 进程
    if not close_spt_processes():
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


def uninstall_all_mods(state: "InstallerState") -> None:
    """一键卸载所有 MOD：删除 mods 目录和 BepInEx/plugins（保留 spt 文件夹）。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    # 检测并关闭 SPT 进程
    if not close_spt_processes():
        return

    # 定义要删除的目录
    mods_dir = install_path / config.TARGET_SUBDIR / "user" / "mods"
    bepinex_plugins_dir = install_path / "BepInEx" / "plugins"

    # 检查是否存在需要删除的内容
    mods_exists = mods_dir.exists()
    plugins_exists = bepinex_plugins_dir.exists()

    if not mods_exists and not plugins_exists:
        print("未检测到已安装的 MOD。")
        return

    # 显示将要删除的内容
    print("\n====== 一键卸载所有 MOD ======")
    print("即将删除以下内容：")
    if mods_exists:
        print(f"  • {mods_dir}")
    if plugins_exists:
        print(f"  • {bepinex_plugins_dir} （除 spt 文件夹外）")
    print("\nSPT 核心文件（spt 文件夹）将保留。")

    if not _confirm("确认删除所有第三方 MOD 吗？"):
        print("已取消。")
        return

    deleted_mods_count = 0
    deleted_plugins_count = 0
    skipped_count = 0

    # 删除 mods 目录
    if mods_exists:
        try:
            shutil.rmtree(mods_dir)
            deleted_mods_count = 1
            print(f"已删除 {mods_dir}")
        except Exception as exc:
            print(f"删除 {mods_dir} 失败: {exc}")
            skipped_count += 1

    # 删除 BepInEx/plugins 下的所有内容（除 spt 文件夹）
    if plugins_exists:
        spt_folder = bepinex_plugins_dir / "spt"
        try:
            for item in bepinex_plugins_dir.iterdir():
                if item.name == "spt":
                    # 保留 spt 文件夹
                    continue
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        deleted_plugins_count += 1
                    else:
                        item.unlink()
                        deleted_plugins_count += 1
                except Exception as exc:
                    print(f"删除 {item} 失败: {exc}")
                    skipped_count += 1
        except Exception as exc:
            print(f"访问 {bepinex_plugins_dir} 失败: {exc}")
            skipped_count += 1

    # 清除 MOD 安装记录
    manifest = load_manifest(install_path)
    if manifest and manifest.get("mods"):
        try:
            manifest["mods"] = {}
            manifest_path = install_path / config.MANIFEST_FILE
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    print("\n====== 卸载完成 ======")
    print(f"已删除 {deleted_mods_count + deleted_plugins_count} 个项目，跳过 {skipped_count} 个项目。")
    if deleted_mods_count > 0:
        print(f"  • 已删除 MOD 目录")
    if deleted_plugins_count > 0:
        print(f"  • 已删除 {deleted_plugins_count} 个 BepInEx 插件")
    print("SPT 环境已恢复到纯净状态。")


def download_mod(state: "InstallerState") -> None:
    """下载指定的 MOD 到 resources/mods 文件夹。"""
    mod_versions = config.discover_mod_versions_from_announcement()
    if not mod_versions:
        print("无法获取 MOD 列表，请检查网络连接。")
        return

    print("\n可用的 MOD：")
    for idx, mod in enumerate(mod_versions, start=1):
        print(f"{idx}. {mod.name}")

    try:
        selection = int(input("请选择要下载的 MOD 编号（0 取消）：").strip() or "0")
    except ValueError:
        print("输入无效。")
        return

    if selection == 0:
        print("已取消。")
        return

    if selection < 1 or selection > len(mod_versions):
        print("编号不存在。")
        return

    selected_mod = mod_versions[selection - 1]

    # 确保 mods 文件夹存在
    config.MODS_DIR.mkdir(parents=True, exist_ok=True)

    mod_zip_path = config.MODS_DIR / selected_mod.zip_name
    if mod_zip_path.exists():
        print(f"MOD {selected_mod.name} 已存在于本地，无需下载。")
        return

    if not _confirm(f"确认下载 MOD {selected_mod.name} 吗？"):
        print("已取消。")
        return

    print(f"正在下载 MOD {selected_mod.name}...")
    success = utils.download_file(selected_mod.download_url, mod_zip_path, show_progress=True)

    if success:
        print(f"MOD {selected_mod.name} 下载完成。")
    else:
        print(f"MOD {selected_mod.name} 下载失败。")
        try:
            mod_zip_path.unlink()
        except Exception:
            pass
