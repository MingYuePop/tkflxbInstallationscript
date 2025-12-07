/* ============================================
   SPT 自动安装器 - JavaScript 应用逻辑
   ============================================ */

/* ============ 全局状态管理 ============ */
const AppState = {
    currentPage: 'home',
    installPath: null,
    serverStatus: 'offline',
    clientStatus: 'offline',
    fikaMode: 'solo', // solo, host, client
    installedMods: [],
    profiles: [],
    serverVersions: []
};

/* ============ DOM 元素缓存 ============ */
const DOM = {
    // 导航
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page'),

    // 顶部栏
    currentPath: document.getElementById('currentPath'),
    selectPathBtn: document.getElementById('selectPathBtn'),
    checkUpdateBtn: document.getElementById('checkUpdateBtn'),

    // 公告
    announcementBar: document.getElementById('announcementBar'),

    // 模态框
    modalOverlay: document.getElementById('modalOverlay'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
    modalFooter: document.getElementById('modalFooter'),
    modalClose: document.getElementById('modalClose'),
    modalCancel: document.getElementById('modalCancel'),
    modalConfirm: document.getElementById('modalConfirm'),

    // Toast 容器
    toastContainer: document.getElementById('toastContainer'),

    // 安装页面
    installPath: document.getElementById('installPath'),
    browsePathBtn: document.getElementById('browsePathBtn'),
    installProgress: document.getElementById('installProgress'),
    installStatus: document.getElementById('installStatus'),
    installPercent: document.getElementById('installPercent'),
    installLog: document.getElementById('installLog'),
    startInstallBtn: document.getElementById('startInstallBtn'),

    // 启动页面
    serverStatus: document.getElementById('serverStatus'),
    clientStatus: document.getElementById('clientStatus'),
    launchServerBtn: document.getElementById('launchServerBtn'),
    launchClientBtn: document.getElementById('launchClientBtn'),
    launchAllBtn: document.getElementById('launchAllBtn'),

    // MOD 页面
    modList: document.getElementById('modList'),
    downloadModBtn: document.getElementById('downloadModBtn'),
    installModBtn: document.getElementById('installModBtn'),
    uninstallAllModsBtn: document.getElementById('uninstallAllModsBtn'),

    // Fika 页面
    fikaCurrentStatus: document.getElementById('fikaCurrentStatus'),
    fikaOptions: document.querySelectorAll('.fika-option-card'),

    // 存档页面
    profileList: document.getElementById('profileList'),
    exportProfileBtn: document.getElementById('exportProfileBtn'),
    importProfileBtn: document.getElementById('importProfileBtn'),

    // 服务端版本页面
    serverList: document.getElementById('serverList'),
    downloadServerBtn: document.getElementById('downloadServerBtn'),
    switchServerBtn: document.getElementById('switchServerBtn'),

    // 设置页面
    installDotnetBtn: document.getElementById('installDotnetBtn'),
    checkUpdateBtnSettings: document.getElementById('checkUpdateBtnSettings'),
    uninstallGameBtn: document.getElementById('uninstallGameBtn'),

    // 主页统计
    modCount: document.getElementById('modCount'),
    serverVersion: document.getElementById('serverVersion'),
    fikaStatus: document.getElementById('fikaStatus'),
    profileCount: document.getElementById('profileCount')
};

/* ============ 页面导航模块 ============ */
const Navigation = {
    init() {
        DOM.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });

        // 快捷操作卡片点击
        document.querySelectorAll('.action-card').forEach(card => {
            card.addEventListener('click', () => {
                const action = card.dataset.action;
                if (action === 'install') {
                    this.navigateTo('install');
                } else if (action === 'launch') {
                    this.navigateTo('launch');
                }
            });
        });
    },

    navigateTo(pageName) {
        // 更新导航状态
        DOM.navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.page === pageName);
        });

        // 更新页面显示
        DOM.pages.forEach(page => {
            page.classList.toggle('active', page.id === `page-${pageName}`);
        });

        AppState.currentPage = pageName;
    }
};

