"""
周报生成器
自动生成情报周报，包含统计分析和趋势图表
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
from src.database import Database


class WeeklyReportGenerator:
    """周报生成器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化周报生成器
        
        Args:
            db_path: 数据库路径
        """
        self.database = Database(db_path or os.getenv('DATABASE_PATH', 'data/intelligence.db'))
        self.report_dir = Path('reports/weekly')
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_weekly_report(self, 
                               start_date: datetime = None,
                               end_date: datetime = None) -> Optional[str]:
        """
        生成周报
        
        Args:
            start_date: 开始日期（默认上周一）
            end_date: 结束日期（默认上周日）
            
        Returns:
            报告文件路径
        """
        try:
            # 计算日期范围
            if not end_date:
                # 默认为上周日
                today = datetime.now()
                days_since_monday = today.weekday()
                last_sunday = today - timedelta(days=days_since_monday + 1)
                end_date = last_sunday.replace(hour=23, minute=59, second=59)
            
            if not start_date:
                # 默认为上周一
                start_date = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0)
            
            logger.info(f"生成周报: {start_date.date()} 至 {end_date.date()}")
            
            # 获取数据
            weekly_data = self._get_weekly_data(start_date, end_date)
            
            if not weekly_data['intelligence_list']:
                logger.warning("本周无情报数据")
                return None
            
            # 生成报告
            report_content = self._format_weekly_report(weekly_data, start_date, end_date)
            
            # 保存报告
            report_filename = f"weekly_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.md"
            report_path = self.report_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"周报已生成: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"生成周报失败: {e}", exc_info=True)
            return None
    
    def _get_weekly_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        获取周报数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            周报数据字典
        """
        try:
            conn = self.database._get_connection()
            cursor = conn.cursor()
            
            # 获取本周情报列表
            cursor.execute("""
                SELECT * FROM intelligence
                WHERE created_at BETWEEN ? AND ?
                ORDER BY priority DESC, created_at DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            intelligence_list = [dict(row) for row in cursor.fetchall()]
            
            # 按分类统计
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM intelligence
                WHERE created_at BETWEEN ? AND ?
                GROUP BY category
                ORDER BY count DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # 按优先级统计
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM intelligence
                WHERE created_at BETWEEN ? AND ?
                GROUP BY priority
            """, (start_date.isoformat(), end_date.isoformat()))
            
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            # 按来源统计
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM intelligence
                WHERE created_at BETWEEN ? AND ?
                GROUP BY source
                ORDER BY count DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            # 每日统计
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM intelligence
                WHERE created_at BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))
            
            daily_stats = {row['date']: row['count'] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'intelligence_list': intelligence_list,
                'by_category': by_category,
                'by_priority': by_priority,
                'by_source': by_source,
                'daily_stats': daily_stats,
                'total_count': len(intelligence_list)
            }
            
        except Exception as e:
            logger.error(f"获取周报数据失败: {e}", exc_info=True)
            return {
                'intelligence_list': [],
                'by_category': {},
                'by_priority': {},
                'by_source': {},
                'daily_stats': {},
                'total_count': 0
            }
    
    def _format_weekly_report(self, 
                             data: Dict,
                             start_date: datetime,
                             end_date: datetime) -> str:
        """
        格式化周报内容
        
        Args:
            data: 周报数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Markdown 格式的报告内容
        """
        # 报告标题
        report = f"""# 情报周报

**报告周期**：{start_date.strftime('%Y年%m月%d日')} - {end_date.strftime('%Y年%m月%d日')}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**情报总数**：{data['total_count']} 条

---

## 📊 数据概览

### 总体统计

- **本周新增情报**：{data['total_count']} 条
- **日均采集量**：{data['total_count'] / 7:.1f} 条
- **数据来源数**：{len(data['by_source'])} 个

### 按分类统计

"""
        
        # 分类统计
        if data['by_category']:
            for category, count in sorted(data['by_category'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / data['total_count'] * 100) if data['total_count'] > 0 else 0
                bar = '█' * int(percentage / 5)  # 每5%一个方块
                report += f"- **{category}**：{count} 条 ({percentage:.1f}%) {bar}\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n### 按优先级统计\n\n"
        
        # 优先级统计
        priority_icons = {'高': '🔴', '中': '🟡', '低': '🟢'}
        if data['by_priority']:
            for priority in ['高', '中', '低']:
                count = data['by_priority'].get(priority, 0)
                percentage = (count / data['total_count'] * 100) if data['total_count'] > 0 else 0
                icon = priority_icons.get(priority, '⚪')
                report += f"- {icon} **{priority}优先级**：{count} 条 ({percentage:.1f}%)\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n### 按来源统计\n\n"
        
        # 来源统计（Top 10）
        if data['by_source']:
            top_sources = sorted(data['by_source'].items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (source, count) in enumerate(top_sources, 1):
                percentage = (count / data['total_count'] * 100) if data['total_count'] > 0 else 0
                report += f"{i}. **{source}**：{count} 条 ({percentage:.1f}%)\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n### 每日采集趋势\n\n"
        
        # 每日统计
        if data['daily_stats']:
            report += "```\n"
            max_count = max(data['daily_stats'].values()) if data['daily_stats'] else 1
            
            # 生成简单的文本图表
            for date_str, count in sorted(data['daily_stats'].items()):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date_obj.weekday()]
                bar_length = int((count / max_count) * 30) if max_count > 0 else 0
                bar = '█' * bar_length
                report += f"{date_str} ({weekday}): {bar} {count}条\n"
            
            report += "```\n"
        else:
            report += "- 暂无数据\n"
        
        report += "\n---\n\n## 🔥 重点情报\n\n"
        
        # 高优先级情报
        high_priority = [item for item in data['intelligence_list'] if item.get('priority') == '高']
        
        if high_priority:
            report += f"本周共有 **{len(high_priority)}** 条高优先级情报：\n\n"
            
            for i, item in enumerate(high_priority[:10], 1):  # 最多显示10条
                report += f"### {i}. 【{item.get('category', '未分类')}】{item.get('title', '无标题')}\n\n"
                report += f"**来源**：{item.get('source', '未知')}  \n"
                report += f"**发布日期**：{item.get('publish_date', '未知')}  \n"
                
                if item.get('summary'):
                    report += f"\n**摘要**：{item.get('summary')}\n"
                
                if item.get('source_url'):
                    report += f"\n[查看原文]({item.get('source_url')})\n"
                
                report += "\n---\n\n"
        else:
            report += "本周暂无高优先级情报。\n\n"
        
        report += "## 📋 分类情报汇总\n\n"
        
        # 按分类汇总
        for category in sorted(data['by_category'].keys()):
            category_items = [item for item in data['intelligence_list'] if item.get('category') == category]
            
            if category_items:
                report += f"### {category}（{len(category_items)} 条）\n\n"
                
                for item in category_items[:5]:  # 每个分类最多显示5条
                    priority_icon = priority_icons.get(item.get('priority', '中'), '⚪')
                    report += f"- {priority_icon} **{item.get('title', '无标题')}**\n"
                    report += f"  - 来源：{item.get('source', '未知')}\n"
                    report += f"  - 日期：{item.get('publish_date', '未知')}\n"
                    
                    if item.get('source_url'):
                        report += f"  - [查看详情]({item.get('source_url')})\n"
                    
                    report += "\n"
                
                if len(category_items) > 5:
                    report += f"*...还有 {len(category_items) - 5} 条情报*\n\n"
        
        report += "---\n\n## 💡 趋势分析\n\n"
        
        # 简单的趋势分析
        report += self._generate_trend_analysis(data)
        
        report += "\n---\n\n## 📌 建议与行动\n\n"
        
        # 生成建议
        report += self._generate_recommendations(data)
        
        report += "\n---\n\n"
        report += f"*本报告由情报分析系统自动生成*  \n"
        report += f"*数据来源：{len(data['by_source'])} 个情报源*  \n"
        report += f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def _generate_trend_analysis(self, data: Dict) -> str:
        """
        生成趋势分析
        
        Args:
            data: 周报数据
            
        Returns:
            趋势分析文本
        """
        analysis = ""
        
        # 分析每日趋势
        if data['daily_stats']:
            daily_counts = list(data['daily_stats'].values())
            
            if len(daily_counts) >= 2:
                # 计算增长趋势
                first_half = sum(daily_counts[:len(daily_counts)//2])
                second_half = sum(daily_counts[len(daily_counts)//2:])
                
                if second_half > first_half:
                    trend = "上升"
                    icon = "📈"
                elif second_half < first_half:
                    trend = "下降"
                    icon = "📉"
                else:
                    trend = "平稳"
                    icon = "➡️"
                
                analysis += f"{icon} **采集趋势**：本周情报采集量呈{trend}趋势\n\n"
        
        # 分析热门分类
        if data['by_category']:
            top_category = max(data['by_category'].items(), key=lambda x: x[1])
            percentage = (top_category[1] / data['total_count'] * 100) if data['total_count'] > 0 else 0
            analysis += f"🏆 **热门分类**：{top_category[0]} 占比 {percentage:.1f}%，是本周关注重点\n\n"
        
        # 分析优先级分布
        if data['by_priority']:
            high_count = data['by_priority'].get('高', 0)
            high_percentage = (high_count / data['total_count'] * 100) if data['total_count'] > 0 else 0
            
            if high_percentage > 30:
                analysis += f"⚠️ **风险提示**：本周高优先级情报占比 {high_percentage:.1f}%，需要重点关注\n\n"
            elif high_percentage < 10:
                analysis += f"✅ **风险评估**：本周高优先级情报占比 {high_percentage:.1f}%，整体风险较低\n\n"
        
        # 分析来源活跃度
        if data['by_source']:
            active_sources = len([s for s, c in data['by_source'].items() if c >= 3])
            analysis += f"📡 **活跃来源**：本周有 {active_sources} 个情报源持续更新（≥3条）\n\n"
        
        return analysis if analysis else "暂无明显趋势。\n\n"
    
    def _generate_recommendations(self, data: Dict) -> str:
        """
        生成建议与行动
        
        Args:
            data: 周报数据
            
        Returns:
            建议文本
        """
        recommendations = ""
        
        # 基于高优先级情报的建议
        high_priority_count = data['by_priority'].get('高', 0)
        if high_priority_count > 0:
            recommendations += f"1. **重点关注**：本周有 {high_priority_count} 条高优先级情报，建议优先处理\n"
        
        # 基于分类的建议
        if data['by_category']:
            top_categories = sorted(data['by_category'].items(), key=lambda x: x[1], reverse=True)[:3]
            categories_str = "、".join([c[0] for c in top_categories])
            recommendations += f"2. **重点领域**：{categories_str} 是本周热点，建议加强监控\n"
        
        # 基于来源的建议
        if data['by_source']:
            inactive_sources = len([s for s, c in data['by_source'].items() if c < 2])
            if inactive_sources > 0:
                recommendations += f"3. **数据源优化**：有 {inactive_sources} 个来源活跃度较低，建议检查或调整\n"
        
        # 通用建议
        recommendations += "4. **持续监控**：保持对重点领域的持续关注，及时发现新动态\n"
        recommendations += "5. **定期复盘**：建议每周回顾情报处理情况，优化工作流程\n"
        
        return recommendations


# 测试代码
if __name__ == "__main__":
    print("="*60)
    print("测试周报生成")
    print("="*60)
    
    # 创建生成器
    generator = WeeklyReportGenerator()
    
    # 生成本周报告
    print("\n生成本周报告...")
    report_path = generator.generate_weekly_report()
    
    if report_path:
        print(f"\n✅ 周报已生成: {report_path}")
        print("\n预览前50行：")
        print("-"*60)
        
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[:50]:
                print(line, end='')
        
        if len(lines) > 50:
            print(f"\n... 还有 {len(lines) - 50} 行")
    else:
        print("\n❌ 周报生成失败")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
