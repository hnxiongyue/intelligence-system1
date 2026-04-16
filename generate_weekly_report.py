"""
周报生成命令行工具
"""
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.weekly_report import WeeklyReportGenerator


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print(f"❌ 日期格式错误: {date_str}，请使用 YYYY-MM-DD 格式")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='生成情报周报',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成上周报告（默认）
  python generate_weekly_report.py
  
  # 生成指定日期范围的报告
  python generate_weekly_report.py --start 2026-04-01 --end 2026-04-07
  
  # 生成最近7天的报告
  python generate_weekly_report.py --recent 7
  
  # 生成最近30天的报告
  python generate_weekly_report.py --recent 30
        """
    )
    
    parser.add_argument(
        '--start',
        type=str,
        help='开始日期 (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        help='结束日期 (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--recent',
        type=int,
        help='最近N天'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='输出目录（默认: reports/weekly）'
    )
    
    args = parser.parse_args()
    
    # 解析日期范围
    start_date = None
    end_date = None
    
    if args.recent:
        # 最近N天
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.recent)
        print(f"📅 生成最近 {args.recent} 天的报告")
    elif args.start and args.end:
        # 指定日期范围
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
        print(f"📅 生成指定日期范围的报告")
    elif args.start or args.end:
        print("❌ 请同时指定 --start 和 --end，或使用 --recent")
        sys.exit(1)
    else:
        # 默认：上周
        print("📅 生成上周报告（周一至周日）")
    
    print(f"日期范围: {start_date.strftime('%Y-%m-%d') if start_date else '上周一'} 至 {end_date.strftime('%Y-%m-%d') if end_date else '上周日'}")
    print("-" * 60)
    
    # 创建生成器
    generator = WeeklyReportGenerator()
    
    # 生成报告
    print("\n⏳ 正在生成周报...")
    report_path = generator.generate_weekly_report(
        start_date=start_date,
        end_date=end_date
    )
    
    if report_path:
        print(f"\n✅ 周报生成成功！")
        print(f"📄 报告路径: {report_path}")
        
        # 显示报告统计
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # 提取关键信息
            for line in lines[:10]:
                if '情报总数' in line:
                    print(f"📊 {line.strip()}")
                elif '日均采集量' in line:
                    print(f"📈 {line.strip()}")
        
        print(f"\n💡 提示: 使用文本编辑器或 Markdown 查看器打开报告文件")
        
        # 询问是否打开报告
        try:
            response = input("\n是否打开报告? (y/n): ").strip().lower()
            if response == 'y':
                import os
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(report_path)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{report_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{report_path}"')
        except KeyboardInterrupt:
            print("\n")
    else:
        print("\n❌ 周报生成失败")
        print("可能原因:")
        print("  - 指定日期范围内没有数据")
        print("  - 数据库连接失败")
        print("  - 权限不足")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
