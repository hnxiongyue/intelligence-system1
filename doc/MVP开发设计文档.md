# MVP 阶段开发设计文档

## 📋 文档说明

**版本**：v1.0  
**目标**：完成可运行的最小可行产品（MVP）  
**周期**：2-3 周  
**核心目标**：验证技术可行性，快速上线

---

## 一、MVP 范围定义

### 1.1 核心功能（必须实现）

✅ **数据采集**
- 5 个核心数据源（国密局、工信部、e签宝、DigiCert、CFCA）
- 支持静态网页采集（Firecrawl MCP）
- 基础错误处理和重试

✅ **数据处理**
- 基础清洗（去除 HTML 标签）
- 简单去重（基于标题）
- 提取关键信息（标题、时间、摘要）

✅ **AI 分析**
- 内容分类（政策/竞品/技术）
- 影响评估（高/中/低）
- 简单建议生成

✅ **推送通知**
- 钉钉 Webhook 推送
- 简单的消息格式化

✅ **数据存储**
- SQLite 数据库
- 基础 CRUD 操作

✅ **定时调度**
- 每日自动运行
- 手动触发支持

### 1.2 暂不实现（后续版本）

❌ PDF 解析
❌ 动态网站采集（Playwright）
❌ RSS 订阅
❌ GitHub 监控
❌ 向量数据库
❌ 角色化推送
❌ 周报生成
❌ Web Dashboard

---

## 二、技术架构（MVP 简化版）

### 2.1 整体架构

```
┌─────────────────────────────────────────────┐
│         定时调度（APScheduler）              │
│              每日 9:00 触发                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         主程序（main.py）                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  1. 采集模块（Firecrawl MCP）                │
│     ↓                                       │
│  2. 清洗模块（基础清洗）                     │
│     ↓                                       │
│  3. 分析模块（DeepSeek LLM）                 │
│     ↓                                       │
│  4. 推送模块（钉钉 Webhook）                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         SQLite 数据库                        │
└─────────────────────────────────────────────┘
```

### 2.2 目录结构（MVP 简化版）

```
intelligence-system/
├── config/
│   ├── sources.yaml          # 数据源配置
│   └── settings.yaml         # 系统配置
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── crawler.py           # 采集模块
│   ├── processor.py         # 清洗模块
│   ├── analyzer.py          # 分析模块
│   ├── notifier.py          # 推送模块
│   ├── database.py          # 数据库操作
│   └── scheduler.py         # 定时调度
├── data/
│   └── intelligence.db      # SQLite 数据库
├── logs/                    # 日志目录
├── .env                     # 环境变量
├── requirements.txt         # 依赖清单
└── README.md               # 项目说明
```

---

## 三、数据库设计（MVP 简化版）

### 3.1 表结构

#### intelligence 表（情报数据）

```sql
CREATE TABLE intelligence (
    id TEXT PRIMARY KEY,              -- UUID
    title TEXT NOT NULL,              -- 标题
    source TEXT NOT NULL,             -- 来源（国密局/工信部等）
    source_url TEXT,                  -- 原始链接
    category TEXT,                    -- 分类（政策/竞品/技术）
    priority TEXT,                    -- 优先级（高/中/低）
    content TEXT,                     -- 原始内容
    summary TEXT,                     -- AI 生成摘要
    suggestions TEXT,                 -- AI 生成建议
    publish_date DATE,                -- 发布日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_notified INTEGER DEFAULT 0     -- 是否已推送
);

-- 索引
CREATE INDEX idx_source ON intelligence(source);
CREATE INDEX idx_category ON intelligence(category);
CREATE INDEX idx_priority ON intelligence(priority);
CREATE INDEX idx_created_at ON intelligence(created_at);
CREATE INDEX idx_is_notified ON intelligence(is_notified);
```

#### crawl_log 表（采集日志）

```sql
CREATE TABLE crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,             -- 数据源
    status TEXT NOT NULL,             -- success/failed
    items_count INTEGER DEFAULT 0,    -- 采集条数
    error_message TEXT,               -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 四、核心模块设计

### 4.1 采集模块（crawler.py）

**功能**：
- 调用 Firecrawl MCP 采集网页
- 基础错误处理
- 重试机制（最多 3 次）

**接口设计**：
```python
class Crawler:
    def crawl(self, url: str) -> dict:
        """采集单个 URL"""
        pass
    
    def crawl_all(self, sources: list) -> list:
        """批量采集"""
        pass
