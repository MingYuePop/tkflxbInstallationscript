import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional

# ANSI 颜色定义，用于菜单/提示高亮
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"


def color_text(text: str, color: str) -> str:
    """根据是否是终端输出决定是否添加颜色。"""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def clear_screen() -> None:
    """清屏，避免多次运行的输出混杂。"""
    os.system("cls" if os.name == "nt" else "clear")


def contains_chinese_root(path: Path) -> bool:
    """仅检查选择路径的最后一级目录名是否包含中文。"""
    return bool(CHINESE_RE.search(path.name))


def is_empty_directory(path: Path) -> bool:
    """判断目录是否为空；不存在的目录视为空。"""
    if not path.exists():
        return True
    if not path.is_dir():
        return False
    return not any(path.iterdir())


def ensure_empty_directory(path: Path) -> Optional[str]:
    """校验目标路径：必须是空文件夹且目录名不含中文；返回错误文本，成功则返回 None。"""
    if path.exists() and not path.is_dir():
        return f"目标路径不是文件夹: {path}"
    if contains_chinese_root(path):
        return f"文件夹名不能包含中文: {path.name}"
    if path.exists() and not is_empty_directory(path):
        return "目标文件夹必须完全为空，请重新选择。"
    path.mkdir(parents=True, exist_ok=True)
    return None


def pick_directory_with_dialog(initial: Optional[Path] = None) -> Optional[Path]:
    """弹出系统目录选择器；失败时降级为手动输入。"""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - GUI fallback
        print(f"无法打开文件夹选择对话框，使用手动输入。原因: {exc}")
        return _manual_path_input()

    root = tk.Tk()
    # 置顶避免对话框被挡在后面
    root.attributes("-topmost", True)
    root.withdraw()
    if initial:
        root.directory = filedialog.askdirectory(initialdir=str(initial))
    else:
        root.directory = filedialog.askdirectory()
    root.update()
    root.destroy()
    if not root.directory:
        return None
    return Path(root.directory)


def _manual_path_input() -> Optional[Path]:
    """命令行手动输入目录路径。"""
    raw = input("请输入安装路径（留空取消）：").strip()
    if not raw:
        return None
    return Path(raw)


def detect_common_root(entries: Iterable[str]) -> Optional[str]:
    """在压缩包条目中探测统一的顶层目录名，便于解压时去掉包裹层。"""
    root_name: Optional[str] = None
    for name in entries:
        parts = PurePosixPath(name).parts
        if not parts:
            continue
        current_root = parts[0]
        if root_name is None:
            root_name = current_root
            continue
        if current_root != root_name:
            return None
    return root_name


def _print_progress(current: int, total: int) -> None:
    """简单文字进度条，按行覆盖显示。"""
    if total == 0:
        return
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = "█" * filled + "-" * (bar_len - filled)
    percent = int(current * 100 / total)
    print(f"\r[{bar}] {percent:3d}% ({current}/{total})", end="", flush=True)


def extract_zip(zip_path: Path, target_dir: Path, strip_common_root: bool = False, show_progress: bool = False) -> None:
    """解压 zip 到目标目录，可选去除统一顶层目录，并显示进度。"""
    with zipfile.ZipFile(zip_path) as archive:
        entries = archive.infolist()
        root_to_strip = detect_common_root(archive.namelist()) if strip_common_root else None
        total = len(entries)
        for idx, info in enumerate(entries, start=1):
            dest_parts = PurePosixPath(info.filename).parts
            if not dest_parts:
                if show_progress:
                    _print_progress(idx, total)
                continue
            if root_to_strip and dest_parts[0] == root_to_strip:
                dest_parts = dest_parts[1:]
            if not dest_parts:
                if show_progress:
                    _print_progress(idx, total)
                continue
            if any(part == ".." for part in dest_parts):
                if show_progress:
                    _print_progress(idx, total)
                continue
            destination = target_dir.joinpath(*dest_parts)
            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as src, destination.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            if show_progress:
                _print_progress(idx, total)
        if show_progress and total:
            print()


def open_in_explorer(path: Path) -> None:
    """在资源管理器中打开指定文件夹。"""
    if os.name != "nt":
        print(f"Explorer 打开跳过（非 Windows 环境）: {path}")
        return
    subprocess.Popen(["explorer", str(path)])