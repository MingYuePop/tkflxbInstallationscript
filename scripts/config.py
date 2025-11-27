from dataclasses import dataclass
from pathlib import Path
from typing import List
import sys

# 路径配置：以仓库根目录为基础，便于在任何位置运行。

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # -----------------------------------------------------------------
    # 程序被 PyInstaller 打包了 (运行 .exe)
    # sys.executable 指向 .exe 文件本身
    # 我们需要 .exe 文件所在的 *目录*
    # -----------------------------------------------------------------
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # -----------------------------------------------------------------
    # 程序未被打包 (运行 .py)
    # sys.executable 指向 Python 解释器
    # 我们需要 .py 文件所在的 *目录*
    # -----------------------------------------------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent
    
RESOURCES_DIR = BASE_DIR / "resources"
SERVER_DIR = RESOURCES_DIR / "server"
CLIENT_DIR = RESOURCES_DIR / "client"
MODS_DIR = RESOURCES_DIR / "mods"
REQUIRED_DIR = RESOURCES_DIR / "required"
# 安装后的 SPT 子目录名
TARGET_SUBDIR = "SPT"
# 安装完成后放置的标记文件，用于判断已安装过
MANIFEST_FILE = ".spt_installed.json"
# 在线公告 URL
ANNOUNCEMENT_URL = "https://gitee.com/ripang/tkflxbInstallationscript/raw/main/announcement.json"
# 软件版本（安装器程序本身的版本）
SOFTWARE_VERSION = "1.3"


@dataclass(frozen=True)
class GameVersion:
    """定义一个可安装的版本：展示标签和对应的压缩包文件名。"""

    label: str
    server_zip: str
    client_zip: str


@dataclass(frozen=True)
class ModPackage:
    """定义一个内置 MOD：展示用名称和压缩包文件名。"""

    display_name: str
    zip_name: str


# 可用版本列表，可随时追加新版本
# 注意：这是本地硬编码的版本列表，服务端版本现在从 announcement.json 动态加载
AVAILABLE_VERSIONS: List[GameVersion] = [
    GameVersion(
        label="4.0.6",
        server_zip="SPT-4.0.6-40087-d13d2dd.zip",
        client_zip="Client.0.16.9.0.40087.zip",
    ),    
]


@dataclass(frozen=True)
class ServerVersion:
    """定义一个可用的服务端版本。"""
    version: str
    server_zip: str
    download_url: str


@dataclass(frozen=True)
class ModVersion:
    """定义一个可下载的 MOD 版本。"""
    name: str
    zip_name: str
    download_url: str


def discover_server_versions_from_announcement() -> List[ServerVersion]:
    """
    从 announcement.json 中动态加载服务端版本列表。
    如果加载失败，返回空列表。
    """
    try:
        import requests
        response = requests.get(ANNOUNCEMENT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        server_versions = data.get("server_versions", [])
        versions = []
        for item in server_versions:
            try:
                version = ServerVersion(
                    version=item.get("version", ""),
                    server_zip=item.get("server_zip", ""),
                    download_url=item.get("download_url", "")
                )
                if version.version and version.server_zip and version.download_url:
                    versions.append(version)
            except Exception:
                continue
        return versions
    except Exception:
        # 网络错误或解析失败时返回空列表
        return []


def discover_mods() -> List[ModPackage]:
    """扫描 resources/mods 自动生成可选 MOD 列表。"""
    if not MODS_DIR.exists():
        return []

    mods: List[ModPackage] = []
    for mod_zip in sorted(MODS_DIR.glob("*.zip")):
        mods.append(ModPackage(display_name=mod_zip.stem, zip_name=mod_zip.name))
    return mods


def discover_mod_versions_from_announcement() -> List[ModVersion]:
    """
    从 announcement.json 中动态加载可下载的 MOD 版本列表。
    如果加载失败，返回空列表。
    """
    try:
        import requests
        response = requests.get(ANNOUNCEMENT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        mod_versions = data.get("mod_versions", [])
        versions = [] # version = [ModVersion(name="", zip_name="", download_url="")]
        for item in mod_versions:
            try:
                version = ModVersion(
                    name=item.get("name", ""),
                    zip_name=item.get("zip_name", ""),
                    download_url=item.get("download_url", "")
                )
                if version.name and version.zip_name and version.download_url:
                    versions.append(version)
            except Exception:
                continue
        return versions
    except Exception:
        # 网络错误或解析失败时返回空列表
        return []


AVAILABLE_MODS = discover_mods()
