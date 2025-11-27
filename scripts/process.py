"""SPT 进程检测与管理模块。"""

import os
import subprocess
from typing import Tuple

from .utils import color_text, Colors


# SPT 进程名称常量
SPT_SERVER_PROCESS = "SPT.Server.exe"
SPT_CLIENT_PROCESS = "patched_SPT.Launcher.exe"
SPT_GAME_PROCESS = "EscapeFromTarkov.exe"


def is_process_running(process_name: str) -> bool:
    """检测指定进程是否正在运行（仅 Windows）。"""
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"], # Windows 命令，列出正在运行的进程
            capture_output=True, # 捕获命令行输出到result.stdout
            text=True, # 输出为字符串（而非字节）
            creationflags=subprocess.CREATE_NO_WINDOW # 避免弹出命令行窗口
        )
        return process_name.lower() in result.stdout.lower()
    except Exception:
        return False


def kill_process(process_name: str) -> bool:
    """强制结束指定进程（仅 Windows）。"""
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except Exception:
        return False


def check_spt_processes() -> Tuple[bool, bool, bool]:
    """
    检测 SPT 服务端、客户端和游戏进程是否正在运行。
    
    Returns:
        (server_running, client_running, game_running) 元组
    """
    server_running = is_process_running(SPT_SERVER_PROCESS)
    client_running = is_process_running(SPT_CLIENT_PROCESS)
    game_running = is_process_running(SPT_GAME_PROCESS)
    return server_running, client_running, game_running


def close_spt_processes(confirm: bool = True) -> bool:
    """
    检测并关闭 SPT 服务端、客户端和游戏进程。
    
    Args:
        confirm: 是否需要用户确认后再关闭
    
    Returns:
        True 表示进程已关闭或无需关闭，False 表示用户取消或关闭失败
    """
    server_running, client_running, game_running = check_spt_processes()
    
    if not server_running and not client_running and not game_running:
        return True  # 无进程运行
    
    # 显示检测到的进程
    print(color_text("\n⚠ 检测到以下进程正在运行：", Colors.YELLOW))
    if server_running:
        print(f"  • {SPT_SERVER_PROCESS}")
    if client_running:
        print(f"  • {SPT_CLIENT_PROCESS}")
    if game_running:
        print(f"  • {SPT_GAME_PROCESS}")
    
    if confirm:
        reply = input("\n是否关闭这些进程以继续操作？(y/N): ").strip().lower()
        if reply != "y":
            print("已取消操作。")
            return False
    
    # 关闭进程（先关游戏，再关客户端，最后关服务端）
    success = True
    if game_running:
        print(f"正在关闭 {SPT_GAME_PROCESS}...")
        if kill_process(SPT_GAME_PROCESS):
            print(color_text(f"  ✓ {SPT_GAME_PROCESS} 已关闭", Colors.GREEN))
        else:
            print(color_text(f"  ✗ {SPT_GAME_PROCESS} 关闭失败，请尝试以管理员运行或手动关闭", Colors.RED))
            success = False
    
    if client_running:
        print(f"正在关闭 {SPT_CLIENT_PROCESS}...")
        if kill_process(SPT_CLIENT_PROCESS):
            print(color_text(f"  ✓ {SPT_CLIENT_PROCESS} 已关闭", Colors.GREEN))
        else:
            print(color_text(f"  ✗ {SPT_CLIENT_PROCESS} 关闭失败，请尝试以管理员运行或手动关闭", Colors.RED))
            success = False
    
    if server_running:
        print(f"正在关闭 {SPT_SERVER_PROCESS}...")
        if kill_process(SPT_SERVER_PROCESS):
            print(color_text(f"  ✓ {SPT_SERVER_PROCESS} 已关闭", Colors.GREEN))
        else:
            print(color_text(f"  ✗ {SPT_SERVER_PROCESS} 关闭失败，请尝试以管理员运行或手动关闭", Colors.RED))
            success = False
    
    return success
