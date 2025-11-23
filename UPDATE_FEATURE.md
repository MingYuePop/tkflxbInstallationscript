# 软件自动更新功能（方案2）实现说明

## 功能概述

实现了完整的软件自动更新功能，包括版本检查、新版本提示和自动下载更新。

## 实现细节

### 1. 下载功能 (`scripts/utils.py`)

添加了 `download_file()` 函数：
- **功能**：从 URL 下载文件到指定路径
- **特性**：
  - 支持进度条显示
  - 自动创建目标目录
  - 超时控制（30秒）
  - 完整的错误处理

```python
def download_file(url: str, dest_path: Path, show_progress: bool = True) -> bool
```

### 2. 版本检查 (`scripts/installers.py`)

#### 2.1 获取最新版本信息
```python
def get_latest_version_info() -> Optional[dict]
```
- 从公告 JSON 文件解析 `latest_version` 和 `download_url`
- 返回版本信息字典或 None

#### 2.2 检查更新
```python
def check_update() -> Optional[dict]
```
- 比较当前版本与最新版本
- 返回更新状态和版本信息
- 返回格式：
  - 有新版本：`{"has_update": True, "latest_version": "...", "current_version": "...", "download_url": "..."}`
  - 已是最新版：`{"has_update": False, "current_version": "..."}`

#### 2.3 自动更新流程
```python
def auto_update() -> None
```
- 检查版本
- 如有新版本：显示版本信息，提示用户确认
- 下载更新包到 `BASE_DIR`（程序运行目录）
- 下载完成后提示是否立即运行更新程序

### 3. 菜单界面 (`scripts/main.py`)

#### 3.1 版本提示
- 在菜单顶部显示新版本提示（如果有新版本）
- 格式：`发现新版本: v1.2.3 (当前: v1.0.0)`
- 使用黄色高亮显示

#### 3.2 新菜单选项
- 添加选项 `6) 检查更新`
- 用户可随时点击检查和下载更新

#### 3.3 菜单流程
```
1) 安装必要的 .NET 环境
2) 选择安装路径
3) 开始自动安装
4) 安装内置 MOD
5) 启动游戏
6) 检查更新        <- 新增
0) 退出
```

## 工作流程

### 有新版本时
1. 菜单顶部显示：`发现新版本: 1.2.3 (当前: 1.0.0)`
2. 用户选择选项 6
3. 程序显示版本信息和下载链接
4. 提示用户确认下载
5. 下载到 `BASE_DIR`，显示进度条
6. 下载完成后提示是否运行更新程序

### 无新版本时
1. 菜单正常显示（无版本提示）
2. 用户选择选项 6
3. 程序显示：`当前已是最新版本（1.0.0），无需更新。`

## 数据流

```
announcement.json
    ↓
get_announcement() (announcement.py)
    ↓
get_latest_version_info() (installers.py)
    ↓
check_update() (installers.py)
    ↓
print_menu() (main.py) - 显示版本提示
    ↓
auto_update() (installers.py) - 下载更新
    ↓
download_file() (utils.py) - 执行下载
```

## 配置要求

### 1. config.py 中的软件版本
```python
SOFTWARE_VERSION = "1.0.0"  # 安装器程序本身的版本
```

### 2. announcement.json 必须包含
```json
{
  "latest_version": "1.2.3",
  "download_url": "https://example.com/installer.exe",
  ...
}
```

**注意**：`latest_version` 与 `config.SOFTWARE_VERSION` 进行比较，用于判断是否有新版本。

## 测试结果

运行 `test_update.py` 验证：
- ✓ 成功获取版本信息
- ✓ 正确检测版本更新
- ✓ 所有模块编译无误

## 文件修改列表

1. **scripts/config.py**
   - 添加 `SOFTWARE_VERSION = "1.0.0"` 常量（软件版本）

2. **scripts/utils.py**
   - 添加 `requests` 导入
   - 添加 `download_file()` 函数

3. **scripts/installers.py**
   - 添加 `announcement` 导入
   - 添加 `get_latest_version_info()` 函数
   - 添加 `check_update()` 函数（使用 `SOFTWARE_VERSION` 比较）
   - 添加 `auto_update()` 函数

4. **scripts/main.py**
   - 导入 `check_update` 和 `auto_update`
   - 修改 `print_menu()` 添加版本检查和提示
   - 添加菜单选项 6 处理
   - 修改主循环处理选项 6

## 依赖

- `requests` 库（用于 HTTP 下载）

## 注意事项

1. 下载链接应指向可执行的更新程序
2. 版本号比较使用字符串相等性，建议使用语义版本号
3. 下载超时设置为 30 秒，可根据需要调整
4. 进度条显示需要终端支持 ANSI 颜色
