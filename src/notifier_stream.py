"""
钉钉 Stream 模式推送器
支持双向交互和实时推送
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from loguru import logger
import dingtalk_stream


class DingTalkStreamNotifier:
    """钉钉 Stream 模式推送器"""
    
    def __init__(self, 
                 client_id: str = None, 
                 client_secret: str = None,
                 enable_bot: bool = False):
        """
        初始化 Stream 推送器
        
        Args:
            client_id: 钉钉应用的 Client ID（默认从环境变量读取）
            client_secret: 钉钉应用的 Client Secret（默认从环境变量读取）
            enable_bot: 是否启用机器人交互功能
        """
        self.client_id = client_id or os.getenv('DINGTALK_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('DINGTALK_CLIENT_SECRET')
        self.enable_bot = enable_bot
        
        if not self.client_id or not self.client_secret:
            logger.warning("未配置 DINGTALK_CLIENT_ID 或 DINGTALK_CLIENT_SECRET，Stream 模式将不可用")
            self.client = None
        else:
            # 创建 Stream 客户端
            credential = dingtalk_stream.Credential(self.client_id, self.client_secret)
            self.client = dingtalk_stream.DingTalkStreamClient(credential)
            
            # 如果启用机器人功能，注册处理器
            if self.enable_bot:
                self.register_bot_handler()
            
            logger.info("钉钉 Stream 模式初始化成功")
    
    def register_bot_handler(self):
        """注册机器人消息处理器"""
        if not self.client:
            return
        
        # 注册聊天机器人处理器
        handler = IntelligenceBotHandler()
        self.client.register_callback_handler(
            dingtalk_stream.chatbot.ChatbotMessage.TOPIC,
            handler
        )
        logger.info("机器人消息处理器已注册")
    
    async def send_message(self, 
                          webhook_url: str,
                          title: str,
                          text: str,
                          msg_type: str = "markdown") -> bool:
        """
        发送消息到钉钉群
        
        Args:
            webhook_url: Webhook URL（Stream 模式下也支持 Webhook）
            title: 消息标题
            text: 消息内容
            msg_type: 消息类型（text/markdown）
            
        Returns:
            是否成功
        """
        try:
            import requests
            
            if msg_type == "markdown":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,
                        "text": text
                    }
                }
            else:
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": text
                    }
                }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"消息发送成功: {title[:30]}")
                return True
            else:
                logger.error(f"消息发送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"消息发送异常: {e}")
            return False
    
    def send_intelligence(self, data: Dict, webhook_url: str = None) -> bool:
        """
        发送情报消息
        
        Args:
            data: 情报数据
            webhook_url: Webhook URL（可选，默认从环境变量读取）
            
        Returns:
            是否成功
        """
        webhook_url = webhook_url or os.getenv('DINGTALK_WEBHOOK')
        
        if not webhook_url:
            logger.warning("未配置 Webhook URL，跳过推送")
            return False
        
        # 格式化消息
        title = f"【{data.get('category', '情报')}】{data.get('title', '无标题')}"
        text = self.format_intelligence_message(data)
        
        # 使用 asyncio 发送
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.send_message(webhook_url, title, text, "markdown")
        )
    
    def format_intelligence_message(self, data: Dict) -> str:
        """
        格式化情报消息
        
        Args:
            data: 情报数据
            
        Returns:
            格式化后的 Markdown 消息
        """
        # 优先级图标
        priority_icons = {
            '高': '🔴',
            '中': '🟡',
            '低': '🟢'
        }
        
        priority = data.get('priority', '中')
        icon = priority_icons.get(priority, '⚪')
        
        # 解析建议
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
    
    def send_batch(self, data_list: List[Dict], webhook_url: str = None) -> Dict:
        """
        批量发送情报
        
        Args:
            data_list: 情报数据列表
            webhook_url: Webhook URL
            
        Returns:
            发送统计
        """
        success_count = 0
        failed_count = 0
        
        for data in data_list:
            if self.send_intelligence(data, webhook_url):
                success_count += 1
            else:
                failed_count += 1
        
        stats = {
            'total': len(data_list),
            'success': success_count,
            'failed': failed_count
        }
        
        logger.info(f"批量推送完成: 成功 {success_count}, 失败 {failed_count}")
        return stats
    
    def start_bot(self):
        """启动机器人（阻塞模式）"""
        if not self.client:
            logger.error("Stream 客户端未初始化")
            return
        
        if not self.enable_bot:
            logger.warning("机器人功能未启用")
            return
        
        logger.info("启动钉钉 Stream 机器人...")
        self.client.start_forever()
    
    async def start_bot_async(self):
        """启动机器人（异步模式）"""
        if not self.client:
            logger.error("Stream 客户端未初始化")
            return
        
        if not self.enable_bot:
            logger.warning("机器人功能未启用")
            return
        
        logger.info("启动钉钉 Stream 机器人（异步模式）...")
        
        while True:
            try:
                await self.client.start()
            except Exception as e:
                logger.error(f"Stream 连接异常: {e}")
                logger.info("5秒后重新连接...")
                await asyncio.sleep(5)


class IntelligenceBotHandler(dingtalk_stream.ChatbotHandler):
    """情报查询机器人处理器"""
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    async def process(self, callback: dingtalk_stream.CallbackMessage):
        """
        处理用户消息
        
        Args:
            callback: 回调消息
            
        Returns:
            处理状态
        """
        try:
            # 解析消息
            incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
            user_text = incoming_message.text.content.strip()
            
            self.logger.info(f"收到用户消息: {user_text}")
            
            # 处理不同的命令
            if user_text in ['帮助', 'help', '?']:
                response = self.get_help_message()
            elif user_text.startswith('查询'):
                response = await self.query_intelligence(user_text)
            elif user_text.startswith('统计'):
                response = await self.get_statistics()
            else:
                response = f"收到消息：{user_text}\n\n发送「帮助」查看可用命令"
            
            # 回复消息
            self.reply_text(response, incoming_message)
            
            return dingtalk_stream.AckMessage.STATUS_OK, 'OK'
            
        except Exception as e:
            self.logger.error(f"处理消息异常: {e}", exc_info=True)
            return dingtalk_stream.AckMessage.STATUS_SYSTEM_EXCEPTION, str(e)
    
    def get_help_message(self) -> str:
        """获取帮助信息"""
        return """## 📚 情报分析系统 - 帮助

