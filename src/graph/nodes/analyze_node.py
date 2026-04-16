"""
分析节点
负责 AI 分析情报内容
"""

from typing import Dict
from loguru import logger
from src.graph.state import IntelligenceState
from src.analyzer import Analyzer
from src.database import Database
import os


def analyze_node(state: IntelligenceState) -> Dict:
    """
    分析节点：使用 AI 分析情报
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("=" * 60)
    logger.info("[分析节点] 开始执行")
    logger.info("=" * 60)
    
    try:
        # 获取去重后的数据
        unique_data = state.get('unique_data', [])
        settings = state.get('settings', {})
        
        if not unique_data:
            logger.warning("没有数据需要分析")
            return {
                'current_step': 'analyze',
                'should_continue': False,
                'error_message': '没有数据需要分析'
            }
        
        # 初始化数据库（用于检查重复）
        db_config = settings.get('database', {})
        database = Database(db_path=db_config.get('path', 'data/intelligence.db'))
        
        # 过滤数据库中已存在的数据
        logger.info("检查数据库重复...")
        new_data = []
        for data in unique_data:
            if not database.check_duplicate(data.get('title', '')):
                new_data.append(data)
            else:
                logger.info(f"数据库中已存在: {data.get('title', '')[:50]}")
        
        logger.info(f"数据库去重后: {len(new_data)} 条新数据")
        
        if not new_data:
            logger.info("没有新数据需要分析")
            return {
                'current_step': 'analyze',
                'should_continue': False,
                'error_message': '没有新数据'
            }
        
        # 初始化分析器
        llm_config = settings.get('llm', {})
        llm_model = os.getenv('LLM_MODEL') or llm_config.get('model', 'deepseek-chat')
        
        analyzer = Analyzer(model=llm_model)
        
        # 分析数据
        logger.info(f"开始分析 {len(new_data)} 条数据...")
        analyzed_data = analyzer.analyze_all(new_data)
        
        # 统计分析结果
        analysis_errors = []
        for i, data in enumerate(new_data):
            if i >= len(analyzed_data):
                analysis_errors.append({
                    'title': data.get('title', '')[:50],
                    'error': '分析失败'
                })
        
        logger.info(f"分析完成: 成功 {len(analyzed_data)}, 失败 {len(analysis_errors)}")
        
        # 判断是否继续
        should_continue = len(analyzed_data) > 0
        
        return {
            'analyzed_data': analyzed_data,
            'analysis_errors': analysis_errors,
            'current_step': 'analyze',
            'should_continue': should_continue,
            'error_message': None if should_continue else '所有数据分析失败'
        }
        
    except Exception as e:
        logger.error(f"[分析节点] 执行失败: {e}", exc_info=True)
        return {
            'current_step': 'analyze',
            'should_continue': False,
            'error_message': f'分析节点异常: {str(e)}'
        }