/* ============ 模态框模块 ============ */
const Modal = {
    show(title, content, options = {}) {
        DOM.modalTitle.textContent = title;
        DOM.modalBody.innerHTML = content;

        // 配置按钮
        if (options.hideCancel) {
            DOM.modalCancel.style.display = 'none';
        } else {
            DOM.modalCancel.style.display = 'block';
            DOM.modalCancel.textContent = options.cancelText || '取消';
        }

        if (options.hideConfirm) {
            DOM.modalConfirm.style.display = 'none';
        } else {
            DOM.modalConfirm.style.display = 'block';
            DOM.modalConfirm.textContent = options.confirmText || '确认';
            DOM.modalConfirm.className = `btn ${options.confirmClass || 'btn-primary'}`;
        }

        // 设置回调
        this.onConfirm = options.onConfirm || (() => { });
        this.onCancel = options.onCancel || (() => { });

        DOM.modalOverlay.classList.add('active');
    },

    hide() {
        DOM.modalOverlay.classList.remove('active');
    },

    init() {
        DOM.modalClose.addEventListener('click', () => this.hide());
        DOM.modalCancel.addEventListener('click', () => {
            this.onCancel();
            this.hide();
        });
        DOM.modalConfirm.addEventListener('click', () => {
            this.onConfirm();
            this.hide();
        });
        DOM.modalOverlay.addEventListener('click', (e) => {
            if (e.target === DOM.modalOverlay) {
                this.hide();
            }
        });
    }
};

/* ============ Toast 通知模块 ============ */
const Toast = {
    show(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
        `;

        DOM.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

/* ============ 安装模块 ============ */
const Installer = {
    isInstalling: false,

    init() {
        DOM.browsePathBtn?.addEventListener('click', () => this.browsePath());
        DOM.startInstallBtn?.addEventListener('click', () => this.startInstall());
        DOM.selectPathBtn?.addEventListener('click', () => this.browsePath());
    },

    browsePath() {
        // 这里将来会调用 pywebview API
        // 现在模拟选择路径
        Modal.show('选择安装路径', `
            <p>请选择 SPT 游戏的安装目录。</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                提示：建议选择一个空文件夹或新建文件夹作为安装目录。
            </p>
        `, {
            confirmText: '选择文件夹',
            onConfirm: () => {
                // 模拟选择了路径
                const mockPath = 'D:\\Games\\SPT';
                this.setPath(mockPath);
                Toast.show('已选择安装路径', 'success');
            }
        });
    },

    setPath(path) {
        AppState.installPath = path;
        DOM.currentPath.textContent = path;
        if (DOM.installPath) {
            DOM.installPath.value = path;
        }
    },

    startInstall() {
        if (this.isInstalling) {
            Toast.show('安装正在进行中...', 'warning');
            return;
        }

        if (!AppState.installPath) {
            Toast.show('请先选择安装路径', 'warning');
            return;
        }

        Modal.show('确认安装', `
            <p>即将开始安装 SPT 游戏到以下目录：</p>
            <p style="margin-top: 8px; padding: 10px; background: var(--bg-tertiary); border-radius: var(--radius-md); font-family: monospace;">
                ${AppState.installPath}
            </p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                安装过程可能需要几分钟，请耐心等待。
            </p>
        `, {
            confirmText: '开始安装',
            onConfirm: () => this.doInstall()
        });
    },

    doInstall() {
        this.isInstalling = true;
        DOM.startInstallBtn.disabled = true;
        DOM.startInstallBtn.innerHTML = `
            <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            安装中...
        `;

        // 模拟安装进度
        this.simulateInstall();
    },

    simulateInstall() {
        const steps = [
            { progress: 10, status: '正在检查系统环境...' },
            { progress: 20, status: '正在下载 SPT 服务端...' },
            { progress: 40, status: '正在解压文件...' },
            { progress: 60, status: '正在配置游戏...' },
            { progress: 80, status: '正在安装补丁...' },
            { progress: 95, status: '正在完成安装...' },
            { progress: 100, status: '安装完成！' }
        ];

        let stepIndex = 0;

        const runStep = () => {
            if (stepIndex >= steps.length) {
                this.installComplete();
                return;
            }

            const step = steps[stepIndex];
            this.updateProgress(step.progress, step.status);
            this.addLog(step.status, step.progress === 100 ? 'success' : '');

            stepIndex++;
            setTimeout(runStep, 1000 + Math.random() * 1000);
        };

        runStep();
    },

    updateProgress(percent, status) {
        DOM.installProgress.style.width = `${percent}%`;
        DOM.installPercent.textContent = `${percent}%`;
        DOM.installStatus.textContent = status;
    },

    addLog(message, type = '') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        DOM.installLog.appendChild(entry);
        DOM.installLog.scrollTop = DOM.installLog.scrollHeight;
    },

    installComplete() {
        this.isInstalling = false;
        DOM.startInstallBtn.disabled = false;
        DOM.startInstallBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            开始自动安装
        `;

        Toast.show('游戏安装完成！', 'success');

        // 更新主页统计
        DOM.serverVersion.textContent = '3.10.5';
    }
};

