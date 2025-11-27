# Fika 联机功能文档

## 功能概述

Fika 联机功能模块为 SPT 自动安装器添加了完整的多人联机支持，允许玩家通过 Fika MOD 进行联机游戏。

## 功能列表

### 1. 启动联机

**功能描述**：初始化联机环境，自动下载并安装 Fika MOD。

**执行流程**：
1. 检查是否已安装 Fika MOD（客户端 + 服务端）
2. 如果未安装：
   - 自动从公告 JSON 获取 Fika MOD 下载链接
   - 静默下载 Fika MOD 到 `resources/mods` 文件夹
   - 自动安装 MOD 到游戏目录
   - 显示提示："联机MOD已安装完成"
3. 如果已安装：跳过下载和安装步骤
4. 配置默认联机环境：
   - 修改 `SPT/user/launcher/config.json` → `Server.Url` = `https://127.0.0.1:6969`
   - 修改 `BepInEx/config/com.fika.core.cfg` → `Force IP` = `Disabled`
   - 修改 `SPT/user/mods/fika-server/assets/configs/fika.jsonc` → 默认本地配置
5. 提示用户登录游戏完成初始化
6. 询问是否关闭游戏进程

**使用场景**：首次使用联机功能时必须执行此步骤。

---

### 2. 创建服务器（房主模式）

**功能描述**：配置为房主模式，允许其他玩家连接到你的服务器。

**前置条件**：必须先执行"启动联机"功能。

**执行流程**：
1. 检查是否已启动联机（检测 Fika MOD 是否存在）
2. 提示用户输入公网 IP（用于其他玩家连接）
3. 修改配置文件：
   - `SPT/user/launcher/config.json` → `Server.Url` = `https://[公网IP]:6969`
   - `BepInEx/config/com.fika.core.cfg` → `Force IP` = `[公网IP]`, `Force Bind IP` = `Disabled`
   - `SPT/user/mods/fika-server/assets/configs/fika.jsonc` → `ip` = `0.0.0.0`, `backendIp` = `[公网IP]`
4. 显示配置完成信息和服务器 IP
5. 询问是否启动游戏（服务端 + 客户端）

**配置说明**：
- **公网 IP**：你的路由器/服务器的公网 IP 地址
- **端口**：默认 6969（需要在路由器上做端口转发）
- **Force IP**：设置为你的公网 IP，确保其他玩家能正确连接

**注意事项**：
- 需要在路由器上配置端口转发（6969 端口）
- 确保防火墙允许该端口的入站连接

---

### 3. 加入服务器（客户端模式）

**功能描述**：配置为客户端模式，连接到房主的服务器。

**前置条件**：必须先执行"启动联机"功能。

**执行流程**：
1. 检查是否已启动联机
2. 提示用户输入：
   - 房主的公网 IP（创建者服务器 IP）
   - 自己的公网 IP（用于 Force IP）
3. 修改配置文件：
   - `SPT/user/launcher/config.json` → `Server.Url` = `https://[房主IP]:6969`
   - `BepInEx/config/com.fika.core.cfg` → `Force IP` = `[自己的公网IP]`, `Force Bind IP` = `Disabled`
   - `SPT/user/mods/fika-server/assets/configs/fika.jsonc` → `ip` = `0.0.0.0`, `backendIp` = `0.0.0.0`
4. 显示配置完成信息
5. 询问是否启动游戏（仅客户端，不启动服务端）

**配置说明**：
- **房主 IP**：从房主处获取的公网 IP 地址
- **自己的 IP**：你自己的公网 IP（用于 P2P 连接）

**注意事项**：
- 客户端模式下不会启动服务端进程
- 需要确保能够连接到房主的服务器

---

### 4. 关闭联机

**功能描述**：完全移除联机功能，恢复单机模式。

**执行流程**：
1. 检查游戏进程是否正在运行
2. 如果游戏运行中：
   - 提示用户关闭游戏
   - 询问是否强制关闭进程
   - 调用 `close_spt_processes()` 关闭游戏
