"""终端交互入口：展示菜单并驱动安装逻辑。"""

import sys

from . import config
from .installers import (
    InstallerState,
    auto_install,
    select_install_path,
)
from .launcher_runner import launch_game
from .dotnet_env import install_dotnet_environment
from .mod_manager import install_mod, uninstall_mod, download_mod, uninstall_all_mods
from .server_version import download_server_version, switch_server_version
from .updater import check_update, auto_update
from .uninstaller import uninstall_game
from .utils import Colors, clear_screen, color_text
from .announcement import get_announcement
from .fika import be_host, join_host, restore_solo, get_fika_status
from .profile_manager import export_profile, import_profile


def print_menu(install_path: str | None) -> None:
    """打印主菜单，使用颜色高亮选项。"""
    # ============ 获取并格式化公告 ============
    ann = get_announcement()
    info = ann["data"] if ann["success"] else {}
    content = info.get("content","官方网站：tkf.pyden.dev").strip()
    title = f"====== SPT 自动安装器 {config.SOFTWARE_VERSION} ====== "
    # 把 \n 变成真正的换行，并加上颜色
    print(color_text(content, Colors.YELLOW))
    print(color_text(title, Colors.CYAN))
    if not ann["success"]:
        # 失败时也用黄色提示，不影响主流程
        print(color_text(f"公告：{ann['error']}", Colors.YELLOW))

    # ============ 检查版本更新 ============
    update_info = check_update()
    if update_info and update_info.get("has_update"):
        version_hint = color_text(
            f"发现新版本: {update_info['latest_version']} (当前: {update_info['current_version']})",
            Colors.YELLOW
        )
        print(version_hint)

    # 打印标题
    if install_path:
        print(color_text(f"当前安装路径: {install_path}", Colors.GREEN))
    else:
        print(color_text("当前安装路径: 未选择", Colors.YELLOW))
    print(color_text("1) 选择游戏安装路径", Colors.CYAN))
    print(color_text("2) 开始自动安装", Colors.CYAN))
    print(color_text("3) 启动游戏", Colors.CYAN))
    print(color_text("4) 其他", Colors.CYAN))
    print(color_text("0) 退出", Colors.RED))


def print_other_menu() -> None:
    """打印"其他"子菜单。"""
    print("\n====== 其他功能 ======")
    print(color_text("1) 安装 .NET 环境", Colors.CYAN))
    print(color_text("2) 检查并更新软件", Colors.CYAN))
    print(color_text("3) MOD 管理", Colors.CYAN))
    print(color_text("4) 服务端版本管理", Colors.CYAN))
    print(color_text("5) Fika 联机功能", Colors.CYAN))
    print(color_text("6) 存档管理", Colors.CYAN))
    print(color_text("7) 卸载游戏", Colors.CYAN))
    print(color_text("0) 返回主菜单", Colors.RED))


def print_mod_menu() -> None:
    """打印 MOD 管理子菜单。"""
    print("\n====== MOD 管理 ======")
    print(color_text("1) 下载 MOD", Colors.CYAN))
    print(color_text("2) 安装 MOD", Colors.CYAN))
    print(color_text("3) 删除已安装的 MOD", Colors.CYAN))
    print(color_text("4) 一键卸载所有 MOD", Colors.CYAN))
    print(color_text("0) 返回上级菜单", Colors.RED))


def print_server_version_menu() -> None:
    """打印服务端版本管理子菜单。"""
    print("\n====== 服务端版本管理 ======")
    print(color_text("1) 下载服务端版本", Colors.CYAN))
    print(color_text("2) 切换服务端版本", Colors.CYAN))
    print(color_text("0) 返回上级菜单", Colors.RED))


