"""
爬虫基类
定义统一的爬虫接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from loguru import logger
import time


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化爬虫
        
        Args:
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    @abstractmethod
    def crawl(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        采集单个 URL
        
        Args:
            url: 目标 URL
            source_name: 数据源名称
            **kwargs: 额外参数
            
        Returns:
            采集结果字典，失败返回 None
        """
        pass
    
    def crawl_with_retry(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        带重试的采集
        
        Args:
            url: 目标 URL
            source_name: 数据源名称
            **kwargs: 额外参数
            
        Returns:
            采集结果字典，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[{self.__class__.__name__}] 开始采集: {source_name} ({url}), 尝试 {attempt + 1}/{self.max_retries}")
                
                result = self.crawl(url, source_name, **kwargs)
                
                if result:
                    logger.info(f"[{self.__class__.__name__}] 采集成功: {source_name}")
                    return result
                else:
                    logger.warning(f"[{self.__class__.__name__}] 采集返回空结果: {source_name}")
                    
            except Exception as e:
                logger.error(f"[{self.__class__.__name__}] 采集异常: {source_name}, 错误: {e}")
                
            # 重试延迟
            if attempt < self.max_retries - 1:
                logger.info(f"等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)
        
        logger.error(f"[{self.__class__.__name__}] 采集最终失败: {source_name}")
        return None
    
    def validate(self, data: Dict) -> bool:
        """
        验证采集结果
        
        Args:
            data: 采集结果
            
        Returns:
            是否有效
        """
        if not data:
            return False
        
        # 检查必要字段
        required_fields = ['source', 'source_url', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"缺少必要字段: {field}")
                return False
        
        # 检查内容长度
        if len(data.get('content', '')) < 100:
            logger.warning("内容过短，可能采集失败")
            return False
        
        return True
    
    def parse(self, raw_content: str) -> str:
        """
        解析原始内容
        
        Args:
            raw_content: 原始内容
            
        Returns:
            解析后的内容
        """
        # 子类可以重写此方法实现自定义解析
        return raw_content
