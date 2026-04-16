"""
LangGraph 工作流状态定义
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add


class IntelligenceState(TypedDict):
    """
    情报分析系统工作流状态
    
    状态在各个节点之间传递，记录整个流程的数据和状态
    """
    
    # 输入配置
    sources: List[Dict]  # 数据源配置列表
    settings: Dict  # 系统配置
    
    # 采集阶段
    raw_data: Annotated[List[Dict], add]  # 原始采集数据（累加）
    crawl_errors: Annotated[List[Dict], add]  # 采集错误记录（累加）
    
    # 清洗阶段
    cleaned_data: Annotated[List[Dict], add]  # 清洗后的数据（累加）
    clean_errors: Annotated[List[Dict], add]  # 清洗错误记录（累加）
    
    # 去重阶段
    unique_data: Annotated[List[Dict], add]  # 去重后的数据（累加）
    duplicate_count: int  # 重复数据数量
    
    # 分析阶段
    analyzed_data: Annotated[List[Dict], add]  # 分析后的数据（累加）
    analysis_errors: Annotated[List[Dict], add]  # 分析错误记录（累加）
    
    # 存储阶段
    saved_data: Annotated[List[Dict], add]  # 已保存的数据（累加）
    save_errors: Annotated[List[Dict], add]  # 保存错误记录（累加）
    
    # 推送阶段
    notified_data: Annotated[List[Dict], add]  # 已推送的数据（累加）
    notification_stats: Dict  # 推送统计信息
    
    # 流程控制
    current_step: str  # 当前步骤
    should_continue: bool  # 是否继续执行
    error_message: Optional[str]  # 错误信息
    
    # 统计信息
    stats: Dict  # 整体统计信息


def create_initial_state(sources: List[Dict], settings: Dict) -> IntelligenceState:
    """
    创建初始状态
    
    Args:
        sources: 数据源配置
        settings: 系统配置
        
    Returns:
        初始化的工作流状态
    """
    return IntelligenceState(
        # 输入配置
        sources=sources,
        settings=settings,
        
        # 采集阶段
        raw_data=[],
        crawl_errors=[],
        
        # 清洗阶段
        cleaned_data=[],
        clean_errors=[],
        
        # 去重阶段
        unique_data=[],
        duplicate_count=0,
        
        # 分析阶段
        analyzed_data=[],
        analysis_errors=[],
        
        # 存储阶段
        saved_data=[],
        save_errors=[],
        
        # 推送阶段
        notified_data=[],
        notification_stats={},
        
        # 流程控制
        current_step="init",
        should_continue=True,
        error_message=None,
        
        # 统计信息
        stats={}
    )
