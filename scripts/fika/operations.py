"""Fika 联机主要操作函数。"""

import shutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .. import config, utils
from ..process import check_spt_processes, close_spt_processes
from ..launcher_runner import launch_game, launch_client_only
from .config_utils import update_json_file, update_cfg_file
from .installer import is_fika_installed, download_and_install_fika

if TYPE_CHECKING:
    from ..installers import InstallerState


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


def start_fika(state: "InstallerState") -> None:
    """启动联机功能。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return
    
    print("\n====== 启动联机 ======")
    
    # 检查是否已安装 Fika
    fika_installed = is_fika_installed(install_path)
    
    if not fika_installed:
        print("正在准备联机环境...")
        # 静默下载并安装 Fika MOD
        success = download_and_install_fika(state, silent=False)
        if not success:
            print("联机功能启动失败。")
            return
        print(utils.color_text("\n✓ Fika MOD 已安装完成！", utils.Colors.GREEN))
    else:
        print(utils.color_text("Fika MOD 已安装。", utils.Colors.GREEN))
    
    print(utils.color_text("\n联机功能已准备就绪。", utils.Colors.GREEN))
    print(utils.color_text("请先登录游戏一次以完成初始化，然后完全退出游戏。", utils.Colors.YELLOW))
    print("接下来请选择：")
    print("  - 创建服务器：作为房主，其他玩家连接到你")
    print("  - 加入服务器：作为客户端，连接到房主")
    
    if _confirm("\n是否现在退出游戏？"):
        # 检查游戏进程
        server_running, client_running, game_running = check_spt_processes()
        if server_running or client_running or game_running:
            if not close_spt_processes(confirm=True):
                print("已取消操作。")
                return
        print("游戏已关闭。")
    else:
        print("请在完成初始化后手动关闭游戏。")


def create_server(state: "InstallerState") -> None:
    """创建服务器（房主模式）。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    # 检查是否已启动联机
    if not is_fika_installed(install_path):
        print(utils.color_text("请先使用'启动联机'功能后再操作", utils.Colors.RED))
        return
    
    print("\n====== 创建服务器 ======")
    print("作为房主，其他玩家将连接到你的服务器。")
    
    # 输入公网IP
    public_ip = input("请输入你的公网IP（其他玩家用于连接）：").strip()
    if not public_ip:
        print("已取消。")
        return
    
    print(f"\n正在配置服务器，公网IP: {public_ip}")
    
    # 获取 SPT 目录
    spt_dir = state.spt_dir()
    
    # 1. 修改 launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not update_json_file(launcher_config, {
        "Server.Url": f"https://{public_ip}:6969"
    }):
        print("配置失败。")
        return
    
    # 2. 修改 com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not update_cfg_file(fika_cfg, "Network", {
        "Force IP": public_ip,
        "Force Bind IP": "Disabled"
    }):
        print("配置失败。")
        return
    
    # 3. 修改 fika.jsonc
    fika_config = spt_dir / "user" / "mods" / "fika-server" / "assets" / "configs" / "fika.jsonc"
    if not fika_config.exists():
        print(utils.color_text("错误: 未找到 fika.jsonc 配置文件，请先启动联机。", utils.Colors.RED))
        return
    
    if not update_json_file(fika_config, {
        "server.SPT.http.ip": "0.0.0.0",
        "server.SPT.http.backendIp": public_ip
    }):
        print("配置失败。")
        return
    
    print(utils.color_text("\n✓ 服务器配置完成！", utils.Colors.GREEN))
    print(utils.color_text(f"\n你的创建者服务器IP是: {public_ip}", utils.Colors.CYAN))
    print(utils.color_text("其他人加入时请提供此IP", utils.Colors.YELLOW))
    
    # 启动游戏
    if _confirm("\n是否现在启动游戏？"):
        launch_game(state)


