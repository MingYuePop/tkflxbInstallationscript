"""终端交互入口：展示菜单并驱动安装逻辑。"""

import sys

from . import config
from .installers import InstallerState, auto_install, install_mod, install_dotnet_environment, launch_game, select_install_path, uninstall_game
from .updater import check_update, auto_update
from .utils import Colors, clear_screen, color_text
from .announcement import get_announcement


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
    print(color_text("2) 检查并更新", Colors.CYAN))
    print(color_text("3) 安装内置 MOD", Colors.CYAN))
    print(color_text("4) 卸载游戏", Colors.CYAN))
    print(color_text("0) 返回主菜单", Colors.RED))


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
            mods = config.discover_mods()
            install_mod(state, mods)
        elif choice == "4":
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
