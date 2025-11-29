import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from . import config
from .process import check_spt_processes, close_spt_processes

if TYPE_CHECKING:
    from .installers import InstallerState


@dataclass
class ServerLogReader:
    """服务端日志读取器，只读取本次运行新增的日志内容。"""
    log_file: Path
    start_position: int = 0
    
    @classmethod
    def create(cls, spt_dir: Path) -> Optional["ServerLogReader"]:
        """启动服务端前调用，记录当前日志位置。"""
        log_dir = spt_dir / "user" / "logs" / "spt"
        if not log_dir.exists():
            return None
        
        # 找最新日志文件
        log_files = sorted(log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not log_files:
            return None
        
        log_file = log_files[0]
        start_pos = log_file.stat().st_size  # 记录当前文件大小
        return ServerLogReader(log_file, start_pos)
    
    def read_new_lines(self) -> list[str]:
        """只读取本次运行新增的日志。"""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.start_position)
            return [line.rstrip("\n\r") for line in f.readlines()]
    
    def read_new_content(self) -> str:
        """读取本次运行新增的日志（返回完整字符串）。"""
        return "\n".join(self.read_new_lines())
    
    def contains(self, keyword: str) -> bool:
        """检查新日志中是否包含指定关键字。"""
        content = self.read_new_content()
        return keyword in content
    
    def wait_for_keyword(self, keyword: str, timeout: float = 30, interval: float = 0.5) -> bool:
        """等待日志中出现指定关键字。
        
        Args:
            keyword: 要等待的关键字
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
        
        Returns:
            True 如果找到关键字，False 如果超时
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.contains(keyword):
                return True
            time.sleep(interval)
        return False


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
    
    # 检测并关闭已运行的游戏进程
    server_running, client_running, game_running = check_spt_processes()
    if server_running or client_running or game_running:
        if not close_spt_processes(confirm=True):
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

    # 创建日志读取器，记录启动前的日志位置
    state.server_log_reader = ServerLogReader.create(spt_dir)

    creation_flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
    try:
        subprocess.Popen([str(server_exe)], cwd=spt_dir, creationflags=creation_flags)
        print("已启动 SPT.Server.exe，等待服务端就绪...")
        
        # 等待服务端启动完成（检测日志关键字）
        server_ready = False
        if state.server_log_reader:
            server_ready = state.server_log_reader.wait_for_keyword(
                "服务端已开启，游戏愉快", timeout=60, interval=0.5
            )
        
        # 调试：超时时显示读取到的日志内容
        if not server_ready and state.server_log_reader:
            new_lines = state.server_log_reader.read_new_lines()
            if new_lines:
                for line in new_lines[-10:]:
                    print(f"  > {line}")
        
        if server_ready:
            print("服务端已就绪，正在启动客户端...")
            subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
            print("客户端已启动。")
        else:
            print("等待超时，未检测到服务端就绪信号。")
            print("（首次启动可能尚未生成文件，请尝试下方手动启动）\n")
            choice = input("是否手动启动客户端？(y/n): ").strip().lower()
            if choice == "y":
                subprocess.Popen([str(launcher_exe)], cwd=spt_dir, creationflags=creation_flags)
                print("客户端已启动。")
            else:
                print("已取消启动客户端。")
        
    except Exception as exc:
        print(f"启动失败: {exc}")


def launch_client_only(state: "InstallerState") -> None:
    """仅启动客户端（不启动服务端）。"""
    # 先检查是否已安装 Fika MOD
    install_path = _require_install_path(state)
    if not install_path:
        return
    # 获取 SPT 目录
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return
    # 检查启动器文件
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
