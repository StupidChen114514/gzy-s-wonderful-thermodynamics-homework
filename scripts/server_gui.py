#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================
            空气等熵压缩应用 - 服务器控制面板 (GUI版)
=========================================================================

功能描述：
    提供图形化界面，实现一键启动/停止HTTP服务器
    无需任何命令行操作，点击按钮即可控制服务器

使用方法：
    双击运行此脚本，或 python server_gui.py

=========================================================================
"""

import os
import sys
import subprocess
import threading
import time
import socket
import signal
import platform

# Tkinter for GUI
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("错误：需要 tkinter 库。请运行: pip install tk")
    sys.exit(1)

# 配置常量
DEFAULT_PORT = 8000
DEFAULT_HOST = '127.0.0.1'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
PID_FILE = os.path.join(PROJECT_ROOT, '.server_pid')


class ServerGUI:
    """服务器控制面板"""

    def __init__(self, root):
        self.root = root
        self.root.title("空气等熵压缩应用 - 服务器控制面板")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # 服务器进程
        self.process = None
        self.server_thread = None
        self.is_running = False

        # 端口
        self.port = DEFAULT_PORT

        # 设置窗口图标（如果可用）
        self.setup_ui()

        # 注册关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # 检查是否有运行中的服务器
        self.check_existing_server()

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = tk.Frame(self.root, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="空气等熵压缩应用",
            font=("Microsoft YaHei UI", 18, "bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = tk.Label(
            main_frame,
            text="服务器控制面板",
            font=("Microsoft YaHei UI", 12),
            fg="gray"
        )
        subtitle_label.pack(pady=(0, 30))

        # 状态显示
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        tk.Label(status_frame, text="服务器状态：", font=("Microsoft YaHei UI", 11)).pack(side=tk.LEFT)
        self.status_label = tk.Label(
            status_frame,
            text="已停止",
            font=("Microsoft YaHei UI", 11, "bold"),
            fg="red"
        )
        self.status_label.pack(side=tk.LEFT)

        # URL显示
        url_frame = tk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=10)

        tk.Label(url_frame, text="访问地址：", font=("Microsoft YaHei UI", 11)).pack(side=tk.LEFT)
        self.url_label = tk.Label(
            url_frame,
            text=f"http://localhost:{DEFAULT_PORT}",
            font=("Microsoft YaHei UI", 11, "underline"),
            fg="blue",
            cursor="hand2"
        )
        self.url_label.pack(side=tk.LEFT)
        self.url_label.bind("<Button-1>", self.open_browser)

        # 按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=30)

        # 启动按钮
        self.start_button = tk.Button(
            button_frame,
            text="启动服务器",
            font=("Microsoft YaHei UI", 12),
            width=15,
            height=2,
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            command=self.start_server
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        # 停止按钮
        self.stop_button = tk.Button(
            button_frame,
            text="停止服务器",
            font=("Microsoft YaHei UI", 12),
            width=15,
            height=2,
            bg="#f44336",
            fg="white",
            relief=tk.FLAT,
            state=tk.DISABLED,
            command=self.stop_server
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # 日志显示区域
        log_frame = tk.LabelFrame(main_frame, text="控制台输出", font=("Microsoft YaHei UI", 10))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = tk.Text(log_frame, height=8, width=50, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 添加滚动条
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def log(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def update_status(self, running, url=None):
        """更新状态显示"""
        if running:
            self.status_label.config(text="运行中", fg="green")
            self.url_label.config(text=url or f"http://localhost:{self.port}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.is_running = True
        else:
            self.status_label.config(text="已停止", fg="red")
            self.url_label.config(text=f"http://localhost:{self.port}")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_running = False

    def check_existing_server(self):
        """检查是否有运行中的服务器"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', DEFAULT_PORT))
                if result == 0:
                    # 端口已被占用
                    self.log(f"检测到端口 {DEFAULT_PORT} 已被占用")
                    self.port = self.find_available_port()
                    if self.port != DEFAULT_PORT:
                        self.log(f"将使用端口 {self.port}")
        except Exception as e:
            self.log(f"检查端口时出错: {e}")

    def find_available_port(self, start=8000, end=9000):
        """查找可用端口"""
        for port in range(start, end):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result != 0:
                        return port
            except:
                pass
        return start

    def check_port_available(self, port):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result != 0
        except:
            return False

    def start_server(self):
        """启动服务器"""
        # 查找可用端口
        original_port = self.port
        while not self.check_port_available(self.port):
            self.log(f"端口 {self.port} 被占用，尝试下一个端口...")
            self.port += 1
            if self.port > 9000:
                self.port = original_port
                messagebox.showerror("错误", "无法找到可用端口")
                return

        if self.port != original_port:
            self.log(f"使用端口 {self.port}")

        # 在后台线程中启动服务器
        self.server_thread = threading.Thread(target=self._start_server_thread, daemon=True)
        self.server_thread.start()

        # 等待服务器启动
        time.sleep(1.5)

        if self.process and self.process.poll() is None:
            self.update_status(True, f"http://localhost:{self.port}")
            self.log(f"服务器启动成功！")
            self.log(f"请在浏览器中访问 http://localhost:{self.port}")
        else:
            self.log("服务器启动失败")
            self.update_status(False)

    def _start_server_thread(self):
        """在独立线程中启动服务器"""
        try:
            cmd = [sys.executable, '-m', 'http.server', str(self.port), '-b', '127.0.0.1']

            if platform.system() == 'Windows':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                creationflags = 0

            self.process = subprocess.Popen(
                cmd,
                cwd=SRC_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags if platform.system() == 'Windows' else 0,
                start_new_session=True if platform.system() != 'Windows' else False
            )

            # 保存PID
            with open(PID_FILE, 'w') as f:
                f.write(str(self.process.pid))

            self.log(f"进程 PID: {self.process.pid}")

            # 等待进程结束
            self.process.wait()

        except Exception as e:
            self.log(f"启动错误: {e}")
            self.root.after(0, lambda: self.update_status(False))

    def stop_server(self):
        """停止服务器"""
        if self.process:
            try:
                self.log("正在停止服务器...")

                if platform.system() == 'Windows':
                    # Windows: 使用 taskkill
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                                   capture_output=True)
                else:
                    # Unix: 发送 SIGTERM
                    self.process.terminate()
                    self.process.wait(timeout=5)

                # 清理PID文件
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)

                self.process = None
                self.update_status(False)
                self.log("服务器已停止")

            except Exception as e:
                self.log(f"停止错误: {e}")
                self.update_status(False)
        else:
            # 尝试通过PID文件停止
            self.stop_by_pid_file()

    def stop_by_pid_file(self):
        """通过PID文件停止服务器"""
        try:
            if os.path.exists(PID_FILE):
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())

                self.log(f"通过PID文件找到进程: {pid}")

                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                                   capture_output=True)
                else:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(1)
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

                os.remove(PID_FILE)
                self.log("服务器已停止")

        except Exception as e:
            self.log(f"停止时出错: {e}")

        self.update_status(False)

    def open_browser(self, event=None):
        """打开浏览器"""
        import webbrowser
        url = f"http://localhost:{self.port}"
        webbrowser.open(url)

    def signal_handler(self, signum, frame):
        """处理信号"""
        self.root.quit()

    def on_close(self):
        """窗口关闭处理"""
        if self.is_running:
            if messagebox.askyesno("确认", "服务器正在运行，确定要关闭吗？"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
