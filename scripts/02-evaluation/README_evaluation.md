# 评分脚本 (Evaluation Scripts)

**用途：** 使用 OpenAI GPT-4o 对采集的新闻进行 AI 智能评分

---

## 📋 脚本列表

### 1. `score_batch.py` - 批量评分 (推荐用于 P1-3 第二步)

**功能：**
- 批量评分所有未评分的文章
- 调用 OpenAI GPT-4o API
- 保存评分到 processed_news 表
- 显示成功率、成本、性能统计
- 提供评分示例

**运行：**
```bash
python score_batch.py
```

**输出示例：**
```
开始评分 77 条新闻...
[████████████████████] 100%

评分结果:
  成功: 77/77 (100%)
  失败: 0
  总成本: $0.23
  平均耗时: 2.5 秒/条
  总耗时: 3 分 15 秒

评分示例:
  标题: AI 新突破：Google DeepMind...
  内容: DeepMind 最新研究显示...
  分数: 92/100
  分类: 技术突破, 创新, 学术研究
  摘要: 这是一项重要的 AI 研究突破...
```

**耗时：** 3-5 分钟（100+ 条文章）

**何时使用：**
- P1-3 第二步
- 采集后评分新闻
- 批量处理大量文章

---

### 2. `score_missing.py` - 补评分

**功能：**
- 重新评分失败的文章
- 逐个调用 OpenAI API
- 保存评分到 processed_news
- 更新 raw_news 状态
- 显示补评分结果

**运行：**
```bash
python score_missing.py
```

**输出示例：**
```
查找未评分的文章...
找到 5 条未评分文章

开始补评分...
[████████        ] 40%
成功: 4/5
失败: 1

失败原因：
  标题: 某篇文章... (错误: API 超时)
```

**耗时：** 取决于未评分文章数

**何时使用：**
- 某些文章评分失败后
- 补充遗漏的评分
- 重新评分某些文章

---

### 3. `test_api.py` - API 诊断

**功能：**
- 测试 OpenAI API 连接
- 验证 API Key 有效性
- 检查响应格式
- 测试成本计算
- 验证配额充足

**运行：**
```bash
python test_api.py
```

**输出示例：**
```
测试 OpenAI API 连接...
API Key: sk-proj-***...***
模型: gpt-4o

[1] 连接测试
    ✓ API 连接正常
    响应时间: 1.2 秒

[2] 格式验证
    ✓ 响应格式有效
    ✓ JSON 解析成功

[3] 成本计算
    输入 tokens: 150
    输出 tokens: 200
    估计成本: $0.02

[4] 配额检查
    ✓ 有足够配额

总结: ✓ API 正常，可以开始评分
```

**耗时：** 5-10 秒

**何时使用：**
- 评分失败时诊断
- 配置新的 API Key
- 检查 API 配额

---

## 🚀 使用流程

### P1-3 第二步（推荐）
```bash
# 假设已在 scripts 目录下
cd scripts/02-evaluation
python score_batch.py
```

### 诊断 API 问题
```bash
python test_api.py
```

### 补评分失败的文章
```bash
python score_missing.py
```

---

## 📊 评分详解

### 评分维度

| 维度 | 范围 | 说明 |
|------|------|------|
| 分数 | 0-100 | 新闻价值和重要程度 |
| 分类 | 多个 | 最多 8 个分类 |

### 分类列表

```
1. 技术突破 (Breakthrough)
2. 创新应用 (Innovation)
3. 产业动态 (Industry)
4. 学术研究 (Academic)
5. 安全隐患 (Security)
6. 伦理讨论 (Ethics)
7. 竞争态势 (Competition)
8. 投融资 (Funding)
```

### 分数说明

```
90-100: 非常重要 (Very Important)
        - 重大技术突破
        - 改变行业格局的事件

80-89:  重要 (Important)
        - 有一定影响力的新闻
        - 值得关注的进展

70-79:  中等 (Medium)
        - 有参考价值
        - 常规新闻

60-69:  较低 (Low)
        - 信息性较强
        - 参考价值有限

< 60:   很低 (Very Low)
        - 不值得深入阅读
        - 可以跳过
```

---

## 🎯 评分成功标准

✅ P1-3 验收标准：
- [ ] 评分成功率 > 95%（最多 5% 失败）
- [ ] 每条耗时 < 5 秒（包括网络延迟）
- [ ] 成本 < $1 / 100 条文章
- [ ] 评分字段完整（分数、分类、摘要）

---

## 💰 成本估计

### 成本模型

```
GPT-4o 定价 (2025-11-02):
  输入: $2.50 / 1M tokens
  输出: $10.00 / 1M tokens

单条文章评分成本:
  输入: ~500 tokens   → $0.00125
  输出: ~200 tokens   → $0.002
  总计: ~$0.003 / 文章

100 条文章评分成本:
  总计: ~$0.30
```

### 优化成本

1. **批处理** - 减少 API 调用次数
2. **缓存** - Redis 缓存已评分的内容
3. **模型选择** - 可选更便宜的 gpt-3.5-turbo

---

## ⚠️ 常见问题

### Q1: 评分超时

**症状：** 脚本运行超过 10 分钟无进展

**原因：** API 延迟或网络问题

**解决：**
```bash
# 测试 API 连接
python test_api.py

# 如果失败，检查
# 1. OpenAI API Key 是否有效
# 2. 网络连接是否正常
# 3. API 是否有配额限制
```

### Q2: "Rate limit exceeded" 错误

**症状：** 评分到一半突然停止

**原因：** OpenAI API 频率限制

**解决：**
```
Option 1: 等待 1-2 分钟后重试
  python score_missing.py

Option 2: 使用更低频率
  编辑 score_batch.py，增加延迟:
  time.sleep(2)  # 每个请求延迟 2 秒
```

### Q3: "Invalid API Key" 错误

**症状：** 无法连接 API

**原因：** API Key 配置错误或过期

**解决：**
1. 检查 .env 文件：
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```
2. 确保 Key 格式正确：`sk-proj-...`
3. 在 OpenAI 官网验证 Key 是否有效

### Q4: 评分结果不准确

**症状：** 评分没有反映文章的真实价值

**原因：** AI 模型可能误判

**解决：**
- 这是 AI 的局限，正常现象
- 可以手动调整评分
- 可以修改评分 prompt

---

## 🔧 高级选项

### 修改评分 Prompt

编辑 `score_batch.py`，找到 `scoring_prompt` 部分，修改评分标准。

### 批量大小

```python
BATCH_SIZE = 10  # 每批评分 10 条，可改为其他值
```

### 并发数

```python
CONCURRENT = 5   # 同时进行 5 个评分任务
```

### 重试策略

```python
MAX_RETRIES = 3  # 失败重试 3 次
RETRY_DELAY = 5  # 重试延迟 5 秒
```

---

## 📊 性能参考

| 项目 | 值 |
|------|-----|
| 单条评分耗时 | 2-5 秒 |
| 100 条总耗时 | 3-5 分钟 |
| 成功率 | > 95% |
| 成本/条 | ~$0.003 |
| API 超时 | 30 秒 |

---

## 🎓 学习资源

- **评分系统：** docs/tech/system-design-summary.md
- **API 集成：** src/services/ai/scoring_service.py
- **完整流程：** docs/development/p1-ready-for-testing.md

---

**最后更新：** 2025-11-02
**脚本状态：** ✅ 生产就绪
