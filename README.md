# 行业情报分析系统

基于 LangGraph 和 AI 的自动化情报采集、分析和推送系统。

## ✨ 核心特性

- 🤖 **LangGraph 工作流**：状态机架构，5个节点协同工作
- 🕷️ **多种爬虫工具**：Firecrawl MCP、Playwright、RSS、PDF、GitHub
- 🧠 **AI 智能分析**：自动分类、优先级评估、影响分析、应对建议
- 📱 **钉钉推送**：Stream 模式双向交互 + Webhook 模式推送
- 💾 **数据管理**：SQLite 存储、自动去重、历史记录
- ⏰ **定时调度**：自动定时采集最新情报

## 🏗️ 系统架构

```
数据源 → 爬取节点 → 清洗节点 → 分析节点 → 保存节点 → 推送节点
         (Firecrawl)  (去重)    (LLM分析)  (SQLite)   (Stream/Webhook)
```

### 工作流节点

1. **爬取节点**：智能选择最佳爬虫工具采集数据
2. **清洗节点**：数据清洗、格式化、去重
3. **分析节点**：AI 分析分类、优先级、影响、建议
4. **保存节点**：存储到 SQLite 数据库
5. **推送节点**：推送到钉钉群并生成报告

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- pip

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，然后配置：

```env
# LLM API（阿里百炼 Qwen）
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# Firecrawl API（高质量网页采集）
FIRECRAWL_API_KEY=fc-your-api-key

# 钉钉 Stream 模式（推荐）
DINGTALK_CLIENT_ID=your-client-id
DINGTALK_CLIENT_SECRET=your-client-secret
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# 数据库
DATABASE_PATH=data/intelligence.db
```

### 4. 运行系统

```bash
# 运行 LangGraph 工作流
.venv\Scripts\python.exe src/main_langgraph.py

# 或使用批处理文件（Windows）
run_langgraph.bat
```

### 5. 测试钉钉推送

```bash
# 测试推送功能
.venv\Scripts\python.exe test_dingtalk.py
```

## 📁 项目结构

```
intelligence-system/
├── config/
│   ├── sources.yaml          # 数据源配置
│   └── settings.yaml         # 系统配置
├── src/
│   ├── graph/               # LangGraph 工作流
│   │   ├── state.py        # 状态定义
│   │   ├── workflow.py     # 工作流编排
│   │   └── nodes/          # 工作流节点
│   │       ├── crawl_node.py
│   │       ├── clean_node.py
│   │       ├── analyze_node.py
│   │       ├── save_node.py
│   │       └── notify_node.py
│   ├── crawlers/           # 爬虫工具集
│   │   ├── base.py         # 基类
│   │   ├── firecrawl_mcp.py    # Firecrawl MCP
│   │   ├── playwright_crawler.py
│   │   ├── rss_parser.py
│   │   ├── pdf_parser.py
│   │   ├── github_mcp.py
│   │   └── crawler_manager.py  # 爬虫管理器
│   ├── main_langgraph.py   # LangGraph 主程序
│   ├── notifier.py         # Webhook 推送
│   ├── notifier_stream.py  # Stream 推送
│   ├── analyzer.py         # AI 分析
│   ├── database.py         # 数据库操作
│   └── scheduler.py        # 定时调度
├── data/
│   └── intelligence.db     # SQLite 数据库
├── reports/                # 生成的报告
├── logs/                   # 日志目录
├── .env                    # 环境变量
├── requirements.txt        # 依赖清单
├── README.md              # 项目说明
├── README_LANGGRAPH.md    # LangGraph 详细文档
├── MCP_SETUP.md           # MCP 配置指南
└── 当前状态说明.md         # 当前状态
```

## 🕷️ 爬虫工具

系统支持多种爬虫工具，自动选择最佳方案：

| 爬虫类型 | 适用场景 | 优先级 |
|---------|---------|--------|
| **Firecrawl MCP** | 高质量网页采集 | 🥇 最高 |
| **Playwright** | 动态网站、JavaScript 渲染 | 🥈 高 |
| **RSS Parser** | RSS/Atom 订阅源 | 🥉 中 |
| **PDF Parser** | PDF 文档解析 | 🥉 中 |
| **GitHub MCP** | GitHub 仓库监控 | 🥉 中 |
| **Simple Crawler** | 静态网页 | 🏅 备用 |

### 智能路由策略

```
Firecrawl MCP → Playwright → Simple Crawler
     ↓              ↓              ↓
  高质量         动态网站        静态网页
```

## 📱 钉钉推送模式

系统自动检测配置并选择推送模式：

### Stream 模式（推荐）✨

- ✅ 支持双向交互（聊天机器人）
- ✅ 无需公网 IP
- ✅ 连接更稳定
- ✅ 可扩展功能

**配置要求：**
```env
DINGTALK_CLIENT_ID=your-client-id
DINGTALK_CLIENT_SECRET=your-client-secret
DINGTALK_WEBHOOK=your-webhook-url
```

**启用机器人（可选）：**
```bash
.venv\Scripts\python.exe src/notifier_stream.py --enable_bot
```

