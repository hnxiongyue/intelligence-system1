"""
采集节点
负责从各个数据源采集信息
"""

from typing import Dict
from loguru import logger
from src.graph.state import IntelligenceState
from src.crawlers.crawler_manager import CrawlerManager


def crawl_node(state: IntelligenceState) -> Dict:
    """
    采集节点：从数据源采集信息
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("=" * 60)
    logger.info("[采集节点] 开始执行")
    logger.info("=" * 60)
    
    crawler_manager = None
    
    try:
        # 获取配置
        sources = state.get('sources', [])
        settings = state.get('settings', {})
        
        if not sources:
            logger.warning("没有配置数据源")
            return {
                'current_step': 'crawl',
                'should_continue': False,
                'error_message': '没有配置数据源'
            }
        
        # 初始化爬虫管理器
        crawler_manager = CrawlerManager(settings)
        
        # 采集数据
        logger.info(f"开始采集 {len(sources)} 个数据源...")
        raw_data = crawler_manager.crawl_all(sources)
        
        # 统计采集结果
        success_count = len(raw_data)
        failed_count = len(sources) - success_count
        
        logger.info(f"采集完成: 成功 {success_count}, 失败 {failed_count}")
        
        # 记录采集错误
        crawl_errors = []
        for source in sources:
            if not any(d.get('source') == source['name'] for d in raw_data):
                crawl_errors.append({
                    'source': source['name'],
                    'error': '采集失败'
                })
        
        # 判断是否继续
        should_continue = len(raw_data) > 0
        
        return {
            'raw_data': raw_data,
            'crawl_errors': crawl_errors,
            'current_step': 'crawl',
            'should_continue': should_continue,
            'error_message': None if should_continue else '所有数据源采集失败'
        }
        
    except Exception as e:
        logger.error(f"[采集节点] 执行失败: {e}", exc_info=True)
        return {
            'current_step': 'crawl',
            'should_continue': False,
            'error_message': f'采集节点异常: {str(e)}'
        }
    
    finally:
        # 关闭爬虫管理器
        if crawler_manager:
            crawler_manager.close()
