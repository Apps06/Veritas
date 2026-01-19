import requests
from config import Config

class ParallelSearchService:
    """Interfaces with Parallel.ai Search API for social media context"""
    
    def __init__(self):
        self.api_key = Config.PARALLEL_API_KEY
        self.base_url = "https://api.parallel.ai/search"
        self.has_parallel = self.api_key and "your_" not in self.api_key
        
    def search_social(self, query, platform="twitter.com"):
        """
        Search for discussions on a specific platform using Parallel Search
        Available platforms: 'twitter.com', 'reddit.com'
        """
        if not self.has_parallel:
            return []
            
        site_query = f"site:{platform} {query}"
        
        try:
            # Parallel Search API structure (based on general AI search API patterns)
            # Parallel usually focuses on high-density excerpts for LLMs
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": site_query,
                "num_results": 5,
                "objective": f"Find recent and relevant discussions on {platform} about the claim: {query}"
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                formatted_results = []
                for res in results:
                    formatted_results.append({
                        "title": res.get("title", "Post"),
                        "url": res.get("url"),
                        "snippet": res.get("excerpt", res.get("snippet", "")),
                        "platform": "Twitter" if "twitter" in platform else "Reddit"
                    })
                return formatted_results
            else:
                print(f"Parallel Search API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error calling Parallel Search: {e}")
            return []

    def get_social_context(self, query):
        """Fetch context from both Twitter and Reddit"""
        social_data = []
        social_data.extend(self.search_social(query, "twitter.com"))
        social_data.extend(self.search_social(query, "reddit.com"))
        return social_data
