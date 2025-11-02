# 如何运行真实 API 测试 - 完整指南

本指南介绍如何使用命令行工具进行真实数据获取、评分和摘要生成的完整验证。

## 快速开始 (3 个步骤)

### 第 1 步: 验证 API 连接

```bash
python scripts/diagnose-api.py
```

**预期输出:**
```
✅ API Key found: sk-proj-...
✅ Key format looks valid (starts with 'sk-')
✅ API Call Successful!
   Response: OK
   Estimated cost: $0.000070

✅ API is working correctly!
```

**如果失败:**
- 检查 `.env` 文件中的 `OPENAI_API_KEY`
- 确保密钥格式正确 (以 `sk-` 开头)
- 检查账户余额: https://platform.openai.com/account/billing/overview

### 第 2 步: 查看演示 (无需 API 成本)

```bash
python scripts/demo-with-mock.py
```

**特点:**
- ✅ 完整的评分、摘要、分析流程
- ✅ 无需实际 API 调用
- ✅ 无成本
- ✅ 看到完整输出格式

### 第 3 步: 运行真实 API 测试

```bash
# 单篇文章
python scripts/test-real-api.py

# 批量评分 (5-10 篇)
python scripts/test-batch-scoring.py 5
```

---

## 详细指南

### 方案 1: API 诊断 (2 分钟)

最快验证 OpenAI 配置是否有效。

```bash
python scripts/diagnose-api.py
```

**输出包含:**
- ✅ API 密钥验证
- ✅ 密钥格式检查
- ✅ API 连接测试
- ✅ 成本估算
- ✅ 故障排除建议

**成本:** ~$0.00007 (超小成本用于测试)

---

### 方案 2: 演示完整流程 (3-5 分钟)

看完整的新闻评分、摘要、分析，**无需任何 API 成本**。

```bash
python scripts/demo-with-mock.py
```

**显示:**
- 📝 新闻文章
- 🎯 评分 (0-100分)
- 📌 关键点提取
- 🏷️  关键词提取
- 📝 专业摘要
- 🔬 科学摘要
- 💰 成本计算
- 📈 月度成本投影

**特点:**
- 使用 Mock 数据，无需 API 调用
- 完全免费
- 展示完整的处理流程
- 显示最终输出格式

**成本:** $0.00

---

### 方案 3: 单篇文章真实评分 (30-60 秒)

使用真实的 OpenAI API 评分一篇文章。

```bash
python scripts/test-real-api.py
```

**流程:**
1. ✅ 验证 API 配置
2. ✅ 创建样本新闻
3. ✅ 调用真实 OpenAI API
4. ✅ 显示完整结果
5. ✅ 计算成本

**预期成本:** ~$0.03-0.05

**输出:**
```
📊 SCORING RESULTS

📰 Article: OpenAI Releases GPT-4o...

🎯 Scoring:
  Score: 87/100
  Category: tech_breakthrough
  Confidence: 94.0%

📌 Key Points:
  1. GPT-4o demonstrates multimodal capabilities
  2. Enhanced reasoning and problem-solving
  ...

🏷️  Keywords: gpt-4o, multimodal, ai, breakthrough

📝 Professional Summary:
  OpenAI released GPT-4o...

🔬 Scientific Summary:
  GPT-4o advances deep learning architecture...

💰 Cost & Performance:
  API Cost: $0.034567
  Processing Time: 8234ms
```

---

### 方案 4: 批量评分 (1-5 分钟)

一次评分多篇文章。

```bash
# 评分 5 篇
python scripts/test-batch-scoring.py 5

# 评分 10 篇
python scripts/test-batch-scoring.py 10
```

**输出:**
```
✅ Successfully Scored: 5 articles

#   Article Title                         Score   Category           Cost
---------------------------------------------------------------------
1   OpenAI Releases GPT-4o               87      tech_breakthrough  $0.034567
2   Google DeepMind Solves Protein       82      research_disc      $0.033456
3   Meta Releases Llama 2                78      model_release      $0.034234
4   Microsoft Invests in Anthropic       75      company_news       $0.034578
5   Tesla Advances Full Self-Driving     80      autonomous_veh     $0.035999

💰 COST SUMMARY
Total Cost: $0.172834
Average Cost per Article: $0.034567

📈 Cost Projections:
  10 articles              $    0.35
  100 articles (1 day)     $    3.46
  3,000 articles (1 month) $  103.70
```

**预期成本:** ~$0.17 (5篇) / ~$0.34 (10篇)

---

### 方案 5: 完整 E2E 测试

运行所有真实 API 测试套件。

```bash
ENABLE_REAL_API_TESTS=1 pytest tests/e2e/test_real_api_optional.py -v -s
```

