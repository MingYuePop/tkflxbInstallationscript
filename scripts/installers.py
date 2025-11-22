import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import config
from .config import GameVersion, ModPackage
from . import checker
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


def _manifest_path(target_root: Path) -> Path:
    """返回标记文件路径。"""
    return target_root / config.MANIFEST_FILE


def _load_manifest(target_root: Path) -> Optional[dict]:
    """读取标记文件，无法读取时返回 None。"""
    path = _manifest_path(target_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_manifest(target_root: Path, version: GameVersion) -> None:
    """写入标记文件，记录已安装的版本和时间。"""
    path = _manifest_path(target_root)
    payload = {
        "version": version.label,
        "server_zip": version.server_zip,
        "client_zip": version.client_zip,
        "installed_at": datetime.now().isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def select_install_path(state: InstallerState) -> None:
    """选取安装目录并校验：必须为空且目录名不含中文。"""
    while True:
        chosen = utils.pick_directory_with_dialog(state.install_path)
        if chosen is None:
            # 用户关闭对话框，则继续下一轮重新弹出
            print("已取消选择。")
            return

        # 中文名校验
        if utils.contains_chinese_root(chosen):
            print(f"文件夹名不能包含中文: {chosen.name}")
            # 稍作等待，避免对话框关闭瞬间又弹出
            time.sleep(2)
            continue

        manifest = _load_manifest(chosen)
        if manifest:
            # 已有安装标记，直接使用该路径
            state.install_path = chosen
            installed_ver = manifest.get("version", "未知版本")
            print(f"检测到已安装版本: {installed_ver}，已选中目录: {chosen}")
            return

        error = utils.ensure_empty_directory(chosen)
        if error:
            print(error)
            # 稍作等待，避免对话框关闭瞬间又弹出
            time.sleep(2)
            continue
        # 成功则保存状态并返回
        state.install_path = chosen
        
        print(f"安装路径已设置: {chosen}")
        return


def _require_install_path(state: InstallerState, enforce_empty: bool = False) -> Optional[Path]:
    """确保已选择安装路径，必要时再次校验为空。"""
    if not state.install_path:
        print("请先通过选项 1 选择安装路径。")
        return None
    if enforce_empty and not _load_manifest(state.install_path):
        # 只有在不存在标记文件时才要求空目录；有标记视为已安装目录。
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


DOTNET_INSTALLERS = {
    ".NET Runtime 9.0.9": (config.REQUIRED_DIR / ".NET 9.0 Runtime (v9.0.9).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Desktop Runtime 9.0.7": (config.REQUIRED_DIR / ".NET 9.0 Desktop Runtime (v9.0.7).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Desktop Runtime 5.0.0": (config.REQUIRED_DIR / ".NET 5.0 Desktop Runtime (v5.0.0).exe", ["/install", "/quiet", "/norestart"]),
    "ASP.NET Core Runtime 9.0.9": (config.REQUIRED_DIR / "ASP.NET Core 9.0 Runtime (v9.0.9).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Framework 4.7.2": (config.REQUIRED_DIR / ".NET Framework 4.7.2.exe", ["/quiet", "/norestart"]),
}


def _auto_install_dotnet(missing_override: Optional[List[str]] = None, require_confirm: bool = True) -> None:
    """检测并安装缺失的 .NET 组件。"""
    missing = missing_override if missing_override is not None else checker.missing_required_components()
    if not missing:
        print("必要环境已全部安装，无需操作。")
        return

    if require_confirm:
        print("检测到以下组件未安装，将为您自动安装：")
        for name in missing:
            print(f" - {name}")
        choice = input("是否立即自动安装？(Y/n): ").strip().lower()
        if choice not in ("", "y"):
            print("已取消本次自动安装。")
            return

    print("开始安装缺失的 .NET 组件...")
    for name in missing:
        installer_info = DOTNET_INSTALLERS.get(name)
        if not installer_info:
            print(f"未配置安装包：{name}，请手动安装。")
            continue
        installer_path, args = installer_info
        if not installer_path.exists():
            print(f"未找到安装包：{installer_path}，请确认 resources/required 是否完整。")
            continue
        try:
            print(f"正在安装 {name} ...")
            subprocess.run([str(installer_path), *args], check=True)
            print(f"{name} 安装命令已执行完成。")
        except subprocess.CalledProcessError as exc:
            print(f"{name} 安装失败，退出码 {exc.returncode}。")
        except Exception as exc:
            print(f"安装 {name} 时出错：{exc}")


def _manual_install_dotnet() -> None:
    """打开本地安装包目录，便于手动安装。"""
    if not config.REQUIRED_DIR.exists():
        print("未找到 resources/required 目录，请确认安装包是否完整。")
        return
    utils.open_in_explorer(config.REQUIRED_DIR)
    print(f"已打开安装包目录：{config.REQUIRED_DIR}")


def install_dotnet_environment(auto: bool = False, missing_override: Optional[List[str]] = None) -> None:
    """提供 .NET 环境安装子菜单或自动安装流程。"""
    if auto:
        _auto_install_dotnet(missing_override=missing_override, require_confirm=False)
        return
    print("====== 安装必要的 .NET 环境 ======")
    print("1) 自动检测并安装")
    print("2) 手动安装")
    print("0) 返回")
    choice = input("请选择：").strip()
    if choice == "1":
        _auto_install_dotnet()
    elif choice == "2":
        _manual_install_dotnet()
    elif choice == "0":
        print("已取消 .NET 安装操作。")
    else:
        print("无效选项，请重新输入。")


def _post_install_dotnet_flow() -> None:
    """在游戏自动安装后执行 .NET 依赖检查与处理。"""
    missing = checker.missing_required_components()
    if not missing:
        print("必要的 .NET 环境已检测到，无需重复安装。")
        return

    print("检测到以下必要组件未安装，将为您自动安装：")
    for name in missing:
        print(f" • {name}")

    choice = input("是否立即开始安装？(Y/n): ").strip().lower()
    if choice in ("", "y"):
        install_dotnet_environment(auto=True, missing_override=missing)
    else:
        print("已取消本次自动安装，将为您打开安装包所在文件夹以便手动安装。")
        if config.REQUIRED_DIR.exists():
            utils.open_in_explorer(config.REQUIRED_DIR)
        else:
            print("未找到安装包目录，请确认 resources/required 是否存在。")


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

    # 如果目录已有标记文件，则直接提示已安装并跳过重装
    manifest = _load_manifest(install_path)
    if manifest:
        print(f"该目录已安装版本 {manifest.get('version', '未知')}，已跳过自动安装。")
        return

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

    # 安装完成后写入标记
    try:
        _write_manifest(install_path, version)
    except Exception as exc:  # 标记写入失败不影响安装结果
        print(f"写入安装标记失败（可忽略）: {exc}")

    print("安装完成，已将文件解压到:", install_path)
    _post_install_dotnet_flow()


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
        print("已启动 SPT.Server.exe，等待 6 秒后启动客户端...")
        time.sleep(6)
        subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
    except Exception as exc:
        print(f"启动失败: {exc}")
        return
    print("客户端已启动。")
