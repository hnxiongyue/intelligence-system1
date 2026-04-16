# MCP 配置指南

本文档说明如何配置和使用 MCP（Model Context Protocol）服务。

## 什么是 MCP？

MCP（Model Context Protocol）是一种标准化的协议，用于连接 AI 应用和外部工具/服务。在本项目中，我们使用 MCP 来：

1. **Firecrawl MCP** - 高质量网页采集服务
2. **GitHub MCP** - GitHub 仓库监控服务

## 1. Firecrawl MCP 配置

### 1.1 注册 Firecrawl 账号

1. 访问 [Firecrawl 官网](https://firecrawl.dev/)
2. 注册账号
3. 获取 API Key

### 1.2 配置 API Key

在 `.env` 文件中添加：

```bash
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 1.3 启用 Firecrawl 数据源

编辑 `config/sources.yaml`，将 Firecrawl 数据源的 `enabled` 设置为 `true`：

```yaml
  - name: "DigiCert (Firecrawl)"
    url: "https://www.digicert.com/blog"
    type: "firecrawl"
    enabled: true  # 改为 true
    category: "竞品"
    formats: ["markdown", "html"]
    only_main_content: true
```

### 1.4 Firecrawl 优势

- ✅ 高质量内容提取（自动识别主要内容）
- ✅ 支持 Markdown 格式输出
- ✅ 绕过大部分反爬虫机制
- ✅ 支持批量采集
- ✅ 稳定可靠

### 1.5 Firecrawl 配置参数

```yaml
  - name: "数据源名称"
    url: "https://example.com"
    type: "firecrawl"
    enabled: true
    category: "分类"
    formats: ["markdown", "html"]  # 返回格式
    only_main_content: true  # 只提取主要内容
    include_tags: ["article", "main"]  # 包含的标签（可选）
    exclude_tags: ["nav", "footer"]  # 排除的标签（可选）
```

## 2. GitHub MCP 配置

### 2.1 生成 GitHub Token

1. 登录 GitHub
2. 访问 [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
3. 点击 "Generate new token (classic)"
4. 选择权限：
   - `repo` - 访问仓库
   - `read:org` - 读取组织信息（可选）
5. 生成并复制 Token

### 2.2 配置 Token

在 `.env` 文件中添加：

```bash
GITHUB_TOKEN=your_github_token_here
```

**注意**：如果不配置 Token，GitHub MCP 将使用匿名访问，有速率限制（每小时 60 次请求）。

### 2.3 启用 GitHub 数据源

编辑 `config/sources.yaml`，将 GitHub 数据源的 `enabled` 设置为 `true`：

```yaml
  - name: "CAB Forum Server Certificate"
    url: "https://github.com/cabforum/servercert"
    type: "github"
    enabled: true  # 改为 true
    category: "合规"
    monitor_types: ["commits", "issues", "pulls", "releases"]
    since_days: 7
```

### 2.4 GitHub MCP 优势

- ✅ 自动监控仓库更新
- ✅ 追踪 Commits、Issues、PRs、Releases
- ✅ 结构化数据输出
- ✅ 支持时间范围过滤

### 2.5 GitHub 配置参数

```yaml
  - name: "仓库名称"
    url: "https://github.com/owner/repo"
    type: "github"
    enabled: true
    category: "分类"
    monitor_types:  # 监控类型
      - "commits"   # 提交记录
      - "issues"    # Issues
      - "pulls"     # Pull Requests
      - "releases"  # 发布版本
    since_days: 7  # 监控最近几天
```

## 3. 完整的 .env 配置示例

```bash
# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# Notification
DINGTALK_WEBHOOK=your_dingtalk_webhook_url

# MCP Services
FIRECRAWL_API_KEY=your_firecrawl_api_key
GITHUB_TOKEN=your_github_token
```

## 4. 测试 MCP 功能

### 4.1 测试 Firecrawl MCP

```bash
python src/crawlers/firecrawl_mcp.py
```

### 4.2 测试 GitHub MCP

```bash
python src/crawlers/github_mcp.py
```

### 4.3 测试完整流程

```bash
# 确保在 config/sources.yaml 中启用了 MCP 数据源
python src/main_langgraph.py
```

## 5. 爬虫类型对比

| 爬虫类型 | 优势 | 劣势 | 适用场景 | 需要配置 |
|---------|------|------|---------|---------|
| **Simple** | 快速、简单 | 容易被拦截 | 简单静态网站 | 无 |
| **Playwright** | 绕过 WAF、支持 JS | 慢、资源消耗大 | 动态网站、反爬虫 | 无 |
| **Firecrawl MCP** | 高质量、稳定 | 需要付费 | 重要数据源 | API Key |
| **GitHub MCP** | 结构化、准确 | 仅限 GitHub | GitHub 监控 | Token（可选）|
| **RSS** | 标准化、快速 | 仅限 RSS | RSS Feed | 无 |
| **PDF** | 支持文档 | 格式复杂 | PDF 文档 | 无 |

## 6. 智能路由策略

爬虫管理器会自动选择最合适的爬虫：

```
1. 检查数据源类型（type 字段）
2. 根据类型选择爬虫：
   - firecrawl → Firecrawl MCP
   - github → GitHub MCP
   - rss → RSS Parser
   - pdf → PDF Parser
   - dynamic_web → Playwright
   - static_web → Simple Crawler
3. 如果 Simple Crawler 失败或被拦截 → 自动切换到 Playwright
```

## 7. 成本估算

### Firecrawl 定价（参考）

- 免费套餐：500 次/月
- 基础套餐：$29/月，5000 次
- 专业套餐：$99/月，20000 次

### GitHub API 限制

- 匿名访问：60 次/小时
- 认证访问：5000 次/小时

## 8. 常见问题

### Q1: Firecrawl API Key 在哪里获取？

访问 [Firecrawl Dashboard](https://firecrawl.dev/dashboard) 获取。

### Q2: GitHub Token 需要什么权限？

基本监控只需要 `repo` 权限。

### Q3: 不配置 MCP 可以运行吗？

可以！系统会自动降级到其他爬虫（Playwright、Simple Crawler）。

### Q4: 如何知道使用了哪个爬虫？

查看日志，会显示 `[爬虫类型] 开始采集...`

### Q5: MCP 采集失败怎么办？

系统会自动重试，如果仍然失败，会记录错误日志。

## 9. 最佳实践

1. **优先使用 Firecrawl MCP** 处理重要数据源（质量高、稳定）
2. **使用 Playwright** 处理被 WAF 拦截的网站
3. **使用 GitHub MCP** 监控开源项目和标准组织
4. **使用 RSS** 处理新闻和博客
5. **定期检查 API 配额** 避免超限

## 10. 下一步

配置完成后，运行系统：

```bash
python src/main_langgraph.py
```

查看日志确认 MCP 是否正常工作。

---

**更新日期**：2026-04-16  
**版本**：v1.0
