"""终端交互入口：展示菜单并驱动安装逻辑。"""

import sys

from . import config
from .installers import InstallerState, auto_install, install_mod, install_dotnet_environment, launch_game, select_install_path
from .utils import Colors, clear_screen, color_text
from .announcement import get_announcement

def print_menu(install_path: str | None) -> None:
    """打印主菜单，使用颜色高亮选项。"""
    # ============ 获取并格式化公告 ============
    ann = get_announcement()

    if ann["success"]:
        info = ann["data"]
        content = info.get("content", "官方网站：tkf.pyden.dev").strip()
        title = info.get("title", "====== SPT 自动安装器 ====== 1.0").strip()
        # 把 \n 变成真正的换行，并加上颜色
        print(color_text(content, Colors.YELLOW))
    else:
        # 失败时也用黄色提示，不影响主流程
        print(color_text(f"公告：{ann['error']}", Colors.YELLOW))
    
    # 打印标题
    print(color_text(f"{title}", Colors.CYAN))
    
    if install_path:
        print(color_text(f"当前安装路径: {install_path}", Colors.GREEN))
    else:
        print(color_text("当前安装路径: 未选择", Colors.YELLOW))
    print(color_text("1) 安装必要的 .NET 环境", Colors.CYAN))
    print(color_text("2) 选择安装路径（必须为空且目录名不含中文）", Colors.CYAN))
    print(color_text("3) 开始自动安装", Colors.CYAN))
    print(color_text("4) 安装内置 MOD", Colors.CYAN))
    print(color_text("5) 启动游戏", Colors.CYAN))
    print(color_text("0) 退出", Colors.RED))


def main() -> None:
    """主循环：展示菜单并根据输入调用对应功能。"""
    state = InstallerState()
    while True:
        clear_screen()
        print_menu(str(state.install_path) if state.install_path else None)
        choice = input("请选择功能：").strip()
        if choice == "1":
            install_dotnet_environment()
        elif choice == "2":
            select_install_path(state)
        elif choice == "3":
            auto_install(state, config.AVAILABLE_VERSIONS)
        elif choice == "4":
            mods = config.discover_mods()
            install_mod(state, mods)
        elif choice == "5":
            launch_game(state)
        elif choice == "0":
            print("已退出。")
            sys.exit(0)
        else:
            print("无效选项，请重新输入。")
        input("\n按回车键返回主菜单...")


if __name__ == "__main__":
    main()
