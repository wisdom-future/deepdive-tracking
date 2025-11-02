# 快速测试参考 - 命令行验证指南

快速获取数据、评分、生成摘要的所有命令。

## 最快方式 (5 分钟)

### 1. 单篇文章评分 (真实 API，完整流程)
```bash
python scripts/test-real-api.py
```

**输出内容:**
- ✅ OpenAI API 配置验证
- ✅ 创建样本新闻
- ✅ 完整 AI 评分 (0-100分)
- ✅ 专业摘要 (100-300 字)
- ✅ 科学摘要 (100-300 字)
- ✅ 关键词提取
- ✅ 成本分析

**预计时间:** 10-30 秒
**预计成本:** ~$0.017

---

## 批量测试 (10-15 分钟)

### 2. 批量评分 5 篇文章
```bash
python scripts/test-batch-scoring.py 5
```

### 3. 批量评分 10 篇文章
```bash
python scripts/test-batch-scoring.py 10
```

**输出内容:**
- ✅ 逐篇评分结果
- ✅ 成本汇总
- ✅ 性能指标
- ✅ 日/月/年成本投影

**预计时间:** 1-5 分钟
**预计成本:** ~$0.085 (5篇) / ~$0.170 (10篇)

---

## 完整 E2E 测试 (无服务成本)

### 4. 运行所有 E2E 测试 (包含真实 API)
```bash
# 设置环境变量，运行真实 API 测试
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py -v -s

# 仅查看单篇文章评分
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py::TestRealAPIScoringIntegration::test_real_api_single_news_scoring -v -s

# 仅查看批量评分
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py::TestRealAPIScoringIntegration::test_real_api_batch_scoring -v -s
```

**预计时间:** 1-5 分钟
**预计成本:** ~$0.10

---

## 单个步骤验证

### 5. 仅验证 API 配置
```bash
python -c "
from src.config.settings import Settings
s = Settings()
print(f'✅ API Key: {s.openai_api_key[:20]}...')
print(f'✅ Model: {s.openai_model}')
"
```

### 6. 成本估算计算器
```bash
python -c "
# GPT-4o 成本计算
per_article = 0.017  # 评分 + 2 个摘要

volumes = {
    '100 articles/day': 100,
    '300 articles/day': 300,
    '500 articles/day': 500,
    '1000 articles/day': 1000,
    '3000 articles/month': 3000,
    '10000 articles/month': 10000,
}

print('Cost Projections:')
print('-' * 40)
for label, count in volumes.items():
    cost = per_article * count
    print(f'{label:<25} ${cost:>10.2f}')
"
```

### 7. 本地 Mock 测试 (免费，快速)
```bash
# 运行所有单元测试 (使用 Mock，无真实 API)
pytest tests/unit/ -v

# 运行所有测试 (除了 E2E)
pytest tests/ -v --ignore=tests/e2e/

# 只查看评分服务测试
pytest tests/unit/services/ai/test_scoring_service.py -v -s
```

---

## 真实数据完整流程

### 8. 从 RSS 获取 + 评分
需要修改脚本，或按照 real-api-testing-guide.md 中的方案 3。

---

## 输出示例

### 单篇文章评分输出
```
================================================================================
📊 SCORING RESULTS
================================================================================

📰 Article: OpenAI Releases GPT-4o - New Multimodal AI Breakthrough

🎯 Scoring:
  Score: 87/100
  Category: ai_breakthrough
  Confidence: 94.0%
  Quality Score: 0.92/1.00

📌 Key Points:
  1. GPT-4o demonstrates multimodal capabilities
  2. Enhanced reasoning and problem-solving
  3. Cost-effective compared to previous versions
  4. Available to researchers immediately
  5. Commercial availability by year end

🏷️  Keywords:
  gpt-4o, multimodal, ai, breakthrough, language-model

📝 Professional Summary:
  OpenAI released GPT-4o, demonstrating significant advancements in
  multimodal AI capabilities. The model shows improved reasoning and
  problem-solving abilities with enhanced support for text, images,
  and audio processing...

🔬 Scientific Summary:
  This represents a major breakthrough in deep learning architecture
  with significant implications for natural language processing and
  multimodal understanding. The advancement addresses previous
  limitations in reasoning capabilities...

💰 Cost & Performance:
  API Cost: $0.034567
  Processing Time: 8234ms
  Models Used: gpt-4o

📊 Cost Breakdown:
  scoring: $0.019234
  summary_pro: $0.007667
  summary_sci: $0.007666

📈 Cost Projections (based on $0.017 per article):
  Daily (100 articles): $1.70
  Daily (300 articles): $5.10
  Monthly (3,000 articles): $51.00
  Monthly (10,000 articles): $170.00
```

