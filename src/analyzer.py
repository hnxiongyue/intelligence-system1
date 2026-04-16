"""
AI 分析模块
负责使用 LLM 分析情报内容
"""

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from loguru import logger


class Analyzer:
    """AI 分析类"""
    
    # 分析 Prompt 模板
    ANALYSIS_PROMPT = """你是一个专业的行业情报分析师，擅长分析电子认证、密码技术、数字签名领域的政策和竞品动态。

请分析以下情报内容：

**来源**：{source}
**标题**：{title}
**内容**：{content}

请按照以下格式输出 JSON（只输出 JSON，不要其他内容）：

{{
  "category": "政策/竞品/技术",
  "priority": "高/中/低",
  "summary": "用 2-3 句话总结核心内容",
  "impact": "分析对电子认证行业的影响",
  "suggestions": [
    "建议1",
    "建议2"
  ]
}}

注意：
1. category 必须是"政策"、"竞品"或"技术"之一
2. priority 根据影响程度判断：高（重大政策/重要竞品动态）、中（一般更新）、低（常规信息）
3. summary 要简洁明了，突出重点
4. impact 要具体分析对行业的影响
5. suggestions 要具体可执行，至少提供 2 条建议
"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        初始化分析器
        
        Args:
            api_key: API Key（默认从环境变量读取）
            base_url: API Base URL
            model: 模型名称
        """
        # 支持多种 LLM 提供商
        self.api_key = api_key or os.getenv('LLM_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url or os.getenv('LLM_BASE_URL') or os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = model or os.getenv('LLM_MODEL') or 'deepseek-chat'
        
        if not self.api_key:
            raise ValueError("未配置 LLM_API_KEY 或 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"初始化 AI 分析器: {self.model}")
    
    def analyze(self, data: Dict) -> Dict:
        """
        分析单条情报
        
        Args:
            data: 情报数据
            
        Returns:
            分析结果
        """
        try:
            source = data.get('source', '')
            title = data.get('title', '')
            content = data.get('content', '')[:3000]  # 限制长度，避免 token 过多
            
            # 构建 Prompt
            prompt = self.ANALYSIS_PROMPT.format(
                source=source,
                title=title,
                content=content
            )
            
            logger.info(f"开始分析: {title[:50]}")
            
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的行业情报分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            
            # 提取 JSON（处理可能的 markdown 代码块）
            result_text = self._extract_json(result_text)
            
            # 解析 JSON
            analysis_result = json.loads(result_text)
            
            # 合并结果
            result = {
                **data,
                'category': analysis_result.get('category', data.get('category', '未分类')),
                'priority': analysis_result.get('priority', '中'),
                'summary': analysis_result.get('summary', ''),
                'impact': analysis_result.get('impact', ''),
                'suggestions': json.dumps(analysis_result.get('suggestions', []), ensure_ascii=False)
            }
            
            logger.info(f"分析成功: {title[:50]} - {result['category']} - {result['priority']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, 响应: {result_text[:200]}")
            return self._fallback_analysis(data)
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return self._fallback_analysis(data)
    
    def analyze_all(self, data_list: List[Dict]) -> List[Dict]:
        """
        批量分析
        
        Args:
            data_list: 情报数据列表
            
        Returns:
            分析结果列表
        """
        results = []
        
        for data in data_list:
            result = self.analyze(data)
            if result:
                results.append(result)
        
        logger.info(f"批量分析完成: {len(results)}/{len(data_list)}")
        return results
    
    def _extract_json(self, text: str) -> str:
        """提取 JSON（处理 markdown 代码块）"""
        # 如果包含 ```json，提取其中的内容
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        # 如果包含 ```，提取其中的内容
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        return text
    
    def _fallback_analysis(self, data: Dict) -> Dict:
        """
        降级分析（LLM 失败时使用）
        
        使用简单规则进行分类
        """
        logger.warning(f"使用降级分析: {data.get('title', '')[:50]}")
        
        content = data.get('content', '').lower()
        title = data.get('title', '').lower()
        
        # 简单分类规则
        category = data.get('category', '未分类')
        
        # 关键词匹配
        policy_keywords = ['政策', '法规', '标准', '规范', '通知', '公告', '管理办法']
        competitor_keywords = ['融资', '发布', '推出', '上线', '合作', '签约']
        tech_keywords = ['技术', '算法', '密码', '加密', '安全']
        
        if any(kw in title or kw in content for kw in policy_keywords):
            category = '政策'
        elif any(kw in title or kw in content for kw in competitor_keywords):
            category = '竞品'
        elif any(kw in title or kw in content for kw in tech_keywords):
            category = '技术'
        
        # 简单优先级判断
        priority = '中'
        high_keywords = ['重要', '紧急', '重大', '关键', '必须']
        if any(kw in title for kw in high_keywords):
            priority = '高'
        
        return {
            **data,
            'category': category,
            'priority': priority,
            'summary': data.get('title', '')[:200],
            'impact': '需要进一步分析',
            'suggestions': json.dumps(['关注后续动态', '评估影响范围'], ensure_ascii=False)
        }


# 测试代码
if __name__ == "__main__":
    # 测试分析
    analyzer = Analyzer()
    
    test_data = {
        'source': '国家密码管理局',
        'title': '关于发布商用密码新标准的公告',
        'content': '''
            国家密码管理局发布了新的商用密码标准 GM/T 0031-2025，
            该标准将于 2026 年 7 月 1 日正式实施。
            新标准对密码算法的安全性提出了更高要求，
            要求所有电子认证服务提供商在规定时间内完成升级。
        '''
    }
    
    result = analyzer.analyze(test_data)
    
    print(f"\n分析结果:")
    print(f"  分类: {result['category']}")
    print(f"  优先级: {result['priority']}")
    print(f"  摘要: {result['summary']}")
    print(f"  影响: {result['impact']}")
    print(f"  建议: {result['suggestions']}")
