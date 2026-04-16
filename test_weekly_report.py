"""测试周报生成功能"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from src.weekly_report import WeeklyReportGenerator

print("="*60)
print("测试周报生成功能")
print("="*60)

# 创建生成器
print("\n1. 初始化周报生成器...")
generator = WeeklyReportGenerator()
print("✅ 初始化成功")

# 测试1：生成上周报告
print("\n2. 生成上周报告...")
print("-"*60)

report_path = generator.generate_weekly_report()

if report_path:
    print(f"✅ 周报已生成: {report_path}")
    
    # 显示报告预览
    print("\n报告预览（前60行）：")
    print("="*60)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:60], 1):
            print(line, end='')
    
    if len(lines) > 60:
        print(f"\n... 还有 {len(lines) - 60} 行")
    
    print("\n" + "="*60)
    print(f"完整报告请查看: {report_path}")
else:
    print("❌ 周报生成失败（可能是本周暂无数据）")

# 测试2：生成指定日期范围的报告
print("\n3. 生成自定义日期范围报告...")
print("-"*60)

# 最近7天
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"日期范围: {start_date.date()} 至 {end_date.date()}")

custom_report_path = generator.generate_weekly_report(
    start_date=start_date,
    end_date=end_date
)

if custom_report_path:
    print(f"✅ 自定义周报已生成: {custom_report_path}")
else:
    print("❌ 自定义周报生成失败")

print("\n" + "="*60)
print("测试完成")
print("="*60)

print("\n💡 使用提示:")
print("- 周报默认生成上周（周一至周日）的数据")
print("- 可以指定任意日期范围生成报告")
print("- 报告保存在 reports/weekly/ 目录")
print("- 包含统计分析、趋势图表、重点情报等内容")
