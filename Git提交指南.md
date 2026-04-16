# Git 提交指南

## 当前状态

✅ 代码已完成
✅ `.gitignore` 已配置（排除敏感数据）
✅ 数据库问题已修复

## Git 操作步骤

### 1. 初始化 Git 仓库

```bash
git init
```

### 2. 添加所有文件

```bash
git add .
```

这会添加所有文件，但 `.gitignore` 中的文件会被自动排除：
- ❌ `.env`（敏感信息）
- ❌ `data/`（数据库文件）
- ❌ `logs/`（日志文件）
- ❌ `reports/`（报告文件）
- ❌ `.venv/`（虚拟环境）

### 3. 查看将要提交的文件

```bash
git status
```

### 4. 提交代码

```bash
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
```

### 5. 添加远程仓库（如果有）

```bash
# GitHub
git remote add origin https://github.com/你的用户名/仓库名.git

# 或 Gitee
git remote add origin https://gitee.com/你的用户名/仓库名.git

# 或其他 Git 服务
git remote add origin <你的仓库地址>
```

### 6. 推送到远程仓库

```bash
# 首次推送
git push -u origin main

# 或者如果默认分支是 master
git push -u origin master
```

## 常用 Git 命令

### 查看状态
```bash
git status
```

### 查看提交历史
```bash
git log --oneline
```

### 添加新文件
```bash
git add <文件名>
# 或添加所有修改
git add .
```

### 提交修改
```bash
git commit -m "提交说明"
```

### 推送到远程
```bash
git push
```

### 拉取远程更新
```bash
git pull
```

## 注意事项

### ⚠️ 敏感信息保护

`.gitignore` 已配置排除以下敏感文件：
- `.env`：包含 API 密钥、数据库密码等
- `data/`：本地数据库文件
- `logs/`：日志文件

### ✅ 需要提交的文件

- 所有源代码（`src/`）
- 配置模板（`config/`）
- 文档（`doc/`、`README.md`）
- 依赖列表（`requirements.txt`）
- 环境变量示例（`.env.example`）
- 批处理脚本（`*.bat`）
- 测试文件（`test_*.py`）

### 📝 环境变量配置

其他人克隆仓库后需要：

1. 复制环境变量模板：
```bash
copy .env.example .env
```

2. 编辑 `.env` 填入自己的密钥：
```
DASHSCOPE_API_KEY=你的密钥
DINGTALK_WEBHOOK=你的webhook
...
```

## 快速开始（一键提交）

```bash
# 初始化并提交
git init
git add .
git commit -m "初始提交：行业情报分析系统"

# 如果有远程仓库
git remote add origin <你的仓库地址>
git push -u origin main
```

## 后续更新流程

每次修改代码后：

```bash
# 1. 查看修改
git status

# 2. 添加修改
git add .

# 3. 提交
git commit -m "描述你的修改"

# 4. 推送
git push
```

## 分支管理（可选）

### 创建开发分支
```bash
git checkout -b dev
```

### 切换分支
```bash
git checkout main
git checkout dev
```

### 合并分支
```bash
git checkout main
git merge dev
```

## 问题排查

### 如果 push 失败

```bash
# 先拉取远程更新
git pull origin main --rebase

# 再推送
git push origin main
```

### 如果不小心提交了敏感文件

```bash
# 从 Git 历史中删除文件
git rm --cached .env
git commit -m "移除敏感文件"
git push
```

### 查看 .gitignore 是否生效

```bash
git status --ignored
```

## 建议的 README.md 更新

在提交前，建议更新 `README.md` 添加以下内容：

```markdown
## 环境配置

1. 克隆仓库
2. 复制 `.env.example` 为 `.env`
3. 填入你的 API 密钥
4. 安装依赖：`pip install -r requirements.txt`
5. 运行：`python src/main_langgraph.py`

## 注意事项

- 不要提交 `.env` 文件
- 数据库文件在本地 `data/` 目录
- 日志文件在 `logs/` 目录
```