**可用命令：**

1. **查询 [关键词]**
   - 示例：查询 国密
   - 功能：搜索包含关键词的情报

2. **统计**
   - 功能：查看今日情报统计

3. **帮助**
   - 功能：显示此帮助信息

---

💡 更多功能开发中...
"""
    
    async def query_intelligence(self, query: str) -> str:
        """
        查询情报
        
        Args:
            query: 查询文本
            
        Returns:
            查询结果
        """
        # 提取关键词
        keyword = query.replace('查询', '').strip()
        
        if not keyword:
            return "请提供查询关键词，例如：查询 国密"
        
        # TODO: 实现实际的数据库查询
        # 这里先返回模拟数据
        return f"""## 🔍 查询结果：{keyword}

**找到 3 条相关情报：**

1. 🔴 【政策】国家密码管理局发布新标准
   - 发布日期：2026-04-15
   - 优先级：高

2. 🟡 【技术】SM4 算法优化指南
   - 发布日期：2026-04-14
   - 优先级：中

3. 🟢 【合规】密码应用安全性评估要求
   - 发布日期：2026-04-13
   - 优先级：低

---

💡 发送「查看 1」查看详情
"""
    
    async def get_statistics(self) -> str:
        """获取统计信息"""
        # TODO: 实现实际的统计查询
        return """## 📊 今日情报统计

**总计**：15 条

**按分类：**
- 政策类：5 条
- 竞品类：6 条
- 技术类：3 条
- 合规类：1 条

**按优先级：**
- 高优先级：3 条 🔴
- 中优先级：8 条 🟡
- 低优先级：4 条 🟢

---

系统运行正常 ✅
"""


# 测试代码
if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='钉钉 Stream 模式推送器')
    parser.add_argument('--client_id', help='钉钉应用 Client ID')
    parser.add_argument('--client_secret', help='钉钉应用 Client Secret')
    parser.add_argument('--enable_bot', action='store_true', help='启用机器人功能')
    parser.add_argument('--test', action='store_true', help='测试推送')
    
    args = parser.parse_args()
    
    # 创建推送器
    notifier = DingTalkStreamNotifier(
        client_id=args.client_id,
        client_secret=args.client_secret,
        enable_bot=args.enable_bot
    )
    
    if args.test:
        # 测试推送
        test_data = {
            'title': '【测试】钉钉 Stream 模式推送',
            'source': '测试系统',
            'category': '测试',
            'priority': '高',
            'publish_date': '2026-04-16',
            'summary': '这是一条测试消息，验证 Stream 模式推送功能。',
            'impact': '无实际影响，仅用于测试。',
            'suggestions': json.dumps(['测试成功'], ensure_ascii=False)
        }
        
        notifier.send_intelligence(test_data)
        print("测试推送完成")
    
    elif args.enable_bot:
        # 启动机器人
        print("启动机器人...")
        notifier.start_bot()
    else:
        print("请使用 --test 测试推送，或 --enable_bot 启动机器人")
