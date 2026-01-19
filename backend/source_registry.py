"""
Veritas Source Registry
Dynamic source credibility system with adaptive confidence scoring.

Scoring Logic:
- New sources start at 100 confidence
- If news from source is FAKE → score halved (100 → 50)
- If news from source is TRUE → score increases proportionally ((100 - current) / 2 + current)
  Example: 50 → 75 → 87.5 → 93.75

This creates a learning system where:
- Unreliable sources quickly lose credibility
- Sources can rebuild trust through consistent accuracy
- Established reliable sources maintain high scores
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from urllib.parse import urlparse


class SourceRegistry:
    """
    Manages a registry of news sources with dynamic credibility scores.
    """
    
    # Pre-seeded trusted sources with high initial scores
    TRUSTED_SOURCES = {
        # Global Tier 1 News
        'reuters.com': 95,
        'apnews.com': 95,
        'bbc.com': 92,
        'bbc.co.uk': 92,
        'nytimes.com': 90,
        'theguardian.com': 88,
        'wsj.com': 90,
        'bloomberg.com': 90,
        'npr.org': 88,
        'aljazeera.com': 85,
        
        # Fact-Checking Sites (highest trust)
        'factcheck.org': 98,
        'snopes.com': 97,
        'politifact.com': 97,
        'fullfact.org': 96,
        'checkyourfact.com': 92,
        
        # Science & Tech
        'nature.com': 95,
        'scientificamerican.com': 92,
        'sciencenews.org': 90,
        'techcrunch.com': 80,
        'wired.com': 82,
        'theverge.com': 78,
        'arstechnica.com': 85,
        
        # India News
        'ndtv.com': 82,
        'thehindu.com': 85,
        'indianexpress.com': 83,
        'hindustantimes.com': 80,
        'livemint.com': 82,
        'scroll.in': 78,
        'thewire.in': 75,
        
        # Other Major
        'cnn.com': 78,
        'washingtonpost.com': 85,
        'usatoday.com': 80,
        'time.com': 82,
        'cnbc.com': 82,
        'dw.com': 85,
        'france24.com': 83,
    }
    
    # Known unreliable sources (start with low scores)
    UNRELIABLE_SOURCES = {
        'infowars.com': 10,
        'naturalnews.com': 15,
        'beforeitsnews.com': 10,
        'worldnewsdailyreport.com': 5,  # Satire site often shared as real
    }
    
    def __init__(self, registry_file: str = "source_registry.json"):
        """
        Initialize the source registry.
        
        Args:
            registry_file: Path to JSON file for persistent storage
        """
        self.registry_file = registry_file
        self.sources: Dict[str, Dict] = {}
        
        # Load existing registry or create new one
        self._load_registry()
        
        print(f"✓ Source Registry initialized ({len(self.sources)} sources tracked)")
    
    def _load_registry(self):
        """Load registry from JSON file or initialize with defaults."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    self.sources = data.get("sources", {})
                    return
            except Exception as e:
                print(f"⚠️ Could not load registry: {e}")
        
        # Initialize with pre-seeded sources
        for domain, score in self.TRUSTED_SOURCES.items():
            self.sources[domain] = {
                "score": score,
                "total_checks": 0,
                "fake_count": 0,
                "true_count": 0,
                "last_updated": datetime.now().isoformat(),
                "category": "trusted"
            }
        
        for domain, score in self.UNRELIABLE_SOURCES.items():
            self.sources[domain] = {
                "score": score,
                "total_checks": 0,
                "fake_count": 0,
                "true_count": 0,
                "last_updated": datetime.now().isoformat(),
                "category": "unreliable"
            }
        
        self._save_registry()
    
    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump({
                    "sources": self.sources,
                    "last_updated": datetime.now().isoformat(),
                    "total_sources": len(self.sources)
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save registry: {e}")
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def get_source_score(self, url: str) -> float:
        """
        Get credibility score for a source.
        
        Args:
            url: URL of the news source
            
        Returns:
            Credibility score (0-100)
        """
        domain = self._extract_domain(url)
        if not domain:
            return 50  # Unknown format
        
        if domain in self.sources:
            return self.sources[domain]["score"]
        
        # New source - start at 100 (benefit of the doubt)
        self._register_new_source(domain)
        return 100
    
    def _register_new_source(self, domain: str):
        """Register a new source with default score."""
        if domain not in self.sources:
            self.sources[domain] = {
                "score": 100,  # New sources start at 100
                "total_checks": 0,
                "fake_count": 0,
                "true_count": 0,
                "last_updated": datetime.now().isoformat(),
                "category": "new"
            }
            self._save_registry()
    
    def report_fake(self, url: str):
        """
        Report that news from this source was FAKE.
        Halves the credibility score.
        
        Args:
            url: URL of the news source
        """
        domain = self._extract_domain(url)
        if not domain:
            return
        
        if domain not in self.sources:
            self._register_new_source(domain)
        
        source = self.sources[domain]
        old_score = source["score"]
        
        # Halve the score (100 → 50 → 25 → 12.5...)
        new_score = max(5, old_score / 2)  # Minimum score of 5
        
        source["score"] = round(new_score, 2)
        source["total_checks"] += 1
        source["fake_count"] += 1
        source["last_updated"] = datetime.now().isoformat()
        
        if source["category"] == "trusted" and new_score < 50:
            source["category"] = "degraded"
        elif source["category"] == "new" and new_score < 50:
            source["category"] = "unreliable"
        
        print(f"📉 Source '{domain}' score: {old_score} → {new_score} (FAKE reported)")
        self._save_registry()
    
    def report_true(self, url: str):
        """
        Report that news from this source was TRUE.
        Increases score proportionally: new = current + (100 - current) / 2
        
        Args:
            url: URL of the news source
        """
        domain = self._extract_domain(url)
        if not domain:
            return
        
        if domain not in self.sources:
            self._register_new_source(domain)
        
        source = self.sources[domain]
        old_score = source["score"]
        
        # Proportional increase: 50 → 75 → 87.5 → 93.75...
        # Formula: new = current + (100 - current) / 2
        gap = 100 - old_score
        new_score = min(100, old_score + gap / 2)
        
        source["score"] = round(new_score, 2)
        source["total_checks"] += 1
        source["true_count"] += 1
        source["last_updated"] = datetime.now().isoformat()
        
        # Upgrade category if score improves significantly
        if source["category"] == "unreliable" and new_score > 60:
            source["category"] = "recovering"
        elif source["category"] in ["recovering", "degraded"] and new_score > 80:
            source["category"] = "trusted"
        
        print(f"📈 Source '{domain}' score: {old_score} → {new_score} (TRUE reported)")
        self._save_registry()
    
    def get_source_info(self, url: str) -> Optional[Dict]:
        """
        Get full information about a source.
        
        Args:
            url: URL of the news source
            
        Returns:
            Source info dict or None
        """
        domain = self._extract_domain(url)
        if domain and domain in self.sources:
            return {
                "domain": domain,
                **self.sources[domain]
            }
        return None
    
    def get_all_sources(self, min_score: float = 0) -> List[Dict]:
        """
        Get all sources with scores above threshold.
        
        Args:
            min_score: Minimum score to include
            
        Returns:
            List of source info dicts sorted by score
        """
        sources = []
        for domain, info in self.sources.items():
            if info["score"] >= min_score:
                sources.append({
                    "domain": domain,
                    **info
                })
        
        return sorted(sources, key=lambda x: x["score"], reverse=True)
    
    def get_trusted_sources(self) -> List[str]:
        """Get list of domains with score > 80."""
        return [domain for domain, info in self.sources.items() if info["score"] > 80]
    
    def get_unreliable_sources(self) -> List[str]:
        """Get list of domains with score < 40."""
        return [domain for domain, info in self.sources.items() if info["score"] < 40]
    
    def calculate_weighted_credibility(self, sources: List[Dict]) -> float:
        """
        Calculate weighted credibility score from multiple sources.
        
        Args:
            sources: List of source dicts with 'url' key
            
        Returns:
            Weighted average credibility (0-100)
        """
        if not sources:
            return 50
        
        total_score = 0
        count = 0
        
        for source in sources:
            url = source.get("url", "")
            if url:
                score = self.get_source_score(url)
                total_score += score
                count += 1
        
        return round(total_score / count, 2) if count > 0 else 50