3. 删除联机相关文件夹：
   - `SPT/user/mods/fika-server`（整个文件夹）
   - `BepInEx/plugins/Fika`（整个文件夹）
4. 恢复默认配置：
   - `SPT/user/launcher/config.json` → `Server.Url` = `https://127.0.0.1:6969`
5. 显示完成信息

**注意事项**：
- 此操作会彻底删除所有联机组件
- 如需再次使用联机功能，需要重新执行"启动联机"

---

## 技术实现

### 核心模块

**文件**：`scripts/fika_manager.py`

**主要函数**：
- `start_fika(state)` - 启动联机
- `create_server(state)` - 创建服务器
- `join_server(state)` - 加入服务器
- `close_fika(state)` - 关闭联机

**辅助函数**：
- `_download_and_install_fika()` - 自动下载并安装 Fika MOD
- `_is_fika_installed()` - 检查 Fika 是否已安装
- `_update_json_file()` - 更新 JSON 配置文件
- `_update_cfg_file()` - 更新 .cfg 配置文件
- `_launch_game_with_server()` - 启动游戏（含服务端）
- `_launch_game_client_only()` - 仅启动客户端

### 配置文件说明

#### 1. launcher/config.json
```json
{
  "Server": {
    "Url": "https://127.0.0.1:6969"  // 服务器地址
  }
}
```

#### 2. com.fika.core.cfg
```ini
[Network]
Force IP = 192.168.1.100  // 强制使用的 IP
Force Bind IP = Disabled  // 强制绑定 IP（通常禁用）
```

#### 3. fika.jsonc
```jsonc
{
  "server": {
    "SPT": {
      "http": {
        "ip": "0.0.0.0",           // 监听地址
        "backendIp": "127.0.0.1"   // 后端 IP
      }
    }
  }
}
```

### 菜单集成

**位置**：主菜单 → 其他 → Fika 联机功能

**菜单选项**：
1. 启动联机
2. 创建服务器（房主模式）
3. 加入服务器（客户端模式）
4. 关闭联机
0. 返回上级菜单

---

## 使用指南

### 房主（创建服务器）

1. 选择"启动联机"（首次使用）
2. 登录游戏一次，完成初始化后退出
3. 选择"创建服务器"
4. 输入你的公网 IP
5. 启动游戏，等待其他玩家加入

### 客户端（加入服务器）

1. 选择"启动联机"（首次使用）
2. 登录游戏一次，完成初始化后退出
3. 选择"加入服务器"
4. 输入房主的公网 IP
5. 输入你自己的公网 IP
6. 启动游戏，连接到房主服务器

### 恢复单机模式

1. 选择"关闭联机"
2. 确认删除所有联机组件
3. 游戏将恢复到纯单机模式

---

## 常见问题

### Q: 如何获取公网 IP？
A: 访问 https://ip.sb 或 https://whatismyip.com 查看你的公网 IP。

### Q: 无法连接到房主服务器？
A: 
- 检查房主是否正确配置了端口转发（6969 端口）
- 确认防火墙允许该端口的入站连接
- 验证输入的 IP 地址是否正确

### Q: 启动联机后游戏崩溃？
A: 
- 确保 Fika MOD 版本与游戏版本兼容
- 检查是否有其他冲突的 MOD
- 尝试重新安装联机功能

### Q: 如何更新 Fika MOD？
A: 
1. 选择"关闭联机"移除旧版本
2. 删除 `resources/mods` 中的旧 Fika MOD 压缩包
3. 重新选择"启动联机"下载最新版本

---

## 更新日志

### v1.0 (2025-11-27)
- ✅ 实现启动联机功能
- ✅ 实现创建服务器功能
- ✅ 实现加入服务器功能
- ✅ 实现关闭联机功能
- ✅ 自动下载并安装 Fika MOD
- ✅ 配置文件自动修改
- ✅ 游戏进程管理
- ✅ 菜单集成

---

## 技术支持

如有问题，请联系：
- 官方交流群：1067632016
- 官方网站：tkf.pyden.dev
