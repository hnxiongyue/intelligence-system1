"""
数据库模块
负责 SQLite 数据库的初始化和 CRUD 操作
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger


class Database:
    """数据库操作类"""
    
    def __init__(self, db_path: str = "data/intelligence.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        return conn
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建情报表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                category TEXT,
                priority TEXT,
                content TEXT,
                summary TEXT,
                impact TEXT,
                suggestions TEXT,
                publish_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_notified INTEGER DEFAULT 0
            )
        """)
        
        # 检查并添加 impact 列（如果不存在）
        try:
            cursor.execute("SELECT impact FROM intelligence LIMIT 1")
        except:
            logger.info("添加 impact 列到数据库表")
            cursor.execute("ALTER TABLE intelligence ADD COLUMN impact TEXT")
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON intelligence(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON intelligence(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON intelligence(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON intelligence(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_notified ON intelligence(is_notified)")
        
        # 创建采集日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                items_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("数据库表初始化完成")
    
    def save_intelligence(self, data: Dict) -> int:
        """
        保存情报数据
        
        Returns:
            数据库 ID（整数），失败返回 None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO intelligence (
                    title, source, source_url, category, priority,
                    content, summary, suggestions, publish_date, impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('title'),
                data.get('source'),
                data.get('source_url'),
                data.get('category'),
                data.get('priority'),
                data.get('content'),
                data.get('summary'),
                data.get('suggestions'),
                data.get('publish_date'),
                data.get('impact')
            ))
            
            # 获取插入的 ID
            intelligence_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            logger.info(f"保存情报成功: ID={intelligence_id}, {data.get('title')}")
            return intelligence_id
            
        except Exception as e:
            logger.error(f"保存情报失败: {e}")
            return None
    
    def get_unnotified(self, limit: int = 100) -> List[Dict]:
        """获取未推送的情报"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM intelligence
                WHERE is_notified = 0
                ORDER BY priority DESC, created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            result = [dict(row) for row in rows]
            logger.info(f"获取未推送情报: {len(result)} 条")
            return result
            
        except Exception as e:
            logger.error(f"获取未推送情报失败: {e}")
            return []
    
    def mark_notified(self, intelligence_id: str) -> bool:
        """标记为已推送"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE intelligence
                SET is_notified = 1
                WHERE id = ?
            """, (intelligence_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"标记已推送: {intelligence_id}")
            return True
            
        except Exception as e:
            logger.error(f"标记已推送失败: {e}")
            return False
    
    def check_duplicate(self, title: str) -> bool:
        """检查是否重复（基于标题）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM intelligence
                WHERE title = ?
            """, (title,))
            
            row = cursor.fetchone()
            conn.close()
            
            return row['count'] > 0
            
        except Exception as e:
            logger.error(f"检查重复失败: {e}")
            return False
    
    def log_crawl(self, source: str, status: str, count: int = 0, error: str = None) -> bool:
        """记录采集日志"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO crawl_log (source, status, items_count, error_message)
                VALUES (?, ?, ?, ?)
            """, (source, status, count, error))
            
            conn.commit()
            conn.close()
            logger.info(f"记录采集日志: {source} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"记录采集日志失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 总情报数
            cursor.execute("SELECT COUNT(*) as total FROM intelligence")
            total = cursor.fetchone()['total']
            
            # 今日新增
            cursor.execute("""
                SELECT COUNT(*) as today FROM intelligence
                WHERE DATE(created_at) = DATE('now')
            """)
            today = cursor.fetchone()['today']
            
            # 按分类统计
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM intelligence
                GROUP BY category
            """)
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # 按优先级统计
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM intelligence
                GROUP BY priority
            """)
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'total': total,
                'today': today,
                'by_category': by_category,
                'by_priority': by_priority
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 命令行工具
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        # 初始化数据库
        db = Database()
        print("数据库初始化完成！")
        
        # 显示统计信息
        stats = db.get_statistics()
        print(f"\n统计信息:")
        print(f"  总情报数: {stats.get('total', 0)}")
        print(f"  今日新增: {stats.get('today', 0)}")
    else:
        print("用法: python database.py init")
