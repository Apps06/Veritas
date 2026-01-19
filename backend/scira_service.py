import os
import requests
from config import Config

class SciraService:
    """
    Service for interacting with Scira AI API.
    Provides web search, aggregation, and context enhancement capabilities.
    Used as a BRIDGE between stages in the verification pipeline.
    """
    
    def __init__(self):
        self.api_key = Config.SCIRA_API_KEY
        self.endpoint = "https://api.scira.ai/search"  # Primary endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.has_scira = bool(self.api_key and "your_" not in self.api_key)
        
        if self.has_scira:
            print("✓ Scira API initialized (Bridge Service)")
        
    def search(self, query, search_type="comprehensive"):
        """
        Search Scira for real-time information.
        
        Args:
            query: Search query
            search_type: Type of search (comprehensive, news, fact-check)
        """
        if not self.has_scira:
            return None
            
        try:
            payload = {
                "query": query,
                "model": "scira-default",
                "search_focus": search_type,
                "max_results": 5
            }
            
            response = requests.post(
                self.endpoint, 
                json=payload, 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Scira API returned {response.status_code}")
                return None
            
        except Exception as e:
            print(f"Scira API error: {e}")
            return None
    
    def aggregate_sources(self, claim, sources):
        """
        BRIDGE 1: Aggregate and cross-reference sources from Stage 1.
        
        Args:
            claim: The original claim text
            sources: List of sources from Exa/Tavily
            
        Returns:
            Aggregated and enriched source data
        """
        if not self.has_scira:
            # Fallback: return sources with basic enrichment
            return {
                "aggregated": sources,
                "cross_referenced": False,
                "scira_context": None
            }
        
        # Use Scira to find additional context
        try:
            # Search for fact-check specific content
            fact_check_query = f"{claim} fact check verification"
            scira_result = self.search(fact_check_query, "fact-check")
            
            return {
                "aggregated": sources,
                "cross_referenced": True,
                "scira_context": scira_result,
                "total_sources": len(sources)
            }
        except Exception as e:
            print(f"Scira aggregation error: {e}")
            return {
                "aggregated": sources,
                "cross_referenced": False,
                "error": str(e)
            }
    
    def enhance_context(self, claim, openai_analysis):
        """
        BRIDGE 2: Enhance context based on OpenAI's analysis.
        
        Args:
            claim: The original claim text
            openai_analysis: Result from OpenAI analysis stage
            
        Returns:
            Enhanced context with additional perspectives
        """
        if not self.has_scira:
            return {
                "enhanced": False,
                "additional_perspectives": []
            }
        
        try:
            # Build query based on OpenAI's verdict
            verdict = openai_analysis.get("verdict", "").lower()
            
            if "fake" in verdict or "false" in verdict:
                enhancement_query = f"{claim} debunked misinformation"
            elif "true" in verdict or "real" in verdict:
                enhancement_query = f"{claim} confirmed verified"
            else:
                enhancement_query = f"{claim} analysis perspective"
            
            scira_result = self.search(enhancement_query, "news")
            
            return {
                "enhanced": True,
                "enhancement_query": enhancement_query,
                "additional_perspectives": scira_result,
                "original_verdict": verdict
            }
        except Exception as e:
            print(f"Scira enhancement error: {e}")
            return {
                "enhanced": False,
                "error": str(e)
            }

