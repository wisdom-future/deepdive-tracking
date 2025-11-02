"""
多渠道发布工作流 - 同时支持 WeChat, GitHub, Email

这是统一的发布工作流，可以同时将文章发布到多个渠道。

支持的渠道：
- WeChat: 使用永久素材API + 群发接口
- GitHub: 生成HTML并上传到GitHub仓库
- Email: 发送HTML邮件到邮件列表
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
    WeChatMediaCache
)

logger = logging.getLogger(__name__)


class MultiChannelPublishingWorkflow:
    """多渠道发布工作流"""

    def __init__(self, db_session: Session):
        """
        初始化多渠道发布工作流

        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db_session = db_session
        self.logger = logger
        self.wechat_publisher = None
        self.github_publisher = None
        self.email_publisher = None

    def configure_wechat(self, app_id: str, app_secret: str):
        """配置WeChat发布器"""
        self.wechat_publisher = WeChatPublisher(app_id, app_secret)
        self.logger.info("✓ WeChat发布器已配置")

    def configure_github(self, github_token: str, github_repo: str, github_username: str, local_repo_path: str):
        """配置GitHub发布器"""
        self.github_publisher = GitHubPublisher(
            github_token=github_token,
            github_repo=github_repo,
            github_username=github_username,
            local_repo_path=local_repo_path
        )
        self.logger.info("✓ GitHub发布器已配置")

    def configure_email(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "DeepDive Tracking",
        email_list: Optional[List[str]] = None
    ):
        """配置Email发布器"""
        self.email_publisher = EmailPublisher(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name,
            email_list=email_list or ["hello.junjie.duan@gmail.com"]
        )
        self.logger.info("✓ Email发布器已配置")

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
                "review_id": review.id
            }

            articles.append(article)

            if len(articles) >= limit:
                break

        self.logger.info(f"找到 {len(articles)} 篇待发布的文章")
        return articles

    async def execute(
        self,
        channels: Optional[List[str]] = None,
        batch_size: int = 5,
        article_limit: int = 10
    ) -> Dict[str, Any]:
        """
        执行多渠道发布工作流

        Args:
            channels: 要发布的渠道列表 (wechat, github, email)
            batch_size: 每次发布的文章数
            article_limit: 最多发布的文章数

        Returns:
            {
                "success": bool,
                "wechat": {...},
                "github": {...},
                "email": {...},
                "summary": {...}
            }
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("启动多渠道发布工作流")
            self.logger.info("=" * 80)

            channels = channels or ["wechat", "github", "email"]
            results = {
                "success": True,
                "wechat": None,
                "github": None,
                "email": None,
                "summary": {
                    "total_articles": 0,
                    "published_channels": []
                }
            }

            # 获取待发布文章
            articles = self._get_approved_articles(limit=article_limit)

            if not articles:
                return {
                    "success": True,
                    "message": "No articles to publish",
                    "summary": {
                        "total_articles": 0,
                        "published_channels": []
                    }
                }

            results["summary"]["total_articles"] = len(articles)

            # WeChat发布
            if "wechat" in channels and self.wechat_publisher:
                self.logger.info("\n[渠道1] 发布到WeChat...")
                try:
                    wechat_result = await self._publish_to_wechat(articles, batch_size)
                    results["wechat"] = wechat_result
                    if wechat_result.get("success"):
                        results["summary"]["published_channels"].append("wechat")
                    else:
                        results["success"] = False
                except Exception as e:
                    self.logger.error(f"✗ WeChat发布失败: {str(e)}")
                    results["wechat"] = {"success": False, "error": str(e)}
                    results["success"] = False

            # GitHub发布
            if "github" in channels and self.github_publisher:
                self.logger.info("\n[渠道2] 发布到GitHub...")
                try:
                    github_result = await self._publish_to_github(articles, batch_size)
                    results["github"] = github_result
                    if github_result.get("success"):
                        results["summary"]["published_channels"].append("github")
                    else:
                        results["success"] = False
                except Exception as e:
                    self.logger.error(f"✗ GitHub发布失败: {str(e)}")
                    results["github"] = {"success": False, "error": str(e)}
                    results["success"] = False

            # Email发布
            if "email" in channels and self.email_publisher:
                self.logger.info("\n[渠道3] 发布到Email...")
                try:
                    email_result = await self._publish_to_email(articles)
                    results["email"] = email_result
                    if email_result.get("success"):
                        results["summary"]["published_channels"].append("email")
                    else:
                        results["success"] = False
                except Exception as e:
                    self.logger.error(f"✗ Email发布失败: {str(e)}")
                    results["email"] = {"success": False, "error": str(e)}
                    results["success"] = False

            self.logger.info("\n" + "=" * 80)
            self.logger.info("多渠道发布工作流完成")
            self.logger.info("=" * 80)
            self.logger.info(f"已发布到: {', '.join(results['summary']['published_channels']) or '无'}")

            return results

        except Exception as e:
            self.logger.error(f"✗ 工作流执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "total_articles": 0,
                    "published_channels": []
                }
            }

    async def _publish_to_wechat(self, articles: List[Dict[str, Any]], batch_size: int) -> Dict[str, Any]:
        """发布到WeChat"""
        published_count = 0
        failed_count = 0
        published_articles = []
        failed_articles = []

        for idx in range(0, len(articles), batch_size):
            batch = articles[idx:idx + batch_size]
            batch_num = (idx // batch_size) + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size

            self.logger.info(f"  [批次 {batch_num}/{total_batches}] 发布 {len(batch)} 篇文章...")

            try:
                result = await self.wechat_publisher.publish_batch_articles(
                    articles=batch,
                    is_to_all=True
                )

                if result.get("success"):
                    for article in batch:
                        try:
                            self._save_published_content(
                                processed_news_id=article["id"],
                                review_id=article["review_id"],
                                channel="wechat",
                                channel_url=f"https://mp.weixin.qq.com/?v={result.get('media_id', '')}",
                                channel_id=result.get("msg_id", "")
                            )
                            published_count += 1
                            published_articles.append(article["title"])
                        except Exception as e:
                            failed_count += 1
                            failed_articles.append(article["title"])
                            self.logger.error(f"保存发布结果失败: {str(e)}")

                    self.logger.info(f"  ✓ 批次发布成功: {len(batch)} 篇")
                else:
                    failed_count += len(batch)
                    failed_articles.extend([a["title"] for a in batch])
                    self.logger.error(f"  ✗ 批次发布失败: {result.get('error', 'Unknown error')}")

            except Exception as e:
                failed_count += len(batch)
                failed_articles.extend([a["title"] for a in batch])
                self.logger.error(f"  ✗ 发布批次出错: {str(e)}")

        return {
            "success": failed_count == 0,
            "published_count": published_count,
            "failed_count": failed_count,
            "published_articles": published_articles[:5],  # 只返回前5个
            "failed_articles": failed_articles
        }

    async def _publish_to_github(self, articles: List[Dict[str, Any]], batch_size: int) -> Dict[str, Any]:
        """发布到GitHub"""
        try:
            result = await self.github_publisher.publish_batch_articles(
                articles=articles,
                batch_name=datetime.now().strftime("%Y%m%d")
            )

            # 保存发布记录
            for article in articles[:len(articles)]:
                try:
                    self._save_published_content(
                        processed_news_id=article["id"],
                        review_id=article["review_id"],
                        channel="github",
                        channel_url=result.get("batch_url", ""),
                        channel_id=""
                    )
                except Exception as e:
                    self.logger.error(f"保存GitHub发布结果失败: {str(e)}")

            self.logger.info(f"✓ GitHub发布完成: {result.get('published_count', 0)} 篇成功, {result.get('failed_count', 0)} 篇失败")
            return result

        except Exception as e:
            self.logger.error(f"✗ GitHub发布失败: {str(e)}")
            return {
                "success": False,
                "published_count": 0,
                "failed_count": len(articles),
                "error": str(e)
            }

    async def _publish_to_email(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """发布到Email"""
        try:
            result = await self.email_publisher.publish_batch_articles(
                articles=articles,
                batch_name=datetime.now().strftime("%Y-%m-%d")
            )

            # 保存发布记录
            for article in articles[:result.get("sent_emails", 0)]:
                try:
                    self._save_published_content(
                        processed_news_id=article["id"],
                        review_id=article["review_id"],
                        channel="email",
                        channel_url="",
                        channel_id=""
                    )
                except Exception as e:
                    self.logger.error(f"保存Email发布结果失败: {str(e)}")

            self.logger.info(f"✓ Email发布完成: 已发送到 {result.get('sent_emails', 0)} 个邮箱")
            return result

        except Exception as e:
            self.logger.error(f"✗ Email发布失败: {str(e)}")
            return {
                "success": False,
                "sent_emails": 0,
                "failed_emails": [],
                "error": str(e)
            }

    def _save_published_content(
        self,
        processed_news_id: int,
        review_id: int,
        channel: str,
        channel_url: str,
        channel_id: str
    ):
        """保存发布内容记录"""
        try:
            # 获取raw_news_id
            processed = self.db_session.query(ProcessedNews).filter(
                ProcessedNews.id == processed_news_id
            ).first()

            if not processed:
                return

            raw_news_id = processed.raw_news_id

            # 创建发布记录
            published = PublishedContent(
                processed_news_id=processed_news_id,
                content_review_id=review_id,
                raw_news_id=raw_news_id,
                publish_status="published",
                published_at=datetime.utcnow(),
                published_by=f"system_{channel}"
            )

            # 设置渠道特定的信息
            if channel == "wechat":
                published.wechat_msg_id = channel_id
                published.wechat_url = channel_url
            elif channel == "github":
                published.wechat_url = channel_url  # 临时使用这个字段
            elif channel == "email":
                pass  # Email不需要特定的URL

            self.db_session.add(published)
            self.db_session.commit()

        except Exception as e:
            self.logger.error(f"保存发布内容失败: {str(e)}")
            raise
