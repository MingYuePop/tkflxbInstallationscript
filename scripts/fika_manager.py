"""Fika 联机功能管理模块。"""

import configparser
import json
import shutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from . import config, utils
from .config import ModVersion
from .manifest import load_manifest, record_mod_installation
from .process import check_spt_processes, close_spt_processes
from .launcher_runner import launch_game, launch_client_only

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


def _get_fika_mod_from_announcement() -> Optional[ModVersion]:
    """从公告中获取 Fika MOD 信息。"""
    mod_versions = config.discover_mod_versions_from_announcement()
    for mod in mod_versions:
        if "fika" in mod.name.lower() or "联机" in mod.name:
            return mod
    return None


def _is_fika_installed(install_path: Path) -> bool:
    """检查 Fika MOD 是否已安装。"""
    fika_server_dir = install_path / config.TARGET_SUBDIR / "user" / "mods" / "fika-server"
    fika_client_dir = install_path / "BepInEx" / "plugins" / "Fika"
    return fika_server_dir.exists() and fika_client_dir.exists()


def _download_and_install_fika(state: "InstallerState", silent: bool = True) -> bool:
    """下载并安装 Fika MOD。
    
    Args:
        state: 安装器状态
        silent: 是否静默安装（不打扰用户）
    
    Returns:
        True 表示安装成功，False 表示失败
    """
    install_path = state.install_path
    if not install_path:
        return False
    
    # 检查是否已安装
    if _is_fika_installed(install_path):
        return True
    
    # 获取 Fika MOD 信息
    fika_mod = _get_fika_mod_from_announcement()
    if not fika_mod:
        if not silent:
            print("无法获取 Fika MOD 信息，请检查网络连接。")
        return False
    
    # 确保 mods 文件夹存在
    config.MODS_DIR.mkdir(parents=True, exist_ok=True)
    
    mod_zip_path = config.MODS_DIR / fika_mod.zip_name
    
    # 下载 MOD
    if not mod_zip_path.exists():
        if not silent:
            print(f"正在下载 Fika 联机 MOD...")
        success = utils.download_file(fika_mod.download_url, mod_zip_path, show_progress=not silent)
        if not success:
            if not silent:
                print("Fika MOD 下载失败。")
            return False
    
    # 安装 MOD
    try:
        if not silent:
            print("正在安装 Fika 联机 MOD...")
        extracted_files = utils.extract_zip(mod_zip_path, install_path, strip_common_root=False, show_progress=not silent)
        
        # 记录安装
        mod_version = fika_mod.name.rsplit('-', 1)[-1] if '-' in fika_mod.name else ""
        manifest = load_manifest(install_path)
        mod_supported_versions = manifest.get("version", "") if manifest else ""
        record_mod_installation(mod_version, mod_supported_versions, install_path, fika_mod.name, extracted_files)
        
        if not silent:
            print("联机MOD已安装完成")
        return True
    except Exception as exc:
        if not silent:
            print(f"Fika MOD 安装失败: {exc}")
        return False


def _update_json_file(file_path: Path, updates: dict) -> bool:
    """更新 JSON 文件中的指定字段。
    
    Args:
        file_path: JSON 文件路径
        updates: 要更新的字段，支持嵌套字典（如 {"server.ip": "0.0.0.0"}）
    
    Returns:
        True 表示更新成功，False 表示失败
    """
    try:
        if not file_path.exists():
            print(f"配置文件不存在: {file_path}")
            return False
        
        # 读取文件内容
        content = file_path.read_text(encoding="utf-8")
        
        # 尝试解析 JSON（支持 jsonc 格式，去除注释）
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # 如果是 jsonc，尝试简单去除注释
            lines = []
            for line in content.split('\n'):
                # 去除行注释
                if '//' in line:
                    line = line[:line.index('//')]
                lines.append(line)
            content_no_comments = '\n'.join(lines)
            data = json.loads(content_no_comments)
        
        # 更新字段
        for key, value in updates.items():
            if '.' in key:
                # 支持嵌套字段，如 "server.ip"
                keys = key.split('.')
                current = data
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                data[key] = value
        
        # 写回文件
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as exc:
        print(f"更新配置文件失败 {file_path}: {exc}")
        return False


def _update_cfg_file(file_path: Path, section: str, updates: dict) -> bool:
    """更新 .cfg 配置文件中的指定字段。
    
    Args:
        file_path: .cfg 文件路径
        section: 配置段落名称（如 "[Network]"）
        updates: 要更新的字段字典
    
    Returns:
        True 表示更新成功，False 表示失败
    """
    try:
        if not file_path.exists():
            print(f"配置文件不存在: {file_path}")
            return False
        
        # 使用 configparser 读取配置文件
        config_parser = configparser.ConfigParser()
        # 保持键的大小写
        config_parser.optionxform = str
        config_parser.read(file_path, encoding="utf-8")
        
        # 检查段落是否存在
        if not config_parser.has_section(section):
            print(f"配置文件中未找到段落: {section}")
            return False
        
        # 更新字段
        for key, value in updates.items():
            config_parser.set(section, key, str(value))
        
        # 写回文件
        with open(file_path, 'w', encoding="utf-8") as f:
            config_parser.write(f, space_around_delimiters=True)
        
        return True
    except Exception as exc:
        print(f"更新配置文件失败 {file_path}: {exc}")
        return False




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
    fika_installed = _is_fika_installed(install_path)
    
    if not fika_installed:
        print("正在准备联机环境...")
        # 静默下载并安装 Fika MOD
        success = _download_and_install_fika(state, silent=False)
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
        server_running, client_running = check_spt_processes()
        if server_running or client_running:
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
    if not _is_fika_installed(install_path):
        print(utils.color_text("请先使用'启动联机'功能安装并启用联机MOD后再操作", utils.Colors.RED))
        return
    
    print("\n====== 创建服务器 ======")
    print("作为房主，其他玩家将连接到你的服务器。")
    
    # 输入公网IP
    public_ip = input("请输入你的公网IP（其他玩家用于连接）：").strip()
    if not public_ip:
        print("已取消。")
        return
    
    print(f"\n正在配置服务器，公网IP: {public_ip}")
    
    spt_dir = state.spt_dir()
    
    # 1. 修改 launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not _update_json_file(launcher_config, {
        "Server.Url": f"https://{public_ip}:6969"
    }):
        print("配置失败。")
        return
    
    # 2. 修改 com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not _update_cfg_file(fika_cfg, "[Network]", {
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
    
    if not _update_json_file(fika_config, {
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
    if not _is_fika_installed(install_path):
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
    
    spt_dir = state.spt_dir()
    
    # 1. 修改 launcher config.json
    launcher_config = spt_dir / "user" / "launcher" / "config.json"
    if not _update_json_file(launcher_config, {
        "Server.Url": f"https://{host_ip}:6969"
    }):
        print("配置失败。")
        return
    
    # 2. 修改 com.fika.core.cfg
    fika_cfg = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    if not _update_cfg_file(fika_cfg, "[Network]", {
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
    
    if not _update_json_file(fika_config, {
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
    if not _is_fika_installed(install_path):
        print("未检测到联机功能。")
        return
    
    print("\n====== 关闭联机 ======")
    
    # 检查游戏是否正在运行
    server_running, client_running = check_spt_processes()
    if server_running or client_running:
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
    _update_json_file(launcher_config, {
        "Server.Url": "https://127.0.0.1:6969"
    })
    
    print(utils.color_text("\n联机功能已关闭，所有联机组件已移除。", utils.Colors.GREEN))
    if deleted_count > 0:
        print(f"已删除 {deleted_count} 个联机组件。")
