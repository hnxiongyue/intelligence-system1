"""
数据处理模块
负责清洗、提取、去重等数据处理任务
"""

import re
import hashlib
from typing import List, Dict
from datetime import datetime
from loguru import logger


class Processor:
    """数据处理类"""
    
    def __init__(self):
        """初始化处理器"""
        self.seen_hashes = set()  # 用于去重
    
    def clean(self, raw_data: Dict) -> Dict:
        """
        清洗单条数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            清洗后的数据
        """
        try:
            content = raw_data.get('content', '')
            
            # 1. 去除多余空白
            content = self._clean_whitespace(content)
            
            # 2. 提取标题（简单实现：取第一行或前100字符）
            title = self._extract_title(content, raw_data.get('source', ''))
            
            # 3. 提取时间（尝试从内容中提取日期）
            publish_date = self._extract_date(content)
            
            cleaned_data = {
                'source': raw_data.get('source'),
                'source_url': raw_data.get('source_url'),
                'category': raw_data.get('category', '未分类'),
                'title': title,
                'content': content[:5000],  # 限制长度
                'publish_date': publish_date,
                'content_hash': self._calculate_hash(content)
            }
            
            logger.info(f"清洗数据成功: {title[:50]}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"清洗数据失败: {e}")
            return raw_data
    
    def clean_all(self, raw_data_list: List[Dict]) -> List[Dict]:
        """
        批量清洗数据
        
        Args:
            raw_data_list: 原始数据列表
            
        Returns:
            清洗后的数据列表
        """
        cleaned_list = []
        
        for raw_data in raw_data_list:
            cleaned = self.clean(raw_data)
            if cleaned:
                cleaned_list.append(cleaned)
        
        logger.info(f"批量清洗完成: {len(cleaned_list)}/{len(raw_data_list)}")
        return cleaned_list
    
    def deduplicate(self, data_list: List[Dict]) -> List[Dict]:
        """
        去重（基于内容哈希）
        
        Args:
            data_list: 数据列表
            
        Returns:
            去重后的数据列表
        """
        unique_list = []
        
        for data in data_list:
            content_hash = data.get('content_hash')
            
            if content_hash and content_hash not in self.seen_hashes:
                self.seen_hashes.add(content_hash)
                unique_list.append(data)
            else:
                logger.info(f"发现重复内容: {data.get('title', '')[:50]}")
        
        logger.info(f"去重完成: 保留 {len(unique_list)}/{len(data_list)}")
        return unique_list
    
    def _clean_whitespace(self, text: str) -> str:
        """清理多余空白"""
        # 替换多个空格为单个空格
        text = re.sub(r' +', ' ', text)
        
        # 替换多个换行为单个换行
        text = re.sub(r'\n+', '\n', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def _extract_title(self, content: str, source: str) -> str:
        """
        提取标题
        
        简单实现：取第一行或前100字符
        实际使用时可以根据网站结构优化
        """
        lines = content.split('\n')
        
        # 找到第一个非空行
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # 至少10个字符
                return line[:200]  # 限制标题长度
        
        # 如果没找到，返回前100字符
        return content[:100] + '...' if len(content) > 100 else content
    
    def _extract_date(self, content: str) -> str:
        """
        提取日期
        
        尝试从内容中提取日期，失败则返回当前日期
        """
        # 常见日期格式
        date_patterns = [
            r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})',  # 2026年4月15日 或 2026-04-15
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2026.04.15
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                year, month, day = match.groups()
                try:
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    # 验证日期有效性
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
                except ValueError:
                    continue
        
        # 如果没找到，返回当前日期
        return datetime.now().strftime('%Y-%m-%d')
    
    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希（用于去重）"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def extract_keywords(self, content: str, keywords_list: List[str]) -> List[str]:
        """
        提取关键词
        
        Args:
            content: 内容
            keywords_list: 关键词列表
            
        Returns:
            匹配到的关键词列表
        """
        found_keywords = []
        
        content_lower = content.lower()
        
        for keyword in keywords_list:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords


# 测试代码
if __name__ == "__main__":
    # 测试处理
    processor = Processor()
    
    test_data = {
        'source': '测试来源',
        'source_url': 'https://example.com',
        'category': '测试',
        'content': '''
            测试标题
            
            这是一段测试内容。
            发布时间：2026年4月15日
            
            这里有一些关键词：国密、SM4、量子密码
        '''
    }
    
    cleaned = processor.clean(test_data)
    
    print(f"标题: {cleaned['title']}")
    print(f"日期: {cleaned['publish_date']}")
    print(f"哈希: {cleaned['content_hash']}")
    
    # 测试去重
    data_list = [cleaned, cleaned]  # 重复数据
    unique_list = processor.deduplicate(data_list)
    print(f"\n去重结果: {len(unique_list)} 条（原始 {len(data_list)} 条）")
