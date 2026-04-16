"""测试向量数据库功能"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

import json
from src.vector_store import VectorStore

print("="*60)
print("测试向量数据库")
print("="*60)

# 初始化
print("\n1. 初始化向量存储...")
try:
    vector_store = VectorStore()
    print("✅ 初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    sys.exit(1)

# 测试数据
test_data = [
    {
        'id': 1001,
        'title': '国家密码管理局发布新标准',
        'content': '国家密码管理局发布了新的商用密码标准，将于2026年7月1日实施。所有电子认证服务提供商需要在规定时间内完成升级改造。',
        'category': '政策',
        'source': '国家密码管理局'
    },
    {
        'id': 1002,
        'title': 'SM4 算法优化指南',
        'content': 'SM4 是国产对称加密算法，本文介绍了 SM4 算法的优化方法和最佳实践。包括硬件加速、并行计算等技术。',
        'category': '技术',
        'source': '技术博客'
    },
    {
        'id': 1003,
        'title': 'DigiCert 推出新的 SSL 证书服务',
        'content': 'DigiCert 宣布推出新的 SSL 证书服务，支持更多的加密算法和更长的有效期。',
        'category': '竞品',
        'source': 'DigiCert'
    }
]

# 2. 添加测试数据
print("\n2. 添加测试数据...")
for item in test_data:
    success = vector_store.add_intelligence(
        intelligence_id=item['id'],
        title=item['title'],
        content=item['content'],
        category=item['category'],
        source=item['source']
    )
    if success:
        print(f"✅ 添加成功: {item['title'][:30]}")
    else:
        print(f"❌ 添加失败: {item['title'][:30]}")

# 3. 测试相似度搜索
print("\n3. 测试相似度搜索...")
print("-"*60)

queries = [
    "密码管理相关政策",
    "加密算法优化",
    "SSL 证书"
]

for query in queries:
    print(f"\n查询: {query}")
    similar = vector_store.search_similar(query, limit=2, score_threshold=0.5)
    
    if similar:
        for item in similar:
            print(f"  - {item['title'][:40]}")
            print(f"    相似度: {item['similarity']:.2f}")
            print(f"    分类: {item['category']}, 来源: {item['source']}")
    else:
        print("  未找到相似结果")

# 4. 测试重复检测
print("\n4. 测试重复检测...")
print("-"*60)

test_cases = [
    {
        'title': '国家密码管理局发布新规定',
        'content': '国家密码管理局最近发布了新的商用密码标准，将在今年7月实施。',
        'expected': True
    },
    {
        'title': '量子计算对密码学的影响',
        'content': '量子计算的发展对传统密码学带来了新的挑战，需要研究抗量子密码算法。',
        'expected': False
    }
]

for i, case in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}: {case['title']}")
    is_dup, dup_info = vector_store.check_duplicate(
        title=case['title'],
        content=case['content'],
        similarity_threshold=0.85
    )
    
    if is_dup:
        print(f"  ✅ 检测为重复")
        print(f"  相似情报: {dup_info['title'][:40]}")
        print(f"  相似度: {dup_info['similarity']:.2f}")
    else:
        print(f"  ✅ 检测为新情报")
    
    # 验证结果
    if is_dup == case['expected']:
        print(f"  ✅ 结果符合预期")
    else:
        print(f"  ⚠️  结果不符合预期（预期: {'重复' if case['expected'] else '新情报'}）")

# 5. 测试获取上下文
print("\n5. 测试获取历史上下文...")
print("-"*60)

categories = ['政策', '技术', None]

for category in categories:
    if category:
        print(f"\n分类: {category}")
    else:
        print(f"\n全部分类")
    
    context = vector_store.get_context(category=category, limit=5)
    
    if context:
        for item in context:
            print(f"  - {item['title'][:40]} ({item['category']})")
    else:
        print("  未找到数据")

# 6. 获取统计信息
print("\n6. 获取统计信息...")
print("-"*60)

stats = vector_store.get_statistics()
if stats:
    print(f"总向量数: {stats.get('total_vectors', 0)}")
    print(f"向量维度: {stats.get('vector_size', 0)}")
    print(f"距离度量: {stats.get('distance_metric', 'unknown')}")
else:
    print("获取统计信息失败")

print("\n" + "="*60)
print("测试完成")
print("="*60)

print("\n💡 提示:")
print("- 向量存储已启用，可以进行语义去重")
print("- 相似度阈值默认为 0.85（可调整）")
print("- 支持按分类获取历史上下文")
print("- 可用于 AI 分析时提供相关历史情报")
