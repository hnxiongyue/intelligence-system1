"""
Firecrawl MCP 爬虫
使用 Firecrawl API 进行高质量网页采集
"""

from typing import Dict, Optional
from loguru import logger
import requests
import os
import time

from src.crawlers.base import BaseCrawler


class FirecrawlMCP(BaseCrawler):
    """Firecrawl MCP 爬虫"""
    
    def __init__(self, 
                 api_key: str = None,
                 timeout: int = 60, 
                 max_retries: int = 3, 
                 retry_delay: int = 2):
        """
        初始化 Firecrawl MCP 爬虫
        
        Args:
            api_key: Firecrawl API Key（默认从环境变量读取）
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        super().__init__(timeout, max_retries, retry_delay)
        
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            logger.warning("未配置 FIRECRAWL_API_KEY，Firecrawl MCP 将不可用")
        
        # 使用 v1 API（v0 已废弃）
        self.base_url = "https://api.firecrawl.dev/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def crawl(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        使用 Firecrawl 采集网页
        
        Args:
            url: 目标 URL
            source_name: 数据源名称
            **kwargs: 额外参数
                - formats: 返回格式列表 ['markdown', 'html', 'rawHtml']
                - only_main_content: 是否只返回主要内容（默认 True）
                - include_tags: 包含的 HTML 标签
                - exclude_tags: 排除的 HTML 标签
                
        Returns:
            采集结果字典
        """
        if not self.api_key:
            logger.error("Firecrawl API Key 未配置")
            return None
        
        try:
            # 构建请求参数
            payload = {
                'url': url,
                'formats': kwargs.get('formats', ['markdown', 'html']),
                'onlyMainContent': kwargs.get('only_main_content', True),
            }
            
            # 可选参数
            if kwargs.get('include_tags'):
                payload['includeTags'] = kwargs.get('include_tags')
            
            if kwargs.get('exclude_tags'):
                payload['excludeTags'] = kwargs.get('exclude_tags')
            
            logger.info(f"[Firecrawl MCP] 开始采集: {url}")
            
            # 调用 Firecrawl v1 API
            response = self.session.post(
                f"{self.base_url}/scrape",
                json=payload,
                timeout=self.timeout
            )
            
            # 检查 HTTP 状态码
            if response.status_code == 401:
                logger.error("Firecrawl API Key 无效或已过期，请访问 https://firecrawl.dev/app/api-keys 获取新 Key")
                # 清空 API Key，避免后续重复尝试
                self.api_key = None
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # v1 API 响应格式检查
            if not data.get('success'):
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"Firecrawl 采集失败: {error_msg}")
                return None
            
            # 提取内容（v1 API 格式）
            result_data = data.get('data', {})
            markdown_content = result_data.get('markdown', '')
            html_content = result_data.get('html', '')
            metadata = result_data.get('metadata', {})
            
            # 优先使用 Markdown，如果没有则使用 HTML
            content = markdown_content if markdown_content else self._html_to_text(html_content)
            
            result = {
                'source': source_name,
                'source_url': url,
                'content': content[:10000],
                'raw_html': html_content[:50000],
                'status_code': 200,
                'metadata': {
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'language': metadata.get('language', ''),
                    'source_url': metadata.get('sourceURL', url),
                }
            }
            
            logger.info(f"[Firecrawl MCP] 采集成功: {source_name}, 内容长度: {len(content)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Firecrawl MCP] 请求失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"[Firecrawl MCP] 采集异常: {e}", exc_info=True)
            return None
    
    def crawl_batch(self, urls: list, source_name: str, **kwargs) -> list:
        """
        批量采集（使用 Firecrawl 的批量 API）
        
        Args:
            urls: URL 列表
            source_name: 数据源名称
            **kwargs: 额外参数
            
        Returns:
            采集结果列表
        """
        if not self.api_key:
            logger.error("Firecrawl API Key 未配置")
            return []
        
        try:
            # 构建批量请求
            payload = {
                'urls': urls,
                'formats': kwargs.get('formats', ['markdown']),
                'onlyMainContent': kwargs.get('only_main_content', True),
            }
            
            logger.info(f"[Firecrawl MCP] 批量采集: {len(urls)} 个 URL")
            
            # 调用批量 API（v1）
            response = self.session.post(
                f"{self.base_url}/batch/scrape",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                logger.error(f"Firecrawl 批量采集失败: {data.get('error')}")
                return []
            
            # 获取批量任务 ID
            batch_id = data.get('id')
            logger.info(f"批量任务 ID: {batch_id}")
            
            # 轮询任务状态
            results = self._poll_batch_status(batch_id, source_name)
            
            logger.info(f"[Firecrawl MCP] 批量采集完成: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"[Firecrawl MCP] 批量采集异常: {e}", exc_info=True)
            return []
    
    def _poll_batch_status(self, batch_id: str, source_name: str, max_wait: int = 300) -> list:
        """
        轮询批量任务状态
        
        Args:
            batch_id: 批量任务 ID
            source_name: 数据源名称
            max_wait: 最大等待时间（秒）
            
        Returns:
            采集结果列表
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/batch/scrape/{batch_id}",
                    timeout=30
                )
                
                response.raise_for_status()
                data = response.json()
                
                status = data.get('status')
                logger.info(f"批量任务状态: {status}")
                
                if status == 'completed':
                    # 任务完成，提取结果
                    results = []
                    for item in data.get('data', []):
                        if item.get('markdown'):
                            results.append({
                                'source': source_name,
                                'source_url': item.get('metadata', {}).get('sourceURL', ''),
                                'content': item.get('markdown', '')[:10000],
                                'raw_html': item.get('html', '')[:50000],
                                'status_code': 200,
                                'metadata': item.get('metadata', {})
                            })
                    return results
                
                elif status == 'failed':
                    logger.error("批量任务失败")
                    return []
                
                # 等待后继续轮询
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"轮询批量任务状态失败: {e}")
                return []
        
        logger.warning("批量任务超时")
        return []
    
    def _html_to_text(self, html: str) -> str:
        """
        将 HTML 转换为纯文本
        
        Args:
            html: HTML 字符串
            
        Returns:
            纯文本
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 移除 script 和 style 标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # 清理空白
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except:
            return html


# 测试代码
if __name__ == "__main__":
    # 测试 Firecrawl MCP
    crawler = FirecrawlMCP()
    
    if crawler.api_key:
        result = crawler.crawl_with_retry(
            url="https://www.digicert.com/blog",
            source_name="DigiCert Blog"
        )
        
        if result:
            print(f"\nFirecrawl MCP 采集成功:")
            print(f"  来源: {result['source']}")
            print(f"  URL: {result['source_url']}")
            print(f"  标题: {result['metadata']['title']}")
            print(f"  内容长度: {len(result['content'])}")
            print(f"  内容预览: {result['content'][:200]}...")
        else:
            print("Firecrawl MCP 采集失败")
    else:
        print("请配置 FIRECRAWL_API_KEY 环境变量")