**机器人命令：**
- `帮助` - 显示帮助信息
- `查询 [关键词]` - 搜索情报
- `统计` - 查看今日统计

### Webhook 模式（备用）

- ✅ 简单直接
- ✅ 单向推送

**配置要求：**
```env
DINGTALK_WEBHOOK=your-webhook-url
```

## ⚙️ 配置说明

### 数据源配置（config/sources.yaml）

```yaml
sources:
  - name: "国家密码管理局"
    url: "https://www.nca.gov.cn"
    enabled: true
    category: "政策"
    crawler_type: "firecrawl"  # 指定爬虫类型（可选）
```

### 系统配置（config/settings.yaml）

```yaml
# 调度配置
schedule:
  enabled: true
  cron: "0 9 * * *"  # 每天早上 9:00

# LLM 配置
llm:
  provider: "qwen"
  model: "qwen-plus"
  
# 爬虫配置
crawler:
  timeout: 30
  max_retries: 3
  
# 推送配置
notifier:
  max_retries: 3
```

## 🔧 使用说明

### 运行工作流

```bash
# 完整 LangGraph 工作流
.venv\Scripts\python.exe src/main_langgraph.py

# 使用批处理文件（Windows）
run_langgraph.bat
```

### 测试推送

```bash
# 测试钉钉推送
.venv\Scripts\python.exe test_dingtalk.py
```

### 查看结果

- **日志文件**：`logs/app.log`
- **数据库**：`data/intelligence.db`
- **报告目录**：`reports/`
- **每日报告**：`reports/daily_report_YYYY-MM-DD.md`

## 📊 采集质量对比

使用 Firecrawl MCP 后，采集质量显著提升：

| 数据源 | 简单爬虫 | Firecrawl MCP | 提升倍数 |
|--------|----------|---------------|----------|
| 国家密码管理局 | 1,856 字符 | 17,875 字符 | 9.6x ⬆️ |
| 工业和信息化部 | 4,608 字符 | 33,704 字符 | 7.3x ⬆️ |
| DigiCert | 83 字符 | 513,059 字符 | 6180x 🚀 |

## 🐛 常见问题

### Q1: Firecrawl 采集失败？

**检查清单：**
- ✅ `FIRECRAWL_API_KEY` 是否正确
- ✅ API 配额是否充足
- ✅ 网络连接是否正常

**解决方案：**
系统会自动降级到 Playwright 或 Simple Crawler

### Q2: AI 分析失败？

**检查清单：**
- ✅ `LLM_API_KEY` 是否正确
- ✅ API 余额是否充足
- ✅ 网络连接是否正常

**解决方案：**
系统会使用降级模式（简单分析）

### Q3: 钉钉推送失败？

**检查清单：**
- ✅ Webhook URL 是否正确
- ✅ 安全设置是否配置关键词 `情报`
- ✅ 消息内容是否包含关键词

**测试命令：**
```bash
.venv\Scripts\python.exe test_dingtalk.py
```

### Q4: Playwright 浏览器未安装？

**影响：**
不影响系统运行（Firecrawl 已接管大部分采集）

**安装方法（可选）：**
```bash
playwright install chromium
```

## 📚 详细文档

- **LangGraph 架构**：`README_LANGGRAPH.md`
- **MCP 配置指南**：`MCP_SETUP.md`
- **当前状态说明**：`当前状态说明.md`

## 📈 开发路线图

### ✅ 已完成

- [x] LangGraph 工作流架构
- [x] 多种爬虫工具集成
- [x] Firecrawl MCP 高质量采集
- [x] 钉钉 Stream 模式推送
- [x] AI 智能分析
- [x] 数据去重和存储
- [x] 向量数据库集成（Qdrant）
- [x] 语义相似度去重
- [x] **周报自动生成** ✨

### 🚧 进行中

- [ ] 定时调度器
- [ ] 机器人交互功能增强

### 📋 计划中

- [ ] 角色路由通知
- [ ] 数据可视化 Dashboard
- [ ] 更多数据源扩展
- [ ] 社交媒体监控

## 🔐 安全说明

### 敏感信息保护

项目已配置 `.gitignore` 排除以下敏感文件：
- ❌ `.env` - API 密钥、数据库密码等
- ❌ `data/` - 本地数据库文件
- ❌ `logs/` - 日志文件
- ❌ `reports/` - 生成的报告
- ❌ `.venv/` - 虚拟环境

### 克隆后配置

其他人克隆仓库后需要：

1. 复制环境变量模板：
```bash
copy .env.example .env
```

2. 编辑 `.env` 填入自己的密钥：
```env
LLM_API_KEY=你的阿里百炼密钥
FIRECRAWL_API_KEY=你的Firecrawl密钥
DINGTALK_CLIENT_ID=你的钉钉ClientID
DINGTALK_CLIENT_SECRET=你的钉钉ClientSecret
DINGTALK_WEBHOOK=你的钉钉Webhook
```

3. 安装依赖并运行：
```bash
pip install -r requirements.txt
python src/main_langgraph.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**版本**：v2.0.0-langgraph  
**更新日期**：2026-04-16