### 批量评分输出摘录
```
✅ Successfully Scored: 5 articles

#   Article Title                               Score   Category        Cost
---------------------------------------------------------------------------
1   OpenAI Releases GPT-4o Multimodal Mode      87      ai_breakthrough $ 0.034567
2   Google DeepMind Solves Protein Structure    82      research_disc   $ 0.033456
3   Meta Releases Llama 2 Open Source           78      model_release   $ 0.034234
4   Microsoft Invests $10 Billion in Anthropic  75      company_news    $ 0.034578
5   Tesla Advances Full Self-Driving            80      autonomous_veh  $ 0.035999

💰 COST SUMMARY

Total Cost: $0.172834
Average Cost per Article: $0.034567

📈 Cost Projections:
  10 articles                   $    0.35
  100 articles (1 day)          $    3.46
  3,000 articles (1 month)      $  103.70
  36,000 articles (1 year)      $1,244.00

⏱️  PERFORMANCE ANALYSIS:
  Total Processing Time: 41237ms
  Average per Article: 8247ms
  Processing Rate: 0.12 articles/second
```

---

## 故障排除

### ❌ "API Key not configured"
```bash
# 检查 .env 文件
grep OPENAI_API_KEY .env

# 如果没有，添加：
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### ❌ "Invalid API Key"
```bash
# 验证密钥格式
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
if key:
    print(f'Format: {key[:10]}...')
    print(f'Valid: {key.startswith(\"sk-\")}')"
```

### ❌ "Request timeout"
```bash
# 检查网络
ping api.openai.com

# 检查 OpenAI 状态
# https://status.openai.com/
```

### ❌ "Insufficient credits"
```bash
# 检查 OpenAI 账户余额
# https://platform.openai.com/account/billing/overview
```

---

## 成本参考表

| 场景 | 单价 | 日成本(100篇) | 月成本(3000篇) |
|------|------|---------------|----------------|
| 评分 + 2摘要 | $0.017 | $1.70 | $51.00 |
| 仅评分 | ~$0.010 | $1.00 | $30.00 |
| 仅摘要 | ~$0.007 | $0.70 | $21.00 |

---

## 常用命令速查

| 任务 | 命令 |
|------|------|
| 单篇文章评分 | `python scripts/test-real-api.py` |
| 批量评分 (5篇) | `python scripts/test-batch-scoring.py 5` |
| 批量评分 (10篇) | `python scripts/test-batch-scoring.py 10` |
| 所有 E2E 测试 | `ENABLE_REAL_API_TESTS=1 pytest tests/e2e/ -v -s` |
| 所有单元测试 | `pytest tests/unit/ -v` |
| 完整测试覆盖率 | `pytest --cov=src --cov-report=html` |
| 查看成本 | 检查脚本输出中的 "💰 Cost" 部分 |

---

## 下一步

完成测试后：

1. ✅ 验证评分准确性
2. ✅ 检查摘要质量
3. ✅ 确认成本计算
4. ⏳ 部署到生产环境
5. ⏳ 实现人工审核流程
6. ⏳ 实现多渠道发布

---

**最后更新**: 2025-11-02
**状态**: 可用
**支持**: 参考 docs/guides/real-api-testing-guide.md
