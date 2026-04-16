"""
Playwright 动态网站爬虫
支持 JavaScript 渲染、反爬虫策略
"""

from typing import Dict, Optional
from loguru import logger
from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import random
import time

from src.crawlers.base import BaseCrawler


class PlaywrightCrawler(BaseCrawler):
    """Playwright 动态网站爬虫"""
    
    # User-Agent 列表（模拟不同浏览器）
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    def __init__(self, 
                 timeout: int = 30, 
                 max_retries: int = 3, 
                 retry_delay: int = 2,
                 headless: bool = True,
                 stealth: bool = True):
        """
        初始化 Playwright 爬虫
        
        Args:
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            headless: 是否无头模式
            stealth: 是否启用隐身模式
        """
        super().__init__(timeout, max_retries, retry_delay)
        self.headless = headless
        self.stealth = stealth
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
    
    def start(self):
        """启动浏览器"""
        if not self.playwright:
            logger.info("启动 Playwright 浏览器...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            logger.info("Playwright 浏览器启动成功")
    
    def close(self):
        """关闭浏览器"""
        if self.browser:
            logger.info("关闭 Playwright 浏览器...")
            self.browser.close()
            self.browser = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
            logger.info("Playwright 浏览器已关闭")
    
    def _create_page(self) -> Page:
        """
        创建新页面并配置
        
        Returns:
            配置好的页面对象
        """
        if not self.browser:
            self.start()
        
        # 创建新页面
        page = self.browser.new_page()
        
        # 设置随机 User-Agent
        user_agent = random.choice(self.USER_AGENTS)
        page.set_extra_http_headers({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 隐身模式：注入脚本隐藏 webdriver 特征
        if self.stealth:
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                
                window.chrome = {
                    runtime: {}
                };
            """)
        
        # 设置视口大小（模拟真实浏览器）
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        return page
    
    def crawl(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        采集单个 URL
        
        Args:
            url: 目标 URL
            source_name: 数据源名称
            **kwargs: 额外参数
                - wait_for: 等待的选择器
                - wait_time: 额外等待时间（秒）
                - scroll: 是否滚动页面
                
        Returns:
            采集结果字典
        """
        page = None
        
        try:
            # 创建页面
            page = self._create_page()
            
            # 随机延迟（模拟人类行为）
            time.sleep(random.uniform(1, 3))
            
            # 访问页面
            logger.info(f"访问页面: {url}")
            response = page.goto(url, timeout=self.timeout * 1000, wait_until='domcontentloaded')
            
            if not response or not response.ok:
                logger.error(f"页面响应失败: {response.status if response else 'None'}")
                return None
            
            # 等待特定元素（如果指定）
            wait_for = kwargs.get('wait_for')
            if wait_for:
                logger.info(f"等待元素: {wait_for}")
                page.wait_for_selector(wait_for, timeout=self.timeout * 1000)
            
            # 额外等待时间（让 JS 执行完成）
            wait_time = kwargs.get('wait_time', 2)
            logger.info(f"等待 {wait_time} 秒让页面加载完成...")
            time.sleep(wait_time)
            
            # 滚动页面（触发懒加载）
            if kwargs.get('scroll', False):
                logger.info("滚动页面...")
                self._scroll_page(page)
            
            # 获取页面内容
            content = page.content()
            text = page.inner_text('body')
            
            # 清理文本
            text = self._clean_text(text)
            
            result = {
                'source': source_name,
                'source_url': url,
                'content': text[:10000],  # 限制长度
                'raw_html': content[:50000],  # 保留原始 HTML
                'status_code': response.status
            }
            
            logger.info(f"采集成功: {source_name}, 内容长度: {len(text)}")
            return result
            
        except PlaywrightTimeout as e:
            logger.error(f"页面加载超时: {e}")
            return None
            
        except Exception as e:
            logger.error(f"采集异常: {e}", exc_info=True)
            return None
            
        finally:
            if page:
                page.close()
    
    def _scroll_page(self, page: Page, scroll_count: int = 3):
        """
        滚动页面（触发懒加载）
        
        Args:
            page: 页面对象
            scroll_count: 滚动次数
        """
        for i in range(scroll_count):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 去除多余空白
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)


# 测试代码
if __name__ == "__main__":
    # 测试 Playwright 爬虫
    with PlaywrightCrawler(timeout=30, headless=True, stealth=True) as crawler:
        # 测试采集
        result = crawler.crawl_with_retry(
            url="https://www.digicert.com/blog",
            source_name="DigiCert Blog",
            wait_time=3,
            scroll=True
        )
        
        if result:
            print(f"\n采集成功:")
            print(f"  来源: {result['source']}")
            print(f"  URL: {result['source_url']}")
            print(f"  状态码: {result['status_code']}")
            print(f"  内容长度: {len(result['content'])}")
            print(f"  内容预览: {result['content'][:200]}...")
        else:
            print("采集失败")
