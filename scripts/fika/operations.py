"""Fika 联机主要操作函数 - 简化版。

提供一键式联机流程：
- 我是房主：自动安装 Fika + 配置 + 启动游戏
- 我要加入：自动安装 Fika + 配置 + 启动客户端
- 恢复单机：重置配置，可选卸载 Fika
"""

import shutil
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

from .. import config, utils
from ..process import check_spt_processes, close_spt_processes
from ..launcher_runner import launch_game, launch_client_only
from ..manifest import get_fika_config, save_fika_config, clear_fika_config
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


def _ensure_fika_installed(state: "InstallerState") -> bool:
    """确保 Fika 已安装，未安装则自动安装。返回是否成功。"""
    install_path = state.install_path
    if is_fika_installed(install_path):
        return True
    
    print("正在准备联机环境...")
    success = download_and_install_fika(state, silent=False)
    if success:
        print(utils.color_text("✓ Fika MOD 安装完成", utils.Colors.GREEN))
    return success


def _close_running_game() -> bool:
    """检测并关闭运行中的游戏。返回是否可以继续。"""
    server_running, client_running, game_running = check_spt_processes()
    if server_running or client_running or game_running:
        return close_spt_processes(confirm=True)
    return True


def _input_ip_with_memory(prompt: str, last_value: str) -> Optional[str]:
    """带记忆功能的 IP 输入。返回 None 表示取消。"""
    if last_value:
        hint = f"（上次: {last_value}，直接回车使用）"
        user_input = input(f"{prompt}{hint}：").strip()
        if not user_input:
            return last_value
        return user_input
    else:
        user_input = input(f"{prompt}：").strip()
        if not user_input:
            print("已取消。")
            return None
        return user_input


def _check_fika_cfg_initialized(state: "InstallerState") -> bool:
    """检测 Fika 配置文件是否已初始化。
    
    Fika 需要用户登录游戏一次才会生成 com.fika.core.cfg 文件。
    如果文件不存在，提示用户先登录游戏完成初始化。
    
    Returns:
        True 如果文件存在或用户选择继续，False 如果用户取消
    """
    fika_cfg = state.install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    
    if fika_cfg.exists():
        return True
    
    # 文件不存在，提示用户
    print(utils.color_text("\n⚠ 未检测到 Fika 配置文件", utils.Colors.YELLOW))
    print("Fika 需要先登录游戏一次才能生成配置文件。")
    print("请启动游戏，登录到角色选择界面，然后退出游戏再来配置联机。\n")
    
    print("请选择操作：")
    print("  1) 启动游戏进行初始化")
    print("  0) 返回上级菜单")
    
    choice = input("\n请选择: ").strip()
    
    if choice == "1":
        print("\n启动游戏中，请登录到角色选择界面后退出游戏...")
        launch_game(state)
        print(utils.color_text("\n完成初始化后，请重新选择 '创建服务器' 或 '加入服务器'。", utils.Colors.CYAN))
        return False
    else:
        print("已取消。")
        return False


def get_fika_status(state: "InstallerState") -> Tuple[bool, Optional[str], str]:
    """获取 Fika 状态信息。
    
    Returns:
        (is_installed, mode, status_text)
        - is_installed: 是否已安装 Fika
        - mode: "host" | "client" | None
        - status_text: 状态描述文本
    """
    if not state.install_path:
        return False, None, "未选择安装路径"
    
    installed = is_fika_installed(state.install_path)
    if not installed:
        return False, None, "未安装联机组件,创建或加入会自动安装"
    
    # 读取配置
    fika_cfg = get_fika_config(state.install_path)
    if not fika_cfg:
        return True, None, "已安装，未配置"
    
    mode = fika_cfg.get("mode")
    host_ip = fika_cfg.get("host_ip", "")
    my_ip = fika_cfg.get("my_ip", "")
    
    if mode == "host":
        return True, "host", f"房主模式 (IP: {host_ip})"
    elif mode == "client":
        return True, "client", f"加入模式 (房主: {host_ip} 自己：{my_ip})"
    else:
        return True, None, "已安装，未配置"


