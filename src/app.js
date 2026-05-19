// 空气等熵压缩过程 - 交互式图形应用
// 工程热力学课程设计

// ==================== 常量定义 ====================
const CONSTANTS = {
    R: 287.058,              // 空气气体常数，J/(kg·K)
    R_MOL: 8.314,            // 通用气体常数，J/(mol·K)
    K: 1.4,                  // 空气比热容比（常数假设）
    M: 0.02897                // 空气摩尔质量，kg/mol
};

// ==================== 默认状态 ====================
const DEFAULT_STATE = {
    temperature: 300,        // 初始温度，K
    pressure: 101325,        // 初始压力，Pa
    compressionRatio: 4,     // 压缩比
    specificHeatMode: 'both' // 显示模式: 'constant', 'variable', 'both'
};

// ==================== 应用状态 ====================
let appState = { ...DEFAULT_STATE };
let uploadedImage = null;

// ==================== DOM 元素引用 ====================
const elements = {
    temperature: document.getElementById('temperature'),
    temperatureValue: document.getElementById('temperature-value'),
    pressure: document.getElementById('pressure'),
    pressureValue: document.getElementById('pressure-value'),
    compression: document.getElementById('compression'),
    compressionValue: document.getElementById('compression-value'),
    mode: document.getElementById('mode'),
    initialV: document.getElementById('initial-v'),
    finalPConstant: document.getElementById('final-p-constant'),
    finalPVariable: document.getElementById('final-p-variable'),
    saveConfig: document.getElementById('save-config'),
    exportImage: document.getElementById('export-image'),
    reset: document.getElementById('reset'),
    canvas: document.getElementById('main-canvas'),
    graphContainer: document.getElementById('graph-container'),
    graphOverlay: document.getElementById('graph-overlay'),
    fileInput: document.getElementById('file-input'),
    notification: document.getElementById('notification')
};

// ==================== 计算模块 ====================
const Calculator = {
    // 计算定压摩尔热容 (温度函数)
    getCpMol: function(T) {
        return 28.11 + 0.1967e-2 * T + 0.4802e-5 * T * T - 1.966e-9 * T * T * T;
    },

    // 计算定容摩尔热容
    getCvMol: function(T) {
        return this.getCpMol(T) - CONSTANTS.R_MOL;
    },

    // 计算比热容比
    getK: function(T) {
        const cp = this.getCpMol(T);
        const cv = this.getCvMol(T);
        return cp / cv;
    },

    // 计算比容
    calculateV: function(p, T) {
        return CONSTANTS.R * T / p;
    },

    // 常数比热容：等熵过程压力计算
    calculateConstantK: function(v, v0, p0, k = CONSTANTS.K) {
        return p0 * Math.pow(v0 / v, k);
    },

    // 变比热容：等熵过程数值求解
    calculateVariableK: function(vArray, v0, p0, T0) {
        const pArray = [p0];
        let T_prev = T0;
        let p_prev = p0;
        let v_prev = v0;

        for (let i = 1; i < vArray.length; i++) {
            const v = vArray[i];
            
            // 数值积分：使用改进欧拉法
            const dv = v - v_prev;
            const cv_mol = this.getCvMol(T_prev);
            const dT = -CONSTANTS.R_MOL * T_prev / cv_mol * (dv / v_prev);
            const T_mid = T_prev + dT / 2;
            const cv_mid = this.getCvMol(T_mid);
            const dT_corr = -CONSTANTS.R_MOL * T_mid / cv_mid * (dv / v_prev);
            const T_new = T_prev + dT_corr;
            
            const p_new = p_prev * (v_prev / v) * (T_new / T_prev);
            
            pArray.push(p_new);
            T_prev = T_new;
            p_prev = p_new;
            v_prev = v;
        }

        return pArray;
    }
};

