#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================
                空气等熵压缩应用 - 一键终止脚本 (改进版)
=========================================================================

功能描述：
    安全终止已启动的 HTTP 服务器进程
    改进版：支持通过端口、PID、命令行等多种方式查找并终止进程

支持平台：
    Windows、macOS、Linux

使用方法：
    python stop_server_v2.py [options]

参数说明：
    --force, -f     强制终止（跳过确认）
    --clean, -c     清理临时文件
    --port, -p      指定端口号（默认：自动检测 8000, 8080）
    --pid, -i       指定 PID
    --all, -a       清理所有相关进程
    --help, -?      显示帮助信息

=========================================================================
"""

import os
import sys
import platform
import argparse
import signal
import time
import re
import subprocess

# 配置常量
PID_FILE = '.server_pid'
LOG_FILE = 'server.log'

class ProcessKiller:
    """进程终止器"""
    
    def __init__(self):
        self.system = platform.system()
        self.killed_processes = []
        
    def read_pid_from_file(self):
        """从 PID 文件读取进程 ID"""
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                return True, pid
            except:
                return False, None
        return False, None
        
    def is_process_running(self, pid):
        """检查进程是否运行"""
        try:
            if self.system == 'Windows':
                result = subprocess.run(
                    ['tasklist', '/FI', 'PID eq %d' % pid],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                return True
        except (PermissionError, ProcessLookupError, FileNotFoundError):
            return False
        except Exception:
            return False
    
    def kill_by_pid(self, pid, force=False):
        """通过 PID 终止进程"""
        try:
            if self.system == 'Windows':
                # Windows: 使用 taskkill /T 终止进程树
                cmd = ['taskkill', '/F', '/T', '/PID', str(pid)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.killed_processes.append(pid)
                    return True, "进程 %d 及其子进程已终止" % pid
                else:
                    return False, "taskkill 失败: %s" % result.stderr.strip()
            else:
                # Unix: 先尝试优雅终止
                if not force:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(1)
                        if not self.is_process_running(pid):
                            self.killed_processes.append(pid)
                            return True, "进程 %d 已终止" % pid
                    except:
                        pass
                
                # 强制终止
                os.kill(pid, signal.SIGKILL)
                self.killed_processes.append(pid)
                return True, "进程 %d 已强制终止" % pid
                
        except ProcessLookupError:
            return False, "进程 %d 不存在" % pid
        except PermissionError:
            return False, "权限不足，无法终止进程 %d" % pid
        except Exception as e:
            return False, "终止进程 %d 失败: %s" % (pid, str(e))
    
    def kill_by_port(self, port):
        """通过端口号查找并终止进程"""
        try:
            # 使用 netstat 查找端口
            if self.system == 'Windows':
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ['netstat', '-tulpn'],
                    capture_output=True,
                    text=True
                )
            
            # 解析输出，查找监听该端口的进程
            for line in result.stdout.split('\n'):
                if ':%d' % port in line and ('LISTENING' in line or 'LISTEN' in line):
                    # 提取 PID
                    if self.system == 'Windows':
                        match = re.search(r'LISTENING\s+(\d+)', line)
                    else:
                        match = re.search(r'(\d+)$', line)
                    
                    if match:
                        pid = int(match.group(1))
                        print("        找到占用端口 %d 的进程: PID %d" % (port, pid))
                        return self.kill_by_pid(pid, force=True)
            
            return False, "端口 %d 未被占用" % port
            
        except Exception as e:
            return False, "查找端口 %d 进程失败: %s" % (port, str(e))
    
    def kill_all_http_servers(self):
        """终止所有 HTTP 服务器进程"""
        killed_count = 0
        
        # 查找所有 python http.server 进程
        if self.system == 'Windows':
            cmd = ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/V']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'http.server' in line.lower():
                    parts = line.split()
                    if parts:
                        try:
                            pid = int(parts[1])
                            success, msg = self.kill_by_pid(pid, force=True)
                            if success:
                                killed_count += 1
                        except:
                            pass
        else:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if 'http.server' in line and 'python' in line:
                    parts = line.split()
                    if parts:
                        try:
                            pid = int(parts[1])
                            success, msg = self.kill_by_pid(pid, force=True)
                            if success:
                                killed_count += 1
                        except:
                            pass
        
        return killed_count
    
    def clean_temp_files(self):
        """清理临时文件"""
        cleaned = []
        
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
                cleaned.append(PID_FILE)
            except:
                pass
        
        if os.path.exists(LOG_FILE):
            try:
                os.remove(LOG_FILE)
                cleaned.append(LOG_FILE)
            except:
                pass
        
        return cleaned

def main():
    parser = argparse.ArgumentParser(description="终止空气等熵压缩应用 HTTP 服务器")
    parser.add_argument('-f', '--force', action='store_true',
                        help="强制终止")
    parser.add_argument('-c', '--clean', action='store_true',
                        help="清理临时文件")
    parser.add_argument('-p', '--port', type=int,
                        help="指定端口号")
    parser.add_argument('-i', '--pid', type=int,
                        help="指定 PID")
    parser.add_argument('-a', '--all', action='store_true',
                        help="清理所有 HTTP 服务器进程")
    args = parser.parse_args()
    
    print("""