def be_host(state: "InstallerState") -> None:
    """我是房主 - 一键创建服务器。
    
    流程：检查安装 → 输入IP → 配置 → 启动游戏
    """
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return
    
    # 关闭运行中的游戏
    if not _close_running_game():
        return
    
    print("\n" + "=" * 40)
    print(utils.color_text("  我是房主 - 创建服务器", utils.Colors.CYAN))
    print("=" * 40)
    print("其他玩家将连接到你的服务器。\n")
    
    # 1. 确保 Fika 已安装
    if not _ensure_fika_installed(state):
        print(utils.color_text("联机组件安装失败。", utils.Colors.RED))
        return
    
    # 2. 检测 Fika 配置文件是否已初始化
    if not _check_fika_cfg_initialized(state):
        return
    
    # 3. 获取上次配置
    last_cfg = get_fika_config(install_path) or {}
    last_ip = last_cfg.get("host_ip", "")
    
    # 4. 输入公网 IP
    public_ip = _input_ip_with_memory("请输入你的公网IP", last_ip)
    if not public_ip:
        return
    
    print(f"\n正在配置服务器...")
    
    # 5. 配置文件
    # launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not update_json_file(launcher_config, {
        "IsDevMode": "true",
        "Server.Url": f"https://127.0.0.1:6969"
    }):
        print(utils.color_text("配置失败。", utils.Colors.RED))
        return
    
    # com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not update_cfg_file(fika_cfg, "Network", {
        "Force IP": public_ip,
        "Force Bind IP": "0.0.0.0"
    }):
        print(utils.color_text("配置失败。", utils.Colors.RED))
        return
    
    # http.json
    http_config = spt_dir / "SPT_Data" / "configs" / "http.json"
    if http_config.exists():
        if not update_json_file(http_config, {
            "ip": "0.0.0.0",
            "backendIp": public_ip
        }):
            print(utils.color_text("配置失败。", utils.Colors.RED))
            return
    
    # 6. 保存配置
    save_fika_config(install_path, mode="host", host_ip=public_ip)
    
    print(utils.color_text("\n✓ 服务器配置完成！", utils.Colors.GREEN))
    print(utils.color_text(f"\n你的服务器IP: {public_ip}", utils.Colors.CYAN))
    print(utils.color_text("请将此IP告诉要加入的玩家", utils.Colors.YELLOW))
    
    # 7. 启动游戏
    if _confirm("\n是否现在启动游戏？"):
        launch_game(state)


def join_host(state: "InstallerState") -> None:
    """我要加入 - 一键连接房主服务器。
    
    流程：检查安装 → 输入房主IP → 输入自己IP → 配置 → 启动客户端
    """
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print(f"未找到 {config.TARGET_SUBDIR} 文件夹，请先完成自动安装。")
        return
    
    # 关闭运行中的游戏
    if not _close_running_game():
        return
    
    print("\n" + "=" * 40)
    print(utils.color_text("  我要加入 - 连接房主", utils.Colors.CYAN))
    print("=" * 40)
    print("你将作为客户端连接到房主的服务器。\n")
    
    # 1. 确保 Fika 已安装
    if not _ensure_fika_installed(state):
        print(utils.color_text("联机组件安装失败。", utils.Colors.RED))
        return
    
    # 2. 检测 Fika 配置文件是否已初始化
    if not _check_fika_cfg_initialized(state):
        return
    
    # 3. 获取上次配置
    last_cfg = get_fika_config(install_path) or {}
    last_host_ip = last_cfg.get("host_ip", "")
    last_my_ip = last_cfg.get("my_ip", "")
    
    # 4. 输入房主 IP
    host_ip = _input_ip_with_memory("请输入房主的服务器IP", last_host_ip)
    if not host_ip:
        return
    
    # 5. 输入自己的 IP
    my_ip = _input_ip_with_memory("请输入你自己的公网IP", last_my_ip)
    if not my_ip:
        return
    
    print(f"\n正在配置客户端...")
    
    # 6. 配置文件
    # launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not update_json_file(launcher_config, {
        "IsDevMode": "true",
        "Server.Url": f"https://{host_ip}:6969"
    }):
        print(utils.color_text("配置失败。", utils.Colors.RED))
        return
    
    # com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not update_cfg_file(fika_cfg, "Network", {
        "Force IP": my_ip,
        "Force Bind IP": "0.0.0.0"
    }):
        print(utils.color_text("配置失败。", utils.Colors.RED))
        return
    
    # http.json
    http_config = spt_dir / "SPT_Data" / "configs" / "http.json"
    if http_config.exists():
        if not update_json_file(http_config, {
            "ip": "0.0.0.0",
            "backendIp": "0.0.0.0"
        }):
            print(utils.color_text("配置失败。", utils.Colors.RED))
            return
    
    # 7. 保存配置
    save_fika_config(install_path, mode="client", host_ip=host_ip, my_ip=my_ip)
    
    print(utils.color_text("\n✓ 客户端配置完成！", utils.Colors.GREEN))
    
    # 8. 启动客户端
    if _confirm("\n是否现在启动游戏？"):
        launch_client_only(state)


