"""Fika MOD 安装与检测。"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .. import config, utils
from ..config import ModVersion
from ..manifest import load_manifest, record_mod_installation

if TYPE_CHECKING:
    from ..installers import InstallerState


def get_fika_mod_from_announcement() -> Optional[ModVersion]:
    """从公告中获取 Fika MOD 信息。"""
    mod_versions = config.discover_mod_versions_from_announcement()
    for mod in mod_versions:
        if "fika" in mod.name.lower() or "联机" in mod.name:
            return mod
    return None


def is_fika_installed(install_path: Path) -> bool:
    """检查 Fika MOD 是否已安装。"""
    fika_server_dir = install_path / config.TARGET_SUBDIR / "user" / "mods" / "fika-server"
    fika_client_dir = install_path / "BepInEx" / "plugins" / "Fika"
    fika_config_file = install_path / "BepInEx" / "config" / "com.fika.core.cfg"
    return fika_server_dir.exists() and fika_client_dir.exists() and fika_config_file.exists()


def download_and_install_fika(state: "InstallerState", silent: bool = True) -> bool:
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
    if is_fika_installed(install_path):
        return True
    
    # 获取 Fika MOD 信息
    fika_mod = get_fika_mod_from_announcement()
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
            print("正在下载 Fika 联机 MOD...")
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
