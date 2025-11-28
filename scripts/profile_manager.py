"""存档管理模块：导出和导入用户存档。"""

import json
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import List, Optional, Tuple

from .config import TARGET_SUBDIR
from .installers import InstallerState
from .utils import Colors, color_text


def _get_profiles_dir(state: InstallerState) -> Optional[Path]:
    """获取存档目录路径。"""
    if not state.install_path:
        print(color_text("请先选择安装路径。", Colors.RED))
        return None
    profiles_dir = state.install_path / TARGET_SUBDIR / "user" / "profiles"
    if not profiles_dir.exists():
        print(color_text(f"存档目录不存在: {profiles_dir}", Colors.RED))
        return None
    return profiles_dir


def _get_profile_username(profile_path: Path) -> Optional[str]:
    """从存档文件中提取用户名。"""
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        info = data.get("info", {})
        username = info.get("username")
        return username if username else None
    except Exception:
        return None


def _list_profiles(profiles_dir: Path) -> List[Tuple[Path, str]]:
    """
    列出所有存档文件及其用户名。
    
    Returns:
        List of (profile_path, username) tuples
    """
    profiles = []
    for profile_file in sorted(profiles_dir.glob("*.json")):
        username = _get_profile_username(profile_file)
        if username:
            profiles.append((profile_file, username))
        else:
            # 如果无法获取用户名，使用文件名
            profiles.append((profile_file, profile_file.stem))
    return profiles


def _pick_save_directory(initial: Optional[Path] = None) -> Optional[Path]:
    """弹出目录选择对话框，让用户选择导出路径。"""
    try:
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        if initial:
            selected = filedialog.askdirectory(initialdir=str(initial), title="选择导出路径")
        else:
            selected = filedialog.askdirectory(title="选择导出路径")
        root.update()
        root.destroy()
        if not selected:
            return None
        return Path(selected)
    except Exception as e:
        print(color_text(f"无法打开文件夹选择对话框: {e}", Colors.RED))
        return None


def _pick_file_to_import() -> Optional[Path]:
    """弹出文件选择对话框，让用户选择要导入的存档文件。"""
    try:
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        selected = filedialog.askopenfilename(
            title="选择要导入的存档文件",
            filetypes=[("JSON 存档文件", "*.json"), ("所有文件", "*.*")]
        )
        root.update()
        root.destroy()
        if not selected:
            return None
        return Path(selected)
    except Exception as e:
        print(color_text(f"无法打开文件选择对话框: {e}", Colors.RED))
        return None


def export_profile(state: InstallerState) -> None:
    """导出存档功能。"""
    profiles_dir = _get_profiles_dir(state)
    if not profiles_dir:
        return
    
    profiles = _list_profiles(profiles_dir)
    if not profiles:
        print(color_text("未找到任何存档文件。", Colors.YELLOW))
        return
    
    print("\n====== 可导出的存档 ======")
    for idx, (profile_path, username) in enumerate(profiles, start=1):
        print(color_text(f"{idx}) {username} ({profile_path.name})", Colors.CYAN))
    print(color_text("0) 取消", Colors.RED))
    
    try:
        choice = input("请选择要导出的存档：").strip()
        if choice == "0" or not choice:
            print("已取消。")
            return
        selection = int(choice)
        if selection < 1 or selection > len(profiles):
            print(color_text("无效选项。", Colors.RED))
            return
    except ValueError:
        print(color_text("无效输入。", Colors.RED))
        return
    
    selected_profile, username = profiles[selection - 1]
    
    # 弹出目录选择对话框
    print("请选择导出路径...")
    export_dir = _pick_save_directory()
    if not export_dir:
        print("已取消导出。")
        return
    
    # 复制文件到目标路径
    dest_file = export_dir / selected_profile.name
    try:
        shutil.copy2(selected_profile, dest_file)
        print(color_text(f"存档已导出到: {dest_file}", Colors.GREEN))
    except Exception as e:
        print(color_text(f"导出失败: {e}", Colors.RED))


def import_profile(state: InstallerState) -> None:
    """导入存档功能。"""
    profiles_dir = _get_profiles_dir(state)
    if not profiles_dir:
        # 如果目录不存在，尝试创建
        if state.install_path:
            profiles_dir = state.install_path / TARGET_SUBDIR / "user" / "profiles"
            try:
                profiles_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(color_text(f"无法创建存档目录: {e}", Colors.RED))
                return
        else:
            return
    
    # 弹出文件选择对话框
    print("请选择要导入的存档文件...")
    import_file = _pick_file_to_import()
    if not import_file:
        print("已取消导入。")
        return
    
    if not import_file.exists():
        print(color_text(f"文件不存在: {import_file}", Colors.RED))
        return
    
    # 验证是否为有效的存档文件
    username = _get_profile_username(import_file)
    if username:
        print(color_text(f"检测到存档用户名: {username}", Colors.GREEN))
    else:
        print(color_text("警告: 无法读取存档用户名，文件可能不是有效的存档。", Colors.YELLOW))
        confirm = input("是否继续导入？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消导入。")
            return
    
    # 检查目标文件是否已存在
    dest_file = profiles_dir / import_file.name
    if dest_file.exists():
        print(color_text(f"警告: 存档文件 {import_file.name} 已存在。", Colors.YELLOW))
        confirm = input("是否覆盖？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消导入。")
            return
    
    # 复制文件到存档目录
    try:
        shutil.copy2(import_file, dest_file)
        print(color_text(f"存档已导入到: {dest_file}", Colors.GREEN))
    except Exception as e:
        print(color_text(f"导入失败: {e}", Colors.RED))
