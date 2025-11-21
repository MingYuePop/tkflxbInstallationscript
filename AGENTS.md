# 仓库指南

## 项目结构与模块组织
- `scripts/` 包含 Python 安装器 CLI：`main.py` 是菜单入口，`installers.py` 负责解压/安装/启动流程，`config.py` 汇总路径和版本信息，`utils.py` 处理文件系统与对话框辅助，`announcement.py` 拉取远程公告。
- `resources/` 存储安装器使用的离线资源：`client/` 和 `server/` 放游戏压缩包，`mods/` 里是自动识别的可选 `.zip` MOD，`required/` 放前置运行库并会复制到目标机器；文件名需与 `config.py` 常量匹配。
- 安装后会在选择的路径旁写入临时标记（如 `.spt_installed.json`），不应提交。

## 构建、测试与开发命令
- 从仓库根目录运行交互式安装器：`python -m scripts.main`。
- 不触碰大压缩包的快速冒烟：`python -m compileall scripts`，及早发现语法或导入问题。

## 代码风格与命名约定
- 4 空格缩进；函数/变量使用 `snake_case`，常量用 `UPPER_SNAKE_CASE`（参考 `config.py`）；优先使用 `pathlib.Path`。
- 面向用户的提示保持简体中文；使用 `utils.color_text` 包装色彩而非直接写 ANSI。
- 已使用类型注解；为新增函数和 dataclass 继续补全。


## 安全与配置提示
- 安装器拒绝包含中文字符的路径；文档与测试保持这一规则。
- 公告获取依赖网络；确保失败时优雅降级、不阻塞安装逻辑。
- 目录和文件名需保持稳定；压缩包文件名变更需同时更新 `config.py` 与随附资源。