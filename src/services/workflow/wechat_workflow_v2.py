"""
WeChat V2 发布工作流 - 使用永久素材 API

这是第二代 WeChat 发布工作流，使用官方支持的永久素材 API 和群发接口。

Features:
- 使用官方支持的 API（不会被弃用）
- 支持单篇和批量发布
- 自动上传媒体并缓存
- 完整的错误处理和重试机制
- 发布统计和监控
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.services.channels.wechat import WeChatPublisher
from src.models import (
    ContentReview,
    PublishedContent,
    ProcessedNews,
    RawNews,
    WeChatMediaCache
)

logger = logging.getLogger(__name__)


class WeChatPublishingWorkflowV2:
    """WeChat V2 发布工作流 - 使用永久素材 API"""

    def __init__(
        self,
        db_session: Session,
        wechat_app_id: str,
        wechat_app_secret: str
    ):
        """
        初始化 WeChat V2 发布工作流

        Args:
            db_session: SQLAlchemy 数据库会话
            wechat_app_id: WeChat 公众号 App ID
            wechat_app_secret: WeChat 公众号 App Secret
        """
        self.db_session = db_session
        self.wechat_publisher = WeChatPublisher(wechat_app_id, wechat_app_secret)
        self.logger = logger

    def _get_approved_articles(self) -> List[Dict[str, Any]]:
        """获取已批准但未发布的文章"""

        self.logger.info("查询已批准的文章...")

        # 获取已批准的审核记录
        approved_reviews = self.db_session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).all()

        if not approved_reviews:
            self.logger.info("没有已批准的文章")
            return []

        self.logger.info(f"找到 {len(approved_reviews)} 篇已批准的文章")

        articles = []
        for review in approved_reviews:
            # 检查是否已发布
            existing_pub = self.db_session.query(PublishedContent).filter(
                PublishedContent.processed_news_id == review.processed_news_id
            ).first()

            if existing_pub:
                self.logger.debug(f"文章已发布，跳过: {review.processed_news_id}")
                continue

            # 获取处理过的文章
            processed_news = self.db_session.query(ProcessedNews).filter(
                ProcessedNews.id == review.processed_news_id
            ).first()

            if not processed_news:
                self.logger.warning(f"找不到处理后的文章: {review.processed_news_id}")
                continue

            # 获取原始文章
            raw_news = self.db_session.query(RawNews).filter(
                RawNews.id == processed_news.raw_news_id
            ).first()

            if not raw_news:
                self.logger.warning(f"找不到原始文章: {processed_news.raw_news_id}")
                continue

            article = {
                "id": processed_news.id,
                "title": raw_news.title,
                "content": raw_news.content or processed_news.summary_pro,
                "summary": processed_news.summary_pro,
                "author": raw_news.author or "DeepDive",
                "source_url": raw_news.url,
                "cover_image_url": None,  # RawNews doesn't have image_url
                "score": processed_news.score,
                "category": processed_news.category,
                "review_id": review.id
            }

            articles.append(article)

        self.logger.info(f"找到 {len(articles)} 篇待发布的文章")
        return articles

    async def execute(self, batch_size: int = 5) -> Dict[str, Any]:
        """
        执行 WeChat V2 发布工作流

        工作流步骤：
        1. 获取已批准的文章
        2. 准备文章数据
        3. 使用 V2 API 发布
        4. 记录发布结果
        5. 生成统计

        Args:
            batch_size: 每次发布的文章数（最多 8 篇）

        Returns:
            {
                "success": bool,
                "published_count": int,
                "failed_count": int,
                "articles": [...],
                "stats": {...},
                "error": str (if failed)
            }
        """
        try:
            self.logger.info("="*80)
            self.logger.info("启动 WeChat V2 发布工作流")
            self.logger.info("="*80)

            # Step 1: 获取待发布文章
            articles = self._get_approved_articles()

            if not articles:
                return {
                    "success": True,
                    "published_count": 0,
                    "failed_count": 0,
                    "articles": [],
                    "message": "No articles to publish"
                }

            # Step 2-3: 批量发布
            published_count = 0
            failed_count = 0
            published_articles = []
            failed_articles = []

            for idx in range(0, len(articles), batch_size):
                batch = articles[idx:idx + batch_size]
                batch_num = (idx // batch_size) + 1
                total_batches = (len(articles) + batch_size - 1) // batch_size

                self.logger.info(f"\n[批次 {batch_num}/{total_batches}] 发布 {len(batch)} 篇文章...")

                try:
                    # 使用 V2 API 批量发布
                    result = await self.wechat_publisher.publish_batch_articles(
                        articles=batch,
                        is_to_all=True
                    )

                    if result["success"]:
                        media_id = result.get("media_id")
                        msg_id = result.get("msg_id")

                        # 记录发布结果
                        for article in batch:
                            try:
                                self._save_published_content(
                                    processed_news_id=article["id"],
                                    review_id=article["review_id"],
                                    media_id=media_id,
                                    msg_id=msg_id,
                                    channel="wechat"
                                )

                                published_count += 1
                                published_articles.append({
                                    "title": article["title"],
                                    "media_id": media_id,
                                    "msg_id": msg_id
                                })

                            except Exception as e:
                                self.logger.error(f"保存发布结果失败: {str(e)}")
                                failed_count += 1
                                failed_articles.append(article["title"])

                        self.logger.info(f"✓ 批次发布成功: {len(batch)} 篇")

                    else:
                        error = result.get("error", "Unknown error")
                        self.logger.error(f"✗ 批次发布失败: {error}")
                        failed_count += len(batch)
                        failed_articles.extend([a["title"] for a in batch])

                except Exception as e:
                    self.logger.error(f"✗ 发布批次出错: {str(e)}")
                    failed_count += len(batch)
                    failed_articles.extend([a["title"] for a in batch])

            # Step 4: 生成统计
            stats = self._generate_statistics()

            self.logger.info("\n" + "="*80)
            self.logger.info("发布工作流完成")
            self.logger.info("="*80)
            self.logger.info(f"成功: {published_count} 篇")
            self.logger.info(f"失败: {failed_count} 篇")

            return {
                "success": failed_count == 0,
                "published_count": published_count,
                "failed_count": failed_count,
                "articles": published_articles,
                "failed_articles": failed_articles,
                "stats": stats,
                "message": f"Published {published_count} articles, {failed_count} failed"
            }

        except Exception as e:
            self.logger.error(f"✗ 工作流执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "published_count": 0,
                "failed_count": 0,
                "error": str(e),
                "message": f"Workflow execution failed: {str(e)}"
            }

    def _get_raw_news_id(self, processed_news_id: int) -> int:
        """Get raw_news_id from processed_news_id."""
        processed = self.db_session.query(ProcessedNews).filter(
            ProcessedNews.id == processed_news_id
        ).first()
        return processed.raw_news_id if processed else 0

    def _save_published_content(
        self,
        processed_news_id: int,
        review_id: int,
        media_id: str,
        msg_id: str,
        channel: str = "wechat"
    ) -> PublishedContent:
        """
        保存发布内容记录

        Args:
            processed_news_id: 处理文章 ID
            review_id: 审核记录 ID
            media_id: WeChat 媒体 ID
            msg_id: WeChat 消息 ID
            channel: 发布渠道

        Returns:
            PublishedContent 对象
        """
        published = PublishedContent(
            processed_news_id=processed_news_id,
            content_review_id=review_id,
            raw_news_id=self._get_raw_news_id(processed_news_id),
            publish_status="published",
            published_at=datetime.utcnow(),
            wechat_msg_id=msg_id,
            wechat_url=f"https://mp.weixin.qq.com/?v={media_id}",
            published_by="system_wechat_v2"
        )

        self.db_session.add(published)
        self.db_session.commit()

        # 同时保存到媒体缓存
        try:
            media_cache = WeChatMediaCache(
                media_id=media_id,
                type="news",
                content_id=published.id,
                upload_time=datetime.utcnow()
            )
            self.db_session.add(media_cache)
            self.db_session.commit()
        except Exception as e:
            self.logger.warning(f"保存媒体缓存失败: {str(e)}")

        return published

    def _generate_statistics(self) -> Dict[str, Any]:
        """生成发布统计"""

        total = self.db_session.query(PublishedContent).count()
        published = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status == "published"
        ).count()
        failed = self.db_session.query(PublishedContent).filter(
            PublishedContent.publish_status == "failed"
        ).count()

        return {
            "total_published": total,
            "success_count": published,
            "failed_count": failed,
            "success_rate": (published / total * 100) if total > 0 else 0
        }


# 为了保持向后兼容，提供一个同步包装函数
def execute_workflow(
    db_session: Session,
    wechat_app_id: str,
    wechat_app_secret: str
) -> Dict[str, Any]:
    """
    同步执行 WeChat V2 发布工作流

    这是一个便利函数，用于从同步代码中调用异步工作流。

    Args:
        db_session: SQLAlchemy 数据库会话
        wechat_app_id: WeChat 公众号 App ID
        wechat_app_secret: WeChat 公众号 App Secret

    Returns:
        工作流执行结果
    """
    workflow = WeChatPublishingWorkflowV2(db_session, wechat_app_id, wechat_app_secret)

    # 创建事件循环来运行异步函数
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(workflow.execute())