=========================================================================
                空气等熵压缩应用 - 终止服务 (改进版)
=========================================================================
    """)
    
    killer = ProcessKiller()
    terminated = False
    target_pid = None
    
    # 策略1：通过命令行参数指定 PID
    if args.pid:
        print("[STEP 1] 使用指定的 PID: %d" % args.pid)
        target_pid = args.pid
        success, msg = killer.kill_by_pid(args.pid, force=args.force)
        if success:
            terminated = True
        else:
            print("        ERROR: %s" % msg)
    
    # 策略2：通过命令行参数指定端口
    elif args.port:
        print("[STEP 1] 通过端口 %d 查找进程..." % args.port)
        success, msg = killer.kill_by_port(args.port)
        if success:
            terminated = True
            print("        %s" % msg)
        else:
            print("        %s" % msg)
    
    # 策略3：通过 PID 文件
    elif not args.all:
        print("[STEP 1] 查找 PID 文件...")
        found, pid = killer.read_pid_from_file()
        
        if found:
            print("        PID 文件: %d" % pid)
            if killer.is_process_running(pid):
                print("        进程状态: 运行中")
                target_pid = pid
                if not args.force:
                    confirm = input("        确认终止进程 %d? (y/N): " % pid)
                    if confirm.lower() != 'y':
                        print("        取消操作")
                        sys.exit(0)
                
                success, msg = killer.kill_by_pid(pid, force=args.force)
                if success:
                    terminated = True
                    print("        %s" % msg)
                else:
                    print("        ERROR: %s" % msg)
            else:
                print("        进程状态: 不存在（PID 文件过期）")
                os.remove(PID_FILE)
                print("        已清理过期的 PID 文件")
        else:
            print("        未找到 PID 文件")
    
    # 策略4：终止所有 HTTP 服务器
    if args.all or not terminated:
        if args.all:
            print("\n[STEP] 终止所有 HTTP 服务器进程...")
            count = killer.kill_all_http_servers()
            if count > 0:
                terminated = True
                print("        成功终止 %d 个进程" % count)
            else:
                print("        未找到 HTTP 服务器进程")
        elif not terminated:
            # 自动尝试常用端口
            print("\n[STEP] 自动检测端口...")
            for port in [8000, 8080, 3000, 5000]:
                success, msg = killer.kill_by_port(port)
                if success:
                    terminated = True
                    print("        成功终止端口 %d 的进程" % port)
                    break
    
    # 清理临时文件
    if args.clean or terminated:
        print("\n[STEP] 清理临时文件...")
        cleaned = killer.clean_temp_files()
        if cleaned:
            print("        已清理: %s" % ', '.join(cleaned))
        else:
            print("        无需清理")
    
    # 验证结果
    print("\n[VERIFY] 验证终止结果...")
    if target_pid:
        if killer.is_process_running(target_pid):
            print("        警告: 进程 %d 仍在运行" % target_pid)
        else:
            print("        成功: 进程已终止")
    
    # 输出结果
    print("\n" + "="*60)
    if terminated or args.all:
        print("[SUCCESS] 服务终止完成！")
    else:
        print("[INFO] 未找到运行中的服务")
    print("="*60)
    
    if killer.killed_processes:
        print("终止的进程: %s" % ', '.join(str(p) for p in killer.killed_processes))
    
    print("\n使用说明：")
    print("   - 服务已完全停止")
    print("   - 可运行 python start_server_v2.py 重新启动")
    print("="*60)

if __name__ == '__main__':
    main()
