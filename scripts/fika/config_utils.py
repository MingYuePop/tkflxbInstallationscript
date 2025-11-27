"""Fika 配置文件操作工具。"""

import json
from pathlib import Path


def update_json_file(file_path: Path, updates: dict) -> bool:
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


def update_cfg_file(file_path: Path, section: str, updates: dict) -> bool:
    """更新 .cfg 配置文件中的指定字段（保留注释和格式）。
    
    Args:
        file_path: .cfg 文件路径
        section: 配置段落名称（如 "Network"，不包含方括号）
        updates: 要更新的字段字典
    
    Returns:
        True 表示更新成功，False 表示失败
    """
    try:
        if not file_path.exists():
            print(f"配置文件不存在: {file_path}")
            return False
        
        # 读取文件内容
        lines = file_path.read_text(encoding="utf-8").split('\n')
        new_lines = []
        in_target_section = False
        section_found = False
        updated_keys = set()
        
        for line in lines:
            stripped = line.strip()
            
            # 检测段落开始
            if stripped.startswith('[') and stripped.endswith(']'):
                # 提取段落名称（移除方括号）
                current_section = stripped[1:-1]
                if current_section == section:
                    in_target_section = True
                    section_found = True
                else:
                    in_target_section = False
                new_lines.append(line)
                continue
            
            # 在目标段落中更新字段
            if in_target_section and '=' in line and not stripped.startswith('#'):
                # 提取键名（去除空格）
                key = line.split('=')[0].strip()
                if key in updates:
                    # 保留原有的缩进和格式
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + f"{key} = {updates[key]}")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 检查段落是否存在
        if not section_found:
            print(f"配置文件中未找到段落: [{section}]")
            return False
        
        # 检查是否所有字段都已更新
        missing_keys = set(updates.keys()) - updated_keys
        if missing_keys:
            print(f"警告: 以下字段未找到: {missing_keys}")
        
        # 写回文件
        file_path.write_text('\n'.join(new_lines), encoding="utf-8")
        return True
    except Exception as exc:
        print(f"更新配置文件失败 {file_path}: {exc}")
        return False
