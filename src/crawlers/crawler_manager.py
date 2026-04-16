"""
爬虫管理器
根据数据源类型自动选择合适的爬虫
"""

from typing import Dict, Optional, List
from loguru import logger

from src.crawler import Crawler as SimpleCrawler
from src.crawlers.playwright_crawler import PlaywrightCrawler
from src.crawlers.rss_parser import RSSParser
from src.crawlers.pdf_parser import PDFParser
from src.crawlers.firecrawl_mcp import FirecrawlMCP
from src.crawlers.github_mcp import GitHubMCP


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self, settings: Dict = None):
        """
        初始化爬虫管理器
        
        Args:
            settings: 配置信息
        """
        self.settings = settings or {}
        crawler_config = self.settings.get('crawler', {})
        
        # 初始化各种爬虫
        self.simple_crawler = SimpleCrawler(
            timeout=crawler_config.get('timeout', 30),
            max_retries=crawler_config.get('max_retries', 3),
            retry_delay=crawler_config.get('retry_delay', 2)
        )
        
        self.rss_parser = RSSParser(
            timeout=crawler_config.get('timeout', 30),
            max_retries=crawler_config.get('max_retries', 3),
            retry_delay=crawler_config.get('retry_delay', 2)
        )
        
        self.pdf_parser = PDFParser(
            timeout=crawler_config.get('timeout', 60),
            max_retries=crawler_config.get('max_retries', 3),
            retry_delay=crawler_config.get('retry_delay', 2)
        )
        
        # MCP 爬虫
        self.firecrawl_mcp = FirecrawlMCP(
            timeout=crawler_config.get('timeout', 60),
            max_retries=crawler_config.get('max_retries', 3),
            retry_delay=crawler_config.get('retry_delay', 2)
        )
        
        self.github_mcp = GitHubMCP(
            timeout=crawler_config.get('timeout', 30),
            max_retries=crawler_config.get('max_retries', 3),
            retry_delay=crawler_config.get('retry_delay', 2)
        )
        
        # Playwright 爬虫（延迟初始化）
        self.playwright_crawler = None
        
        logger.info("爬虫管理器初始化完成")
    
    def crawl(self, source: Dict) -> Optional[Dict]:
        """
        根据数据源类型自动选择爬虫
        
        智能路由策略：
        1. 优先使用 Firecrawl MCP（如果配置了 API Key）
        2. 根据类型选择专用爬虫
        3. 失败时自动降级
        
        Args:
            source: 数据源配置
            
        Returns:
            采集结果
        """
        source_type = source.get('type', 'static_web')
        url = source.get('url')
        name = source.get('name')
        use_firecrawl_fallback = source.get('use_firecrawl_fallback', True)
        
        logger.info(f"选择爬虫类型: {source_type} for {name}")
        
        try:
            # 特殊类型：直接使用对应爬虫
            if source_type == 'rss':
                return self.rss_parser.crawl_with_retry(url, name)
                
            elif source_type == 'pdf':
                return self.pdf_parser.crawl_with_retry(url, name)
                
            elif source_type == 'github':
                return self.github_mcp.crawl_with_retry(
                    url, name,
                    monitor_types=source.get('monitor_types', ['commits', 'issues', 'pulls', 'releases']),
                    since_days=source.get('since_days', 7)
                )
                
            elif source_type == 'firecrawl':
                return self.firecrawl_mcp.crawl_with_retry(
                    url, name,
                    formats=source.get('formats', ['markdown', 'html']),
                    only_main_content=source.get('only_main_content', True)
                )
            
            # Web 类型：智能选择策略
            # 策略 1: 如果配置了 Firecrawl API Key，优先使用（质量最高）
            if self.firecrawl_mcp.api_key and use_firecrawl_fallback:
                logger.info(f"优先使用 Firecrawl MCP: {name}")
                result = self.firecrawl_mcp.crawl_with_retry(
                    url, name,
                    formats=['markdown', 'html'],
                    only_main_content=True
                )
                if result:
                    return result
                # 如果 API Key 被禁用（401 错误），记录一次警告
                if not self.firecrawl_mcp.api_key:
                    logger.warning(f"Firecrawl API Key 无效，已自动禁用，后续将使用其他爬虫")
                else:
                    logger.warning(f"Firecrawl MCP 失败，尝试其他爬虫: {name}")
            
            # 策略 2: 动态网站使用 Playwright
            if source_type == 'dynamic_web':
                return self._crawl_with_playwright(source)
            
            # 策略 3: 静态网站先用简单爬虫
            result = self.simple_crawler.crawl(url, name)
            
            # 策略 4: 如果简单爬虫失败或被拦截，降级到 Playwright
            if not result or 'incapsula' in result.get('content', '').lower() or 'access denied' in result.get('content', '').lower():
                logger.warning(f"简单爬虫失败或被拦截，降级到 Playwright: {name}")
                return self._crawl_with_playwright(source)
            
            return result
                
        except Exception as e:
            logger.error(f"采集失败: {name}, 错误: {e}")
            return None
    
    def _crawl_with_playwright(self, source: Dict) -> Optional[Dict]:
        """
        使用 Playwright 采集
        
        Args:
            source: 数据源配置
            
        Returns:
            采集结果
        """
        # 延迟初始化 Playwright（避免不必要的浏览器启动）
        if not self.playwright_crawler:
            logger.info("初始化 Playwright 爬虫...")
            self.playwright_crawler = PlaywrightCrawler(
                timeout=30,
                max_retries=2,
                retry_delay=3,
                headless=True,
                stealth=True
            )
            self.playwright_crawler.start()
        
        url = source.get('url')
        name = source.get('name')
        
        # 获取额外配置
        wait_for = source.get('wait_for')
        wait_time = source.get('wait_time', 3)
        scroll = source.get('scroll', False)
        
        return self.playwright_crawler.crawl_with_retry(
            url, name,
            wait_for=wait_for,
            wait_time=wait_time,
            scroll=scroll
        )
    
    def crawl_all(self, sources: List[Dict]) -> List[Dict]:
        """
        批量采集
        
        Args:
            sources: 数据源列表
            
        Returns:
            采集结果列表
        """
        results = []
        
        for source in sources:
            # 跳过禁用的数据源
            if not source.get('enabled', True):
                logger.info(f"跳过禁用的数据源: {source['name']}")
                continue
            
            result = self.crawl(source)
            
            if result:
                # 添加额外信息
                result['category'] = source.get('category', '未分类')
                results.append(result)
            else:
                logger.warning(f"数据源采集失败: {source['name']}")
        
        logger.info(f"批量采集完成: 成功 {len(results)}/{len(sources)}")
        return results
    
    def close(self):
        """关闭所有爬虫"""
        if self.playwright_crawler:
            logger.info("关闭 Playwright 爬虫...")
            self.playwright_crawler.close()
            self.playwright_crawler = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


# 测试代码
if __name__ == "__main__":
    import yaml
    from pathlib import Path
    
    # 加载配置
    config_path = Path("config/sources.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            sources = config.get('sources', [])
    else:
        sources = [
            {
                'name': '测试网站',
                'url': 'https://www.example.com',
                'type': 'static_web',
                'enabled': True,
                'category': '测试'
            }
        ]
    
    # 测试爬虫管理器
    with CrawlerManager() as manager:
        results = manager.crawl_all(sources[:1])
        
        for result in results:
            print(f"\n数据源: {result['source']}")
            print(f"内容长度: {len(result['content'])}")
            print(f"内容预览: {result['content'][:200]}...")
