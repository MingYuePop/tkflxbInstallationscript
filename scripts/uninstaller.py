"""游戏卸载功能模块。"""

import json
import shutil
from pathlib import Path

from . import config
from .installers import InstallerState, _require_install_path, _PERSIST_FILE, _PERSIST_KEY
from .process import close_spt_processes


def _confirm(message: str) -> bool:
    """通用二次确认，输入 y 继续。"""
    reply = input(f"{message} (y/N): ").strip().lower()
    return reply == "y"


def uninstall_game(state: InstallerState) -> None:
    """卸载游戏：删除当前选择的安装路径下的所有内容。"""
    install_path = _require_install_path(state, enforce_empty=False)
    if not install_path:
        return
    
    if not install_path.exists():
        print(f"安装路径不存在: {install_path}")
        return
    
    # 显示将要删除的内容
    print(f"将要卸载的路径: {install_path}")
    print("警告：此操作将删除该目录下的所有内容，且无法恢复！")
    
    # 二次确认
    if not _confirm("确认要卸载游戏吗？"):
        print("已取消卸载。")
        return
    
    if not _confirm("这是最后一次确认，确定要删除所有文件吗？"):
        print("已取消卸载。")
        return
    
    # 检测并关闭 SPT 进程
    if not close_spt_processes():
        return
    
    try:
        print("正在卸载游戏...")
        shutil.rmtree(install_path)
        print(f"游戏已成功卸载，目录已删除: {install_path}")
        
        # 清除保存的安装路径
        state.install_path = None
        state.loaded_from_cache = False
        try:
            if _PERSIST_FILE.exists():
                data = json.loads(_PERSIST_FILE.read_text(encoding="utf-8"))
                if _PERSIST_KEY in data:
                    del data[_PERSIST_KEY]
                    _PERSIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # 清除保存路径失败不影响卸载结果
            pass
        
    except PermissionError:
        print(f"权限不足，无法删除文件。请确保没有程序正在使用这些文件，或已管理员运行")
    except Exception as exc:
        print(f"卸载失败: {exc}")