def print_fika_menu(state: InstallerState) -> None:
    """打印 Fika 联机功能子菜单。"""
    print("\n" + "=" * 40)
    print(color_text("  Fika 联机功能", Colors.CYAN))
    print("=" * 40)
    
    # 获取状态
    is_installed, mode, status_text = get_fika_status(state)
    
    # 状态显示
    if mode == "host":
        print(color_text(f"当前状态: {status_text}", Colors.GREEN))
    elif mode == "client":
        print(color_text(f"当前状态: {status_text}", Colors.CYAN))
    elif is_installed:
        print(color_text(f"当前状态: {status_text}", Colors.YELLOW))
    else:
        print(color_text(f"当前状态: {status_text}", Colors.YELLOW))
    
    print()
    print(color_text("1) 我是房主（创建服务器）", Colors.CYAN))
    print(color_text("2) 我要加入（连接房主）", Colors.CYAN))
    print(color_text("3) 恢复单机模式", Colors.CYAN))
    print(color_text("0) 返回上级菜单", Colors.RED))


def handle_mod_menu(state: InstallerState) -> None:
    """处理 MOD 管理子菜单的选择。"""
    while True:
        clear_screen()
        print_mod_menu()
        choice = input("请选择功能：").strip()
        if choice == "1":
            download_mod(state)
        elif choice == "2":
            mods = config.discover_mods()
            install_mod(state, mods)
        elif choice == "3":
            uninstall_mod(state)
        elif choice == "4":
            uninstall_all_mods(state)
        elif choice == "0":
            print("已返回上级菜单。")
            return
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键继续...")


def handle_server_version_menu(state: InstallerState) -> None:
    """处理服务端版本管理子菜单的选择。"""
    while True:
        clear_screen()
        print_server_version_menu()
        choice = input("请选择功能：").strip()
        if choice == "1":
            download_server_version(state)
        elif choice == "2":
            switch_server_version(state)
        elif choice == "0":
            print("已返回上级菜单。")
            return
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键继续...")


def handle_fika_menu(state: InstallerState) -> None:
    """处理 Fika 联机功能子菜单的选择。"""
    while True:
        clear_screen()
        print_fika_menu(state)
        choice = input("请选择功能：").strip()
        if choice == "1":
            be_host(state)
        elif choice == "2":
            join_host(state)
        elif choice == "3":
            restore_solo(state)
        elif choice == "0":
            print("已返回上级菜单。")
            return
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键继续...")


def print_profile_menu() -> None:
    """打印存档管理子菜单。"""
    print("\n====== 存档管理 ======")
    print(color_text("1) 导出存档", Colors.CYAN))
    print(color_text("2) 导入存档", Colors.CYAN))
    print(color_text("0) 返回上级菜单", Colors.RED))


def handle_profile_menu(state: InstallerState) -> None:
    """处理存档管理子菜单的选择。"""
    while True:
        clear_screen()
        print_profile_menu()
        choice = input("请选择功能：").strip()
        if choice == "1":
            export_profile(state)
        elif choice == "2":
            import_profile(state)
        elif choice == "0":
            print("已返回上级菜单。")
            return
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键继续...")


def handle_other_menu(state: InstallerState) -> None:
    """处理"其他"子菜单的选择。"""
    while True:
        clear_screen()
        print_other_menu()
        choice = input("请选择功能：").strip()
        if choice == "1":
            install_dotnet_environment()
        elif choice == "2":
            auto_update()
        elif choice == "3":
            handle_mod_menu(state)
        elif choice == "4":
            handle_server_version_menu(state)
        elif choice == "5":
            handle_fika_menu(state)
        elif choice == "6":
            handle_profile_menu(state)
        elif choice == "7":
            uninstall_game(state)
        elif choice == "0":
            print("已返回主菜单。")
            return
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键继续...")


def main() -> None:
    """主循环：展示菜单并根据输入调用对应功能。"""
    state = InstallerState()
    while True:
        clear_screen()
        print_menu(str(state.install_path) if state.install_path else None)
        choice = input("请选择功能：").strip()
        if choice == "1":
            select_install_path(state)
        elif choice == "2":
            auto_install(state, config.AVAILABLE_VERSIONS)
        elif choice == "3":
            launch_game(state)
        elif choice == "4":
            handle_other_menu(state)
        elif choice == "0":
            print("已退出。")
            sys.exit(0)
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键返回主菜单...")


if __name__ == "__main__":
    main()
