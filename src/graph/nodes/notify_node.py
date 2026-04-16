"""
推送节点
负责推送通知和生成报告
"""

import os
from typing import Dict
from loguru import logger
from src.graph.state import IntelligenceState
from src.notifier import Notifier
from src.notifier_stream import DingTalkStreamNotifier
from src.database import Database


def notify_node(state: IntelligenceState) -> Dict:
    """
    推送节点：推送通知和生成报告
    
    Args:
        state: 工作流状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("=" * 60)
    logger.info("[推送节点] 开始执行")
    logger.info("=" * 60)
    
    try:
        # 获取配置
        settings = state.get('settings', {})
        
        # 初始化数据库
        db_config = settings.get('database', {})
        database = Database(db_path=db_config.get('path', 'data/intelligence.db'))
        
        # 获取未推送的数据
        logger.info("获取未推送的数据...")
        unnotified = database.get_unnotified()
        
        if not unnotified:
            logger.info("没有需要推送的数据")
            
            # 发送汇总消息
            stats = database.get_statistics()
            notifier_config = settings.get('notifier', {})
            notifier = Notifier(max_retries=notifier_config.get('max_retries', 3))
            notifier.send_summary(stats)
            
            return {
                'notification_stats': {'total': 0, 'success': 0, 'failed': 0},
                'current_step': 'notify',
                'should_continue': True,
                'error_message': None
            }
        
        # 初始化推送器（优先使用 Stream 模式）
        notifier_config = settings.get('notifier', {})
        
        # 检查是否配置了 Stream 模式
        client_id = os.getenv('DINGTALK_CLIENT_ID')
        client_secret = os.getenv('DINGTALK_CLIENT_SECRET')
        
        if client_id and client_secret:
            logger.info("使用钉钉 Stream 模式推送")
            stream_notifier = DingTalkStreamNotifier(
                client_id=client_id,
                client_secret=client_secret,
                enable_bot=False
            )
            push_stats = stream_notifier.send_batch(unnotified)
            notifier = stream_notifier  # 用于后续的报告生成
        else:
            logger.info("使用钉钉 Webhook 模式推送")
            notifier = Notifier(max_retries=notifier_config.get('max_retries', 3))
            push_stats = notifier.send_batch(unnotified)
        
        logger.info(f"推送 {len(unnotified)} 条数据...")
        
        # 标记为已推送
        notified_data = []
        if push_stats['success'] > 0:
            for item in unnotified:
                database.mark_notified(item['id'])
                notified_data.append(item)
        
        logger.info(f"推送完成: 成功 {push_stats['success']}, 失败 {push_stats['failed']}")
        
        # 生成每日报告（仅 Webhook 模式支持）
        report_path = None
        if isinstance(notifier, Notifier):
            report_path = notifier.generate_daily_report(unnotified)
            if report_path:
                logger.info(f"每日报告已生成: {report_path}")
        
        # 发送汇总消息
        stats = database.get_statistics()
        if isinstance(notifier, Notifier):
            notifier.send_summary(stats)
        else:
            # Stream 模式发送汇总
            summary_data = {
                'title': f"【汇总】今日情报统计 ({stats.get('today', 0)} 条)",
                'source': '情报分析系统',
                'category': '统计',
                'priority': '中',
                'publish_date': stats.get('date', ''),
                'summary': f"今日共采集 {stats.get('today', 0)} 条情报，累计 {stats.get('total', 0)} 条。",
                'impact': f"按分类：{stats.get('by_category', {})}",
                'suggestions': '[]'
            }
            notifier.send_intelligence(summary_data)
        
        return {
            'notified_data': notified_data,
            'notification_stats': push_stats,
            'current_step': 'notify',
            'should_continue': True,
            'error_message': None
        }
        
    except Exception as e:
        logger.error(f"[推送节点] 执行失败: {e}", exc_info=True)
        return {
            'notification_stats': {'total': 0, 'success': 0, 'failed': 0},
            'current_step': 'notify',
            'should_continue': True,  # 推送失败不影响整体流程
            'error_message': f'推送节点异常: {str(e)}'
        }