**包含:**
- ✅ 单篇文章评分
- ✅ 批量评分 (3 篇)
- ✅ 令牌计数验证
- ✅ 成本投影

**预期成本:** ~$0.10-0.15

---

## 命令参考表

| 任务 | 命令 | 时间 | 成本 | 特点 |
|------|------|------|------|------|
| 诊断 API | `diagnose-api.py` | 5-10s | ~$0 | 验证连接 |
| 查看演示 | `demo-with-mock.py` | 3s | $0 | 无需 API |
| 单篇评分 | `test-real-api.py` | 30s | ~$0.03 | 真实 API |
| 批量5篇 | `test-batch-scoring.py 5` | 1m | ~$0.17 | 真实 API |
| 批量10篇 | `test-batch-scoring.py 10` | 2m | ~$0.34 | 真实 API |
| 完整E2E | E2E 测试 | 2m | ~$0.15 | 完整测试 |

---

## 故障排除

### ❌ "ModuleNotFoundError: No module named 'src'"

**原因:** Python 找不到项目模块

**解决:**
```bash
# 在项目根目录运行
cd D:\projects\deepdive-tracking
python scripts/diagnose-api.py
```

### ❌ "UnicodeEncodeError: 'gbk' codec can't encode"

**原因:** Windows 编码问题（已修复）

**检查:**
- 脚本已包含 UTF-8 修复
- 如果仍然出现，设置环境变量:
```bash
set PYTHONIOENCODING=utf-8
python scripts/diagnose-api.py
```

### ❌ "401 Unauthorized - Invalid API key"

**原因:** API 密钥无效或过期

**解决:**
```bash
# 1. 生成新密钥
# https://platform.openai.com/account/api-keys

# 2. 更新 .env 文件
echo OPENAI_API_KEY=sk-your-new-key >> .env

# 3. 重新运行诊断
python scripts/diagnose-api.py
```

### ❌ "429 Too Many Requests - Rate limit exceeded"

**原因:** 请求过于频繁

**解决:**
```bash
# 等待 1 分钟，再重试
python scripts/diagnose-api.py
```

### ❌ "quota exceeded or insufficient balance"

**原因:** 账户没有足够的余额

**解决:**
1. 检查账户: https://platform.openai.com/account/billing/overview
2. 添加付款方式或充值
3. 设置使用限额防止超支

---

## 成本参考

### 单次调用成本

| 操作 | 成本 |
|------|------|
| API 诊断 | ~$0.00007 |
| 单篇评分 + 2 摘要 | ~$0.03-0.05 |
| 批量 5 篇 | ~$0.17 |
| 批量 10 篇 | ~$0.34 |

### 月度成本投影

| 日处理量 | 日成本 | 月成本 |
|---------|--------|--------|
| 100 篇 | $1.70 | $51 |
| 300 篇 | $5.10 | $153 |
| 500 篇 | $8.50 | $255 |
| 1000 篇 | $17 | $510 |

---

## 建议工作流

### 初次设置

1. **验证配置** (2 分钟)
   ```bash
   python scripts/diagnose-api.py
   ```

2. **查看演示** (3 分钟)
   ```bash
   python scripts/demo-with-mock.py
   ```

3. **测试单篇** (1 分钟)
   ```bash
   python scripts/test-real-api.py
   ```

**总时间:** 6 分钟
**总成本:** ~$0.04

### 日常验证

1. **运行演示** (验证代码改动)
   ```bash
   python scripts/demo-with-mock.py  # 无成本
   ```

2. **运行单篇测试** (验证 API)
   ```bash
   python scripts/test-real-api.py   # ~$0.04
   ```

### 部署前验证

1. **完整 E2E 测试**
   ```bash
   ENABLE_REAL_API_TESTS=1 pytest tests/e2e/ -v -s
   ```

2. **批量测试**
   ```bash
   python scripts/test-batch-scoring.py 10  # 验证批量处理
   ```

---

## 常见问题

**Q: 哪个脚本最便宜?**

A: `demo-with-mock.py` 完全免费，显示完整流程。

---

**Q: 哪个脚本最快?**

A: `diagnose-api.py` 最快，只需 5-10 秒。

---

**Q: 如何节省成本?**

A:
1. 使用 `demo-with-mock.py` 进行开发和测试
2. 仅在需要验证真实 API 时使用 `test-real-api.py`
3. 使用 E2E Mock 测试进行 CI/CD

---

**Q: 可以修改测试文章吗?**

A: 可以，编辑脚本中的 SAMPLE_ARTICLES 或 sample_content。

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

**文档版本**: 1.0
**最后更新**: 2025-11-02
**状态**: 可用
**支持脚本版本**: 所有新脚本 (diagnose-api, demo-with-mock, test-real-api, test-batch-scoring)
