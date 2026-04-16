"""
RSS 订阅解析器
支持解析 RSS/Atom Feed
"""

from typing import Dict, Optional, List
from loguru import logger
import feedparser
import requests
from datetime import datetime

from src.crawlers.base import BaseCrawler


class RSSParser(BaseCrawler):
    """RSS 订阅解析器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化 RSS 解析器
        
        Args:
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        super().__init__(timeout, max_retries, retry_delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        解析 RSS Feed
        
        Args:
            url: RSS Feed URL
            source_name: 数据源名称
            **kwargs: 额外参数
                - max_items: 最大条目数（默认 10）
                
        Returns:
            采集结果字典
        """
        try:
            # 获取 RSS 内容
            logger.info(f"获取 RSS Feed: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析 RSS
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"RSS Feed 没有条目: {url}")
                return None
            
            # 获取最大条目数
            max_items = kwargs.get('max_items', 10)
            entries = feed.entries[:max_items]
            
            logger.info(f"解析到 {len(entries)} 条 RSS 条目")
            
            # 格式化内容
            content_parts = []
            content_parts.append(f"# {feed.feed.get('title', source_name)}\n")
            
            if feed.feed.get('subtitle'):
                content_parts.append(f"{feed.feed.get('subtitle')}\n")
            
            content_parts.append("\n---\n\n")
            
            for i, entry in enumerate(entries, 1):
                content_parts.append(f"## {i}. {entry.get('title', '无标题')}\n")
                content_parts.append(f"**链接**: {entry.get('link', '')}\n")
                
                # 发布时间
                published = self._parse_date(entry)
                if published:
                    content_parts.append(f"**发布时间**: {published}\n")
                
                # 摘要
                summary = entry.get('summary', entry.get('description', ''))
                if summary:
                    # 清理 HTML 标签
                    summary = self._clean_html(summary)
                    content_parts.append(f"\n{summary}\n")
                
                content_parts.append("\n---\n\n")
            
            content = ''.join(content_parts)
            
            result = {
                'source': source_name,
                'source_url': url,
                'content': content[:10000],
                'raw_html': str(feed),
                'status_code': response.status_code,
                'feed_info': {
                    'title': feed.feed.get('title', ''),
                    'link': feed.feed.get('link', ''),
                    'updated': feed.feed.get('updated', ''),
                    'entries_count': len(entries)
                }
            }
            
            logger.info(f"RSS 解析成功: {source_name}, {len(entries)} 条")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RSS 获取失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"RSS 解析异常: {e}", exc_info=True)
            return None
    
    def _parse_date(self, entry: Dict) -> Optional[str]:
        """
        解析条目日期
        
        Args:
            entry: RSS 条目
            
        Returns:
            格式化的日期字符串
        """
        # 尝试多个日期字段
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if field in entry:
                try:
                    # feedparser 已经解析为 time.struct_time
                    date_tuple = entry.get(f'{field}_parsed')
                    if date_tuple:
                        dt = datetime(*date_tuple[:6])
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        return None
    
    def _clean_html(self, html: str) -> str:
        """
        清理 HTML 标签
        
        Args:
            html: HTML 字符串
            
        Returns:
            纯文本
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            # 清理多余空白
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return ' '.join(lines)
        except:
            return html
    
    def parse_multiple(self, urls: List[str], source_name: str, **kwargs) -> List[Dict]:
        """
        解析多个 RSS Feed
        
        Args:
            urls: RSS Feed URL 列表
            source_name: 数据源名称
            **kwargs: 额外参数
            
        Returns:
            采集结果列表
        """
        results = []
        
        for url in urls:
            result = self.crawl_with_retry(url, source_name, **kwargs)
            if result:
                results.append(result)
        
        return results


# 测试代码
if __name__ == "__main__":
    # 测试 RSS 解析器
    parser = RSSParser(timeout=30)
    
    # 测试 IETF RFC Feed
    result = parser.crawl_with_retry(
        url="https://www.rfc-editor.org/rfcrss.xml",
        source_name="IETF RFC",
        max_items=5
    )
    
    if result:
        print(f"\nRSS 解析成功:")
        print(f"  来源: {result['source']}")
        print(f"  URL: {result['source_url']}")
        print(f"  条目数: {result['feed_info']['entries_count']}")
        print(f"  内容预览: {result['content'][:500]}...")
    else:
        print("RSS 解析失败")