/* ============ 启动器模块 ============ */
const Launcher = {
    init() {
        DOM.launchServerBtn?.addEventListener('click', () => this.launchServer());
        DOM.launchClientBtn?.addEventListener('click', () => this.launchClient());
        DOM.launchAllBtn?.addEventListener('click', () => this.launchAll());
    },

    launchServer() {
        Toast.show('正在启动服务端...', 'success');
        this.updateServerStatus('running');
    },

    launchClient() {
        if (AppState.serverStatus !== 'running') {
            Toast.show('请先启动服务端', 'warning');
            return;
        }
        Toast.show('正在启动客户端...', 'success');
        this.updateClientStatus('running');
    },

    launchAll() {
        Toast.show('正在启动游戏...', 'success');

        setTimeout(() => {
            this.updateServerStatus('running');
            setTimeout(() => {
                this.updateClientStatus('running');
                Toast.show('游戏已启动！', 'success');
            }, 1500);
        }, 1000);
    },

    updateServerStatus(status) {
        AppState.serverStatus = status;
        const statusEl = DOM.serverStatus;
        if (status === 'running') {
            statusEl.innerHTML = '<span class="status-dot online"></span> 运行中';
            DOM.launchServerBtn.textContent = '停止';
        } else {
            statusEl.innerHTML = '<span class="status-dot offline"></span> 未运行';
            DOM.launchServerBtn.textContent = '启动';
        }
    },

    updateClientStatus(status) {
        AppState.clientStatus = status;
        const statusEl = DOM.clientStatus;
        if (status === 'running') {
            statusEl.innerHTML = '<span class="status-dot online"></span> 运行中';
            DOM.launchClientBtn.textContent = '停止';
        } else {
            statusEl.innerHTML = '<span class="status-dot offline"></span> 未运行';
            DOM.launchClientBtn.textContent = '启动';
        }
    }
};

/* ============ MOD 管理模块 ============ */
const ModManager = {
    init() {
        DOM.downloadModBtn?.addEventListener('click', () => this.downloadMod());
        DOM.installModBtn?.addEventListener('click', () => this.installMod());
        DOM.uninstallAllModsBtn?.addEventListener('click', () => this.uninstallAllMods());
    },

    downloadMod() {
        Modal.show('下载 MOD', `
            <p>从 MOD 仓库下载并安装 MOD。</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                此功能将打开 MOD 下载列表，您可以选择需要的 MOD 进行下载。
            </p>
        `, {
            confirmText: '打开下载列表',
            onConfirm: () => {
                Toast.show('正在获取 MOD 列表...', 'success');
            }
        });
    },

    installMod() {
        Modal.show('安装 MOD', `
            <p>从本地文件安装 MOD。</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                支持 .zip 格式的 MOD 文件。
            </p>
        `, {
            confirmText: '选择文件',
            onConfirm: () => {
                Toast.show('请选择 MOD 文件', 'success');
            }
        });
    },

    uninstallAllMods() {
        Modal.show('确认卸载', `
            <p style="color: var(--danger);">⚠️ 此操作将卸载所有已安装的 MOD！</p>
            <p style="margin-top: 12px;">确定要继续吗？此操作不可撤销。</p>
        `, {
            confirmText: '确认卸载',
            confirmClass: 'btn-danger',
            onConfirm: () => {
                Toast.show('已卸载所有 MOD', 'success');
                DOM.modCount.textContent = '0';
            }
        });
    }
};

