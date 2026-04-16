@echo off
chcp 65001 >nul
echo ============================================
echo 推送到 GitHub
echo ============================================
echo.

REM 初始化 Git（如果还没有）
if not exist .git (
    echo [1/4] 初始化 Git 仓库...
    git init
    echo ✅ 完成
    echo.
)

REM 添加所有文件
echo [2/4] 添加文件...
git add .
echo ✅ 完成
echo.

REM 提交
echo [3/4] 提交到本地仓库...
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

if %errorlevel% neq 0 (
    echo.
    echo ℹ️ 没有新的更改需要提交
    echo.
)

REM 配置远程仓库
echo [4/4] 推送到 GitHub...
echo.

REM 检查是否已配置远程仓库
git remote -v | findstr origin >nul 2>&1
if %errorlevel% neq 0 (
    echo 配置远程仓库...
    git remote add origin https://github.com/hnxiongyue/intelligence-system1.git
    echo ✅ 远程仓库配置完成
    echo.
)

REM 设置主分支为 main
git branch -M main

REM 推送
echo 正在推送到 GitHub...
echo.
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo ✅ 推送成功！
    echo ============================================
    echo.
    echo 🎉 你的代码已经上传到：
    echo    https://github.com/hnxiongyue/intelligence-system1
    echo.
) else (
    echo.
    echo ============================================
    echo ⚠️ 推送失败
    echo ============================================
    echo.
    echo 可能的原因：
    echo   1. 需要 GitHub 身份验证
    echo   2. 网络连接问题
    echo.
    echo 💡 解决方案：
    echo.
    echo 方法 1：使用 GitHub CLI（推荐）
    echo   gh auth login
    echo   然后重新运行此脚本
    echo.
    echo 方法 2：使用 Personal Access Token
    echo   1. 访问：https://github.com/settings/tokens
    echo   2. 生成新 Token（勾选 repo 权限）
    echo   3. 运行：git push -u origin main
    echo   4. 用户名：hnxiongyue
    echo   5. 密码：粘贴你的 Token
    echo.
    echo 方法 3：使用 SSH
    echo   1. 生成 SSH 密钥：ssh-keygen -t ed25519 -C "your_email@example.com"
    echo   2. 添加到 GitHub：https://github.com/settings/keys
    echo   3. 修改远程地址：git remote set-url origin git@github.com:hnxiongyue/intelligence-system1.git
    echo   4. 重新推送：git push -u origin main
    echo.
)

pause
