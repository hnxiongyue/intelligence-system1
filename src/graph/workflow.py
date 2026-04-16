"""
LangGraph 主工作流
"""

from langgraph.graph import StateGraph, END
from loguru import logger

from src.graph.state import IntelligenceState, create_initial_state
from src.graph.nodes.crawl_node import crawl_node
from src.graph.nodes.clean_node import clean_node
from src.graph.nodes.analyze_node import analyze_node
from src.graph.nodes.save_node import save_node
from src.graph.nodes.notify_node import notify_node


def should_continue(state: IntelligenceState) -> str:
    """
    条件路由：判断是否继续执行
    
    Args:
        state: 工作流状态
        
    Returns:
        下一个节点名称或 END
    """
    if not state.get('should_continue', True):
        logger.warning(f"工作流中断: {state.get('error_message', '未知原因')}")
        return END
    
    current_step = state.get('current_step', '')
    
    # 根据当前步骤决定下一步
    if current_step == 'crawl':
        return 'clean'
    elif current_step == 'clean':
        return 'analyze'
    elif current_step == 'analyze':
        return 'save'
    elif current_step == 'save':
        return 'notify'
    elif current_step == 'notify':
        return END
    else:
        return END


def create_workflow() -> StateGraph:
    """
    创建 LangGraph 工作流
    
    Returns:
        编译后的工作流
    """
    logger.info("创建 LangGraph 工作流...")
    
    # 创建状态图
    workflow = StateGraph(IntelligenceState)
    
    # 添加节点
    workflow.add_node("crawl", crawl_node)
    workflow.add_node("clean", clean_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("save", save_node)
    workflow.add_node("notify", notify_node)
    
    # 设置入口点
    workflow.set_entry_point("crawl")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "crawl",
        should_continue,
        {
            "clean": "clean",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "clean",
        should_continue,
        {
            "analyze": "analyze",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "save": "save",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "save",
        should_continue,
        {
            "notify": "notify",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "notify",
        should_continue,
        {
            END: END
        }
    )
    
    # 编译工作流
    app = workflow.compile()
    
    logger.info("LangGraph 工作流创建完成")
    
    return app


# 测试代码
if __name__ == "__main__":
    # 创建测试工作流
    app = create_workflow()
    
    # 创建测试状态
    test_sources = [
        {
            'name': '测试数据源',
            'url': 'https://www.example.com',
            'enabled': True,
            'category': '测试'
        }
    ]
    
    test_settings = {
        'crawler': {'timeout': 30, 'max_retries': 3},
        'database': {'path': 'data/intelligence.db'},
        'llm': {'model': 'deepseek-chat'},
        'notifier': {'max_retries': 3}
    }
    
    initial_state = create_initial_state(test_sources, test_settings)
    
    # 运行工作流
    print("开始运行测试工作流...")
    result = app.invoke(initial_state)
    
    print(f"\n工作流执行完成:")
    print(f"  当前步骤: {result.get('current_step')}")
    print(f"  是否继续: {result.get('should_continue')}")
    print(f"  错误信息: {result.get('error_message')}")