// ==================== 渲染模块 ====================
const Renderer = {
    ctx: null,
    width: 0,
    height: 0,
    padding: 60,

    // 初始化画布
    init: function() {
        this.ctx = elements.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
    },

    // 调整画布大小
    resize: function() {
        const container = elements.graphContainer;
        const rect = container.getBoundingClientRect();
        
        this.width = rect.width - 48;
        this.height = rect.height - 48;
        
        elements.canvas.width = this.width;
        elements.canvas.height = this.height;
        
        this.render();
    },

    // 主渲染函数
    render: function() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;

        // 清空画布
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, w, h);

        // 绘制背景网格
        this.drawGrid();

        // 绘制坐标轴
        this.drawAxes();

        // 绘制上传的图像（如果有）
        if (uploadedImage) {
            this.drawUploadedImage();
        }

        // 计算并绘制等熵曲线
        this.drawIsentropicCurves();
    },

    // 绘制背景网格
    drawGrid: function() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const p = this.padding;

        ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)';
        ctx.lineWidth = 1;

        // 垂直网格线
        const xStep = (w - 2 * p) / 10;
        for (let i = 0; i <= 10; i++) {
            const x = p + i * xStep;
            ctx.beginPath();
            ctx.moveTo(x, p);
            ctx.lineTo(x, h - p);
            ctx.stroke();
        }

        // 水平网格线
        const yStep = (h - 2 * p) / 8;
        for (let i = 0; i <= 8; i++) {
            const y = p + i * yStep;
            ctx.beginPath();
            ctx.moveTo(p, y);
            ctx.lineTo(w - p, y);
            ctx.stroke();
        }
    },

    // 绘制坐标轴
    drawAxes: function() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const p = this.padding;

        ctx.strokeStyle = 'rgba(241, 245, 249, 0.3)';
        ctx.lineWidth = 2;

        // X轴
        ctx.beginPath();
        ctx.moveTo(p, h - p);
        ctx.lineTo(w - p, h - p);
        ctx.stroke();

        // Y轴
        ctx.beginPath();
        ctx.moveTo(p, h - p);
        ctx.lineTo(p, p);
        ctx.stroke();

        // 坐标轴标签
        ctx.fillStyle = '#cbd5e1';
        ctx.font = '14px "JetBrains Mono"';
        ctx.textAlign = 'center';
        ctx.fillText('比容 v (m³/kg)', w / 2, h - 15);
        
        ctx.save();
        ctx.translate(20, h / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('压力 p (kPa)', 0, 0);
        ctx.restore();

        // 刻度标签
        ctx.font = '10px "Fira Code"';
        ctx.fillStyle = '#94a3b8';
        
        const T0 = appState.temperature;
        const p0 = appState.pressure;
        const v0 = Calculator.calculateV(p0, T0);
        const vMin = v0 / appState.compressionRatio;
        const vMax = v0 * 1.2;
        const pMax = p0 * Math.pow(appState.compressionRatio, CONSTANTS.K) * 1.1;

        // X轴刻度
        for (let i = 0; i <= 5; i++) {
            const v = vMin + (vMax - vMin) * i / 5;
            const x = p + (v - vMin) / (vMax - vMin) * (w - 2 * p);
            ctx.fillText(v.toFixed(3), x, h - p + 20);
        }

        // Y轴刻度
        for (let i = 0; i <= 5; i++) {
            const p_val = pMax * i / 5;
            const y = h - p - (p_val) / pMax * (h - 2 * p);
            ctx.textAlign = 'right';
            ctx.fillText((p_val / 1000).toFixed(1), p - 10, y + 4);
        }
    },

    // 绘制等熵曲线
    drawIsentropicCurves: function() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const p = this.padding;

        const T0 = appState.temperature;
        const p0 = appState.pressure;
        const v0 = Calculator.calculateV(p0, T0);
        const vMin = v0 / appState.compressionRatio;
        const vMax = v0 * 1.2;
        const pMax = p0 * Math.pow(appState.compressionRatio, CONSTANTS.K) * 1.1;

        // 生成比容数组
        const numPoints = 200;
        const vArray = [];
        for (let i = 0; i < numPoints; i++) {
            vArray.push(vMin + (vMax - vMin) * i / (numPoints - 1));
        }

        // 坐标转换函数
        const toCanvasX = (v) => p + (v - vMin) / (vMax - vMin) * (w - 2 * p);
        const toCanvasY = (p_val) => h - p - (p_val) / pMax * (h - 2 * p);

        // 绘制常数比热容曲线
        if (appState.specificHeatMode === 'both' || appState.specificHeatMode === 'constant') {
            ctx.strokeStyle = '#0ea5e9';
            ctx.lineWidth = 3;
            ctx.beginPath();
            
            for (let i = 0; i < vArray.length; i++) {
                const v = vArray[i];
                const p_val = Calculator.calculateConstantK(v, v0, p0);
                const x = toCanvasX(v);
                const y = toCanvasY(p_val);
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.stroke();
        }

        // 绘制变比热容曲线
        if (appState.specificHeatMode === 'both' || appState.specificHeatMode === 'variable') {
            const pArrayVar = Calculator.calculateVariableK(vArray, v0, p0, T0);
            
            ctx.strokeStyle = '#8b5cf6';
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 4]);
            ctx.beginPath();
            
            for (let i = 0; i < vArray.length; i++) {
                const v = vArray[i];
                const p_val = pArrayVar[i];
                const x = toCanvasX(v);
                const y = toCanvasY(p_val);
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // 绘制起点标记
        const startX = toCanvasX(v0);
        const startY = toCanvasY(p0);
        
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(startX, startY, 8, 0, 2 * Math.PI);
        ctx.fill();
        
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 更新状态信息
        this.updateInfo(v0, vArray, p0, pMax);
    },

    // 更新状态信息显示
    updateInfo: function(v0, vArray, p0, pMax) {
        const idx = Math.floor(vArray.length / 2);
        const vFinal = vArray[0];
        
        // 常数比热容终点压力
        const pFinalConst = Calculator.calculateConstantK(vFinal, v0, p0);
        
        // 变比热容终点压力
        const pArrayVar = Calculator.calculateVariableK(vArray, v0, p0, appState.temperature);
        const pFinalVar = pArrayVar[0];

        elements.initialV.textContent = v0.toFixed(4) + ' m³/kg';
        elements.finalPConstant.textContent = (pFinalConst / 1000).toFixed(2) + ' kPa';
        elements.finalPVariable.textContent = (pFinalVar / 1000).toFixed(2) + ' kPa';
    },

    // 绘制上传的图像
    drawUploadedImage: function() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const p = this.padding;

        ctx.globalAlpha = 0.3;
        
        // 计算缩放比例以适应画布
        const imgRatio = uploadedImage.width / uploadedImage.height;
        const canvasRatio = (w - 2 * p) / (h - 2 * p);
        
        let drawWidth, drawHeight;
        if (imgRatio > canvasRatio) {
            drawWidth = w - 2 * p;
            drawHeight = (w - 2 * p) / imgRatio;
        } else {
            drawHeight = h - 2 * p;
            drawWidth = (h - 2 * p) * imgRatio;
        }
        
        const x = p + (w - 2 * p - drawWidth) / 2;
        const y = p + (h - 2 * p - drawHeight) / 2;
        
        ctx.drawImage(uploadedImage, x, y, drawWidth, drawHeight);
        ctx.globalAlpha = 1;
    }
};

