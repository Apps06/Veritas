"""
TruthGuard Staged Analyzer
3-Stage Verification Pipeline:
  Stage 1: Exa + Tavily (source discovery)
  Bridge 1: Scira (aggregation)
  Stage 2: OpenAI GPT-4 (analysis)
  Bridge 2: Scira (context enhancement)
  Stage 3: X/Twitter (social verification)
  
+ Dynamic Source Registry for adaptive credibility scoring
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import time

# Import source registry
try:
    from source_registry import SourceRegistry
    HAS_SOURCE_REGISTRY = True
except ImportError:
    HAS_SOURCE_REGISTRY = False


class StagedAnalyzer:
    """
    Orchestrates the 3-stage verification pipeline for maximum accuracy.
    Includes dynamic source credibility scoring.
    """
    
    def __init__(self, news_analyzer, openai_analyzer, scira_service, social_service, source_registry=None):
        """
        Initialize with existing service instances.
        
        Args:
            news_analyzer: NewsAnalyzer instance (Exa + Tavily)
            openai_analyzer: OpenAIAnalyzer instance
            scira_service: SciraService instance
            social_service: SocialMediaService instance
            source_registry: Optional SourceRegistry instance
        """
        self.news_analyzer = news_analyzer
        self.openai_analyzer = openai_analyzer
        self.scira_service = scira_service
        self.social_service = social_service
        
        # Initialize source registry
        if source_registry:
            self.source_registry = source_registry
        elif HAS_SOURCE_REGISTRY:
            self.source_registry = SourceRegistry()
        else:
            self.source_registry = None
        
        # Stage timing for debugging
        self.stage_times = {}
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Run the complete 3-stage verification pipeline.
        
        Args:
            text: The news claim to verify
            
        Returns:
            Complete analysis result with verdict, confidence, and stage details
        """
        print(f"\n{'='*60}")
        print(f"STAGED ANALYSIS: {text[:80]}...")
        print(f"{'='*60}")
        
        result = {
            "claim": text,
            "stages": {},
            "verdict": "Uncertain",
            "confidence": 0,
            "reasoning": "",
            "color": "#f39c12"
        }
        
        # ============================================
        # STAGE 1: Source Discovery (Exa + Tavily)
        # ============================================
        start = time.time()
        stage1_result = self._stage1_source_discovery(text)
        self.stage_times["stage1"] = time.time() - start
        result["stages"]["source_discovery"] = stage1_result
        print(f"✓ Stage 1 complete: {len(stage1_result.get('sources', []))} sources found ({self.stage_times['stage1']:.2f}s)")
        
        # ============================================
        # BRIDGE 1: Scira Aggregation
        # ============================================
        start = time.time()
        bridge1_result = self._bridge1_scira_aggregate(text, stage1_result)
        self.stage_times["bridge1"] = time.time() - start
        result["stages"]["scira_aggregation"] = bridge1_result
        print(f"✓ Bridge 1 complete: Scira aggregation ({self.stage_times['bridge1']:.2f}s)")
        
        # ============================================
        # STAGE 2: OpenAI Analysis
        # ============================================
        start = time.time()
        stage2_result = self._stage2_openai_analysis(text, bridge1_result)
        self.stage_times["stage2"] = time.time() - start
        result["stages"]["openai_analysis"] = stage2_result
        print(f"✓ Stage 2 complete: OpenAI verdict = {stage2_result.get('verdict', 'N/A')} ({self.stage_times['stage2']:.2f}s)")
        
        # ============================================
        # BRIDGE 2: Scira Context Enhancement
        # ============================================
        start = time.time()
        bridge2_result = self._bridge2_scira_enhance(text, stage2_result)
        self.stage_times["bridge2"] = time.time() - start
        result["stages"]["scira_enhancement"] = bridge2_result
        print(f"✓ Bridge 2 complete: Context enhancement ({self.stage_times['bridge2']:.2f}s)")
        
        # ============================================
        # STAGE 3: X/Twitter Verification
        # ============================================
        start = time.time()
        stage3_result = self._stage3_twitter_verification(text, stage2_result)
        self.stage_times["stage3"] = time.time() - start
        result["stages"]["twitter_verification"] = stage3_result
        print(f"✓ Stage 3 complete: {stage3_result.get('tweet_count', 0)} tweets analyzed ({self.stage_times['stage3']:.2f}s)")
        
        # ============================================
        # FINAL VERDICT SYNTHESIS
        # ============================================
        final = self._synthesize_verdict(result)
        result.update(final)
        
        print(f"\n{'='*60}")
        print(f"FINAL VERDICT: {result['verdict']} ({result['confidence']}% confidence)")
        print(f"{'='*60}\n")
        
        return result
    
        return result
    
    def analyze_hyper(self, text: str) -> Dict[str, Any]:
        """
        HYPER MODE: Maximized for Speed & Accuracy.
        
        Pipeline:
        1. Parallel Search: Exa (Neural) + Scira (Web)
        2. Immediate Analysis: OpenAI GPT-4 with aggregated context
        
        Removes Tavily and Twitter for reduced latency and complexity.
        """
        print(f"\n{'='*60}")
        print(f"🚀 HYPER ANALYSIS: {text[:80]}...")
        print(f"{'='*60}")
        
        overall_start = time.time()
        result = {
            "claim": text,
            "stages": {},
            "verdict": "Uncertain",
            "confidence": 0,
            "reasoning": "",
            "color": "#f39c12",
            "mode": "hyper"
        }
        
        # =============================================
        # PARALLEL PHASE 1: Exa + Scira Search
        # =============================================
        exa_results = []
        scira_result = None
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Launch Exa and Scira concurrently
            future_exa = None
            future_scira = None
            
            if self.news_analyzer.has_exa:
                future_exa = executor.submit(self.news_analyzer.search_with_exa, text, 5)
            
            if self.scira_service.has_scira:
                future_scira = executor.submit(self.scira_service.search, text)
            
            # Wait for results
            start = time.time()
            try:
                if future_exa:
                    exa_results = future_exa.result(timeout=10)
            except Exception as e:
                print(f"⚠️ Exa error: {e}")
                
            try:
                if future_scira:
                    scira_result = future_scira.result(timeout=10)
            except Exception as e:
                print(f"⚠️ Scira error: {e}")
                
            self.stage_times["stage1_hyper"] = time.time() - start
            print(f"✓ Stage 1: Found {len(exa_results)} Exa sources + Scira context ({self.stage_times['stage1_hyper']:.2f}s)")
            
            # Aggregate sources
            sources = []
            sources.extend(exa_results)
            
            # Add Scira sources if available (assuming scira_result has 'sources' or similar logic)
            # For now, we mainly use Scira for the context string, but if it has structured sources, add them
            if scira_result and isinstance(scira_result, dict) and 'sources' in scira_result:
                 for s in scira_result.get('sources', []):
                     if s not in sources:
                         sources.append(s)
            
            # Calculate source scores from Registry
            weighted_credibility = 0
            for source in sources:
                if source.get('url'):
                    if self.source_registry:
                        source['registry_score'] = self.source_registry.get_source_score(source['url'])
                        source['domain_score'] = source['registry_score'] / 100
                    else:
                         source['domain_score'] = 0.5
                         source['registry_score'] = 50
                    weighted_credibility += source['registry_score']
            
            avg_credibility = weighted_credibility / len(sources) if sources else 50
            
            result["stages"]["source_discovery"] = {
                "sources": sources,
                "total_count": len(sources),
                "avg_source_credibility": round(avg_credibility, 2),
                "scira_context": scira_result
            }
        
        # =============================================
        # PHASE 2: OpenAI Analysis
        # =============================================
        start = time.time()
        
        # Prepare context for OpenAI
        # We pass the sources list which now contains Exa results
        # We can also pass Scira summary if available
        
        if not self.openai_analyzer.has_openai:
             stage2_result = {"verdict": "Uncertain", "confidence": 0, "reasoning": "OpenAI unavailable."}
        else:
            # Use analyze_claim_with_sources but simplified
            stage2_result = self.openai_analyzer.analyze_claim_with_sources(text, sources)
            
        self.stage_times["stage2_hyper"] = time.time() - start
        result["stages"]["openai_analysis"] = stage2_result
        print(f"✓ Stage 2: OpenAI verdict = {stage2_result.get('verdict', 'N/A')} ({self.stage_times['stage2_hyper']:.2f}s)")
        
        # =============================================
        # FINAL VERDICT
        # =============================================
        final = self._synthesize_verdict(result) # Reuse valid synthesis logic
        result.update(final)
        
        total_time = time.time() - overall_start
        result["total_time"] = round(total_time, 2)
        
        print(f"\n{'='*60}")
        print(f"🚀 HYPER VERDICT: {result['verdict']} ({result['confidence']}%) in {total_time:.2f}s")
        print(f"{'='*60}\n")
        
        return result
    
    def _stage1_source_discovery(self, text: str) -> Dict[str, Any]:
        """
        Stage 1: Run Exa and Tavily searches concurrently.
        """
        sources = []
        exa_results = []
        tavily_results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            if self.news_analyzer.has_exa:
                futures['exa'] = executor.submit(
                    self.news_analyzer.search_with_exa, text, 5
                )
            
            if self.news_analyzer.has_tavily:
                futures['tavily'] = executor.submit(
                    self.news_analyzer.search_with_tavily, text, 5
                )
            
            for key, future in futures.items():
                try:
                    result = future.result(timeout=15)
                    if key == 'exa':
                        exa_results = result
                    elif key == 'tavily':
                        tavily_results = result
                except Exception as e:
                    print(f"  Stage 1 {key} error: {e}")
        
        sources.extend(exa_results)
        sources.extend(tavily_results)
        
        # Calculate domain scores using Source Registry
        weighted_credibility = 0
        for source in sources:
            if source.get('url'):
                # Use registry score if available, otherwise fall back to static scoring
                if self.source_registry:
                    source['registry_score'] = self.source_registry.get_source_score(source['url'])
                    source['domain_score'] = source['registry_score'] / 100  # Normalize to 0-1
                else:
                    source['domain_score'] = self.news_analyzer.get_domain_score(source['url'])
                    source['registry_score'] = source['domain_score'] * 100
                weighted_credibility += source['registry_score']
        
        avg_credibility = weighted_credibility / len(sources) if sources else 50
        
        return {
            "sources": sources,
            "exa_count": len(exa_results),
            "tavily_count": len(tavily_results),
            "total_count": len(sources),
            "avg_source_credibility": round(avg_credibility, 2)
        }
    
    def _bridge1_scira_aggregate(self, text: str, stage1: Dict) -> Dict[str, Any]:
        """
        Bridge 1: Use Scira to aggregate and cross-reference sources.
        """
        if not self.scira_service.has_scira:
            # Fallback: just pass through stage 1 results
            return {
                "aggregated_sources": stage1.get("sources", []),
                "scira_available": False,
                "additional_context": None
            }
        
        # Use Scira to search for additional context
        scira_result = self.scira_service.search(text)
        
        return {
            "aggregated_sources": stage1.get("sources", []),
            "scira_available": True,
            "scira_search": scira_result,
            "additional_context": scira_result
        }
    
    def _stage2_openai_analysis(self, text: str, bridge1: Dict) -> Dict[str, Any]:
        """
        Stage 2: Use OpenAI GPT-4 to analyze claim against sources.
        """
        sources = bridge1.get("aggregated_sources", [])
        
        if not self.openai_analyzer.has_openai:
            return {
                "verdict": "Uncertain",
                "confidence": 30,
                "reasoning": "OpenAI not available for analysis",
                "openai_available": False
            }
        
        # If we have sources, use source-based analysis
        if sources:
            result = self.openai_analyzer.analyze_claim_with_sources(text, sources)
        else:
            # Direct text analysis without sources
            result = self.openai_analyzer.analyze_text(text)
        
        if result and not result.get("error"):
            return {
                "verdict": result.get("verdict", "Uncertain"),
                "confidence": result.get("confidence", 50),
                "reasoning": result.get("reasoning", ""),
                "openai_available": True,
                "raw_response": result
            }
        
        # Fallback for ANY OpenAI failure if we have sources
        error_msg = result.get("error", "Analysis failed") if result else "No response"
        
        if sources:
             return {
                 "verdict": "Sources Found",
                 "confidence": 40,
                 "reasoning": f"AI analysis unavailable ({error_msg}). Found {len(sources)} relevant sources - please verify manually.",
                 "openai_available": False,
                 "error": error_msg
             }
        
        return {
            "verdict": "Uncertain",
            "confidence": 30,
            "reasoning": f"AI Analysis Error: {error_msg}",
            "openai_available": False
        }
    
    def _bridge2_scira_enhance(self, text: str, stage2: Dict) -> Dict[str, Any]:
        """
        Bridge 2: Use Scira to fetch additional context based on OpenAI's analysis.
        """
        if not self.scira_service.has_scira:
            return {
                "enhanced": False,
                "scira_available": False
            }
        
        # Build enhanced query based on OpenAI's verdict
        verdict = stage2.get("verdict", "")
        enhanced_query = f"{text} fact check {verdict.lower()}"
        
        scira_result = self.scira_service.search(enhanced_query)
        
        return {
            "enhanced": True,
            "scira_available": True,
            "enhancement_query": enhanced_query,
            "scira_result": scira_result
        }
    
    def _stage3_twitter_verification(self, text: str, stage2: Dict) -> Dict[str, Any]:
        """
        Stage 3: Use X/Twitter to verify through social consensus.
        """
        if not self.social_service.has_twitter:
            return {
                "tweets": [],
                "tweet_count": 0,
                "twitter_available": False,
                "social_consensus": None
            }
        
        # Search Twitter for the claim
        tweets = self.social_service.search_twitter(text[:100], max_results=10)
        
        # Analyze social consensus
        consensus = self._analyze_twitter_consensus(tweets, stage2)
        
        return {
            "tweets": tweets,
            "tweet_count": len(tweets),
            "twitter_available": True,
            "social_consensus": consensus
        }
    
    def _analyze_twitter_consensus(self, tweets: List[Dict], stage2: Dict) -> Optional[Dict]:
        """
        Analyze Twitter results for social consensus.
        """
        if not tweets:
            return None
        
        # Simple sentiment analysis based on engagement
        total_engagement = 0
        supporting = 0
        contradicting = 0
        
        openai_verdict = stage2.get("verdict", "").lower()
        
        for tweet in tweets:
            metrics = tweet.get("metrics", {})
            engagement = (
                metrics.get("like_count", 0) +
                metrics.get("retweet_count", 0) * 2 +
                metrics.get("reply_count", 0)
            )
            total_engagement += engagement
            
            # Very basic keyword matching for now
            tweet_text = tweet.get("text", "").lower()
            if any(word in tweet_text for word in ["fake", "false", "hoax", "debunked"]):
                contradicting += 1
            elif any(word in tweet_text for word in ["true", "confirmed", "verified", "real"]):
                supporting += 1
        
        return {
            "total_tweets": len(tweets),
            "total_engagement": total_engagement,
            "supporting_tweets": supporting,
            "contradicting_tweets": contradicting,
            "consensus_direction": "supporting" if supporting > contradicting else "contradicting" if contradicting > supporting else "neutral"
        }
    
    def _synthesize_verdict(self, result: Dict) -> Dict[str, Any]:
        """
        Synthesize final verdict from all stages.
        """
        stages = result.get("stages", {})
        
        # Get OpenAI verdict (primary)
        openai = stages.get("openai_analysis", {})
        openai_verdict = openai.get("verdict", "Uncertain")
        openai_confidence = openai.get("confidence", 30)
        openai_reasoning = openai.get("reasoning", "")
        
        # Get source count
        sources = stages.get("source_discovery", {})
        source_count = sources.get("total_count", 0)
        
        # Get Twitter consensus
        twitter = stages.get("twitter_verification", {})
        consensus = twitter.get("social_consensus", {})
        
        # Calculate final confidence with stage adjustments
        final_confidence = openai_confidence
        
        # Boost if sources support
        if source_count >= 3:
            final_confidence = min(100, final_confidence + 10)
        
        # Adjust based on Twitter consensus
        if consensus:
            consensus_dir = consensus.get("consensus_direction", "neutral")
            if "True" in openai_verdict or "Real" in openai_verdict:
                if consensus_dir == "supporting":
                    final_confidence = min(100, final_confidence + 5)
                elif consensus_dir == "contradicting":
                    final_confidence = max(20, final_confidence - 10)
            elif "False" in openai_verdict or "Fake" in openai_verdict:
                if consensus_dir == "contradicting":
                    final_confidence = min(100, final_confidence + 5)
        
        # Determine final verdict and color
        if "True" in openai_verdict or "Real" in openai_verdict or "Support" in openai_verdict:
            verdict = "Verified Real"
            color = "#2ecc71"
        elif "False" in openai_verdict or "Fake" in openai_verdict or "Contradict" in openai_verdict:
            verdict = "Likely Fake"
            color = "#e74c3c"
        elif "Partial" in openai_verdict:
            verdict = "Partially True"
            color = "#f39c12"
        else:
            verdict = "Unverifiable"
            color = "#f39c12"
        
        return {
            "verdict": verdict,
            "confidence": round(final_confidence),
            "reasoning": openai_reasoning,
            "color": color,
            "stage_times": self.stage_times
        }
    
    def update_source_scores(self, sources: List[Dict], is_fake: bool):
        """
        Update source registry scores based on verdict.
        
        Args:
            sources: List of source dicts with 'url' keys
            is_fake: True if the news was determined to be fake
        """
        if not self.source_registry:
            return
        
        for source in sources:
            url = source.get("url", "")
            if url:
                if is_fake:
                    self.source_registry.report_fake(url)
                else:
                    self.source_registry.report_true(url)
    
    def report_feedback(self, result: Dict, user_feedback: str):
        """
        Process user feedback to update source scores.
        
        Args:
            result: The analysis result dict with stages
            user_feedback: 'correct' or 'incorrect'
        """
        sources = result.get("stages", {}).get("source_discovery", {}).get("sources", [])
        verdict = result.get("verdict", "")
        
        # Determine if the news was actually fake based on feedback
        is_fake_verdict = "Fake" in verdict or "False" in verdict
        
        if user_feedback == "correct":
            # Our verdict was right
            # If we said fake and user confirms, report sources as fake
            # If we said real and user confirms, report sources as true
            self.update_source_scores(sources, is_fake_verdict)
        elif user_feedback == "incorrect":
            # Our verdict was wrong - flip the logic
            self.update_source_scores(sources, not is_fake_verdict)
    
    def get_source_info(self, url: str) -> Optional[Dict]:
        """Get source registry info for a URL."""
        if self.source_registry:
            return self.source_registry.get_source_info(url)
        return None
    
    def get_all_sources_ranked(self) -> List[Dict]:
        """Get all sources ranked by credibility score."""
        if self.source_registry:
            return self.source_registry.get_all_sources()
        return []
