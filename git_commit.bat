@echo off
chcp 65001 >nul
echo ============================================
echo Git 提交助手
echo ============================================
echo.

REM 检查是否已初始化 Git
if not exist .git (
    echo [1/5] 初始化 Git 仓库...
    git init
    echo ✅ Git 仓库初始化完成
    echo.
) else (
    echo ✅ Git 仓库已存在
    echo.
)

echo [2/5] 查看将要提交的文件...
echo.
git status
echo.

echo [3/5] 添加所有文件...
git add .
echo ✅ 文件添加完成
echo.

echo [4/5] 提交到本地仓库...
git commit -m "初始提交：行业情报分析系统完整实现

功能特性：
- LangGraph 工作流架构
- 多种爬虫支持（Firecrawl MCP、Playwright、RSS、PDF）
- 向量数据库集成（Qdrant + 阿里云百炼）
- 三层去重机制（哈希、语义、数据库）
- AI 智能分析（Qwen）
- 钉钉推送（Stream 模式）
- 周报生成
- 系统验证工具"

if %errorlevel% equ 0 (
    echo ✅ 提交成功
) else (
    echo ❌ 提交失败
    pause
    exit /b 1
)
echo.

echo [5/5] 推送到远程仓库...
echo.

REM 检查是否已配置远程仓库
git remote -v | findstr origin >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 远程仓库已配置
    echo.
) else (
    echo 配置远程仓库...
    git remote add origin https://github.com/hnxiongyue/intelligence-system1.git
    echo ✅ 远程仓库配置完成
    echo.
)

REM 设置主分支为 main
git branch -M main

echo 推送到 GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ 推送成功！
    echo.
    echo 🎉 你的代码已经上传到：
    echo    https://github.com/hnxiongyue/intelligence-system1
    echo.
) else (
    echo ❌ 推送失败
    echo.
    echo 可能的原因：
    echo   1. 需要 GitHub 身份验证（用户名和密码/Token）
    echo   2. 网络连接问题
    echo.
    echo 解决方案：
    echo   - 使用 GitHub Desktop 或 Git Credential Manager
    echo   - 或手动运行：git push -u origin main
    echo.
)

echo ============================================
echo ✅ 本地提交完成！
echo ============================================
echo.
echo 查看提交历史：
git log --oneline -5
echo.

pause
