"""
定时调度模块
负责定时执行情报采集任务
"""

import sys
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from dotenv import load_dotenv
import yaml

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import IntelligenceSystem, setup_logging


def load_schedule_config(config_file: str = "config/settings.yaml") -> dict:
    """加载调度配置"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
        return {
            'enabled': True,
            'cron': '0 9 * * *',  # 每天 9:00
            'timezone': 'Asia/Shanghai'
        }
    
    with open(config_path, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)
        return settings.get('schedule', {})


def run_task():
    """执行任务"""
    try:
        logger.info("定时任务触发")
        system = IntelligenceSystem()
        system.run()
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}", exc_info=True)


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 配置日志
    setup_logging()
    
    # 加载调度配置
    schedule_config = load_schedule_config()
    
    if not schedule_config.get('enabled', True):
        logger.warning("定时调度已禁用")
        return
    
    # 创建调度器
    scheduler = BlockingScheduler(timezone=schedule_config.get('timezone', 'Asia/Shanghai'))
    
    # 添加定时任务
    cron_expr = schedule_config.get('cron', '0 9 * * *')
    logger.info(f"配置定时任务: {cron_expr}")
    
    # 解析 cron 表达式
    # 格式：分 时 日 月 周
    parts = cron_expr.split()
    if len(parts) == 5:
        minute, hour, day, month, day_of_week = parts
        
        scheduler.add_job(
            run_task,
            trigger=CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=schedule_config.get('timezone', 'Asia/Shanghai')
            ),
            id='intelligence_task',
            name='情报采集任务',
            replace_existing=True
        )
    else:
        logger.error(f"无效的 cron 表达式: {cron_expr}")
        return
    
    # 打印下次执行时间
    next_run = scheduler.get_job('intelligence_task').next_run_time
    logger.info(f"下次执行时间: {next_run}")
    
    # 启动调度器
    logger.info("定时调度器启动")
    logger.info("按 Ctrl+C 停止")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时调度器停止")


if __name__ == "__main__":
    main()