// ==================== 存储模块 ====================
const Storage = {
    STORAGE_KEY: 'isentropic_app_config',

    // 保存配置
    saveConfig: function() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(appState));
            showNotification('配置已保存！', 'success');
        } catch (e) {
            showNotification('保存失败：' + e.message, 'error');
        }
    },

    // 加载配置
    loadConfig: function() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                appState = JSON.parse(saved);
                updateUIFromState();
                showNotification('配置已加载！', 'success');
            }
        } catch (e) {
            console.error('加载配置失败:', e);
        }
    },

    // 导出图像
    exportImage: function() {
        try {
            const dataURL = elements.canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = 'isentropic_compression_' + new Date().toISOString().slice(0, 10) + '.png';
            link.href = dataURL;
            link.click();
            showNotification('图像已导出！', 'success');
        } catch (e) {
            showNotification('导出失败：' + e.message, 'error');
        }
    },

    // 重置配置
    resetConfig: function() {
        appState = { ...DEFAULT_STATE };
        updateUIFromState();
        uploadedImage = null;
        elements.graphOverlay.style.display = 'flex';
        showNotification('已重置为默认设置！', 'success');
    }
};

// ==================== UI 辅助函数 ====================
function updateUIFromState() {
    elements.temperature.value = appState.temperature;
    elements.temperatureValue.textContent = appState.temperature + ' K';
    
    elements.pressure.value = appState.pressure / 1000;
    elements.pressureValue.textContent = (appState.pressure / 1000).toFixed(2) + ' kPa';
    
    elements.compression.value = appState.compressionRatio;
    elements.compressionValue.textContent = appState.compressionRatio.toFixed(1) + ':1';
    
    elements.mode.value = appState.specificHeatMode;
    
    Renderer.render();
}

function updateStateFromUI() {
    appState.temperature = parseFloat(elements.temperature.value);
    appState.pressure = parseFloat(elements.pressure.value) * 1000;
    appState.compressionRatio = parseFloat(elements.compression.value);
    appState.specificHeatMode = elements.mode.value;
    
    elements.temperatureValue.textContent = appState.temperature + ' K';
    elements.pressureValue.textContent = (appState.pressure / 1000).toFixed(2) + ' kPa';
    elements.compressionValue.textContent = appState.compressionRatio.toFixed(1) + ':1';
    
    Renderer.render();
}

function showNotification(message, type = 'success') {
    elements.notification.textContent = message;
    elements.notification.className = 'notification ' + type + ' show';
    
    setTimeout(() => {
        elements.notification.classList.remove('show');
    }, 3000);
}

// ==================== 事件绑定 ====================
function bindEvents() {
    // 滑块和选择器事件
    elements.temperature.addEventListener('input', updateStateFromUI);
    elements.pressure.addEventListener('input', updateStateFromUI);
    elements.compression.addEventListener('input', updateStateFromUI);
    elements.mode.addEventListener('change', updateStateFromUI);

    // 按钮事件
    elements.saveConfig.addEventListener('click', () => Storage.saveConfig());
    elements.exportImage.addEventListener('click', () => Storage.exportImage());
    elements.reset.addEventListener('click', () => Storage.resetConfig());

    // 双击加载图像
    elements.graphContainer.addEventListener('dblclick', () => {
        elements.fileInput.click();
    });

    // 文件选择
    elements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    uploadedImage = img;
                    elements.graphOverlay.style.display = 'none';
                    Renderer.render();
                    showNotification('图像已加载！', 'success');
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 's') {
                e.preventDefault();
                Storage.saveConfig();
            } else if (e.key === 'e') {
                e.preventDefault();
                Storage.exportImage();
            } else if (e.key === 'r') {
                e.preventDefault();
                Storage.resetConfig();
            }
        }
    });
}

// ==================== 初始化 ====================
function init() {
    // 初始化渲染器
    Renderer.init();
    
    // 尝试加载保存的配置
    Storage.loadConfig();
    
    // 绑定事件
    bindEvents();
    
    // 初始渲染
    Renderer.render();
}

// 启动应用
window.addEventListener('DOMContentLoaded', init);