/* ============ Fika 联机模块 ============ */
const FikaManager = {
    init() {
        DOM.fikaOptions?.forEach(option => {
            option.addEventListener('click', () => {
                const action = option.dataset.action;
                this.handleAction(action);
            });
        });
    },

    handleAction(action) {
        switch (action) {
            case 'host':
                this.beHost();
                break;
            case 'join':
                this.joinHost();
                break;
            case 'solo':
                this.restoreSolo();
                break;
        }
    },

    beHost() {
        Modal.show('创建服务器', `
            <p>您将作为房主创建联机服务器。</p>
            <div style="margin-top: 16px;">
                <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">服务器端口</label>
                <input type="text" class="path-input" value="6969" style="width: 100%;">
            </div>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                创建后，将您的 IP 地址分享给好友即可加入。
            </p>
        `, {
            confirmText: '创建服务器',
            onConfirm: () => {
                this.updateStatus('host');
                Toast.show('服务器创建成功！', 'success');
            }
        });
    },

    joinHost() {
        Modal.show('加入服务器', `
            <p>输入房主的服务器地址加入游戏。</p>
            <div style="margin-top: 16px;">
                <label style="display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px;">服务器地址</label>
                <input type="text" class="path-input" placeholder="例如: 192.168.1.100:6969" style="width: 100%;">
            </div>
        `, {
            confirmText: '加入服务器',
            onConfirm: () => {
                this.updateStatus('client');
                Toast.show('正在连接服务器...', 'success');
            }
        });
    },

    restoreSolo() {
        Modal.show('恢复单机模式', `
            <p>确定要切换回单机模式吗？</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                这将断开当前的联机连接。
            </p>
        `, {
            confirmText: '确认',
            onConfirm: () => {
                this.updateStatus('solo');
                Toast.show('已切换到单机模式', 'success');
            }
        });
    },

    updateStatus(mode) {
        AppState.fikaMode = mode;

        const statusTexts = {
            solo: '单机模式',
            host: '联机模式 (房主)',
            client: '联机模式 (客户端)'
        };

        DOM.fikaCurrentStatus.textContent = statusTexts[mode];
        DOM.fikaStatus.textContent = mode === 'solo' ? '单机' : '联机';

        // 更新侧边栏状态
        const statusIndicator = document.querySelector('.status-text');
        statusIndicator.textContent = statusTexts[mode];

        const statusDot = document.querySelector('.sidebar-footer .status-dot');
        statusDot.classList.toggle('online', mode !== 'solo');
    }
};

/* ============ 存档管理模块 ============ */
const ProfileManager = {
    init() {
        DOM.exportProfileBtn?.addEventListener('click', () => this.exportProfile());
        DOM.importProfileBtn?.addEventListener('click', () => this.importProfile());
    },

    exportProfile() {
        Modal.show('导出存档', `
            <p>将当前存档导出为备份文件。</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                导出的存档可以在其他设备上导入使用。
            </p>
        `, {
            confirmText: '选择保存位置',
            onConfirm: () => {
                Toast.show('存档导出成功！', 'success');
            }
        });
    },

    importProfile() {
        Modal.show('导入存档', `
            <p>从备份文件导入存档。</p>
            <p style="margin-top: 12px; color: var(--warning); font-size: 13px;">
                ⚠️ 导入将覆盖当前存档，请确保已备份。
            </p>
        `, {
            confirmText: '选择文件',
            onConfirm: () => {
                Toast.show('存档导入成功！', 'success');
            }
        });
    }
};

