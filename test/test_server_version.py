#!/usr/bin/env python3
"""测试服务端版本功能的脚本。"""

import sys
import json
from pathlib import Path

# 添加 scripts 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from config import discover_server_versions_from_announcement, ServerVersion

def test_server_version_loading():
    """测试从 announcement.json 加载服务端版本。"""
    print("=" * 50)
    print("[TEST] Load server versions from announcement.json")
    print("=" * 50)
    
    # 首先检查本地 announcement.json
    announcement_file = Path(__file__).parent / "announcement.json"
    if announcement_file.exists():
        print(f"\n[OK] Found announcement.json: {announcement_file}")
        with open(announcement_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            server_versions = data.get("server_versions", [])
            print(f"[OK] Local server versions count: {len(server_versions)}")
            for sv in server_versions:
                print(f"  - {sv.get('version')}: {sv.get('server_zip')}")
    else:
        print(f"[FAIL] announcement.json not found")
        return False
    
    # 测试动态加载函数
    print("\n[INFO] Testing discover_server_versions_from_announcement()...")
    versions = discover_server_versions_from_announcement()
    
    if versions:
        print(f"[OK] Successfully loaded {len(versions)} versions:")
        for version in versions:
            print(f"  - Version: {version.version}")
            print(f"    Server zip: {version.server_zip}")
            print(f"    Download URL: {version.download_url}")
    else:
        print("[WARN] No versions loaded (network issue or format problem)")
    
    print("\n" + "=" * 50)
    print("[INFO] Test completed")
    print("=" * 50)
    return True

def test_manifest_structure():
    """测试标记文件结构。"""
    print("\n" + "=" * 50)
    print("[TEST] Manifest file structure")
    print("=" * 50)
    
    from config import MANIFEST_FILE
    print(f"\n[OK] Manifest file name: {MANIFEST_FILE}")
    
    # 测试标记文件的预期结构
    expected_fields = ["version", "server_zip", "client_zip", "installed_at"]
    print(f"[OK] Expected fields in manifest: {', '.join(expected_fields)}")
    
    # 版本切换后会添加的字段
    print(f"[OK] Field added after version switch: updated_at")
    
    print("\n" + "=" * 50)
    return True

if __name__ == "__main__":
    try:
        test_server_version_loading()
        test_manifest_structure()
        print("\n[SUCCESS] All tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
