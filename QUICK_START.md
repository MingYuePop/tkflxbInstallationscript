# 自动更新功能快速开始

## 用户使用指南

### 检查更新
1. 运行程序进入主菜单
2. 如果有新版本，菜单顶部会显示：`发现新版本: 1.2.3 (当前: 1.0.0)`
3. 选择选项 `6) 检查更新`

### 下载更新
1. 选择选项 6 后，程序会显示版本信息
2. 确认下载：输入 `y` 确认
3. 程序自动下载到程序运行目录
4. 下载完成后，选择是否立即运行更新程序

## 开发者指南

### 1. 更新 config.py 中的软件版本

```python
# scripts/config.py
SOFTWARE_VERSION = "1.0.1"  # 更新为新版本号
```

### 2. 更新 announcement.json

```json
{
  "latest_version": "1.0.1",
  "update_time": "2025-11-23",
  "title": "====== SPT 自动安装器 1.0.1 ======",
  "content": "官方交流群：1067632016",
  "force_update": false,
  "download_url": "https://github.com/tkflxb/SPT-Install-Script/releases/download/v1.0.1/SPT-Installer-1.0.1.exe"
}
```

### 关键字段说明
- `latest_version`: 最新版本号（与 `config.SOFTWARE_VERSION` 对比）
- `download_url`: 更新包下载链接（必须是可直接下载的 URL）

### 版本比较逻辑
- 当前版本来自 `config.SOFTWARE_VERSION`（安装器程序本身的版本）
- 与 `announcement.json` 中的 `latest_version` 进行字符串比较
- 如果不相等，则认为有新版本

### 测试更新功能

```bash
python test_update.py
```

输出示例：
```
Test 3: Configuration Info
==================================================
BASE_DIR: E:\tkflxbInstallationscript
Current version: 4.0.6

Test 1: Get Latest Version Info
==================================================
[OK] Successfully retrieved version info:
  - Latest version: 1.0
  - Download URL: https://github.com/tkflxb/SPT-Install-Script/releases/latest

Test 2: Check Update
==================================================
[OK] New version found:
  - Current version: 4.0.6
  - Latest version: 1.0
  - Download URL: https://github.com/tkflxb/SPT-Install-Script/releases/latest
```

## 常见问题

### Q: 下载失败怎么办？
A: 检查网络连接和 `download_url` 是否有效。程序会显示错误信息。

### Q: 如何手动下载更新？
A: 从 `announcement.json` 中的 `download_url` 手动下载，保存到程序运行目录。

### Q: 版本号格式有要求吗？
A: 目前使用字符串比较，建议使用语义版本号（如 1.0.0, 1.2.3）。

### Q: 更新程序在哪里保存？
A: 保存在 `BASE_DIR`（程序运行目录），文件名从 URL 中提取。

## 集成检查清单

- [ ] 更新 `announcement.json` 中的 `latest_version` 和 `download_url`
- [ ] 确保 `download_url` 指向有效的可执行文件
- [ ] 测试版本检查功能
- [ ] 测试下载功能
- [ ] 验证菜单显示正确
- [ ] 在 PyInstaller 打包前测试