def join_server(state: "InstallerState") -> None:
    """加入服务器（客户端模式）。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    # 检查是否已启动联机
    if not is_fika_installed(install_path):
        print(utils.color_text("请先启动联机后再加入服务器", utils.Colors.RED))
        return
    
    print("\n====== 加入服务器 ======")
    print("作为客户端，你将连接到房主的服务器。")
    
    # 输入房主IP
    host_ip = input("请输入创建者的服务器IP（房主公网IP）：").strip()
    if not host_ip:
        print("已取消。")
        return
    
    # 输入自己的IP
    my_ip = input("请输入你自己的公网IP（用于Force IP）：").strip()
    if not my_ip:
        print("已取消。")
        return
    
    print(f"\n正在配置客户端，房主IP: {host_ip}, 你的IP: {my_ip}")
    
    # 获取 SPT 目录
    spt_dir = state.spt_dir()
    
    # 1. 修改 launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not update_json_file(launcher_config, {
        "Server.Url": f"https://{host_ip}:6969"
    }):
        print("配置失败。")
        return
    
    # 2. 修改 com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not update_cfg_file(fika_cfg, "Network", {
        "Force IP": my_ip,
        "Force Bind IP": "Disabled"
    }):
        print("配置失败。")
        return
    
    # 3. 修改 fika.jsonc
    fika_config = spt_dir / "user" / "mods" / "fika-server" / "assets" / "configs" / "fika.jsonc"
    if not fika_config.exists():
        print(utils.color_text("错误: 未找到 fika.jsonc 配置文件，请先启动联机。", utils.Colors.RED))
        return
    
    if not update_json_file(fika_config, {
        "server.SPT.http.ip": "0.0.0.0",
        "server.SPT.http.backendIp": "0.0.0.0"
    }):
        print("配置失败。")
        return
    
    print(utils.color_text("\n✓ 客户端配置完成！", utils.Colors.GREEN))
    
    # 仅启动客户端
    if _confirm("\n是否现在启动游戏？"):
        launch_client_only(state)


def close_fika(state: "InstallerState") -> None:
    """关闭联机功能。"""
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    # 检查是否已安装 Fika
    if not is_fika_installed(install_path):
        print("未检测到联机功能。")
        return
    
    print("\n====== 关闭联机 ======")
    
    # 检查游戏是否正在运行
    server_running, client_running, game_running = check_spt_processes()
    if server_running or client_running or game_running:
        print(utils.color_text("检测到游戏正在运行。", utils.Colors.YELLOW))
        if _confirm("请先完全关闭游戏后再关闭联机功能，是否现在关闭游戏？"):
            if not close_spt_processes(confirm=False):
                print("游戏关闭失败，请手动关闭后重试。")
                return
            print("游戏已关闭。")
        else:
            print("请手动关闭游戏后重试。")
            return
    
    if not _confirm("确认关闭联机功能并移除所有联机组件吗？"):
        print("已取消。")
        return
    
    # 删除联机相关文件夹
    fika_server_dir = install_path / config.TARGET_SUBDIR / "user" / "mods" / "fika-server"
    fika_client_dir = install_path / "BepInEx" / "plugins" / "Fika"
    
    deleted_count = 0
    
    if fika_server_dir.exists():
        try:
            shutil.rmtree(fika_server_dir)
            print(f"已删除: {fika_server_dir}")
            deleted_count += 1
        except Exception as exc:
            print(f"删除失败 {fika_server_dir}: {exc}")
    
    if fika_client_dir.exists():
        try:
            shutil.rmtree(fika_client_dir)
            print(f"已删除: {fika_client_dir}")
            deleted_count += 1
        except Exception as exc:
            print(f"删除失败 {fika_client_dir}: {exc}")
    
    # 恢复默认配置
    spt_dir = state.spt_dir()
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    update_json_file(launcher_config, {
        "Server.Url": "https://127.0.0.1:6969"
    })
    
    print(utils.color_text("\n联机功能已关闭，所有联机组件已移除。", utils.Colors.GREEN))
    if deleted_count > 0:
        print(f"已删除 {deleted_count} 个联机组件。")
