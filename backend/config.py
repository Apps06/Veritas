import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for all API keys and settings"""
    
    # API Keys loaded from .env
    EXA_API_KEY = os.getenv("EXA_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")
    
    # X (Twitter) API credentials
    TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
    TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    
    # Reddit API
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Veritas/5.0")
    
    # Other APIs
    SCIRA_API_KEY = os.getenv("SCIRA_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    @staticmethod
    def validate():
        """Validate that required API keys are present"""
        keys = {
            "EXA_API_KEY": Config.EXA_API_KEY,
            "TAVILY_API_KEY": Config.TAVILY_API_KEY,
            "OPENAI_API_KEY": Config.OPENAI_API_KEY,
        }
        
        optional_keys = {
            "PARALLEL_API_KEY": Config.PARALLEL_API_KEY,
            "TWITTER_BEARER_TOKEN": Config.TWITTER_BEARER_TOKEN,
            "REDDIT_CLIENT_ID": Config.REDDIT_CLIENT_ID,
            "SCIRA_API_KEY": Config.SCIRA_API_KEY,
        }

        missing_keys = [k for k, v in keys.items() if not v or "your_" in v]
        missing_optional = [k for k, v in optional_keys.items() if not v or "your_" in v]
        
        if missing_keys:
            print(f"\n⚠️  Missing required API keys: {', '.join(missing_keys)}")
            print("Core features will be limited.\n")
        
        if missing_optional:
            print(f"ℹ️  Optional keys not set: {', '.join(missing_optional)}")
        
        if not missing_keys:
            print("✓ Required API keys loaded successfully")
            
        return len(missing_keys) == 0
