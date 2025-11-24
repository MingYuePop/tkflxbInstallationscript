import subprocess
from typing import List, Optional

from . import checker, config, utils

DOTNET_INSTALLERS = {
    ".NET Runtime 9.0.9": (config.REQUIRED_DIR / ".NET 9.0 Runtime (v9.0.9).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Desktop Runtime 9.0.7": (config.REQUIRED_DIR / ".NET 9.0 Desktop Runtime (v9.0.7).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Desktop Runtime 5.0.0": (config.REQUIRED_DIR / ".NET 5.0 Desktop Runtime (v5.0.0).exe", ["/install", "/quiet", "/norestart"]),
    "ASP.NET Core Runtime 9.0.9": (config.REQUIRED_DIR / "ASP.NET Core 9.0 Runtime (v9.0.9).exe", ["/install", "/quiet", "/norestart"]),
    ".NET Framework 4.7.2": (config.REQUIRED_DIR / ".NET Framework 4.7.2.exe", ["/quiet", "/norestart"]),
}


def _confirm(message: str) -> bool:
    """通用二次确认，输入 y 继续。"""
    reply = input(f"{message} (y/N): ").strip().lower()
    return reply == "y"


def _auto_install_dotnet(missing_override: Optional[List[str]] = None, require_confirm: bool = True) -> None:
    """检测并安装缺失的 .NET 组件。"""
    missing = missing_override if missing_override is not None else checker.missing_required_components()
    if not missing:
        print("必要环境已全部安装，无需操作。")
        return

    if require_confirm:
        print("检测到以下组件未安装，将为您自动安装：")
        for name in missing:
            print(f" - {name}")
        choice = input("是否立即自动安装？(Y/n): ").strip().lower()
        if choice not in ("", "y"):
            print("已取消本次自动安装。")
            return

    print("开始安装缺失的 .NET 组件...")
    for name in missing:
        installer_info = DOTNET_INSTALLERS.get(name)
        if not installer_info:
            print(f"未配置安装包：{name}，请手动安装。")
            continue
        installer_path, args = installer_info
        if not installer_path.exists():
            print(f"未找到安装包：{installer_path}，请确认 resources/required 是否完整。")
            continue
        try:
            print(f"正在安装 {name} ...")
            subprocess.run([str(installer_path), *args], check=True)
            print(f"{name} 安装命令已执行完成。")
        except subprocess.CalledProcessError as exc:
            if exc.returncode == 1638:
                print(f"{name} 安装失败（错误码 1638）。")
                print("您的电脑已安装了其他版本的 .NET，此版本无需安装。")
                print("可以直接启动游戏，无需重复安装。")
            else:
                print(f"{name} 安装失败，退出码 {exc.returncode}。")
        except Exception as exc:
            print(f"安装 {name} 时出错：{exc}")


def _manual_install_dotnet() -> None:
    """打开本地安装包目录，便于手动安装。"""
    if not config.REQUIRED_DIR.exists():
        print("未找到 resources/required 目录，请确认安装包是否完整。")
        return
    utils.open_in_explorer(config.REQUIRED_DIR)
    print(f"已打开安装包目录：{config.REQUIRED_DIR}")


def install_dotnet_environment(auto: bool = False, missing_override: Optional[List[str]] = None) -> None:
    """提供 .NET 环境安装子菜单或自动安装流程。"""
    if auto:
        _auto_install_dotnet(missing_override=missing_override, require_confirm=False)
        return
    print("====== 安装必要的 .NET 环境 ======")
    print("1) 自动检测并安装")
    print("2) 手动安装")
    print("0) 返回")
    choice = input("请选择: ").strip()
    if choice == "1":
        _auto_install_dotnet()
    elif choice == "2":
        _manual_install_dotnet()
    elif choice == "0":
        print("已取消 .NET 安装操作。")
    else:
        print("无效选项，请重新输入。")


def post_install_dotnet_flow() -> None:
    """在游戏自动安装后执行 .NET 依赖检查与处理。"""
    missing = checker.missing_required_components()
    if not missing:
        print("必要的 .NET 环境已检测到，无需重复安装。")
        return

    print("检测到以下必要组件未安装，将为您自动安装：")
    for name in missing:
        print(f" - {name}")

    choice = input("是否立即开始安装？(Y/n): ").strip().lower()
    if choice in ("", "y"):
        install_dotnet_environment(auto=True, missing_override=missing)
    else:
        print("已取消本次自动安装，将为您打开安装包所在文件夹以便手动安装。")
        if config.REQUIRED_DIR.exists():
            utils.open_in_explorer(config.REQUIRED_DIR)
        else:
            print("未找到安装包目录，请确认 resources/required 是否存在。")
