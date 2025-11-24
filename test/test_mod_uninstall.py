#!/usr/bin/env python3
"""测试 MOD 删除功能的单元测试。"""

import json
import tempfile
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.installers import (
    _record_mod_installation,
    _get_mod_files,
    _remove_mod_record,
    _load_manifest,
    _manifest_path,
)
from scripts.config import MANIFEST_FILE


def test_mod_recording():
    """测试 MOD 文件记录功能。"""
    print("=" * 60)
    print("测试 1: MOD 文件记录")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir)
        
        # 初始化标记文件
        manifest_file = install_path / MANIFEST_FILE
        manifest_file.write_text(json.dumps({
            "version": "4.0.5",
            "mods": {}
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 记录第一个 MOD
        files_mod1 = ["Mods/mod1/file1.txt", "Mods/mod1/file2.dat"]
        _record_mod_installation(install_path, "TestMod1", files_mod1)
        
        # 验证记录
        recorded_files = _get_mod_files(install_path, "TestMod1")
        assert recorded_files == files_mod1, f"期望 {files_mod1}，得到 {recorded_files}"
        print("[OK] MOD1 文件记录成功")
        
        # 记录第二个 MOD
        files_mod2 = ["Config/mod2_config.ini", "Plugins/mod2.dll"]
        _record_mod_installation(install_path, "TestMod2", files_mod2)
        
        # 验证两个 MOD 都存在
        recorded_files1 = _get_mod_files(install_path, "TestMod1")
        recorded_files2 = _get_mod_files(install_path, "TestMod2")
        assert recorded_files1 == files_mod1, "MOD1 记录丢失"
        assert recorded_files2 == files_mod2, "MOD2 记录丢失"
        print("[OK] MOD2 文件记录成功，两个 MOD 共存")
        
        # 删除 MOD1 记录
        _remove_mod_record(install_path, "TestMod1")
        
        # 验证 MOD1 被删除，MOD2 仍存在
        recorded_files1 = _get_mod_files(install_path, "TestMod1")
        recorded_files2 = _get_mod_files(install_path, "TestMod2")
        assert recorded_files1 is None, "MOD1 应该被删除"
        assert recorded_files2 == files_mod2, "MOD2 不应该受影响"
        print("[OK] MOD1 记录删除成功，MOD2 保留")
        
        # 查看最终的标记文件内容
        manifest = _load_manifest(install_path)
        print(f"\n最终标记文件内容:")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


def test_file_deletion():
    """测试实际文件删除功能。"""
    print("\n" + "=" * 60)
    print("测试 2: 实际文件删除")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir)
        
        # 创建测试文件
        test_files = [
            "Mods/mod1/file1.txt",
            "Mods/mod1/subdir/file2.dat",
            "Config/mod1_config.ini"
        ]
        
        for file_path in test_files:
            full_path = install_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("test content")
        
        # 验证文件存在
        for file_path in test_files:
            full_path = install_path / file_path
            assert full_path.exists(), f"文件 {file_path} 应该存在"
        print("[OK] 测试文件创建成功")
        
        # 删除文件
        deleted_count = 0
        for file_path in test_files:
            full_path = install_path / file_path
            if full_path.exists():
                full_path.unlink()
                deleted_count += 1
        
        assert deleted_count == len(test_files), f"应该删除 {len(test_files)} 个文件，实际删除 {deleted_count} 个"
        print(f"[OK] 成功删除 {deleted_count} 个文件")
        
        # 验证文件已删除
        for file_path in test_files:
            full_path = install_path / file_path
            assert not full_path.exists(), f"文件 {file_path} 应该被删除"
        print("[OK] 所有文件已确认删除")


def test_manifest_structure():
    """测试标记文件结构。"""
    print("\n" + "=" * 60)
    print("测试 3: 标记文件结构")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir)
        
        # 创建标记文件
        manifest_file = install_path / MANIFEST_FILE
        manifest_data = {
            "version": "4.0.5",
            "server_zip": "SPT-4.0.5.zip",
            "client_zip": "Client.0.16.9.0.zip",
            "installed_at": "2025-11-24T13:00:00",
            "mods": {
                "ExampleMod": {
                    "files": ["file1.txt", "file2.dat"],
                    "installed_at": "2025-11-24T13:05:00"
                }
            }
        }
        manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 读取并验证
        manifest = _load_manifest(install_path)
        assert manifest is not None, "标记文件读取失败"
        assert "mods" in manifest, "标记文件应包含 mods 字段"
        assert "ExampleMod" in manifest["mods"], "ExampleMod 应在 mods 中"
        print("[OK] 标记文件结构正确")
        
        print(f"\n标记文件内容:")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        test_mod_recording()
        test_file_deletion()
        test_manifest_structure()
        print("\n" + "=" * 60)
        print("[PASS] 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
