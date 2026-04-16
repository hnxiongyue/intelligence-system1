@echo off
chcp 65001 >nul
echo ========================================
echo 情报周报生成工具
echo ========================================
echo.

.venv\Scripts\python.exe generate_weekly_report.py %*

if errorlevel 1 (
    echo.
    echo 生成失败，请检查错误信息
    pause
) else (
    echo.
    pause
)
