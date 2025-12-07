"""PyWebView GUI 入口点"""

import webview
import os
import sys

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT_DIR, 'web')


class Api:
    """Python 后端 API，供前端 JavaScript 调用"""
    
    def __init__(self):
        self.window = None
    
    def set_window(self, window):
        """设置窗口引用"""
        self.window = window
    
    def select_folder(self):
        """打开文件夹选择对话框"""
        result = self.window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=os.path.expanduser('~')
        )
        if result and len(result) > 0:
            return result[0]
        return None
    
    def select_file(self, file_types=('All files (*.*)',)):
        """打开文件选择对话框"""
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            directory=os.path.expanduser('~'),
            file_types=file_types
        )
        if result and len(result) > 0:
            return result[0]
        return None
    
    def save_file(self, filename='', file_types=('All files (*.*)',)):
        """打开文件保存对话框"""
        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=os.path.expanduser('~'),
            save_filename=filename,
            file_types=file_types
        )
        return result
    
    def show_message(self, title, message):
        """显示消息对话框"""
        self.window.evaluate_js(f'''
            Toast.show("{message}", "success");
        ''')
    
    def get_version(self):
        """获取软件版本"""
        # 这里将来可以从 config 中读取
        return "1.0.0"


def main():
    """主函数：创建并启动 GUI 窗口"""
    api = Api()
    
    # 创建窗口
    window = webview.create_window(
        title='SPT 自动安装器',
        url=os.path.join(WEB_DIR, 'index.html'),
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
        js_api=api,
        text_select=False,
    )
    
    # 设置窗口引用
    api.set_window(window)
    
    # 启动 GUI
    webview.start(debug=True)


if __name__ == '__main__':
    main()
