"""PyInstaller 构建 启动脚本入口点"""

from scripts.main import main
import time

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        time.sleep(2)
        print("\n软件退出中...")
        exit(0)
