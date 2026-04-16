"""
主程序入口（LangGraph 版本）
使用 LangGraph 工作流协调各个模块
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

from src.graph.workflow import create_workflow
from src.graph.state import create_initial_state


class IntelligenceSystemLangGraph:
    """情报分析系统主类（LangGraph 版本）"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化系统

        Args:
            config_dir: 配置文件目录
        """
        # 加载环境变量
        load_dotenv()

        # 确定配置文件目录
        config_path = Path(config_dir)
        if not config_path.exists():
            project_root = Path(__file__).parent.parent
            config_path = project_root / config_dir

        self.config_dir = config_path
        self.sources = self._load_sources()
        self.settings = self._load_settings()

        # 创建 LangGraph 工作流
        self.workflow = create_workflow()

        logger.info("情报分析系统（LangGraph 版本）初始化完成")

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
        logger.info("开始执行情报采集任务（LangGraph 工作流）")
        logger.info("=" * 60)

        try:
            # 创建初始状态
            initial_state = create_initial_state(self.sources, self.settings)

            # 运行 LangGraph 工作流
            logger.info("启动 LangGraph 工作流...")
            result = self.workflow.invoke(initial_state)

            # 输出结果统计
            logger.info("\n" + "=" * 60)
            logger.info("任务执行完成")
            logger.info("=" * 60)
            
            logger.info(f"最终步骤: {result.get('current_step')}")
            logger.info(f"采集数据: {len(result.get('raw_data', []))} 条")
            logger.info(f"清洗数据: {len(result.get('cleaned_data', []))} 条")
            logger.info(f"去重数据: {len(result.get('unique_data', []))} 条")
            logger.info(f"分析数据: {len(result.get('analyzed_data', []))} 条")
            logger.info(f"保存数据: {len(result.get('saved_data', []))} 条")
            logger.info(f"推送数据: {len(result.get('notified_data', []))} 条")
            
            notification_stats = result.get('notification_stats', {})
            logger.info(f"推送统计: 成功 {notification_stats.get('success', 0)}, 失败 {notification_stats.get('failed', 0)}")
            
            if result.get('error_message'):
                logger.warning(f"错误信息: {result.get('error_message')}")

        except Exception as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            raise

    def test(self):
        """测试模式：只采集一个数据源"""
        logger.info("运行测试模式（LangGraph 工作流）...")

        # 只测试第一个启用的数据源
        test_sources = [s for s in self.sources if s.get('enabled', True)][:1]

        if not test_sources:
            logger.error("没有可用的数据源")
            return

        logger.info(f"测试数据源: {test_sources[0]['name']}")

        # 创建测试状态
        initial_state = create_initial_state(test_sources, self.settings)

        # 运行工作流
        result = self.workflow.invoke(initial_state)

        # 输出结果
        raw_data = result.get('raw_data', [])
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
    parser = argparse.ArgumentParser(description="行业情报分析系统（LangGraph 版本）")
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--config', default='config', help='配置文件目录')
    parser.add_argument('--log-level', default='INFO', help='日志级别')

    args = parser.parse_args()

    # 配置日志
    setup_logging(log_level=args.log_level)

    # 初始化系统
    system = IntelligenceSystemLangGraph(config_dir=args.config)

    # 运行
    if args.test:
        system.test()
    else:
        system.run()


if __name__ == "__main__":
    main()