```

### 4.2 清洗模块（processor.py）

**功能**：
- 去除 HTML 标签
- 提取标题、时间
- 简单去重（基于标题哈希）

**接口设计**：
```python
class Processor:
    def clean(self, raw_data: dict) -> dict:
        """清洗单条数据"""
        pass
    
    def extract_info(self, content: str) -> dict:
        """提取关键信息"""
        pass
    
    def deduplicate(self, data_list: list) -> list:
        """去重"""
        pass
```

### 4.3 分析模块（analyzer.py）

**功能**：
- 调用 DeepSeek LLM
- 内容分类
- 影响评估
- 生成建议

**接口设计**：
```python
class Analyzer:
    def analyze(self, data: dict) -> dict:
        """分析单条情报"""
        pass
    
    def classify(self, content: str) -> str:
        """分类"""
        pass
    
    def assess_priority(self, content: str) -> str:
        """评估优先级"""
        pass
```

### 4.4 推送模块（notifier.py）

**功能**：
- 钉钉 Webhook 推送
- 消息格式化
- 推送失败重试

**接口设计**：
```python
class Notifier:
    def send_to_dingtalk(self, data: dict) -> bool:
        """发送到钉钉"""
        pass
    
    def format_message(self, data: dict) -> str:
        """格式化消息"""
        pass
```

### 4.5 数据库模块（database.py）

**功能**：
- SQLite 连接管理
- CRUD 操作
- 查询接口

**接口设计**：
```python
class Database:
    def save_intelligence(self, data: dict) -> bool:
        """保存情报"""
        pass
    
    def get_unnotified(self) -> list:
        """获取未推送的情报"""
        pass
    
    def mark_notified(self, id: str) -> bool:
        """标记为已推送"""
        pass
    
    def log_crawl(self, source: str, status: str, count: int) -> bool:
        """记录采集日志"""
        pass
```

---

## 五、配置文件设计

### 5.1 sources.yaml（数据源配置）

```yaml
sources:
  - name: "国家密码管理局"
    url: "https://www.nca.gov.cn"
    enabled: true
    
  - name: "工业和信息化部"
    url: "https://www.miit.gov.cn"
    enabled: true
    
  - name: "e签宝"
    url: "https://www.esign.cn/news"
    enabled: true
    
  - name: "DigiCert"
    url: "https://www.digicert.com/blog"
    enabled: true
    
  - name: "CFCA"
    url: "https://www.cfca.com.cn"
    enabled: true
```

### 5.2 settings.yaml（系统配置）

```yaml
# 调度配置
schedule:
  enabled: true
  cron: "0 9 * * *"  # 每天 9:00

# 钉钉配置
dingtalk:
  webhook_url: "${DINGTALK_WEBHOOK}"  # 从环境变量读取

# LLM 配置
llm:
  provider: "deepseek"
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-chat"
  temperature: 0.7

# 数据库配置
database:
  path: "data/intelligence.db"

# 日志配置
logging:
  level: "INFO"
  file: "logs/app.log"
```

### 5.3 .env（环境变量）

```bash
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# 钉钉 Webhook
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# Firecrawl API（如果使用）
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

---

## 六、工作流程设计

### 6.1 主流程

```python
def main():
    """主流程"""
    # 1. 加载配置
    sources = load_sources()
    
    # 2. 采集数据
    raw_data = crawler.crawl_all(sources)
    
    # 3. 清洗数据
    cleaned_data = processor.clean_all(raw_data)
    
    # 4. 去重
    unique_data = processor.deduplicate(cleaned_data)
    
    # 5. AI 分析
    analyzed_data = analyzer.analyze_all(unique_data)
    
    # 6. 保存到数据库
    database.save_all(analyzed_data)
    
    # 7. 推送通知
    unnotified = database.get_unnotified()
    for item in unnotified:
        notifier.send_to_dingtalk(item)
        database.mark_notified(item['id'])
```

### 6.2 错误处理策略

```python
# 采集失败：记录日志，继续下一个
try:
    data = crawler.crawl(url)
except Exception as e:
    logger.error(f"采集失败: {url}, 错误: {e}")
    database.log_crawl(source, "failed", 0, str(e))
    continue

# LLM 调用失败：重试 3 次，失败则跳过
@retry(max_attempts=3, delay=2)
def analyze_with_retry(data):
    return analyzer.analyze(data)

# 推送失败：记录日志，下次重试
try:
    notifier.send_to_dingtalk(item)
except Exception as e:
    logger.error(f"推送失败: {item['id']}, 错误: {e}")
    # 不标记为已推送，下次继续尝试
```

