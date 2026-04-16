"""
保存节点
负责将数据保存到数据库
"""

import os
from typing import Dict
from loguru import logger
from src.graph.state import IntelligenceState
from src.database import Database
from src.vector_store import VectorStore


def save_node(state: IntelligenceState) -> Dict:
    """
    保存节点：保存数据到数据库
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("=" * 60)
    logger.info("[保存节点] 开始执行")
    logger.info("=" * 60)
    
    try:
        # 获取分析后的数据
        analyzed_data = state.get('analyzed_data', [])
        settings = state.get('settings', {})
        
        if not analyzed_data:
            logger.warning("没有数据需要保存")
            return {
                'current_step': 'save',
                'should_continue': False,
                'error_message': '没有数据需要保存'
            }
        
        # 初始化数据库
        db_config = settings.get('database', {})
        database = Database(db_path=db_config.get('path', 'data/intelligence.db'))
        
        # 保存数据
        logger.info(f"开始保存 {len(analyzed_data)} 条数据...")
        saved_data = []
        save_errors = []
        
        # 初始化向量存储（如果启用）
        vector_enabled = os.getenv('VECTOR_STORE_ENABLED', 'false').lower() == 'true'
        vector_store = None
        if vector_enabled:
            try:
                vector_store = VectorStore()
                logger.info("向量存储已启用")
            except Exception as e:
                logger.warning(f"向量存储初始化失败，跳过: {e}")
                vector_store = None
        
        for data in analyzed_data:
            # 保存到 SQLite
            intelligence_id = database.save_intelligence(data)
            
            if intelligence_id:
                data['id'] = intelligence_id
                saved_data.append(data)
                
                # 保存到向量数据库
                if vector_store:
                    try:
                        vector_store.add_intelligence(
                            intelligence_id=intelligence_id,
                            title=data.get('title', ''),
                            content=data.get('content', ''),
                            category=data.get('category'),
                            source=data.get('source')
                        )
                    except Exception as e:
                        logger.warning(f"保存向量失败: {e}")
            else:
                save_errors.append({
                    'title': data.get('title', '')[:50],
                    'error': '保存失败'
                })
        
        logger.info(f"保存完成: 成功 {len(saved_data)}, 失败 {len(save_errors)}")
        
        # 记录采集日志
        sources = state.get('sources', [])
        raw_data = state.get('raw_data', [])
        for source in sources:
            source_name = source['name']
            source_data = [d for d in raw_data if d.get('source') == source_name]
            status = 'success' if source_data else 'failed'
            database.log_crawl(source_name, status, len(source_data))
        
        # 判断是否继续
        should_continue = len(saved_data) > 0
        
        return {
            'saved_data': saved_data,
            'save_errors': save_errors,
            'current_step': 'save',
            'should_continue': should_continue,
            'error_message': None if should_continue else '所有数据保存失败'
        }
        
    except Exception as e:
        logger.error(f"[保存节点] 执行失败: {e}", exc_info=True)
        return {
            'current_step': 'save',
            'should_continue': False,
            'error_message': f'保存节点异常: {str(e)}'
        }