/* ============ 服务端版本管理模块 ============ */
const ServerVersionManager = {
    init() {
        DOM.downloadServerBtn?.addEventListener('click', () => this.downloadVersion());
        DOM.switchServerBtn?.addEventListener('click', () => this.switchVersion());
    },

    downloadVersion() {
        Modal.show('下载服务端版本', `
            <p>选择要下载的服务端版本：</p>
            <div class="version-list" style="margin-top: 16px;">
                <label class="version-item">
                    <input type="radio" name="download-version" value="3.10.5" checked>
                    <div class="version-info">
                        <span class="version-name">SPT 3.10.5</span>
                        <span class="version-tag latest">最新</span>
                    </div>
                </label>
                <label class="version-item">
                    <input type="radio" name="download-version" value="3.10.4">
                    <div class="version-info">
                        <span class="version-name">SPT 3.10.4</span>
                    </div>
                </label>
            </div>
        `, {
            confirmText: '开始下载',
            onConfirm: () => {
                Toast.show('正在下载服务端...', 'success');
            }
        });
    },

    switchVersion() {
        Toast.show('请从列表中选择要切换的版本', 'warning');
    }
};

/* ============ 设置模块 ============ */
const Settings = {
    init() {
        DOM.installDotnetBtn?.addEventListener('click', () => this.installDotnet());
        DOM.checkUpdateBtnSettings?.addEventListener('click', () => this.checkUpdate());
        DOM.checkUpdateBtn?.addEventListener('click', () => this.checkUpdate());
        DOM.uninstallGameBtn?.addEventListener('click', () => this.uninstallGame());
    },

    installDotnet() {
        Modal.show('安装 .NET 环境', `
            <p>即将安装 .NET 6.0 运行时环境。</p>
            <p style="margin-top: 12px; color: var(--text-muted); font-size: 13px;">
                这是运行 SPT 服务端所必需的组件。
            </p>
        `, {
            confirmText: '开始安装',
            onConfirm: () => {
                Toast.show('正在安装 .NET 环境...', 'success');
            }
        });
    },

    checkUpdate() {
        Toast.show('正在检查更新...', 'success');

        setTimeout(() => {
            Modal.show('检查更新', `
                <div style="text-align: center; padding: 20px 0;">
                    <svg style="width: 48px; height: 48px; color: var(--success); margin-bottom: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    <p style="font-size: 16px; font-weight: 500;">当前已是最新版本</p>
                    <p style="margin-top: 8px; color: var(--text-secondary);">版本 v1.0.0</p>
                </div>
            `, {
                hideCancel: true,
                confirmText: '确定'
            });
        }, 1500);
    },

    uninstallGame() {
        Modal.show('卸载游戏', `
            <p style="color: var(--danger);">⚠️ 危险操作！</p>
            <p style="margin-top: 12px;">此操作将完全删除已安装的 SPT 游戏，包括：</p>
            <ul style="margin-top: 8px; padding-left: 20px; color: var(--text-secondary);">
                <li>游戏文件</li>
                <li>服务端文件</li>
                <li>MOD 文件</li>
                <li>存档数据</li>
            </ul>
            <p style="margin-top: 12px; color: var(--danger); font-weight: 500;">此操作不可撤销！</p>
        `, {
            confirmText: '确认卸载',
            confirmClass: 'btn-danger',
            onConfirm: () => {
                Toast.show('游戏已卸载', 'success');
            }
        });
    }
};

/* ============ 应用初始化 ============ */
const App = {
    init() {
        // 初始化所有模块
        Navigation.init();
        Modal.init();
        Installer.init();
        Launcher.init();
        ModManager.init();
        FikaManager.init();
        ProfileManager.init();
        ServerVersionManager.init();
        Settings.init();

        // 添加 CSS 动画
        this.addStyles();

        console.log('SPT 自动安装器已初始化');
    },

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            .spin {
                animation: spin 1s linear infinite;
            }
        `;
        document.head.appendChild(style);
    }
};

/* ============ 启动应用 ============ */
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

/* ============ PyWebView API 桥接（预留） ============ */
// 当 pywebview 准备就绪时，这些函数将被调用
window.pywebviewReady = false;

window.addEventListener('pywebviewready', () => {
    window.pywebviewReady = true;
    console.log('PyWebView API 已就绪');

    // 这里可以调用 Python 后端的初始化函数
    // window.pywebview.api.init().then(...)
});
