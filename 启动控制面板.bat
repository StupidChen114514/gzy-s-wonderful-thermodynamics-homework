@echo off
chcp 65001 >nul
title 空气等熵压缩应用 - 服务器控制面板
cd /d "%~dp0"
python scripts\server_gui.py
pause
