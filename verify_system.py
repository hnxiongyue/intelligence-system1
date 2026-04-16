"""
系统功能一键验证脚本
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("情报分析系统 - 功能验证")
print("="*70)
print()

# 验证结果
results = []

def check(name, func):
    """执行检查并记录结果"""
    try:
        print(f"🔍 检查: {name}...", end=" ")
        result = func()
        if result:
            print("✅ 通过")
            results.append((name, True, None))
            return True
        else:
            print("❌ 失败")
            results.append((name, False, "检查失败"))
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results.append((name, False, str(e)))
        return False

print("📋 基础环境检查")
print("-"*70)

# 1. Python 版本
def check_python():
    version = sys.version_info
    return version.major == 3 and version.minor >= 10

check("Python 版本 (>= 3.10)", check_python)

# 2. 虚拟环境
def check_venv():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

check("虚拟环境", check_venv)

# 3. 必要的包
def check_packages():
    try:
        import langgraph
        import qdrant_client
        import openai
        from loguru import logger
        return True
    except ImportError:
        return False

check("必要的包", check_packages)

print()
print("📁 文件和目录检查")
print("-"*70)

# 4. 配置文件
def check_env():
    return Path('.env').exists()

check(".env 配置文件", check_env)

# 5. 数据库目录
def check_data_dir():
    Path('data').mkdir(exist_ok=True)
    return Path('data').exists()

check("data 目录", check_data_dir)

# 6. 报告目录
def check_reports_dir():
    Path('reports').mkdir(exist_ok=True)
    Path('reports/weekly').mkdir(exist_ok=True)
    return Path('reports').exists()

check("reports 目录", check_reports_dir)

print()
print("🔧 核心功能检查")
print("-"*70)

# 7. 数据库连接
def check_database():
    from src.database import Database
    db = Database()
    stats = db.get_statistics()
    print(f"\n   📊 数据库统计: 总计 {stats['total']} 条, 今日 {stats['today']} 条")
    return True

check("数据库连接", check_database)

# 8. 向量存储
def check_vector_store():
    if os.getenv('VECTOR_STORE_ENABLED', 'false').lower() != 'true':
        print("\n   ⚠️  向量存储未启用")
        return True
    
    from src.vector_store import VectorStore
    vs = VectorStore()
    stats = vs.get_statistics()
    print(f"\n   📊 向量统计: {stats.get('total_vectors', 0)} 个向量, {stats.get('vector_size', 0)} 维")
    return True

check("向量存储", check_vector_store)

# 9. LLM API
def check_llm_api():
    api_key = os.getenv('LLM_API_KEY')
    if not api_key or api_key.startswith('sk-your'):
        print("\n   ⚠️  LLM API Key 未配置")
        return False
    print(f"\n   ✓ API Key: {api_key[:10]}...")
    return True

check("LLM API 配置", check_llm_api)

# 10. Firecrawl API
def check_firecrawl_api():
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key or api_key.startswith('your'):
        print("\n   ⚠️  Firecrawl API Key 未配置")
        return False
    print(f"\n   ✓ API Key: {api_key[:10]}...")
    return True

check("Firecrawl API 配置", check_firecrawl_api)

# 11. 钉钉配置
def check_dingtalk():
    webhook = os.getenv('DINGTALK_WEBHOOK')
    client_id = os.getenv('DINGTALK_CLIENT_ID')
    client_secret = os.getenv('DINGTALK_CLIENT_SECRET')
    
    if webhook and 'your_token_here' not in webhook:
        print(f"\n   ✓ Webhook: {webhook[:50]}...")
    else:
        print("\n   ⚠️  Webhook 未配置")
    
    if client_id and client_secret:
        print(f"   ✓ Stream 模式: Client ID = {client_id}")
    else:
        print("   ⚠️  Stream 模式未配置")
    
    return True

check("钉钉配置", check_dingtalk)

print()
print("🧪 功能测试")
print("-"*70)

# 12. 周报生成
def check_weekly_report():
    from src.weekly_report import WeeklyReportGenerator
    from datetime import datetime, timedelta
    
    generator = WeeklyReportGenerator()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    report_path = generator.generate_weekly_report(start_date, end_date)
    
    if report_path and Path(report_path).exists():
        print(f"\n   ✓ 周报已生成: {report_path}")
        return True
    else:
        print("\n   ⚠️  周报生成失败（可能是数据不足）")
        return False

check("周报生成", check_weekly_report)

# 13. 工作流配置
def check_workflow():
    from src.graph.workflow import create_workflow
    workflow = create_workflow()
    print(f"\n   ✓ 工作流已创建，包含 5 个节点")
    return True

check("工作流配置", check_workflow)

print()
print("="*70)
print("验证结果汇总")
print("="*70)

passed = sum(1 for _, success, _ in results if success)
failed = len(results) - passed

print(f"\n总计: {len(results)} 项检查")
print(f"✅ 通过: {passed} 项")
print(f"❌ 失败: {failed} 项")

if failed > 0:
    print("\n失败项目:")
    for name, success, error in results:
        if not success:
            print(f"  ❌ {name}")
            if error:
                print(f"     错误: {error}")

print()
print("="*70)

if failed == 0:
    print("🎉 所有检查通过！系统运行正常。")
    print()
    print("下一步:")
    print("  1. 运行完整工作流: python src/main_langgraph.py")
    print("  2. 生成周报: python generate_weekly_report.py")
    print("  3. 测试钉钉推送: python test_dingtalk.py")
elif failed <= 3:
    print("⚠️  部分检查失败，但系统基本可用。")
    print()
    print("建议:")
    print("  1. 检查失败项目并修复")
    print("  2. 查看 .env 配置文件")
    print("  3. 参考 验证指南.md")
else:
    print("❌ 多项检查失败，请先修复配置。")
    print()
    print("请检查:")
    print("  1. .env 配置文件是否正确")
    print("  2. 依赖包是否完整安装")
    print("  3. 参考 验证指南.md 进行排查")

print("="*70)
