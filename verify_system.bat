@echo off
chcp 65001 >nul
echo ========================================
echo 系统功能验证
echo ========================================
echo.

.venv\Scripts\python.exe verify_system.py

echo.
pause
