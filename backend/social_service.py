"""
Social Media Service for Veritas
Integrates directly with Twitter API v2 (Tweepy) and Reddit API (PRAW)
"""
import os
from config import Config

class SocialMediaService:
    """Direct integration with Twitter and Reddit APIs"""
    
    def __init__(self):
        self.twitter_client = None
        self.reddit_client = None
        self.has_twitter = False
        self.has_reddit = False
        
        self._init_twitter()
        self._init_reddit()
    
    def _init_twitter(self):
        """Initialize X (Twitter) API v2 client using Tweepy
        Supports both Bearer Token (app-only) and OAuth 1.0a (user context)
        """
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        
        # Check if we have valid credentials
        has_bearer = bearer_token and "your_" not in bearer_token
        has_oauth = consumer_key and consumer_secret and "your_" not in consumer_key
        
        if has_bearer or has_oauth:
            try:
                import tweepy
                
                if has_oauth and has_bearer:
                    # Full access with OAuth 1.0a + Bearer Token
                    self.twitter_client = tweepy.Client(
                        bearer_token=bearer_token,
                        consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        wait_on_rate_limit=True
                    )
                    print("✓ X API initialized (OAuth 1.0a + Bearer Token)")
                elif has_bearer:
                    # App-only auth with bearer token
                    self.twitter_client = tweepy.Client(
                        bearer_token=bearer_token,
                        wait_on_rate_limit=True
                    )
                    print("✓ X API initialized (Bearer Token only)")
                
                self.has_twitter = True
            except ImportError:
                print("⚠️  Tweepy not installed. Run: pip install tweepy")
            except Exception as e:
                print(f"⚠️  Could not initialize X API: {e}")
    
    def _init_reddit(self):
        """Initialize Reddit API client using PRAW"""
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "Veritas/4.0")
        
        if client_id and client_secret and "your_" not in client_id:
            try:
                import praw
                self.reddit_client = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                self.has_reddit = True
                print("✓ Reddit API initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize Reddit API: {e}")
    
    def search_twitter(self, query, max_results=5):
        """Search recent tweets about a topic"""
        if not self.has_twitter:
            return []
        
        try:
            # Twitter API v2 recent search
            response = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 10),
                tweet_fields=["created_at", "public_metrics", "author_id"]
            )
            
            results = []
            if response.data:
                for tweet in response.data:
                    results.append({
                        "platform": "Twitter",
                        "text": tweet.text[:200],
                        "url": f"https://twitter.com/i/status/{tweet.id}",
                        "metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                    })
            return results
            
        except Exception as e:
            print(f"Twitter search error: {e}")
            return []
    
    def search_reddit(self, query, max_results=5):
        """Search Reddit for relevant discussions"""
        if not self.has_reddit:
            return []
        
        try:
            results = []
            # Search across all of Reddit
            for submission in self.reddit_client.subreddit("all").search(query, limit=max_results, time_filter="week"):
                results.append({
                    "platform": "Reddit",
                    "title": submission.title,
                    "text": submission.selftext[:200] if submission.selftext else "",
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": str(submission.subreddit),
                    "score": submission.score
                })
            return results
            
        except Exception as e:
            print(f"Reddit search error: {e}")
            return []
    
    def get_social_context(self, query):
        """Get combined social context from Twitter and Reddit"""
        twitter_results = self.search_twitter(query)
        reddit_results = self.search_reddit(query)
        
        return {
            "twitter": twitter_results,
            "reddit": reddit_results,
            "total_twitter": len(twitter_results),
            "total_reddit": len(reddit_results)
        }
