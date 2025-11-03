"""Prompt templates for AI scoring and classification."""

from typing import Dict, Any

# 8大类别定义
CATEGORIES = [
    "company_news",      # 公司新闻
    "tech_breakthrough", # 技术突破
    "applications",      # 应用落地
    "infrastructure",    # 基础设施
    "policy",           # 政策监管
    "market_trends",    # 市场动态
    "expert_opinions",  # 专家观点
    "learning_resources" # 学习资源
]


def get_scoring_prompt(title: str, content: str) -> str:
    """Generate scoring and classification prompt.

    Args:
        title: News article title
        content: News article content

    Returns:
        Formatted prompt for scoring
    """
    return f"""你是AI资讯评分专家。请分析以下AI相关新闻的重要性、影响力和价值。

【新闻标题】
{title}

【新闻内容】
{content}

请按照以下要求进行分析，并返回JSON格式的结果：

【评分规则】（0-100分）
- 90-100分：行业重大突破、影响深远、改变格局（如GPT-4发布、BERT出现）
- 70-89分：重要技术进展、新模型发布、重要融资（百万级以上）
- 50-69分：中等重要性、应用案例、产品更新
- 30-49分：公司动态、小幅更新、政策变化
- 0-29分：低相关性、转发内容、辅助信息

【分类规则】（选择最匹配的一个）
- company_news：公司融资、人事变动、战略调整
- tech_breakthrough：新技术发布、模型突破、开源项目
- applications：应用落地、实际案例、行业方案
- infrastructure：计算资源、算力、基础设施、硬件
- policy：政策监管、法规、合规性、安全
- market_trends：市场趋势、竞争格局、商业分析
- expert_opinions：专家观点、分析评论、深度解读
- learning_resources：教程、文档、学习资源、教育内容

【返回格式】（必须是有效的JSON）
{{
    "score": <0-100整数>,
    "score_reasoning": "<为什么给这个分数，2-3句话>",
    "category": "<选择的分类>",
    "sub_categories": [<相关的次分类，可选，最多3个>],
    "confidence": <0-1之间的浮点数，表示分类置信度>,
    "key_points": [<新闻的3-5个关键要点，每个5-20字>],
    "keywords": [<5-8个关键词，按重要性排序>],
    "entities": {{
        "companies": [<提及的公司名称，最多5个>],
        "technologies": [<提及的技术名称，最多5个>],
        "people": [<提及的人名，最多3个>]
    }},
    "impact_analysis": "<简要分析这条新闻的影响，1-2句话>"
}}

请确保返回的是完整、有效的JSON。"""


def get_summary_prompt(
    title: str, content: str, score: int, category: str, key_points: list
) -> Dict[str, str]:
    """Generate summary generation prompts (professional and scientific versions).

    Args:
        title: News article title
        content: News article content
        score: Article score
        category: Article category
        key_points: Key points from scoring

    Returns:
        Dictionary with professional, scientific, professional_en, and scientific_en summaries
    """
    # 中文基础提示词
    base_prompt_zh = f"""基于以下新闻信息，请生成摘要：

【新闻信息】
标题：{title}
内容：{content}
评分：{score}/100
分类：{category}
关键点：{', '.join(key_points)}

要求：
- 摘要长度：150-200字
- 语言准确、表述清晰
- 保留新闻的核心信息和重要细节"""

    professional_prompt = f"""{base_prompt_zh}

【专业版摘要要求】
- 面向技术决策者和AI从业者
- 保留技术术语和专业细节
- 重点强调对技术发展的意义
- 包含具体的数据和指标

请返回JSON格式：
{{"summary_pro": "<专业版摘要>"}}"""

    scientific_prompt = f"""{base_prompt_zh}

【科普版摘要要求】
- 面向非专业人士（PM、投资人、爱好者）
- 用通俗易懂的语言解释技术概念
- 比喻和类比辅助理解
- 强调现实意义和应用价值

请返回JSON格式：
{{"summary_sci": "<科普版摘要>"}}"""

    # English base prompt
    base_prompt_en = f"""Based on the following news information, please generate a summary:

[News Information]
Title: {title}
Content: {content}
Score: {score}/100
Category: {category}
Key Points: {', '.join(key_points)}

Requirements:
- Summary length: 150-200 words
- Accurate language and clear expression
- Preserve core information and important details from the article"""

    professional_prompt_en = f"""{base_prompt_en}

[Professional Summary Requirements]
- Targeted at tech decision-makers and AI practitioners
- Preserve technical terminology and professional details
- Emphasize significance for technology development
- Include specific data and metrics

Please return in JSON format:
{{"summary_pro_en": "<professional summary>"}}"""

    scientific_prompt_en = f"""{base_prompt_en}

[Popular Science Summary Requirements]
- Targeted at non-technical audience (PMs, investors, enthusiasts)
- Explain technical concepts in accessible language
- Use analogies and metaphors for understanding
- Emphasize practical significance and application value

Please return in JSON format:
{{"summary_sci_en": "<popular science summary>"}}"""

    return {
        "professional": professional_prompt,
        "scientific": scientific_prompt,
        "professional_en": professional_prompt_en,
        "scientific_en": scientific_prompt_en,
    }


# 预定义的Prompt模板供快速使用
SCORING_SYSTEM_PROMPT = """你是一个专业的AI资讯评分和分类专家。
你的职责是：
1. 准确理解AI相关新闻的技术内容和行业影响
2. 根据新闻的重要性、突破性、影响范围进行0-100分评分
3. 将新闻分类到8大类别之一
4. 识别关键信息、实体和技术术语
5. 返回结构化的JSON数据

你的评分标准必须一致，考虑以下维度：
- 创新性：是否有技术创新？
- 影响力：受众范围和影响深度？
- 时效性：是否是最新发展？
- 相关性：与当前AI趋势的关系？
- 实用性：是否有实际应用价值？"""
