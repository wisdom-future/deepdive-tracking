"""HTML Content Cleaner - 将 HTML 内容转换为纯文本

功能：
  - 移除 HTML 标签
  - 处理 HTML 实体 (&nbsp; 等)
  - 提取有意义的文本
  - 清理多余空白
  - 保留段落结构
"""

import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HTMLCleaner:
    """HTML 内容清理器"""

    # 需要完全移除的标签 (脚本、样式等)
    REMOVE_TAGS = {
        'script', 'style', 'head', 'meta', 'link',
        'iframe', 'noscript', 'object', 'embed'
    }

    # 块级标签，需要在前后加换行
    BLOCK_TAGS = {
        'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'pre', 'hr', 'ul', 'ol', 'li',
        'section', 'article', 'aside', 'header', 'footer',
        'main', 'nav', 'figure', 'figcaption'
    }

    @staticmethod
    def clean(html_content: Optional[str]) -> str:
        """清理 HTML 内容转为纯文本

        Args:
            html_content: 包含 HTML 的字符串

        Returns:
            清理后的纯文本内容
        """
        if not html_content:
            return ""

        # 1. 处理空字符串
        if not isinstance(html_content, str):
            return ""

        # 2. 移除注释
        text = HTMLCleaner._remove_comments(html_content)

        # 3. 移除脚本和样式标签内容
        text = HTMLCleaner._remove_tag_content(text, 'script')
        text = HTMLCleaner._remove_tag_content(text, 'style')
        text = HTMLCleaner._remove_tag_content(text, 'head')

        # 4. 在块级标签前后添加换行
        for tag in HTMLCleaner.BLOCK_TAGS:
            text = re.sub(
                f'<{tag}[^>]*>',
                '\n',
                text,
                flags=re.IGNORECASE
            )
            text = re.sub(
                f'</{tag}>',
                '\n',
                text,
                flags=re.IGNORECASE
            )

        # 5. 移除所有 HTML 标签
        text = HTMLCleaner._remove_all_tags(text)

        # 6. 处理 HTML 实体
        text = html.unescape(text)

        # 7. 移除额外空白
        text = HTMLCleaner._clean_whitespace(text)

        return text.strip()

    @staticmethod
    def _remove_comments(text: str) -> str:
        """移除 HTML 注释"""
        return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    @staticmethod
    def _remove_tag_content(text: str, tag: str) -> str:
        """移除特定标签及其内容"""
        pattern = f'<{tag}[^>]*>.*?</{tag}>'
        return re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    @staticmethod
    def _remove_all_tags(text: str) -> str:
        """移除所有 HTML 标签"""
        # 移除开始标签
        text = re.sub(r'<[^>]+>', '', text)
        return text

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """清理多余空白"""
        # 移除多余空格
        text = re.sub(r'[ \t]+', ' ', text)

        # 移除多余换行 (保留最多 2 个连续换行)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # 移除行首行尾空白
        lines = text.split('\n')
        lines = [line.strip() for line in lines]

        # 移除空行
        lines = [line for line in lines if line]

        return '\n'.join(lines)

    @staticmethod
    def extract_plain_text(html_content: Optional[str]) -> str:
        """快速方法：清理 HTML 到纯文本

        这是 clean() 的别名，为了向后兼容
        """
        return HTMLCleaner.clean(html_content)

    @staticmethod
    def get_first_paragraph(text: str, max_length: int = 200) -> str:
        """提取第一个有意义的段落

        Args:
            text: 纯文本内容
            max_length: 最大长度

        Returns:
            第一段落（截断到 max_length）
        """
        if not text:
            return ""

        # 分割段落
        paragraphs = text.split('\n\n')

        # 找到第一个非空段落
        for paragraph in paragraphs:
            para = paragraph.strip()
            if para and len(para) > 10:  # 至少 10 个字符
                if len(para) > max_length:
                    return para[:max_length] + "..."
                return para

        return ""


def clean_html_content(html_content: Optional[str]) -> str:
    """方便函数：清理 HTML 内容

    Usage:
        from src.utils.html_cleaner import clean_html_content
        text = clean_html_content("<p>Hello <b>World</b></p>")
    """
    return HTMLCleaner.clean(html_content)
