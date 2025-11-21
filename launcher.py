"""PyInstaller 构建 启动脚本入口点"""

from inspect import Traceback
from scripts.main import main
import time
import traceback

if __name__ == "__main__":
    try:
        main()
        
    except KeyboardInterrupt:
        print("程序退出，感谢你的使用")
        exit(0)
        
    except Exception as e:
        print("程序遇到未处理的异常")
        traceback.print_exc()
        input("按 Enter 键退出程序...")
        exit(1)