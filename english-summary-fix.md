# 英文摘要完整修复方案

## 问题描述

邮件中的英文摘要显示为硬编码的占位符文本 `(摘要展示，已提炼核心信息)`，而不是真实的AI生成内容。这个问题源自多个层面：

1. **邮件模板问题**：英文摘要字段显示硬编码占位符
2. **数据库问题**：英文摘要字段 `summary_pro_en` 和 `summary_sci_en` 可能为 NULL 或包含错误信息
3. **摘要生成错误处理**：API 调用失败时，没有妥善的 fallback 机制
4. **邮件发送逻辑**：调用 API 时没有传入英文摘要参数

## 修复步骤

### 1. 邮件模板修复 (email_publisher.py)

**变更内容**：
- 添加 `summary_en` 参数到 `publish_article()` 方法
- 更新 `_generate_email_html()` 方法，接收并正确显示英文摘要
- 移除硬编码的占位符文本

**代码变更**：
```python
# 之前
<div class="summary-en">
    (摘要展示，已提炼核心信息)
</div>

# 之后
<div class="summary-en">
    {html.escape(summary_en) if summary_en else '(No English summary available)'}
</div>
```

**文件**: `src/services/channels/email/email_publisher.py`

### 2. 摘要生成错误处理强化 (scoring_service.py)

**变更内容**：
- 改进 JSON 解析错误处理
- 添加多层 fallback 机制
- 完善 API 调用异常处理
- 验证摘要内容质量

**改进点**：
```python
# 异常处理层级：
1. 成功解析 JSON → 返回摘要
2. JSON 解析失败 → 尝试返回原始文本
3. 响应过短 → 使用 fallback 文本
4. API 错误 → 捕获并记录错误
5. 未知错误 → 通用错误消息
```

**文件**: `src/services/ai/scoring_service.py`

### 3. 邮件发送脚本修复

#### send_top_news_email.py
- 传入 `summary_en` 参数
- 验证英文摘要内容（如果缺失则使用中文）
- 改进摘要选择逻辑

#### send_top_ai_news_digest.py
- 改进双语摘要处理
- 在卡片中显示中文为主、英文为辅
- 验证摘要内容有效性

**文件**:
- `scripts/publish/send_top_news_email.py`
- `scripts/publish/send_top_ai_news_digest.py`

### 4. 数据库修复脚本（可选）

**文件**: `fix_english_summaries.py`

如果现有数据中英文摘要为空，可运行此脚本：
```bash
python fix_english_summaries.py
```

该脚本会：
1. 找出所有缺少英文摘要的记录
2. 重新生成英文摘要
3. 更新数据库
4. 验证修复结果

## 技术细节

### 错误处理流程图

```
API 调用
  ↓
获取响应 → 提取文本
  ↓
清理 markdown 代码块
  ↓
尝试 JSON 解析
  ├─ 成功 → 提取摘要字段 → 验证长度 → 返回
  └─ 失败 ↓
       检查响应格式
       ├─ 看起来像 JSON → 返回原始文本
       ├─ 纯文本且足够长 → 使用为摘要
       └─ 其他 → 返回错误信息
```

### Fallback 策略

1. **邮件发送** (send_top_news_email.py)：
   - 优先使用 `summary_pro_en`
   - 次优使用 `summary_sci_en`
   - 最后使用中文摘要

2. **摘要生成** (scoring_service.py)：
   - 优先 JSON 解析结果
   - 次优原始文本响应
   - 最后错误提示

## 验证方法

### 邮件验证
发送邮件后检查：
1. 中文摘要（📌 摘要（中文））显示真实内容
2. 英文摘要（📄 Summary (English)）显示真实内容或合理的 fallback
3. 没有硬编码的占位符文本

### 数据库验证
```sql
-- 检查英文摘要字段是否有数据
SELECT COUNT(*) FROM processed_news
WHERE summary_pro_en IS NOT NULL AND summary_pro_en != '';

SELECT COUNT(*) FROM processed_news
WHERE summary_sci_en IS NOT NULL AND summary_sci_en != '';
```

### 日志验证
查看应用日志，确保：
- 没有大量的 "JSON parse error" 警告
- "Using fallback summary" 的情况在预期范围内
- API 调用成功率高

## 预期改进

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 英文摘要显示 | 硬编码占位符 | 真实 AI 生成内容 |
| 错误恢复 | 无 | 多层 fallback |
| 双语支持 | 不完整 | 完整 |
| 数据库一致性 | 可能缺失 | 有保障 |

## 注意事项

1. **历史数据**：如果数据库中已有大量英文摘要为 NULL 的记录，运行 `fix_english_summaries.py` 进行补充
2. **API 成本**：重新生成摘要会产生额外的 OpenAI API 成本
3. **逐步推出**：建议先在测试环境验证，再上线到生产环境
4. **监控**：上线后监控日志和用户反馈，确保没有新的问题

## 总结

这个修复方案从四个维度彻底解决了英文摘要问题：
1. ✅ 邮件模板层 - 正确显示
2. ✅ 摘要生成层 - 错误处理
3. ✅ 数据库层 - 数据补充
4. ✅ API 调用层 - 参数传递

确保整个流程中，英文摘要都能被正确生成、存储和显示。
