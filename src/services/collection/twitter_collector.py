"""Twitter/X API collector implementation."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

import tweepy
from pytz import UTC

try:
    from langdetect import detect, LangDetectException
except ImportError:
    # Fallback if langdetect not installed
    detect = None
    LangDetectException = Exception

from src.models import DataSource, RawNews
from src.services.collection.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """Collector for Twitter/X tweets."""

    def __init__(self, data_source: DataSource):
        """Initialize Twitter collector with API credentials.

        Args:
            data_source: DataSource model instance with Twitter configuration

        Raises:
            ValueError: If required Twitter API credentials are not configured
        """
        super().__init__(data_source)

        # Get Twitter API credentials from environment or data_source config
        bearer_token = (
            data_source.auth_token
            or os.getenv("TWITTER_BEARER_TOKEN")
        )

        if not bearer_token:
            raise ValueError(
                "Twitter bearer token not configured. "
                "Set TWITTER_BEARER_TOKEN environment variable or "
                "configure auth_token in data_source"
            )

        # Initialize Tweepy client with API v2
        self.client = tweepy.Client(bearer_token=bearer_token)

        # Twitter API rate limits for Free tier
        # User timeline endpoint: 50 requests / 15 minutes
        self.max_results_per_request = 100  # Max allowed per request
        self.max_requests = 50  # Free tier limit per 15 minutes
        self.request_delay = 0.5  # Delay between requests (seconds)

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect tweets from a Twitter user timeline.

        Returns:
            List of tweet dictionaries with standardized fields:
            - title: Tweet text (truncated to 200 chars for title)
            - url: Tweet URL
            - content: Full tweet text
            - author: Twitter username
            - published_at: Tweet creation time
            - language: Detected language
            - html_content: None (not applicable for tweets)
        """
        if not self.data_source.url:
            raise ValueError(
                f"Twitter username not configured for {self.data_source.name}"
            )

        try:
            # Extract username from URL (format: https://twitter.com/username or just @username)
            username = self._extract_username(self.data_source.url)

            tweets = await self._fetch_user_timeline(username)
            self.log_collection_attempt(
                True, f"Collected {len(tweets)} tweets from @{username}"
            )
            return tweets

        except Exception as e:
            self.log_collection_attempt(False, str(e), e)
            raise

    async def _fetch_user_timeline(self, username: str) -> List[Dict[str, Any]]:
        """Fetch tweets from user timeline using Tweepy.

        Args:
            username: Twitter username (without @)

        Returns:
            List of parsed tweet dictionaries
        """
        try:
            # Look up user to get user ID
            user = await asyncio.to_thread(
                self.client.get_user, username=username
            )

            if not user.data:
                raise ValueError(f"User not found: @{username}")

            user_id = user.data.id
            self.logger.info(f"Found user {username} (ID: {user_id})")

            # Fetch user's recent tweets
            # Free tier: 450 tweets per 15-minute window, max 100 per request
            tweets_response = await asyncio.to_thread(
                self.client.get_users_tweets,
                id=user_id,
                max_results=self.max_results_per_request,
                tweet_fields=[
                    "created_at",
                    "author_id",
                    "public_metrics",
                    "lang",
                ],
                expansions=["author_id"],
                user_fields=["username"],
            )

            if not tweets_response.data:
                self.logger.warning(f"No tweets found for user {username}")
                return []

            # Parse tweets into standardized format
            articles = []
            users_dict = {u.id: u.username for u in tweets_response.includes["users"]}

            for tweet in tweets_response.data:
                try:
                    article = self._parse_tweet(
                        tweet,
                        username=users_dict.get(tweet.author_id, username),
                    )
                    articles.append(article)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse tweet {tweet.id}: {e}"
                    )
                    continue

            return articles

        except tweepy.TweepyException as e:
            self.logger.error(
                f"Twitter API error for user {username}: {e}",
                extra={"source_id": self.data_source.id},
            )
            raise

    def _parse_tweet(self, tweet: Any, username: str) -> Dict[str, Any]:
        """Parse a tweet into standardized format.

        Args:
            tweet: Tweepy Tweet object
            username: Tweet author's username

        Returns:
            Dictionary with standardized news fields
        """
        # Generate tweet URL
        tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"

        # Extract text (tweets can be up to 280 chars)
        tweet_text = tweet.text

        # Detect language (use tweet's lang field if available)
        language = self._detect_language(tweet_text)

        # Create article dict matching BaseCollector format
        article = {
            "title": tweet_text[:200] if len(tweet_text) > 200 else tweet_text,
            "url": tweet_url,
            "content": tweet_text,
            "author": username,
            "published_at": tweet.created_at,
            "language": language or "en",
            "html_content": None,
        }

        return article

    @staticmethod
    def _extract_username(url_or_handle: str) -> str:
        """Extract username from URL or handle format.

        Args:
            url_or_handle: URL (https://twitter.com/username) or @username

        Returns:
            Username without @ symbol
        """
        url_or_handle = url_or_handle.strip()

        # Remove @ if present
        if url_or_handle.startswith("@"):
            return url_or_handle[1:]

        # Extract from URL
        if "twitter.com/" in url_or_handle or "x.com/" in url_or_handle:
            parts = url_or_handle.rstrip("/").split("/")
            if parts:
                return parts[-1]

        # Assume it's a plain username
        return url_or_handle

    @staticmethod
    def _detect_language(text: str) -> str:
        """Auto-detect language from tweet text.

        Args:
            text: Tweet content to detect language from

        Returns:
            Two-letter language code (e.g., 'en', 'zh')
            Returns 'unknown' if detection fails
        """
        # Need minimum text length for reliable detection
        if not text or len(text) < 10:
            return "unknown"

        try:
            if detect is None:
                # langdetect not available, default to 'en'
                return "en"

            lang = detect(text)

            # Ensure we have 2-letter code
            if isinstance(lang, str) and len(lang) >= 2:
                return lang[:2].lower()

            return "unknown"

        except Exception as e:
            # Log detection failure but don't break processing
            logger.debug(f"Language detection failed for tweet: {e}")
            return "unknown"