def restore_solo(state: "InstallerState") -> None:
    """恢复单机模式。
    
    重置配置为本地模式，可选择是否卸载 Fika。
    """
    install_path = _require_install_path(state)
    if not install_path:
        return
    
    spt_dir = state.spt_dir()
    if not spt_dir or not spt_dir.exists():
        print("未找到游戏安装。")
        return
    
    print("\n" + "=" * 40)
    print(utils.color_text("  恢复单机模式", utils.Colors.CYAN))
    print("=" * 40)
    
    # 检查游戏是否运行
    server_running, client_running, game_running = check_spt_processes()
    if server_running or client_running or game_running:
        print(utils.color_text("检测到游戏正在运行。", utils.Colors.YELLOW))
        if _confirm("需要先关闭游戏，是否现在关闭？"):
            if not close_spt_processes(confirm=False):
                print("游戏关闭失败，请手动关闭后重试。")
                return
        else:
            return
    
    # 恢复配置
    print("\n正在恢复单机配置...")
    
    # launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    update_json_file(launcher_config, {
        "IsDevMode": "true",
        "Server.Url": "https://127.0.0.1:6969"
    })
    
    # http.json
    http_config = spt_dir / "SPT_Data" / "configs" / "http.json"
    if http_config.exists():
        update_json_file(http_config, {
            "ip": "127.0.0.1",
            "backendIp": "127.0.0.1"
        })
    
    # 清除 Fika 配置记录
    clear_fika_config(install_path)
    
    print(utils.color_text("✓ 已恢复单机配置", utils.Colors.GREEN))
    
    # 询问是否卸载 Fika
    if is_fika_installed(install_path):
        print("\n检测到已安装的联机组件。")
        if _confirm("是否同时卸载联机组件？（保留则下次可快速联机）"):
            _uninstall_fika_files(install_path)
            print(utils.color_text("✓ 联机组件已卸载", utils.Colors.GREEN))
        else:
            print("已保留联机组件。")


def _uninstall_fika_files(install_path: Path) -> None:
    """卸载 Fika 相关文件。"""
    fika_server_dir = install_path / config.TARGET_SUBDIR / "user" / "mods" / "fika-server"
    fika_client_dir = install_path / "BepInEx" / "plugins" / "Fika"
    
    for fika_dir in [fika_server_dir, fika_client_dir]:
        if fika_dir.exists():
            try:
                shutil.rmtree(fika_dir)
            except Exception as exc:
                print(f"删除失败 {fika_dir}: {exc}")


# ============ 兼容旧接口 ============
# 保留旧函数名以兼容现有代码

def start_fika(state: "InstallerState") -> None:
    """[已废弃] 请使用 be_host() 或 join_host()"""
    print(utils.color_text("提示：此功能已整合到'我是房主'和'我要加入'选项中。", utils.Colors.YELLOW))


def create_server(state: "InstallerState") -> None:
    """[已废弃] 请使用 be_host()"""
    be_host(state)


def join_server(state: "InstallerState") -> None:
    """[已废弃] 请使用 join_host()"""
    join_host(state)


def close_fika(state: "InstallerState") -> None:
    """[已废弃] 请使用 restore_solo()"""
    restore_solo(state)
