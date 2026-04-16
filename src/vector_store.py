"""
向量数据库管理
使用 Qdrant 实现情报的语义搜索和去重
"""

import os
from typing import List, Dict, Optional, Tuple
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from openai import OpenAI


class VectorStore:
    """向量数据库管理器"""
    
    def __init__(self, 
                 collection_name: str = "intelligence",
                 qdrant_url: str = None,
                 qdrant_api_key: str = None,
                 embedding_model: str = "text-embedding-v4"):
        """
        初始化向量数据库
        
        Args:
            collection_name: 集合名称
            qdrant_url: Qdrant 服务地址（默认本地）
            qdrant_api_key: Qdrant API Key（云服务需要）
            embedding_model: 嵌入模型（默认使用阿里云百炼 text-embedding-v4）
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # 初始化 Qdrant 客户端
        if qdrant_url:
            # 云服务模式
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
            logger.info(f"连接到 Qdrant 云服务: {qdrant_url}")
        else:
            # 本地模式
            qdrant_path = os.getenv('QDRANT_PATH', './data/qdrant')
            self.client = QdrantClient(path=qdrant_path)
            logger.info(f"使用本地 Qdrant: {qdrant_path}")
        
        # 初始化 OpenAI 客户端（用于生成嵌入向量）
        # 使用阿里云百炼 API
        self.openai_client = OpenAI(
            api_key=os.getenv('LLM_API_KEY'),
            base_url=os.getenv('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        )
        
        # 确保集合存在
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保集合存在，不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"创建集合: {self.collection_name}")
                
                # 创建集合
                # text-embedding-v4: 1024 维
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1024,  # text-embedding-v4 向量维度
                        distance=Distance.COSINE  # 余弦相似度
                    )
                )
                logger.info("集合创建成功")
            else:
                logger.info(f"集合已存在: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"确保集合存在失败: {e}", exc_info=True)
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本的嵌入向量（使用阿里云百炼 text-embedding-v4）
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        try:
            # 截断过长的文本（避免超过模型限制）
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length]
                logger.debug(f"文本过长，截断至 {max_length} 字符")
            
            # 调用阿里云百炼 API
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"生成嵌入向量成功: 维度 {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}", exc_info=True)
            # 返回零向量作为降级方案
            logger.warning("使用零向量作为降级方案")
            return [0.0] * 1024
    
    def add_intelligence(self, 
                        intelligence_id: int,
                        title: str,
                        content: str,
                        category: str = None,
                        source: str = None) -> bool:
        """
        添加情报到向量数据库
        
        Args:
            intelligence_id: 情报 ID（来自 SQLite）
            title: 标题
            content: 内容
            category: 分类
            source: 来源
            
        Returns:
            是否成功
        """
        try:
            # 组合文本用于生成嵌入
            combined_text = f"{title}\n\n{content}"
            
            # 生成嵌入向量
            embedding = self.generate_embedding(combined_text)
            
            # 构建 payload（元数据）
            payload = {
                'intelligence_id': intelligence_id,
                'title': title,
                'category': category or 'unknown',
                'source': source or 'unknown'
            }
            
            # 添加到 Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=intelligence_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"添加情报到向量库: ID={intelligence_id}, 标题={title[:30]}")
            return True
            
        except Exception as e:
            logger.error(f"添加情报到向量库失败: {e}", exc_info=True)
            return False
    
    def search_similar(self, 
                      text: str,
                      limit: int = 5,
                      score_threshold: float = 0.7) -> List[Dict]:
        """
        搜索相似情报
        
        Args:
            text: 查询文本
            limit: 返回数量
            score_threshold: 相似度阈值（0-1）
            
        Returns:
            相似情报列表
        """
        try:
            # 生成查询向量
            query_vector = self.generate_embedding(text)
            
            # 搜索（使用 query 方法）
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # 格式化结果
            similar_items = []
            for result in results.points:
                similar_items.append({
                    'intelligence_id': result.payload['intelligence_id'],
                    'title': result.payload['title'],
                    'category': result.payload.get('category'),
                    'source': result.payload.get('source'),
                    'similarity': result.score
                })
            
            logger.info(f"找到 {len(similar_items)} 条相似情报")
            return similar_items
            
        except Exception as e:
            logger.error(f"搜索相似情报失败: {e}", exc_info=True)
            return []
    
    def check_duplicate(self, 
                       title: str,
                       content: str,
                       similarity_threshold: float = 0.85) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否为重复情报
        
        Args:
            title: 标题
            content: 内容
            similarity_threshold: 相似度阈值（默认 0.85）
            
        Returns:
            (是否重复, 最相似的情报)
        """
        try:
            # 组合文本
            combined_text = f"{title}\n\n{content}"
            
            # 搜索最相似的情报
            similar_items = self.search_similar(
                text=combined_text,
                limit=1,
                score_threshold=similarity_threshold
            )
            
            if similar_items:
                most_similar = similar_items[0]
                logger.info(
                    f"发现重复情报: {title[:30]} "
                    f"与 ID={most_similar['intelligence_id']} 相似度={most_similar['similarity']:.2f}"
                )
                return True, most_similar
            else:
                logger.debug(f"未发现重复: {title[:30]}")
                return False, None
                
        except Exception as e:
            logger.error(f"检查重复失败: {e}", exc_info=True)
            return False, None
    
    def get_context(self, 
                   category: str = None,
                   limit: int = 10) -> List[Dict]:
        """
        获取历史上下文（用于 AI 分析）
        
        Args:
            category: 分类过滤（可选）
            limit: 返回数量
            
        Returns:
            历史情报列表
        """
        try:
            # 构建过滤条件
            filter_condition = None
            if category:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category)
                        )
                    ]
                )
            
            # 滚动获取数据
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # 格式化结果
            context_items = []
            for record in records:
                context_items.append({
                    'intelligence_id': record.payload['intelligence_id'],
                    'title': record.payload['title'],
                    'category': record.payload.get('category'),
                    'source': record.payload.get('source')
                })
            
            logger.info(f"获取历史上下文: {len(context_items)} 条")
            return context_items
            
        except Exception as e:
            logger.error(f"获取历史上下文失败: {e}", exc_info=True)
            return []
    
    def delete_intelligence(self, intelligence_id: int) -> bool:
        """
        删除情报
        
        Args:
            intelligence_id: 情报 ID
            
        Returns:
            是否成功
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[intelligence_id]
            )
            logger.info(f"删除情报: ID={intelligence_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除情报失败: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict:
        """
        获取向量库统计信息
        
        Returns:
            统计信息
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                'total_vectors': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.name
            }
            
            logger.info(f"向量库统计: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return {}


# 测试代码
if __name__ == "__main__":
    import json
    
    print("="*60)
    print("测试向量数据库")
    print("="*60)
    
    # 初始化
    vector_store = VectorStore()
    
    # 测试数据
    test_data = [
        {
            'id': 1,
            'title': '国家密码管理局发布新标准',
            'content': '国家密码管理局发布了新的商用密码标准，将于2026年7月1日实施。',
            'category': '政策',
            'source': '国家密码管理局'
        },
        {
            'id': 2,
            'title': 'SM4 算法优化指南',
            'content': 'SM4 是国产对称加密算法，本文介绍了 SM4 算法的优化方法。',
            'category': '技术',
            'source': '技术博客'
        }
    ]
    
    # 1. 添加测试数据
    print("\n1. 添加测试数据...")
    for item in test_data:
        vector_store.add_intelligence(
            intelligence_id=item['id'],
            title=item['title'],
            content=item['content'],
            category=item['category'],
            source=item['source']
        )
    
    # 2. 测试相似度搜索
    print("\n2. 测试相似度搜索...")
    query = "密码管理相关政策"
    similar = vector_store.search_similar(query, limit=2)
    print(f"\n查询: {query}")
    print(f"结果: {json.dumps(similar, ensure_ascii=False, indent=2)}")
    
    # 3. 测试重复检测
    print("\n3. 测试重复检测...")
    is_dup, dup_info = vector_store.check_duplicate(
        title="国家密码管理局发布新规定",
        content="国家密码管理局最近发布了新的商用密码标准。"
    )
    print(f"是否重复: {is_dup}")
    if dup_info:
        print(f"重复信息: {json.dumps(dup_info, ensure_ascii=False, indent=2)}")
    
    # 4. 获取统计信息
    print("\n4. 获取统计信息...")
    stats = vector_store.get_statistics()
    print(f"统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
