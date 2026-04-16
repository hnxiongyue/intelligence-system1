"""
PDF 解析器
支持下载和解析 PDF 文档
"""

from typing import Dict, Optional
from loguru import logger
import requests
import pdfplumber
from pathlib import Path
import tempfile
import os

from src.crawlers.base import BaseCrawler


class PDFParser(BaseCrawler):
    """PDF 解析器"""
    
    def __init__(self, timeout: int = 60, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化 PDF 解析器
        
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
        下载并解析 PDF
        
        Args:
            url: PDF URL
            source_name: 数据源名称
            **kwargs: 额外参数
                - max_pages: 最大页数（默认 50）
                - extract_tables: 是否提取表格（默认 False）
                
        Returns:
            采集结果字典
        """
        temp_file = None
        
        try:
            # 下载 PDF
            logger.info(f"下载 PDF: {url}")
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # 检查是否是 PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"不是 PDF 文件: {content_type}")
                return None
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                temp_file = f.name
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"PDF 下载完成: {temp_file}")
            
            # 解析 PDF
            text = self._extract_text(temp_file, **kwargs)
            
            if not text:
                logger.warning("PDF 解析失败或内容为空")
                return None
            
            result = {
                'source': source_name,
                'source_url': url,
                'content': text[:10000],  # 限制长度
                'raw_html': '',  # PDF 没有 HTML
                'status_code': response.status_code,
                'pdf_info': {
                    'size': os.path.getsize(temp_file),
                    'content_type': content_type
                }
            }
            
            logger.info(f"PDF 解析成功: {source_name}, 内容长度: {len(text)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"PDF 下载失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"PDF 解析异常: {e}", exc_info=True)
            return None
            
        finally:
            # 删除临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.info(f"临时文件已删除: {temp_file}")
                except:
                    pass
    
    def _extract_text(self, pdf_path: str, **kwargs) -> str:
        """
        从 PDF 提取文本
        
        Args:
            pdf_path: PDF 文件路径
            **kwargs: 额外参数
            
        Returns:
            提取的文本
        """
        max_pages = kwargs.get('max_pages', 50)
        extract_tables = kwargs.get('extract_tables', False)
        
        text_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF 总页数: {total_pages}")
                
                # 限制页数
                pages_to_extract = min(total_pages, max_pages)
                logger.info(f"提取前 {pages_to_extract} 页")
                
                for i, page in enumerate(pdf.pages[:pages_to_extract], 1):
                    # 提取文本
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n--- Page {i} ---\n")
                        text_parts.append(page_text)
                    
                    # 提取表格（如果需要）
                    if extract_tables:
                        tables = page.extract_tables()
                        if tables:
                            text_parts.append(f"\n[Tables on page {i}]\n")
                            for table in tables:
                                text_parts.append(self._format_table(table))
                
                text = ''.join(text_parts)
                return text
                
        except Exception as e:
            logger.error(f"PDF 文本提取失败: {e}")
            return ""
    
    def _format_table(self, table: list) -> str:
        """
        格式化表格
        
        Args:
            table: 表格数据（二维列表）
            
        Returns:
            格式化的表格字符串
        """
        if not table:
            return ""
        
        lines = []
        for row in table:
            # 过滤 None 值
            row_data = [str(cell) if cell else '' for cell in row]
            lines.append(' | '.join(row_data))
        
        return '\n'.join(lines) + '\n'


# 测试代码
if __name__ == "__main__":
    # 测试 PDF 解析器
    parser = PDFParser(timeout=60)
    
    # 测试 NIST 文档
    result = parser.crawl_with_retry(
        url="https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf",
        source_name="NIST SP 800-57",
        max_pages=10
    )
    
    if result:
        print(f"\nPDF 解析成功:")
        print(f"  来源: {result['source']}")
        print(f"  URL: {result['source_url']}")
        print(f"  文件大小: {result['pdf_info']['size']} bytes")
        print(f"  内容长度: {len(result['content'])}")
        print(f"  内容预览: {result['content'][:500]}...")
    else:
        print("PDF 解析失败")
