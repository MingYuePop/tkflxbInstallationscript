import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import GameVersion, MANIFEST_FILE


def manifest_path(target_root: Path) -> Path:
    """返回标记文件路径。"""
    return target_root / MANIFEST_FILE


def load_manifest(target_root: Path) -> Optional[dict]:
    """读取标记文件，无法读取时返回 None。"""
    path = manifest_path(target_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_manifest(target_root: Path, version: GameVersion) -> None:
    """写入标记文件，记录已安装的版本和时间。"""
    path = manifest_path(target_root)
    payload = {
        "version": version.label,
        "server_zip": version.server_zip,
        "client_zip": version.client_zip,
        "installed_at": datetime.now().isoformat(timespec="seconds"),
        "mods": {},  # 初始为空的 MOD 记录
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def update_manifest_server_version(target_root: Path, server_version: str, server_zip: str) -> None:
    """更新标记文件中的服务端版本信息。"""
    path = manifest_path(target_root)
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["version"] = server_version
        payload["server_zip"] = server_zip
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def record_mod_installation(target_root: Path, mod_name: str, files: List[str]) -> None:
    """记录 MOD 安装的文件列表到标记文件。"""
    path = manifest_path(target_root)
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "mods" not in payload:
            payload["mods"] = {}
        payload["mods"][mod_name] = {
            "files": files,
            "installed_at": datetime.now().isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_mod_files(target_root: Path, mod_name: str) -> Optional[List[str]]:
    """获取已安装 MOD 的文件列表。"""
    manifest = load_manifest(target_root)
    if not manifest:
        return None
    mods = manifest.get("mods", {})
    mod_info = mods.get(mod_name)
    if not mod_info:
        return None
    return mod_info.get("files", [])


def remove_mod_record(target_root: Path, mod_name: str) -> None:
    """从标记文件中删除 MOD 记录。"""
    path = manifest_path(target_root)
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "mods" in payload and mod_name in payload["mods"]:
            del payload["mods"][mod_name]
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
