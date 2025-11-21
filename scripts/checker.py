"""检测系统中是否安装了必要的软件。"""

import subprocess
import re
from typing import Dict, List, Tuple
from pathlib import Path


def check_dotnet_runtime(version: str) -> bool:
    """
    检查是否安装了指定版本的 .NET Runtime。
    
    Args:
        version: 版本号，如 "9.0.9" 或 "5.0.0"
    
    Returns:
        True 如果已安装，False 否则
    """
    try:
        result = subprocess.run(
            ["dotnet", "--list-runtimes"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False
        
        # 查找匹配的版本
        # 输出格式: "Microsoft.NETCore.App 9.0.9 [C:\...]"
        for line in result.stdout.split('\n'):
            if version in line:
                return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_dotnet_desktop_runtime(version: str) -> bool:
    """
    检查是否安装了指定版本的 .NET Desktop Runtime。
    
    Args:
        version: 版本号，如 "9.0.7" 或 "5.0.0"
    
    Returns:
        True 如果已安装，False 否则
    """
    try:
        result = subprocess.run(
            ["dotnet", "--list-runtimes"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False
        
        # 查找 Desktop Runtime
        # 输出格式: "Microsoft.WindowsDesktop.App 9.0.7 [C:\...]"
        for line in result.stdout.split('\n'):
            if "WindowsDesktop" in line and version in line:
                return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_dotnet_aspcore_runtime(version: str) -> bool:
    """
    检查是否安装了指定版本的 ASP.NET Core Runtime。
    
    Args:
        version: 版本号，如 "9.0.9"
    
    Returns:
        True 如果已安装，False 否则
    """
    try:
        result = subprocess.run(
            ["dotnet", "--list-runtimes"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False
        
        # 查找 ASP.NET Core Runtime
        # 输出格式: "Microsoft.AspNetCore.App 9.0.9 [C:\...]"
        for line in result.stdout.split('\n'):
            if "AspNetCore" in line and version in line:
                return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ndp_framework(version: str = "4.7.2") -> bool:
    """
    检查是否安装了 .NET Framework。
    
    Args:
        version: 版本号，如 "4.7.2"
    
    Returns:
        True 如果已安装，False 否则
    """
    try:
        # 通过注册表检查 .NET Framework
        result = subprocess.run(
            [
                "reg", "query",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full",
                "/v", "Release"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_all_required() -> Dict[str, bool]:
    """
    检查所有必需的软件。
    
    Returns:
        字典，键为软件名称，值为是否已安装
    """
    return {
        ".NET Runtime 9.0.9": check_dotnet_runtime("9.0.9"),
        ".NET Desktop Runtime 9.0.7": check_dotnet_desktop_runtime("9.0.7"),
        ".NET Desktop Runtime 5.0.0": check_dotnet_desktop_runtime("5.0.0"),
        "ASP.NET Core Runtime 9.0.9": check_dotnet_aspcore_runtime("9.0.9"),
        ".NET Framework 4.7.2": check_ndp_framework("4.7.2"),
    }


def print_check_results() -> None:
    """打印检查结果。"""
    results = check_all_required()
    
    print("\n========== 系统软件检查 ==========")
    all_installed = True
    for software, installed in results.items():
        status = "✓ 已安装" if installed else "✗ 未安装"
        print(f"{software}: {status}")
        if not installed:
            all_installed = False
    
    print("=" * 35)
    if all_installed:
        print("✓ 所有必需软件已安装")
    else:
        print("✗ 部分软件未安装，请运行 required 文件夹中的安装程序")
    print()


if __name__ == "__main__":
    print_check_results()
