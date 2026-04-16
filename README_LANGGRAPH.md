# 行业情报分析系统 - LangGraph 完整版

基于 LangGraph 的 AI 自动化情报采集、分析和推送系统。

## 🆕 LangGraph 版本特性

### 与 MVP 版本的区别

| 特性 | MVP 版本 | LangGraph 版本 |
|------|---------|---------------|
| 架构 | 简单顺序调用 | LangGraph 状态机 |
| 流程控制 | 硬编码 | 条件路由 |
| 错误处理 | 基础 | 完善的状态追踪 |
| 可扩展性 | 一般 | 高（易于添加节点） |
| 可观测性 | 日志 | 状态追踪 + 日志 |

### 核心优势

1. **状态管理**：所有数据在状态中流转，易于追踪和调试
2. **条件路由**：根据执行结果动态决定下一步
3. **节点化设计**：每个功能独立为节点，易于维护和扩展
4. **错误隔离**：单个节点失败不影响整体流程
5. **可视化**：可以导出工作流图（未来支持）

## 📋 功能特性

- ✅ LangGraph 工作流编排
- ✅ 状态化数据流转
- ✅ 条件路由控制
- ✅ 自动采集多个数据源
- ✅ AI 智能分析
- ✅ 钉钉自动推送
- ✅ 数据去重和存储
- ✅ 定时自动运行

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- pip

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate

# 安装依赖（包含 LangGraph）
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置文件
copy .env.example .env

# 编辑 .env 文件，填入以下信息：
# - LLM_API_KEY: LLM API Key（DeepSeek/OpenAI）
# - LLM_BASE_URL: API Base URL
# - LLM_MODEL: 模型名称
# - DINGTALK_WEBHOOK: 钉钉 Webhook URL
```

### 4. 初始化数据库

```bash
python src/database.py init
```

### 5. 运行 LangGraph 版本

```bash
# 使用快速启动脚本
run_langgraph.bat

# 或直接运行
python src/main_langgraph.py

# 测试模式
python src/main_langgraph.py --test
```

## 📁 项目结构（LangGraph 版本）

```
intelligence-system/
├── config/
│   ├── sources.yaml          # 数据源配置
│   └── settings.yaml         # 系统配置
├── src/
│   ├── main_langgraph.py    # LangGraph 主程序 ⭐
│   ├── graph/               # LangGraph 工作流 ⭐
│   │   ├── state.py         # 状态定义
│   │   ├── workflow.py      # 工作流编排
│   │   └── nodes/           # 工作流节点
│   │       ├── crawl_node.py    # 采集节点
│   │       ├── clean_node.py    # 清洗节点
│   │       ├── analyze_node.py  # 分析节点
│   │       ├── save_node.py     # 保存节点
│   │       └── notify_node.py   # 推送节点
│   ├── crawler.py           # 采集模块
│   ├── processor.py         # 清洗模块
│   ├── analyzer.py          # 分析模块
│   ├── notifier.py          # 推送模块
│   ├── database.py          # 数据库操作
│   └── scheduler.py         # 定时调度
├── data/
│   └── intelligence.db      # SQLite 数据库
├── logs/                    # 日志目录
├── reports/                 # 报告目录
├── .env                     # 环境变量
├── requirements.txt         # 依赖清单
├── run_langgraph.bat       # 快速启动脚本 ⭐
└── README_LANGGRAPH.md     # 本文档
```

## 🔄 LangGraph 工作流

### 工作流图

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌─────────────┐
│ Crawl Node  │ ← 采集数据
└──────┬──────┘
       │ should_continue?
       ▼
┌─────────────┐
│ Clean Node  │ ← 清洗数据
└──────┬──────┘
       │ should_continue?
       ▼
┌──────────────┐
│ Analyze Node │ ← AI 分析
└──────┬───────┘
       │ should_continue?
       ▼
┌─────────────┐
│  Save Node  │ ← 保存数据库
└──────┬──────┘
       │ should_continue?
       ▼
┌──────────────┐
│ Notify Node  │ ← 推送通知
└──────┬───────┘
       │
       ▼
   ┌─────┐
   │ End │
   └─────┘
```

### 状态流转

每个节点接收 `IntelligenceState` 并返回更新后的状态字段：

