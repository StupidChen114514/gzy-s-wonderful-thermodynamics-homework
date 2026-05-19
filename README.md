# 空气等熵压缩过程 - 交互式热力学分析工具

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/HTML5-Canvas-orange.svg" alt="HTML5">
</p>

一个用于可视化空气等熵压缩过程的交互式Web应用。通过此工具，用户可以直观地观察和分析热力学过程中压力与比容的变化关系。

## 功能特性

- 实时交互式参数调节（初始温度、压力、压缩比）
- 支持常数比热容与变比热容两种计算模型对比
- 基于Canvas的高性能图形渲染
- 支持图像加载与叠加对比
- 配置保存与导出功能
- 响应式设计，适配多种屏幕尺寸

## 项目结构

```
gzy/
├── src/                      # 前端源代码
│   ├── index.html           # 主页面
│   ├── app.js               # 应用逻辑
│   └── styles.css           # 样式文件
├── scripts/                  # Python脚本
│   ├── start_server_v2.py   # 服务器启动脚本
│   └── stop_server_v2.py    # 服务器停止脚本
├── docs/                     # 项目文档
└── README.md                # 项目说明文件
```

## 快速开始

### 环境要求

- Python 3.6 或更高版本
- 现代浏览器（Chrome、Firefox、Edge、Safari）

### 安装与运行

1. 克隆仓库
```bash
git clone https://github.com/StupidChen114514/gzy.git
cd gzy
```

2. 启动服务
```bash
python scripts/start_server_v2.py
```

3. 在浏览器中访问
```
http://localhost:8000
```

### 使用方法

1. **调节参数**：通过左侧控制面板调节初始温度、压力和压缩比
2. **切换模式**：选择显示模式（常数比热容/变比热容/同时显示）
3. **加载图像**：双击画布区域加载本地图像进行对比
4. **保存配置**：点击保存按钮将当前配置保存至浏览器本地存储
5. **导出图像**：点击导出按钮将当前图形保存为PNG文件

## 技术栈

- **前端**：HTML5、CSS3、JavaScript
- **图形渲染**：HTML5 Canvas API
- **后端**：Python HTTP Server
- **计算模型**：工程热力学等熵过程计算

## 计算原理

### 常数比热容模型

使用固定的比热容比 k = 1.4 进行计算：

$$p = p_0 \cdot \left(\frac{v_0}{v}\right)^k$$

### 变比热容模型

考虑温度对比热容的影响，使用逐点数值积分方法求解：

$$C_p(T) = 28.11 + 0.1967 \times 10^{-2} T + 0.4802 \times 10^{-5} T^2 - 1.966 \times 10^{-9} T^3$$

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存配置 |
| `Ctrl + E` | 导出图像 |
| `Ctrl + R` | 重置参数 |

## 开发指南

### 运行开发服务器

```bash
python scripts/start_server_v2.py -p 8080
```

### 构建部署

本项目为纯静态页面，可直接部署至任何Web服务器：

```bash
# Nginx
cp -r src/* /var/www/html/

# Python http.server
cd src && python -m http.server 80
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 版本历史

- **v1.0.0** (2026-05-19)
  - 初始版本发布
  - 支持常数/变比热容两种计算模型
  - 实现交互式参数调节
  - 支持图像加载与导出功能

## 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 作者

[StupidChen114514](https://github.com/StupidChen114514)

## 致谢

- 工程热力学课程设计项目
- 基于热力学原理的数值计算方法参考