---

## 七、Prompt 设计

### 7.1 分析 Prompt

```python
ANALYSIS_PROMPT = """
你是一个专业的行业情报分析师，擅长分析电子认证、密码技术领域的政策和竞品动态。

请分析以下情报内容：

**来源**：{source}
**标题**：{title}
**内容**：{content}

请按照以下格式输出 JSON：

{{
  "category": "政策/竞品/技术",
  "priority": "高/中/低",
  "summary": "用 2-3 句话总结核心内容",
  "impact": "分析对电子认证行业的影响",
  "suggestions": [
    "建议1",
    "建议2"
  ]
}}

注意：
1. category 必须是"政策"、"竞品"或"技术"之一
2. priority 根据影响程度判断
3. summary 要简洁明了
4. suggestions 要具体可执行
"""
```

---

## 八、开发优先级

### 第 1 天：环境搭建
- [ ] 创建项目结构
- [ ] 安装依赖
- [ ] 配置环境变量
- [ ] 初始化数据库

### 第 2-3 天：采集模块
- [ ] 实现 Crawler 类
- [ ] 测试 Firecrawl MCP
- [ ] 测试 5 个数据源

### 第 4-5 天：清洗和分析
- [ ] 实现 Processor 类
- [ ] 实现 Analyzer 类
- [ ] 测试 LLM 调用

### 第 6-7 天：推送和存储
- [ ] 实现 Notifier 类
- [ ] 实现 Database 类
- [ ] 测试钉钉推送

### 第 8-9 天：集成和测试
- [ ] 实现主流程
- [ ] 端到端测试
- [ ] Bug 修复

### 第 10 天：定时调度
- [ ] 实现 Scheduler
- [ ] 测试定时任务
- [ ] 部署上线

---

## 九、测试计划

### 9.1 单元测试

```python
# 测试采集
def test_crawler():
    crawler = Crawler()
    result = crawler.crawl("https://www.nca.gov.cn")
    assert result is not None
    assert 'content' in result

# 测试清洗
def test_processor():
    processor = Processor()
    raw_data = {"content": "<p>测试内容</p>"}
    cleaned = processor.clean(raw_data)
    assert "<p>" not in cleaned['content']

# 测试分析
def test_analyzer():
    analyzer = Analyzer()
    data = {"title": "国密局发布新标准", "content": "..."}
    result = analyzer.analyze(data)
    assert result['category'] in ['政策', '竞品', '技术']
```

### 9.2 集成测试

```python
def test_end_to_end():
    """端到端测试"""
    # 1. 采集
    raw_data = crawler.crawl_all(sources)
    assert len(raw_data) > 0
    
    # 2. 清洗
    cleaned = processor.clean_all(raw_data)
    assert len(cleaned) > 0
    
    # 3. 分析
    analyzed = analyzer.analyze_all(cleaned)
    assert all('category' in item for item in analyzed)
    
    # 4. 保存
    database.save_all(analyzed)
    
    # 5. 推送
    unnotified = database.get_unnotified()
    assert len(unnotified) > 0
```

---

## 十、部署清单

### 10.1 部署前检查

- [ ] 所有依赖已安装
- [ ] 环境变量已配置
- [ ] 数据库已初始化
- [ ] 钉钉 Webhook 已测试
- [ ] LLM API 已测试
- [ ] 日志目录已创建

### 10.2 部署步骤

```bash
# 1. 克隆代码
git clone <repo_url>
cd intelligence-system

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 初始化数据库
python src/database.py init

# 6. 测试运行
python src/main.py --test

# 7. 启动定时任务
python src/scheduler.py
```

---

## 十一、成功标准

### MVP 完成标准

✅ **功能完整性**
- 5 个数据源采集成功率 > 90%
- AI 分析准确率 > 80%（人工抽检）
- 钉钉推送成功率 > 95%

✅ **稳定性**
- 连续运行 3 天无崩溃
- 错误日志 < 5%

✅ **可用性**
- 每日自动运行
- 手动触发正常
- 日志清晰可读

---

**文档版本**：v1.0  
**创建日期**：2026-04-15  
**目标完成时间**：2-3 周
