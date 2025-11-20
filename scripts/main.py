"""终端交互入口：展示菜单并驱动安装逻辑。"""

import sys

from . import config
from .installers import InstallerState, auto_install, install_mod, launch_game, select_install_path
from .utils import Colors, clear_screen, color_text


def print_menu(install_path: str | None) -> None:
    """打印主菜单，使用颜色高亮选项。"""
    title = color_text("====== SPT 自动安装器 ======", Colors.CYAN)
    print(f"\n{title}")
    if install_path:
        print(color_text(f"当前安装路径: {install_path}", Colors.GREEN))
    else:
        print(color_text("当前安装路径: 未选择", Colors.YELLOW))
    print(color_text("1) 选择安装路径（必须为空且目录名不含中文）", Colors.CYAN))
    print(color_text("2) 开始自动安装", Colors.CYAN))
    print(color_text("3) 安装内置 MOD", Colors.CYAN))
    print(color_text("4) 启动游戏", Colors.CYAN))
    print(color_text("0) 退出", Colors.RED))


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
            mods = config.discover_mods()
            install_mod(state, mods)
        elif choice == "4":
            launch_game(state)
        elif choice == "0":
            print("已退出。")
            sys.exit(0)
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键返回主菜单...")


if __name__ == "__main__":
    main()
