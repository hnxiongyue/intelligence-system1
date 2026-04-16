"""
采集模块
负责从各个数据源采集信息
MVP 版本：使用简单的 HTTP 请求 + BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from loguru import logger
import time


class Crawler:
    """网页采集类"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化采集器
        
        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl(self, url: str, source_name: str) -> Optional[Dict]:
        """
        采集单个 URL
        
        Args:
            url: 目标 URL
            source_name: 数据源名称
            
        Returns:
            采集结果字典，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"开始采集: {source_name} ({url}), 尝试 {attempt + 1}/{self.max_retries}")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                
                # 解析 HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取文本内容
                # 移除 script 和 style 标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 获取文本
                text = soup.get_text()
                
                # 清理空白
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                result = {
                    'source': source_name,
                    'source_url': url,
                    'content': text[:10000],  # 限制长度，避免太长
                    'raw_html': response.text[:50000],  # 保留原始 HTML（限制长度）
                    'status_code': response.status_code
                }
                
                logger.info(f"采集成功: {source_name}, 内容长度: {len(text)}")
                return result
                
            except requests.exceptions.Timeout:
                logger.warning(f"采集超时: {source_name}, 尝试 {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"采集失败: {source_name}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"采集异常: {source_name}, 错误: {e}")
                break
        
        logger.error(f"采集最终失败: {source_name}")
        return None
    
    def crawl_all(self, sources: List[Dict]) -> List[Dict]:
        """
        批量采集
        
        Args:
            sources: 数据源列表，每个元素包含 name, url, enabled 等字段
            
        Returns:
            采集结果列表
        """
        results = []
        
        for source in sources:
            # 跳过禁用的数据源
            if not source.get('enabled', True):
                logger.info(f"跳过禁用的数据源: {source['name']}")
                continue
            
            result = self.crawl(source['url'], source['name'])
            
            if result:
                # 添加额外信息
                result['category'] = source.get('category', '未分类')
                results.append(result)
                
                # 添加延迟，避免请求过快
                time.sleep(1)
            else:
                logger.warning(f"数据源采集失败: {source['name']}")
        
        logger.info(f"批量采集完成: 成功 {len(results)}/{len(sources)}")
        return results
    
    def extract_news_items(self, html: str, source_name: str) -> List[Dict]:
        """
        从 HTML 中提取新闻列表（可选功能）
        
        Args:
            html: HTML 内容
            source_name: 数据源名称
            
        Returns:
            新闻列表
        """
        # TODO: 根据不同网站的结构提取新闻列表
        # 这里只是示例，实际需要针对每个网站定制
        
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # 示例：查找所有包含标题和链接的元素
        # 实际使用时需要根据网站结构调整选择器
        for item in soup.select('.news-item, .article-item'):
            title_elem = item.select_one('.title, h3, h4')
            link_elem = item.select_one('a')
            
            if title_elem and link_elem:
                items.append({
                    'title': title_elem.get_text(strip=True),
                    'url': link_elem.get('href'),
                    'source': source_name
                })
        
        return items


# 测试代码
if __name__ == "__main__":
    # 测试采集
    crawler = Crawler()
    
    test_sources = [
        {
            'name': '测试网站',
            'url': 'https://www.example.com',
            'enabled': True,
            'category': '测试'
        }
    ]
    
    results = crawler.crawl_all(test_sources)
    
    for result in results:
        print(f"\n数据源: {result['source']}")
        print(f"内容长度: {len(result['content'])}")
        print(f"内容预览: {result['content'][:200]}...")
