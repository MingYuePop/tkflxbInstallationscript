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
    BASE_DIR = Path(__file__).resolve().parent
    
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
ANNOUNCEMENT_URL = "https://raw.githubusercontent.com/MingYuePop/tkflxbInstallationscript/refs/heads/main/announcement.json"


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
AVAILABLE_VERSIONS: List[GameVersion] = [
    GameVersion(
        label="4.0.6",
        server_zip="SPT-4.0.6-40087-d13d2dd.zip",
        client_zip="Client.0.16.9.0.40087.zip",
    ),
]


def discover_mods() -> List[ModPackage]:
    """扫描 resources/mods 自动生成可选 MOD 列表。"""
    if not MODS_DIR.exists():
        return []

    mods: List[ModPackage] = []
    for mod_zip in sorted(MODS_DIR.glob("*.zip")):
        mods.append(ModPackage(display_name=mod_zip.stem, zip_name=mod_zip.name))
    return mods


AVAILABLE_MODS = discover_mods()
