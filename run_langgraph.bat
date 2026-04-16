@echo off
REM 运行 LangGraph 版本的情报分析系统

echo ========================================
echo 行业情报分析系统 (LangGraph 版本)
echo ========================================
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo 虚拟环境已激活
) else (
    echo 警告: 虚拟环境不存在，使用系统 Python
)

echo.
echo 开始运行...
echo.

REM 运行主程序
python src/main_langgraph.py %*

echo.
echo 执行完成
pause
