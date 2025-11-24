# 服务端版本切换功能说明

## 功能概述

本功能允许用户在已安装的 SPT 游戏中切换不同版本的服务端，以及从线上下载新的服务端版本。

## 核心功能

### 1. 动态加载服务端版本列表
- 从 `announcement.json` 中读取可用的服务端版本
- 支持在线更新版本列表，无需修改程序代码
- 版本列表格式：
  ```json
  "server_versions": [
    {
      "version": "4.0.6",
      "server_zip": "SPT-4.0.6-40087-d13d2dd.zip",
      "download_url": "https://example.com/SPT-4.0.6-40087-d13d2dd.zip"
    },
    {
      "version": "4.0.5",
      "server_zip": "SPT-4.0.5-40087-d13d2dd.zip",
      "download_url": "https://example.com/SPT-4.0.5-40087-d13d2dd.zip"
    }
  ]
  ```

### 2. 下载服务端版本
- 菜单选项：其他 → 下载服务端版本（选项 4）
- 功能流程：
  1. 检查是否已安装游戏
  2. 从 `announcement.json` 获取可用版本列表
  3. 显示版本列表供用户选择
  4. 检查本地是否已存在该版本
  5. 若不存在，下载到 `resources/server` 文件夹
  6. 显示下载进度条

### 3. 切换服务端版本
- 菜单选项：其他 → 切换服务端版本（选项 5）
- 功能流程：
  1. 显示当前安装的服务端版本
  2. 扫描 `resources/server` 文件夹中的所有 `.zip` 文件
  3. 显示可用的本地版本列表
  4. 用户选择目标版本
  5. 将目标版本的文件解压到安装目录，覆盖当前版本
  6. 更新标记文件中的版本信息
  7. 显示切换完成提示

## 实现细节

### 文件修改

#### 1. `announcement.json`
- 新增 `server_versions` 字段
- 包含版本号、服务端包名称和下载链接

#### 2. `scripts/config.py`
- 新增 `ServerVersion` 数据类
- 新增 `discover_server_versions_from_announcement()` 函数
  - 从线上 `announcement.json` 加载版本列表
  - 网络错误时返回空列表，不影响程序运行

#### 3. `scripts/installers.py`
- ??????????????????????????

#### 4. `scripts/main.py`
- ?????????????????
- ???????????????
  - ?? 4????????
  - ?? 5????????
  - ??????????? 6

#### 5. `scripts/server_version.py`
- ?? `download_server_version()` ??
  - ??????????? `resources/server`
- ?? `switch_server_version()` ??
  - ???????????
- ????????????????????

#### 6. `scripts/manifest.py`
- ?? `update_manifest_server_version()` ?????????

### ??????
安装完成后在安装目录生成 `.spt_installed.json` 标记文件：

```json
{
  "version": "4.0.6",
  "server_zip": "SPT-4.0.6-40087-d13d2dd.zip",
  "client_zip": "Client.0.16.9.0.40087.zip",
  "installed_at": "2025-11-23T21:30:00",
  "updated_at": "2025-11-23T21:35:00"
}
```

- `version`：当前服务端版本
- `server_zip`：当前使用的服务端包文件名
- `client_zip`：客户端包文件名
- `installed_at`：初始安装时间
- `updated_at`：版本切换时间（仅在切换后出现）

## 使用流程

### 场景 1：下载旧版本并切换

1. 启动程序，进入菜单
2. 选择"其他"（选项 4）
3. 选择"下载服务端版本"（选项 4）
4. 选择要下载的版本（如 4.0.5）
5. 确认下载，等待完成
6. 返回菜单，选择"其他"（选项 4）
7. 选择"切换服务端版本"（选项 5）
8. 选择要切换的版本（如 4.0.5）
9. 确认切换，等待完成

### 场景 2：在已下载的版本间切换

1. 启动程序，进入菜单
2. 选择"其他"（选项 4）
3. 选择"切换服务端版本"（选项 5）
4. 选择要切换的版本
5. 确认切换，等待完成

## 技术特点

- **网络容错**：网络错误时程序继续运行，不影响其他功能
- **进度显示**：下载和解压过程显示进度条
- **版本检测**：自动检测当前版本，防止重复切换
- **文件验证**：检查本地是否已存在版本，避免重复下载
- **安全确认**：关键操作前进行二次确认
- **错误恢复**：下载失败时自动清理失败的文件

## 配置示例

在 `announcement.json` 中添加新版本：

```json
{
  "server_versions": [
    {
      "version": "4.0.6",
      "server_zip": "SPT-4.0.6-40087-d13d2dd.zip",
      "download_url": "https://your-server.com/SPT-4.0.6-40087-d13d2dd.zip"
    },
    {
      "version": "4.0.5",
      "server_zip": "SPT-4.0.5-40087-d13d2dd.zip",
      "download_url": "https://your-server.com/SPT-4.0.5-40087-d13d2dd.zip"
    },
    {
      "version": "4.0.4",
      "server_zip": "SPT-4.0.4-40087-d13d2dd.zip",
      "download_url": "https://your-server.com/SPT-4.0.4-40087-d13d2dd.zip"
    }
  ]
}
```

## 注意事项

1. **下载链接**：确保 `announcement.json` 中的下载链接有效且可访问
2. **文件完整性**：下载的服务端包应与本地版本包结构一致
3. **版本兼容性**：不同版本的服务端可能需要不同的客户端版本
4. **网络环境**：下载大文件时确保网络稳定
5. **磁盘空间**：确保 `resources/server` 文件夹有足够的磁盘空间

## 故障排除

### 问题：无法获取服务端版本列表
- 检查网络连接
- 确认 `announcement.json` 的在线链接是否正确
- 检查 `announcement.json` 的格式是否正确

### 问题：下载失败
- 检查下载链接是否有效
- 检查网络连接和防火墙设置
- 确保 `resources/server` 文件夹存在且有写入权限

### 问题：版本切换失败
- 确认服务端包文件完整
- 检查 SPT 安装目录是否有写入权限
- 确认没有其他程序占用 SPT 文件

## 相关文件

- `announcement.json` - 配置文件
- `scripts/config.py` - 配置和版本加载
- `scripts/installers.py` - 安装和版本切换逻辑
- `scripts/main.py` - 菜单集成
- `scripts/utils.py` - 下载和解压工具
