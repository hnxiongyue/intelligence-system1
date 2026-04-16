"""测试钉钉推送"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.notifier import Notifier
import json

print("="*60)
print("测试钉钉推送")
print("="*60)

# 初始化推送器
notifier = Notifier()

if not notifier.webhook_url:
    print("\n❌ 未配置 DINGTALK_WEBHOOK")
    print("\n请按以下步骤配置：")
    print("1. 在钉钉群里添加自定义机器人")
    print("2. 安全设置选择'自定义关键词'，添加关键词：情报")
    print("3. 复制 Webhook URL")
    print("4. 更新 .env 文件：")
    print("   DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxxxx")
    sys.exit(1)

print(f"\n✅ Webhook URL 已配置")
print(f"URL: {notifier.webhook_url[:50]}...")

# 测试数据
test_data = {
    'title': '【测试】国家密码管理局发布新标准',
    'source': '国家密码管理局',
    'source_url': 'https://www.nca.gov.cn',
    'category': '政策',
    'priority': '高',
    'publish_date': '2026-04-16',
    'summary': '这是一条测试情报，用于验证钉钉推送功能是否正常。国家密码管理局发布了新的商用密码标准，将于2026年7月1日实施。',
    'impact': '所有电子认证服务提供商需要在规定时间内完成升级改造。影响范围广，需要提前准备。',
    'suggestions': json.dumps([
        '立即启动技术预研，评估改造工作量',
        '2周内完成详细方案设计',
        'Q2完成开发和测试',
        '6月底前完成上线部署'
    ], ensure_ascii=False)
}

print("\n开始测试推送...")
print("-"*60)

# 1. 测试格式化消息
print("\n1. 格式化消息预览：")
print("-"*60)
message = notifier.format_message(test_data)
print(message)
print("-"*60)

# 2. 测试发送到钉钉
print("\n2. 发送到钉钉...")
success = notifier.send_to_dingtalk(test_data)

if success:
    print("\n" + "="*60)
    print("✅ 推送成功！")
    print("="*60)
    print("\n请检查钉钉群，应该能看到测试消息。")
    print("\n消息特点：")
    print("- 标题包含【测试】标记")
    print("- 使用 Markdown 格式")
    print("- 包含优先级图标（🔴 高优先级）")
    print("- 包含摘要、影响分析、应对建议")
else:
    print("\n" + "="*60)
    print("❌ 推送失败")
    print("="*60)
    print("\n可能的原因：")
    print("1. Webhook URL 不正确")
    print("2. 安全设置问题（关键词不匹配）")
    print("   - 如果使用'自定义关键词'，消息必须包含该关键词")
    print("   - 建议关键词：情报")
    print("3. 网络连接问题")
    print("\n请检查日志了解详细错误信息")

# 3. 测试保存 Markdown
print("\n3. 保存为 Markdown 文件...")
notifier.save_to_markdown(test_data)
print("✅ Markdown 文件已保存到 reports/ 目录")

print("\n" + "="*60)
print("测试完成")
print("="*60)
