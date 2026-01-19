from concurrent.futures import ThreadPoolExecutor, as_completed
from exa_py import Exa
from tavily import TavilyClient
from config import Config
from parallel_service import ParallelSearchService
from social_service import SocialMediaService
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class NewsAnalyzer:
    """Analyzes news using Exa and Tavily APIs for real-time verification"""
    
    def __init__(self):
        """Initialize API clients with keys from config"""
        # Initialize Clients
        self.exa_client = None
        self.has_exa = False
        self.tavily_client = None
        self.has_tavily = False
        self.parallel_service = ParallelSearchService()
        self.has_parallel = self.parallel_service.has_parallel
        
        # Initialize Social Media Service (Twitter/Reddit)
        self.social_service = SocialMediaService()
        self.has_twitter = self.social_service.has_twitter
        self.has_reddit = self.social_service.has_reddit
        
        if Config.EXA_API_KEY and Config.EXA_API_KEY != "your_exa_api_key_here":
            try:
                self.exa_client = Exa(api_key=Config.EXA_API_KEY)
                self.has_exa = True
                print("✓ Exa API initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize Exa API: {e}")
        
        # Initialize Tavily client if API key is available
        if Config.TAVILY_API_KEY and Config.TAVILY_API_KEY != "your_tavily_api_key_here":
            try:
                self.tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)
                self.has_tavily = True
                print("✓ Tavily API initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize Tavily API: {e}")
    
    def search_with_exa(self, query, num_results=5):
        """
        Search for news articles using Exa's neural search
        
        Args:
            query: The news claim to search for
            num_results: Number of results to return
            
        Returns:
            List of search results with titles, URLs, and excerpts
        """
        if not self.has_exa:
            return []
        
        try:
            # Use Exa's neural search to find relevant articles
            search_response = self.exa_client.search_and_contents(
                query,
                type="neural",
                num_results=num_results,
                text={"max_characters": 500}
            )
            
            results = []
            for result in search_response.results:
                results.append({
                    "title": result.title,
                    "url": result.url,
                    "excerpt": result.text[:300] if result.text else "",
                    "source": "Exa"
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching with Exa: {e}")
            return []
    
    def search_with_tavily(self, query, num_results=5):
        """
        Research news using Tavily's API
        
        Args:
            query: The news claim to research
            num_results: Number of results to return
            
        Returns:
            List of research results with titles, URLs, and content
        """
        if not self.has_tavily:
            return []
        
        try:
            # Use Tavily to research the claim
            search_response = self.tavily_client.search(
                query=query,
                search_depth="advanced",  # Deep research mode
                max_results=num_results,
                include_answer=True,
                include_raw_content=True  # Full content for better analysis
            )
            
            results = []
            
            # Add the AI-generated answer if available
            if search_response.get("answer"):
                results.append({
                    "title": "AI Summary",
                    "url": "",
                    "excerpt": search_response["answer"],
                    "source": "Tavily AI"
                })
            
            # Add search results
            for result in search_response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "excerpt": result.get("content", "")[:300],
                    "source": "Tavily"
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching with Tavily: {e}")
            return []
    
    def get_domain_score(self, url):
        """
        Scoring for reputable news domains.
        Updated to include Tech, Science, and Regional (India) sources.
        """
        reputable_domains = [
            # Global Tier 1
            'reuters.com', 'apnews.com', 'nytimes.com', 'bbc.com', 'bbc.co.uk',
            'theguardian.com', 'wsj.com', 'bloomberg.com', 'aljazeera.com',
            'npr.org', 'cnbc.com', 'cnn.com', 'dw.com', 'france24.com',
            'washingtonpost.com', 'usatoday.com', 'time.com',
            
            # Tech & Science
            'nature.com', 'scientificamerican.com', 'sciencenews.org',
            'techcrunch.com', 'wired.com', 'theverge.com', 'arstechnica.com',
            'phys.org', 'newscientist.com', 'ieee.org',
            
            # India (Contextual)
            'ndtv.com', 'timesofindia.indiatimes.com', 'thehindu.com', 
            'indianexpress.com', 'hindustantimes.com', 'deccanherald.com',
            'scroll.in', 'thewire.in', 'livemint.com', 'news18.com',
            'indiatoday.in'
        ]
        
        for domain in reputable_domains:
            if domain in url.lower():
                return 0.8  # High score for reputable sources
        return 0.3  # Default score for others
    
    def analyze_news(self, text):
        """
        Analyze news claim using both Exa and Tavily with enhanced Semantic Verification (TF-IDF).
        Runs API calls CONCURRENTLY for faster response time.
        """
        all_sources = []
        credibility_score = 0
        matching_reputable_sources = 0
        
        # Run API calls CONCURRENTLY using ThreadPoolExecutor
        exa_results = []
        tavily_results = []
        social_context = {"twitter": [], "reddit": [], "total_twitter": 0, "total_reddit": 0}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit Exa search
            if self.has_exa:
                futures['exa'] = executor.submit(self.search_with_exa, text, 3)
            
            # Submit Tavily search
            if self.has_tavily:
                futures['tavily'] = executor.submit(self.search_with_tavily, text, 3)
            
            # Submit Social Media search
            if self.has_twitter or self.has_reddit:
                futures['social'] = executor.submit(self.social_service.get_social_context, text)
            elif self.has_parallel:
                futures['parallel'] = executor.submit(self.parallel_service.get_social_context, text)
            
            # Collect results with timeout
            for key, future in futures.items():
                try:
                    result = future.result(timeout=10)
                    if key == 'exa':
                        exa_results = result
                    elif key == 'tavily':
                        tavily_results = result
                    elif key == 'social':
                        social_context = result
                    elif key == 'parallel':
                        social_context = {"twitter": [], "reddit": [], "parallel": result, "total_twitter": 0, "total_reddit": 0}
                except Exception as e:
                    print(f"API call {key} failed or timed out: {e}")
        
        # Combine results
        all_sources.extend(exa_results)
        all_sources.extend(tavily_results)
        
        # --- NEW SEMANTIC VERIFICATION LOGIC ---
        if all_sources:
            try:
                # Prepare Corpus: [Query] + [Source 1] + [Source 2] ...
                documents = [text]
                for src in all_sources:
                    # Combine title and excerpt
                    content = f"{src.get('title', '')} . {src.get('excerpt', '')}"
                    documents.append(content)
                
                # Compute TF-IDF
                vectorizer = TfidfVectorizer(stop_words='english')
                tfidf_matrix = vectorizer.fit_transform(documents)
                
                # Compute Cosine Similarity (Query vs All Sources)
                # Compare doc[0] (query) with doc[1:] (sources)
                cosine_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
                
            except Exception as e:
                print(f"⚠️ Similarity check failed: {e}")
                cosine_sims = [0.1] * len(all_sources) # Fallback to low similarity
        else:
            cosine_sims = []

        # Scoring Logic
        for i, source in enumerate(all_sources):
            if not source['url']: continue
            
            # Get similarity score (default 0 if index error)
            sim = cosine_sims[i] if i < len(cosine_sims) else 0
            
            # Get domain score
            domain_score = self.get_domain_score(source['url'])
            
            # Strict Verification: Needs Reputable Domain AND Semantic Match (>0.15)
            # Threshold 0.15 filters out completely unrelated articles while allowing for different phrasings
            if domain_score > 0.5 and sim > 0.15:
                matching_reputable_sources += 1
                source_score = domain_score * 2.0  # Big boost
            else:
                source_score = domain_score * 0.5 * sim # Tiny score if not matching well
                
            credibility_score += source_score
        
        # Final Credibility Score Normalization
        if matching_reputable_sources >= 2:
            final_credibility = min(100, 85 + (credibility_score * 5))
        elif matching_reputable_sources == 1:
            final_credibility = 70 # Needs at least one solid match
        else:
            final_credibility = min(40, credibility_score * 10) # Low confidence
            
        return {
            "sources": all_sources,
            "social_context": social_context,
            "total_sources": len(all_sources),
            "total_twitter": social_context.get("total_twitter", 0),
            "total_reddit": social_context.get("total_reddit", 0),
            "credibility_score": round(final_credibility, 1),
            "matching_reputable_sources": matching_reputable_sources,
            "has_realtime_data": len(all_sources) > 0
        }
