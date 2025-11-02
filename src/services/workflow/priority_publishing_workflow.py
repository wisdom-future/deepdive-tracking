"""
优先级发布工作流

根据配置的优先级，按照 Email -> GitHub -> WeChat 的顺序发布文章。
支持灵活的优先级配置、时间限制、评分过滤等。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.services.channels.wechat import WeChatPublisher
from src.services.channels.github import GitHubPublisher
from src.services.channels.email import EmailPublisher
from src.models import (
    ContentReview,
    PublishedContent,
    ProcessedNews,
    RawNews,
    WeChatMediaCache,
    PublishPriority,
)

logger = logging.getLogger(__name__)


class PriorityPublishingWorkflow:
    """
    优先级发布工作流

    支持按优先级顺序发布到多个渠道，每个渠道有独立的配置。
    """

    def __init__(self, db_session: Session):
        """
        初始化优先级发布工作流

        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db_session = db_session
        self.logger = logger
        self.publishers = {}
        self.priorities = {}

    def configure_channels(
        self,
        wechat_config: Optional[Dict] = None,
        github_config: Optional[Dict] = None,
        email_config: Optional[Dict] = None,
    ):
        """配置所有渠道"""
        if wechat_config:
            self.publishers["wechat"] = WeChatPublisher(
                app_id=wechat_config.get("app_id"),
                app_secret=wechat_config.get("app_secret"),
            )

        if github_config:
            self.publishers["github"] = GitHubPublisher(
                github_token=github_config.get("token"),
                github_repo=github_config.get("repo"),
                github_username=github_config.get("username"),
                local_repo_path=github_config.get("local_path"),
            )

        if email_config:
            self.publishers["email"] = EmailPublisher(
                smtp_host=email_config.get("smtp_host"),
                smtp_port=email_config.get("smtp_port", 587),
                smtp_user=email_config.get("smtp_user"),
                smtp_password=email_config.get("smtp_password"),
                from_email=email_config.get("from_email"),
                from_name=email_config.get("from_name", "DeepDive Tracking"),
                email_list=email_config.get("email_list"),
            )

        self.logger.info(f"✓ 配置了 {len(self.publishers)} 个发布渠道")

    def _load_channel_priorities(self) -> List[tuple]:
        """从数据库加载渠道优先级配置"""
        priorities = (
            self.db_session.query(PublishPriority)
            .filter(PublishPriority.is_enabled == True)
            .order_by(PublishPriority.priority.desc())  # 优先级高的先发布
            .all()
        )

        return [(p.channel, p) for p in priorities]

    def _get_approved_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取已批准但未发布的文章"""
        self.logger.info("查询已批准的文章...")

        approved_reviews = self.db_session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).all()

        if not approved_reviews:
            self.logger.info("没有已批准的文章")
            return []

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
                "score": processed_news.score,
                "category": processed_news.category,
                "review_id": review.id,
            }

            articles.append(article)

            if len(articles) >= limit:
                break

        self.logger.info(f"找到 {len(articles)} 篇待发布的文章")
        return articles

    def _filter_articles(
        self,
        articles: List[Dict[str, Any]],
        priority_config: PublishPriority,
    ) -> List[Dict[str, Any]]:
        """根据优先级配置过滤文章"""
        filtered = []

        for article in articles:
            # 检查最低评分
            if article["score"] < priority_config.min_score:
                self.logger.debug(
                    f"文章 {article['title'][:30]} 评分过低"
                    f" ({article['score']} < {priority_config.min_score})"
                )
                continue

            # 检查分类
            if priority_config.allowed_categories:
                if article["category"] not in priority_config.allowed_categories:
                    self.logger.debug(
                        f"文章分类 {article['category']} 不在允许列表中"
                    )
                    continue

            # 检查阻止的关键词
            if priority_config.blocked_keywords:
                title_lower = article["title"].lower()
                if any(kw.lower() in title_lower for kw in priority_config.blocked_keywords):
                    self.logger.debug(f"文章标题含有阻止关键词")
                    continue

            filtered.append(article)

        return filtered

    async def execute(
        self,
        article_limit: int = 10,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        执行优先级发布工作流

        Args:
            article_limit: 最多发布的文章数
            dry_run: 是否为试运行模式（不实际发布）

        Returns:
            {
                "success": bool,
                "channels_executed": [str],
                "articles_by_channel": {...},
                "total_published": int,
                "summary": str
            }
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("启动优先级发布工作流")
            self.logger.info("=" * 80)

            # 加载优先级配置
            channel_priorities = self._load_channel_priorities()

            if not channel_priorities:
                self.logger.warning("没有配置任何发布优先级")
                return {
                    "success": False,
                    "error": "No channel priorities configured",
                    "channels_executed": [],
                }

            self.logger.info(f"发布优先级顺序:")
            for channel, config in channel_priorities:
                status = "✅" if self.publishers.get(channel) else "❌"
                print(f"  {status} {channel.upper()}: 优先级 {config.priority}/10")

            # 获取待发布文章
            articles = self._get_approved_articles(limit=article_limit)

            if not articles:
                return {
                    "success": True,
                    "message": "No articles to publish",
                    "channels_executed": [],
                    "total_published": 0,
                }

            # 按优先级发布到各渠道
            results = {
                "success": True,
                "channels_executed": [],
                "articles_by_channel": {},
                "total_published": 0,
            }

            for channel, priority_config in channel_priorities:
                if channel not in self.publishers:
                    self.logger.warning(f"{channel.upper()} 发布器未配置，跳过")
                    continue

                if not priority_config.auto_publish:
                    self.logger.info(f"{channel.upper()} 自动发布已禁用，跳过")
                    continue

                if not priority_config.is_time_to_publish():
                    self.logger.warning(
                        f"{channel.upper()} 不在发布时间范围内 "
                        f"({priority_config.publish_time_start}-{priority_config.publish_time_end})"
                    )
                    continue

                self.logger.info(f"\n[优先级 {priority_config.priority}] 发布到 {channel.upper()}")

                # 过滤文章
                filtered_articles = self._filter_articles(articles, priority_config)

                if not filtered_articles:
                    self.logger.warning(f"没有符合 {channel.upper()} 条件的文章")
                    continue

                try:
                    # 执行发布
                    channel_result = await self._publish_to_channel(
                        channel=channel,
                        articles=filtered_articles[: priority_config.batch_size],
                        priority_config=priority_config,
                        dry_run=dry_run,
                    )

                    if channel_result.get("success"):
                        results["channels_executed"].append(channel)
                        results["articles_by_channel"][channel] = channel_result
                        results["total_published"] += channel_result.get("published_count", 0)

                        # 更新优先级配置统计
                        priority_config.total_published += channel_result.get("published_count", 0)
                        priority_config.last_publish_at = datetime.utcnow()
                        self.db_session.commit()

                        self.logger.info(
                            f"✓ {channel.upper()} 发布成功: {channel_result.get('published_count')} 篇"
                        )
                    else:
                        self.logger.error(
                            f"✗ {channel.upper()} 发布失败: {channel_result.get('error')}"
                        )

                except Exception as e:
                    self.logger.error(f"✗ {channel.upper()} 发布出错: {str(e)}")
                    results["success"] = False

            self.logger.info("\n" + "=" * 80)
            self.logger.info("优先级发布工作流完成")
            self.logger.info("=" * 80)
            self.logger.info(f"总共发布到 {len(results['channels_executed'])} 个渠道")
            self.logger.info(f"总发布数: {results['total_published']} 篇")

            return results

        except Exception as e:
            self.logger.error(f"✗ 工作流执行失败: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "channels_executed": [],
            }

    async def _publish_to_channel(
        self,
        channel: str,
        articles: List[Dict[str, Any]],
        priority_config: PublishPriority,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """发布到单个渠道"""
        publisher = self.publishers.get(channel)
        if not publisher:
            return {"success": False, "error": f"Publisher not configured for {channel}"}

        try:
            if channel == "email":
                return await self._publish_email(publisher, articles, dry_run)
            elif channel == "github":
                return await self._publish_github(publisher, articles, dry_run)
            elif channel == "wechat":
                return await self._publish_wechat(publisher, articles, dry_run)
            else:
                return {"success": False, "error": f"Unknown channel: {channel}"}

        except Exception as e:
            self.logger.error(f"发布到 {channel} 失败: {str(e)}")
            return {"success": False, "error": str(e), "published_count": 0}

    async def _publish_email(
        self,
        publisher: EmailPublisher,
        articles: List[Dict[str, Any]],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """发布到 Email"""
        if dry_run:
            return {
                "success": True,
                "published_count": len(articles),
                "message": "Dry run mode - no emails sent",
            }

        result = await publisher.publish_batch_articles(
            articles=articles, batch_name=datetime.now().strftime("%Y-%m-%d")
        )

        # 保存发布记录
        for article in articles:
            try:
                self._save_published_content(
                    processed_news_id=article["id"],
                    review_id=article["review_id"],
                    channel="email",
                    channel_url="",
                    channel_id="",
                )
            except Exception as e:
                self.logger.error(f"保存 Email 发布记录失败: {str(e)}")

        return {
            "success": result.get("success", False),
            "published_count": result.get("sent_emails", 0),
            "failed_count": len(result.get("failed_emails", [])),
        }

    async def _publish_github(
        self,
        publisher: GitHubPublisher,
        articles: List[Dict[str, Any]],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """发布到 GitHub"""
        if dry_run:
            return {
                "success": True,
                "published_count": len(articles),
                "message": "Dry run mode - no GitHub commits made",
            }

        result = await publisher.publish_batch_articles(
            articles=articles, batch_name=datetime.now().strftime("%Y%m%d")
        )

        # 保存发布记录
        for article in articles:
            try:
                self._save_published_content(
                    processed_news_id=article["id"],
                    review_id=article["review_id"],
                    channel="github",
                    channel_url=result.get("batch_url", ""),
                    channel_id="",
                )
            except Exception as e:
                self.logger.error(f"保存 GitHub 发布记录失败: {str(e)}")

        return {
            "success": result.get("success", False),
            "published_count": result.get("published_count", 0),
            "failed_count": result.get("failed_count", 0),
        }

    async def _publish_wechat(
        self,
        publisher: WeChatPublisher,
        articles: List[Dict[str, Any]],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """发布到 WeChat"""
        if dry_run:
            return {
                "success": True,
                "published_count": len(articles),
                "message": "Dry run mode - no WeChat messages sent",
            }

        result = await publisher.publish_batch_articles(
            articles=articles, is_to_all=True
        )

        # 保存发布记录
        for article in articles:
            try:
                self._save_published_content(
                    processed_news_id=article["id"],
                    review_id=article["review_id"],
                    channel="wechat",
                    channel_url=f"https://mp.weixin.qq.com/?v={result.get('media_id', '')}",
                    channel_id=result.get("msg_id", ""),
                )
            except Exception as e:
                self.logger.error(f"保存 WeChat 发布记录失败: {str(e)}")

        return {
            "success": result.get("success", False),
            "published_count": result.get("published_count", 0),
            "failed_count": result.get("failed_count", 0),
        }

    def _save_published_content(
        self,
        processed_news_id: int,
        review_id: int,
        channel: str,
        channel_url: str,
        channel_id: str,
    ):
        """保存发布内容记录"""
        processed = self.db_session.query(ProcessedNews).filter(
            ProcessedNews.id == processed_news_id
        ).first()

        if not processed:
            return

        raw_news_id = processed.raw_news_id

        published = PublishedContent(
            processed_news_id=processed_news_id,
            content_review_id=review_id,
            raw_news_id=raw_news_id,
            publish_status="published",
            published_at=datetime.utcnow(),
            published_by=f"system_{channel}",
        )

        if channel == "wechat":
            published.wechat_msg_id = channel_id
            published.wechat_url = channel_url
        elif channel == "github":
            published.wechat_url = channel_url  # 临时字段
        elif channel == "email":
            pass

        self.db_session.add(published)
        self.db_session.commit()
