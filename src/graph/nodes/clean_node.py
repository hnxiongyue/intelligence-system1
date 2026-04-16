"""
清洗节点
负责清洗和提取数据
"""

import os
from typing import Dict
from loguru import logger
from src.graph.state import IntelligenceState
from src.processor import Processor
from src.vector_store import VectorStore


def clean_node(state: IntelligenceState) -> Dict:
    """
    清洗节点：清洗和提取数据
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("=" * 60)
    logger.info("[清洗节点] 开始执行")
    logger.info("=" * 60)
    
    try:
        # 获取原始数据
        raw_data = state.get('raw_data', [])
        
        if not raw_data:
            logger.warning("没有原始数据需要清洗")
            return {
                'current_step': 'clean',
                'should_continue': False,
                'error_message': '没有原始数据'
            }
        
        # 初始化处理器
        processor = Processor()
        
        # 清洗数据
        logger.info(f"开始清洗 {len(raw_data)} 条数据...")
        cleaned_data = processor.clean_all(raw_data)
        
        logger.info(f"清洗完成: {len(cleaned_data)} 条")
        
        # 去重（基于哈希）
        logger.info("开始基础去重...")
        unique_data = processor.deduplicate(cleaned_data)
        duplicate_count = len(cleaned_data) - len(unique_data)
        
        logger.info(f"基础去重完成: 保留 {len(unique_data)} 条, 去除 {duplicate_count} 条重复")
        
        # 向量去重（基于语义相似度）
        vector_enabled = os.getenv('VECTOR_STORE_ENABLED', 'false').lower() == 'true'
        vector_duplicate_count = 0
        
        if vector_enabled and unique_data:
            try:
                logger.info("开始向量去重...")
                vector_store = VectorStore()
                
                final_data = []
                for item in unique_data:
                    # 检查语义重复
                    is_dup, dup_info = vector_store.check_duplicate(
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        similarity_threshold=0.85
                    )
                    
                    if not is_dup:
                        final_data.append(item)
                    else:
                        vector_duplicate_count += 1
                        logger.info(
                            f"向量去重: {item.get('title', '')[:30]} "
                            f"与 ID={dup_info['intelligence_id']} 相似"
                        )
                
                unique_data = final_data
                logger.info(f"向量去重完成: 去除 {vector_duplicate_count} 条语义重复")
                
            except Exception as e:
                logger.warning(f"向量去重失败，跳过: {e}")
        
        total_duplicate = duplicate_count + vector_duplicate_count
        
        # 判断是否继续
        should_continue = len(unique_data) > 0
        
        return {
            'cleaned_data': cleaned_data,
            'unique_data': unique_data,
            'duplicate_count': total_duplicate,
            'current_step': 'clean',
            'should_continue': should_continue,
            'error_message': None if should_continue else '清洗后没有有效数据'
        }
        
    except Exception as e:
        logger.error(f"[清洗节点] 执行失败: {e}", exc_info=True)
        return {
            'current_step': 'clean',
            'should_continue': False,
            'error_message': f'清洗节点异常: {str(e)}'
        }
