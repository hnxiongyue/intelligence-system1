"""
推送通知模块
负责将情报推送到钉钉等平台
"""

import requests
import json
import os
from typing import Dict, List
from loguru import logger


class Notifier:
    """推送通知类"""
    
    def __init__(self, webhook_url: str = None, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化推送器
        
        Args:
            webhook_url: 钉钉 Webhook URL（默认从环境变量读取）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.webhook_url = webhook_url or os.getenv('DINGTALK_WEBHOOK')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not self.webhook_url:
            logger.warning("未配置 DINGTALK_WEBHOOK，推送功能将不可用")
    
    def send_to_dingtalk(self, data: Dict) -> bool:
        """
        发送到钉钉
        
        Args:
            data: 情报数据
            
        Returns:
            是否成功
        """
        if not self.webhook_url:
            logger.warning("未配置 Webhook URL，跳过推送")
            return False
        
        try:
            # 格式化消息
            message = self.format_message(data)
            
            # 构建钉钉消息
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "行业情报速递",
                    "text": message
                }
            }
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"推送成功: {data.get('title', '')[:50]}")
                return True
            else:
                logger.error(f"推送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"推送异常: {e}")
            return False
    
    def save_to_markdown(self, data: Dict, output_dir: str = "reports") -> bool:
        """
        保存为 Markdown 文件（用于预览）
        
        Args:
            data: 情报数据
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        try:
            from pathlib import Path
            from datetime import datetime
            
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 格式化消息
            message = self.format_message(data)
            
            # 生成文件名（使用时间戳和标题）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            title_safe = data.get('title', 'untitled')[:30].replace('/', '_').replace('\\', '_')
            filename = f"{timestamp}_{title_safe}.md"
            
            file_path = output_path / filename
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(message)
            
            logger.info(f"保存 Markdown 成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存 Markdown 失败: {e}")
            return False
    
    def format_message(self, data: Dict) -> str:
        """
        格式化消息（Markdown 格式）
        
        Args:
            data: 情报数据
            
        Returns:
            格式化后的消息
        """
        # 优先级图标
        priority_icons = {
            '高': '🔴',
            '中': '🟡',
            '低': '🟢'
        }
        
        priority = data.get('priority', '中')
        icon = priority_icons.get(priority, '⚪')
        
        # 解析建议（JSON 字符串）
        suggestions_str = data.get('suggestions', '[]')
        try:
            suggestions = json.loads(suggestions_str)
        except:
            suggestions = []
        
        # 构建消息
        message = f"""## {icon} 【{data.get('category', '未分类')}】{data.get('title', '无标题')}

**来源**：{data.get('source', '未知')}  
**优先级**：{priority}  
**发布日期**：{data.get('publish_date', '未知')}

---

### 📝 内容摘要
{data.get('summary', '暂无摘要')}

### 📊 影响分析
{data.get('impact', '暂无分析')}

### 💡 应对建议
"""
        
        # 添加建议列表
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                message += f"{i}. {suggestion}\n"
        else:
            message += "暂无建议\n"
        
        # 添加原文链接
        if data.get('source_url'):
            message += f"\n[查看原文]({data.get('source_url')})"
        
        return message
    
    def send_batch(self, data_list: List[Dict], save_markdown: bool = True) -> Dict:
        """
        批量推送
        
        Args:
            data_list: 情报数据列表
            save_markdown: 是否保存为 Markdown 文件
            
        Returns:
            推送统计信息
        """
        success_count = 0
        failed_count = 0
        
        for data in data_list:
            # 保存为 Markdown
            if save_markdown:
                self.save_to_markdown(data)
            
            # 如果配置了 Webhook，也发送到钉钉
            if self.webhook_url:
                if self.send_to_dingtalk(data):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                # 没有配置 Webhook，只保存文件也算成功
                success_count += 1
        
        stats = {
            'total': len(data_list),
            'success': success_count,
            'failed': failed_count
        }
        
        logger.info(f"批量推送完成: 成功 {success_count}, 失败 {failed_count}")
        return stats
    
    def send_summary(self, stats: Dict):
        """
        发送汇总消息
        
        Args:
            stats: 统计信息
        """
        if not self.webhook_url:
            return
        
        message = f"""## 📊 今日情报汇总

**总计**：{stats.get('total', 0)} 条  
**政策类**：{stats.get('by_category', {}).get('政策', 0)} 条  
**竞品类**：{stats.get('by_category', {}).get('竞品', 0)} 条  
**技术类**：{stats.get('by_category', {}).get('技术', 0)} 条

**高优先级**：{stats.get('by_priority', {}).get('高', 0)} 条  
**中优先级**：{stats.get('by_priority', {}).get('中', 0)} 条  
**低优先级**：{stats.get('by_priority', {}).get('低', 0)} 条

---

系统运行正常 ✅
"""
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": "今日情报汇总",
                "text": message
            }
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            logger.info("汇总消息发送成功")
        except Exception as e:
            logger.error(f"汇总消息发送失败: {e}")
    
    def generate_daily_report(self, data_list: List[Dict], output_dir: str = "reports") -> str:
        """
        生成每日汇总报告
        
        Args:
            data_list: 情报数据列表
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        try:
            from pathlib import Path
            from datetime import datetime
            
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"daily_report_{date_str}.md"
            file_path = output_path / filename
            
            # 统计信息
            total = len(data_list)
            by_category = {}
            by_priority = {}
            
            for data in data_list:
                category = data.get('category', '未分类')
                priority = data.get('priority', '中')
                
                by_category[category] = by_category.get(category, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # 生成报告内容
            report = f"""# 行业情报日报 - {date_str}

## 📊 统计概览

- **总计**：{total} 条
- **政策类**：{by_category.get('政策', 0)} 条
- **竞品类**：{by_category.get('竞品', 0)} 条
- **技术类**：{by_category.get('技术', 0)} 条
- **未分类**：{by_category.get('未分类', 0)} 条

---

- **高优先级**：{by_priority.get('高', 0)} 条
- **中优先级**：{by_priority.get('中', 0)} 条
- **低优先级**：{by_priority.get('低', 0)} 条

---

## 📋 详细情报

"""
            
            # 按优先级和分类排序
            sorted_data = sorted(
                data_list,
                key=lambda x: (
                    {'高': 0, '中': 1, '低': 2}.get(x.get('priority', '中'), 1),
                    x.get('category', '未分类')
                )
            )
            
            # 添加每条情报
            for i, data in enumerate(sorted_data, 1):
                priority_icons = {'高': '🔴', '中': '🟡', '低': '🟢'}
                icon = priority_icons.get(data.get('priority', '中'), '⚪')
                
                report += f"""
### {i}. {icon} {data.get('title', '无标题')}

**来源**：{data.get('source', '未知')}  
**分类**：{data.get('category', '未分类')}  
**优先级**：{data.get('priority', '中')}  
**发布日期**：{data.get('publish_date', '未知')}

#### 📝 内容摘要
{data.get('summary', '暂无摘要')}

#### 📊 影响分析
{data.get('impact', '暂无分析')}

#### 💡 应对建议
"""
                
                # 解析建议
                suggestions_str = data.get('suggestions', '[]')
                try:
                    suggestions = json.loads(suggestions_str)
                    for j, suggestion in enumerate(suggestions, 1):
                        report += f"{j}. {suggestion}\n"
                except:
                    report += "暂无建议\n"
                
                # 添加原文链接
                if data.get('source_url'):
                    report += f"\n**原文链接**：{data.get('source_url')}\n"
                
                report += "\n---\n"
            
            # 添加页脚
            report += f"""
## 📌 说明

- 本报告由 AI 自动生成
- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 数据来源：{', '.join(set(d.get('source', '未知') for d in data_list))}

---

**系统运行正常** ✅
"""
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"生成日报成功: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"生成日报失败: {e}")
            return ""


# 测试代码
if __name__ == "__main__":
    # 测试推送
    notifier = Notifier()
    
    test_data = {
        'title': '国家密码管理局发布新标准',
        'source': '国家密码管理局',
        'source_url': 'https://www.nca.gov.cn',
        'category': '政策',
        'priority': '高',
        'publish_date': '2026-04-15',
        'summary': '国家密码管理局发布了新的商用密码标准，将于2026年7月1日实施。',
        'impact': '所有电子认证服务提供商需要在规定时间内完成升级。',
        'suggestions': json.dumps(['立即启动技术预研', '2周内完成方案设计'], ensure_ascii=False)
    }
    
    # 格式化消息
    message = notifier.format_message(test_data)
    print("格式化消息:")
    print(message)
    
    # 发送测试（需要配置 Webhook URL）
    # notifier.send_to_dingtalk(test_data)