```python
class IntelligenceState(TypedDict):
    # 输入配置
    sources: List[Dict]
    settings: Dict
    
    # 各阶段数据
    raw_data: List[Dict]          # 原始数据
    cleaned_data: List[Dict]      # 清洗后数据
    unique_data: List[Dict]       # 去重后数据
    analyzed_data: List[Dict]     # 分析后数据
    saved_data: List[Dict]        # 已保存数据
    notified_data: List[Dict]     # 已推送数据
    
    # 流程控制
    current_step: str             # 当前步骤
    should_continue: bool         # 是否继续
    error_message: Optional[str]  # 错误信息
    
    # 统计信息
    stats: Dict
```

### 条件路由

`should_continue` 函数根据状态决定下一步：

```python
def should_continue(state: IntelligenceState) -> str:
    if not state.get('should_continue', True):
        return END
    
    current_step = state.get('current_step', '')
    
    if current_step == 'crawl':
        return 'clean'
    elif current_step == 'clean':
        return 'analyze'
    # ...
```

## 🔧 使用说明

### 手动运行

```bash
# 完整流程
python src/main_langgraph.py

# 测试模式
python src/main_langgraph.py --test

# 指定配置目录
python src/main_langgraph.py --config /path/to/config

# 指定日志级别
python src/main_langgraph.py --log-level DEBUG
```

### 使用快速启动脚本

```bash
# Windows
run_langgraph.bat

# 测试模式
run_langgraph.bat --test
```

### 定时运行

修改 `src/scheduler.py` 导入 LangGraph 版本：

```python
from src.main_langgraph import IntelligenceSystemLangGraph

def run_task():
    system = IntelligenceSystemLangGraph()
    system.run()
```

## 📊 数据流程（LangGraph 版本）

```
1. 创建初始状态
   ↓
2. Crawl Node（采集）
   → 更新 raw_data
   → 检查 should_continue
   ↓
3. Clean Node（清洗）
   → 更新 cleaned_data, unique_data
   → 检查 should_continue
   ↓
4. Analyze Node（分析）
   → 更新 analyzed_data
   → 检查 should_continue
   ↓
5. Save Node（保存）
   → 更新 saved_data
   → 检查 should_continue
   ↓
6. Notify Node（推送）
   → 更新 notified_data
   → 生成报告
   ↓
7. 结束
```

## 🎯 开发指南

### 添加新节点

1. 在 `src/graph/nodes/` 创建新节点文件
2. 定义节点函数，接收和返回状态
3. 在 `src/graph/workflow.py` 中注册节点
4. 添加条件边

示例：

```python
# src/graph/nodes/my_node.py
def my_node(state: IntelligenceState) -> Dict:
    logger.info("[我的节点] 开始执行")
    
    # 处理逻辑
    result = do_something(state)
    
    return {
        'my_data': result,
        'current_step': 'my_node',
        'should_continue': True
    }

# src/graph/workflow.py
workflow.add_node("my_node", my_node)
workflow.add_conditional_edges("previous_node", should_continue, {
    "my_node": "my_node",
    END: END
})
```

### 修改状态定义

在 `src/graph/state.py` 中添加新字段：

```python
class IntelligenceState(TypedDict):
    # ... 现有字段
    my_new_field: List[Dict]  # 新字段
```

### 调试工作流

```python
# 运行单个节点测试
from src.graph.nodes.crawl_node import crawl_node
from src.graph.state import create_initial_state

state = create_initial_state(sources, settings)
result = crawl_node(state)
print(result)
```

## 🐛 常见问题

### Q1: LangGraph 导入失败？

```bash
# 确保安装了 LangGraph
pip install langgraph>=0.2.0
```

### Q2: 状态更新不生效？

检查节点返回的字典是否包含正确的字段名。

### Q3: 工作流中断？

查看日志中的 `should_continue` 和 `error_message` 字段。

### Q4: 如何查看工作流执行过程？

设置日志级别为 DEBUG：

```bash
python src/main_langgraph.py --log-level DEBUG
```

## 📈 后续计划

- [ ] 工作流可视化
- [ ] 并行节点执行
- [ ] 人工审核节点
- [ ] 工作流回滚
- [ ] 状态持久化
- [ ] 分布式执行

## 🔄 从 MVP 迁移

如果你已经在使用 MVP 版本：

1. 安装新依赖：`pip install -r requirements.txt`
2. 数据库兼容，无需迁移
3. 配置文件兼容，无需修改
4. 使用 `src/main_langgraph.py` 替代 `src/main.py`

两个版本可以并存，根据需要选择使用。

## 📄 许可证

MIT License

---

**版本**：v2.0.0-langgraph  
**更新日期**：2026-04-16  
**基于**：LangGraph 0.2.0+
