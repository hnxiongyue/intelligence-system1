"""
主程序入口
协调各个模块完成情报采集、分析、推送流程
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler import Crawler
from src.processor import Processor
from src.analyzer import Analyzer
from src.notifier import Notifier
from src.database import Database


class IntelligenceSystem:
    """情报分析系统主类"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化系统

        Args:
            config_dir: 配置文件目录
        """
        # 加载环境变量
        load_dotenv()

        # 确定配置文件目录（支持相对路径和绝对路径）
        config_path = Path(config_dir)

        # 如果配置目录不存在，尝试从项目根目录查找
        if not config_path.exists():
            # 获取当前文件所在目录的父目录（项目根目录）
            project_root = Path(__file__).parent.parent
            config_path = project_root / config_dir

        self.config_dir = config_path
        self.sources = self._load_sources()
        self.settings = self._load_settings()

        # 初始化模块
        self.crawler = Crawler(
            timeout=self.settings.get('crawler', {}).get('timeout', 30),
            max_retries=self.settings.get('crawler', {}).get('max_retries', 3)
        )

        self.processor = Processor()

        # 初始化 Analyzer - 优先使用环境变量
        llm_model = os.getenv('LLM_MODEL') or self.settings.get('llm', {}).get('model', 'qwen-plus')

        self.analyzer = Analyzer(
            model=llm_model
        )

        self.notifier = Notifier(
            max_retries=self.settings.get('notifier', {}).get('max_retries', 3)
        )

        self.database = Database(
            db_path=self.settings.get('database', {}).get('path', 'data/intelligence.db')
        )

        logger.info("情报分析系统初始化完成")

    def _load_sources(self) -> list:
        """加载数据源配置"""
        sources_file = self.config_dir / "sources.yaml"

        if not sources_file.exists():
            logger.error(f"数据源配置文件不存在: {sources_file}")
            return []

        with open(sources_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            sources = config.get('sources', [])
            logger.info(f"加载数据源配置: {len(sources)} 个")
            return sources

    def _load_settings(self) -> dict:
        """加载系统配置"""
        settings_file = self.config_dir / "settings.yaml"

        if not settings_file.exists():
            logger.warning(f"系统配置文件不存在: {settings_file}，使用默认配置")
            return {}

        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
            logger.info("加载系统配置完成")
            return settings

    def run(self):
        """运行主流程"""
        logger.info("=" * 60)
        logger.info("开始执行情报采集任务")
        logger.info("=" * 60)

        try:
            # 1. 采集数据
            logger.info("\n[1/6] 开始采集数据...")
            raw_data = self.crawler.crawl_all(self.sources)
            logger.info(f"采集完成: {len(raw_data)} 条")

            if not raw_data:
                logger.warning("没有采集到数据，任务结束")
                return

            # 记录采集日志
            for source in self.sources:
                source_name = source['name']
                source_data = [d for d in raw_data if d.get('source') == source_name]
                status = 'success' if source_data else 'failed'
                self.database.log_crawl(source_name, status, len(source_data))

            # 2. 清洗数据
            logger.info("\n[2/6] 开始清洗数据...")
            cleaned_data = self.processor.clean_all(raw_data)
            logger.info(f"清洗完成: {len(cleaned_data)} 条")

            # 3. 去重
            logger.info("\n[3/6] 开始去重...")
            unique_data = self.processor.deduplicate(cleaned_data)
            logger.info(f"去重完成: {len(unique_data)} 条")

            # 进一步检查数据库中的重复
            new_data = []
            for data in unique_data:
                if not self.database.check_duplicate(data.get('title', '')):
                    new_data.append(data)
                else:
                    logger.info(f"数据库中已存在: {data.get('title', '')[:50]}")

            logger.info(f"数据库去重后: {len(new_data)} 条新数据")

            if not new_data:
                logger.info("没有新数据，任务结束")
                return

            # 4. AI 分析
            logger.info("\n[4/6] 开始 AI 分析...")
            analyzed_data = self.analyzer.analyze_all(new_data)
            logger.info(f"分析完成: {len(analyzed_data)} 条")

            # 5. 保存到数据库
            logger.info("\n[5/6] 开始保存数据...")
            saved_count = 0
            for data in analyzed_data:
                if self.database.save_intelligence(data):
                    saved_count += 1
            logger.info(f"保存完成: {saved_count} 条")

            # 6. 推送通知
            logger.info("\n[6/6] 开始推送通知...")
            unnotified = self.database.get_unnotified()

            if unnotified:
                push_stats = self.notifier.send_batch(unnotified)

                # 标记为已推送
                for item in unnotified:
                    if push_stats['success'] > 0:
                        self.database.mark_notified(item['id'])

                logger.info(f"推送完成: 成功 {push_stats['success']}, 失败 {push_stats['failed']}")

                # 生成每日汇总报告
                report_path = self.notifier.generate_daily_report(unnotified)
                if report_path:
                    logger.info(f"每日报告已生成: {report_path}")
            else:
                logger.info("没有需要推送的数据")

            # 发送汇总消息（如果配置了钉钉）
            stats = self.database.get_statistics()
            self.notifier.send_summary(stats)

            logger.info("\n" + "=" * 60)
            logger.info("任务执行完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            raise

    def test(self):
        """测试模式：只采集一个数据源"""
        logger.info("运行测试模式...")

        # 只测试第一个启用的数据源
        test_sources = [s for s in self.sources if s.get('enabled', True)][:1]

        if not test_sources:
            logger.error("没有可用的数据源")
            return

        logger.info(f"测试数据源: {test_sources[0]['name']}")

        # 采集
        raw_data = self.crawler.crawl_all(test_sources)

        if raw_data:
            logger.info(f"采集成功: {len(raw_data)} 条")
            logger.info(f"内容预览: {raw_data[0].get('content', '')[:200]}...")
        else:
            logger.error("采集失败")


def setup_logging(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """配置日志"""
    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置 loguru
    logger.remove()  # 移除默认处理器

    # 控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

    # 文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="10 MB",
        retention="30 days"
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="行业情报分析系统")
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--config', default='config', help='配置文件目录')
    parser.add_argument('--log-level', default='INFO', help='日志级别')

    args = parser.parse_args()

    # 配置日志
    setup_logging(log_level=args.log_level)

    # 初始化系统
    system = IntelligenceSystem(config_dir=args.config)

    # 运行
    if args.test:
        system.test()
    else:
        system.run()


if __name__ == "__main__":
    main()
