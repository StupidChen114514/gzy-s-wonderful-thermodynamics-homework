#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================
                空气等熵压缩应用 - 一键启动脚本 (改进版)
=========================================================================

功能描述：
    自动启动 HTTP 服务器，用于运行空气等熵压缩过程交互式图形应用
    改进版：修复了 Windows 环境下的进程管理和 Ctrl+C 信号处理问题

支持平台：
    Windows、macOS、Linux

使用方法：
    python start_server_v2.py [options]

参数说明：
    --port, -p     指定服务端口（默认：8000）
    --host, -h     指定绑定地址（默认：127.0.0.1）
    --help, -?     显示帮助信息

=========================================================================
"""

import os
import sys
import socket
import subprocess
import platform
import argparse
import atexit
import signal
import time

# 配置常量
DEFAULT_PORT = 8000
DEFAULT_HOST = '127.0.0.1'
PID_FILE = '.server_pid'
LOG_FILE = 'server.log'

class ServerManager:
    """服务器管理器"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.process = None
        self.pid = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.work_dir = os.path.dirname(self.script_dir)
        self.src_dir = os.path.join(self.work_dir, 'src')
        
    def check_python_version(self):
        """检查 Python 版本"""
        if sys.version_info < (3, 6):
            print("[ERROR] 需要 Python 3.6 或更高版本")
            print("        当前版本:", sys.version.split()[0])
            return False
        return True
    
    def check_port_available(self):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = s.connect_ex((self.host, self.port))
                if result == 0:
                    return False, "端口 %d 已被占用" % self.port
                return True, "端口 %d 可用" % self.port
        except Exception as e:
            return False, "检查端口失败: %s" % str(e)
    
    def find_index_file(self):
        """查找 index.html 文件"""
        index_path = os.path.join(self.src_dir, 'index.html')
        if os.path.exists(index_path):
            return True, os.path.abspath(index_path)
        return False, "未找到 index.html 文件，请确保 src/ 目录下存在该文件"
    
    def start_server(self):
        """启动 HTTP 服务器"""
        system = platform.system()
        
        try:
            cmd = [sys.executable, '-m', 'http.server', str(self.port), '-b', self.host]
            
            print("[INFO] 启动命令: %s" % ' '.join(cmd))
            print("[INFO] 工作目录: %s" % self.src_dir)
            
            # 关键改进：使用 PIPE 确保主进程持有句柄
            if system == 'Windows':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                creationflags = 0
            
            # 不使用 DETACHED_PROCESS，以便能够管理子进程
            self.process = subprocess.Popen(
                cmd,
                cwd=self.src_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags if system == 'Windows' else 0,
                start_new_session=True if system != 'Windows' else False
            )
            
            self.pid = self.process.pid
            
            # 保存 PID
            with open(PID_FILE, 'w') as f:
                f.write(str(self.pid))
            
            print("[INFO] 进程 PID: %d" % self.pid)
            
            # 等待一下让服务启动
            time.sleep(2)
            
            # 检查是否成功启动
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                return False, "服务启动失败，退出码: %d\n错误信息: %s" % (
                    self.process.returncode, 
                    stderr.decode('utf-8', errors='ignore')
                )
            
            return True, self.pid
            
        except Exception as e:
            return False, "启动失败: %s" % str(e)
    
    def stop_server(self):
        """停止服务器"""
        if self.process:
            try:
                # 先尝试优雅终止
                if platform.system() == 'Windows':
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)
                
                # 等待最多5秒
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 超时后强制终止
                    self.process.kill()
                    self.process.wait()
                    
            except Exception as e:
                print("[WARN] 终止进程时出错: %s" % str(e))
    
    def cleanup(self):
        """清理资源"""
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except:
                pass
    
    def register_cleanup(self):
        """注册清理函数"""
        atexit.register(self.cleanup)
        
        def signal_handler(signum, frame):
            print("\n[INFO] 收到终止信号，正在关闭服务...")
            self.stop_server()
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动空气等熵压缩应用 HTTP 服务器")
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help="服务端口（默认：%d）" % DEFAULT_PORT)
    parser.add_argument('-host', '--host', type=str, default=DEFAULT_HOST,
                        help="绑定地址（默认：%s）" % DEFAULT_HOST)
    args = parser.parse_args()
    
    print("""
=========================================================================
                空气等熵压缩应用 - 启动服务 (改进版)
=========================================================================
    """)
    
    # 创建服务器管理器
    manager = ServerManager(args.host, args.port)
    
    # 注册清理函数
    manager.register_cleanup()
    
    # 检查 Python 版本
    print("[CHECK] 检查 Python 版本...")
    if not manager.check_python_version():
        sys.exit(1)
    print("        OK: Python %s" % sys.version.split()[0])
    
    # 检查应用文件
    print("[CHECK] 检查应用文件...")
    success, msg = manager.find_index_file()
    if not success:
        print("        ERROR: %s" % msg)
        sys.exit(1)
    print("        OK: %s" % msg)
    
    # 检查端口
    print("[CHECK] 检查端口 %d..." % args.port)
    available, msg = manager.check_port_available()
    if not available:
        print("        ERROR: %s" % msg)
        print("        HINT: 使用其他端口，如 python start_server_v2.py -p 8080")
        sys.exit(1)
    print("        OK: %s" % msg)
    
    # 启动服务
    print("\n[START] 启动 HTTP 服务器 (%s:%d)..." % (args.host, args.port))
    success, result = manager.start_server()
    
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] 服务启动成功！")
        print("="*60)
        print("服务地址: http://%s:%d" % (args.host, args.port))
        print("本地访问: http://localhost:%d" % args.port)
        print("进程 PID: %d" % result)
        print("PID 文件: %s" % os.path.abspath(PID_FILE))
        print("="*60)
        print("\n使用说明：")
        print("   - 打开浏览器访问上述地址即可使用应用")
        print("   - 按 Ctrl+C 停止服务")
        print("   - 或运行 python stop_server_v2.py 停止服务")
        print("="*60)
        
        # 等待进程结束
        try:
            manager.process.wait()
        except KeyboardInterrupt:
            print("\n[INFO] 用户中断，服务已停止")
            manager.stop_server()
            manager.cleanup()
    else:
        print("\n[ERROR] 服务启动失败:")
        print(result)
        manager.cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main()
