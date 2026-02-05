"""
Unified AI Analysis Service for TruthGuard
Handles primary analysis via OpenAI with fallback to Groq
"""
from openai_service import OpenAIAnalyzer
from groq_service import GroqAnalyzer

class UnifiedAIAnalyzer:
    def __init__(self):
        self.openai = OpenAIAnalyzer()
        self.groq = GroqAnalyzer()
        
        self.has_openai = self.openai.has_openai
        self.has_groq = self.groq.has_groq
        self.has_ai = self.has_openai or self.has_groq

    def analyze_text(self, text):
        # Try OpenAI first
        if self.has_openai:
            try:
                result = self.openai.analyze_text(text)
                if result and "error" not in result:
                    return result
                print("OpenAI returned an error, trying Groq fallback...")
            except Exception as e:
                print(f"OpenAI failed, trying Groq fallback: {e}")
        
        # Fallback to Groq
        if self.has_groq:
            print(f"Using Groq for analysis (API Key: {os.getenv('GROQ_API_KEY')[:5]}...)")
            return self.groq.analyze_text(text)
        else:
            print("Groq fallback skipped: has_groq is False (API Key missing or invalid)")
        
        return {"error": "No AI service available", "verdict": "Uncertain", "confidence": 0}

    def analyze_image(self, image_base64):
        if self.has_openai:
            try:
                result = self.openai.analyze_image(image_base64)
                if result and "error" not in result:
                    return result
            except Exception as e:
                print(f"OpenAI Vision failed, trying Groq fallback: {e}")
        
        if self.has_groq:
            return self.groq.analyze_image(image_base64)
            
        return {"error": "No AI vision service available", "verdict": "Uncertain", "confidence": 0}

    def analyze_claim_with_sources(self, claim, sources):
        if self.has_openai:
            try:
                result = self.openai.analyze_claim_with_sources(claim, sources)
                if result and "error" not in result:
                    return result
            except Exception as e:
                print(f"OpenAI Source Analysis failed, trying Groq fallback: {e}")
        
        if self.has_groq:
            return self.groq.analyze_claim_with_sources(claim, sources)
            
        return {"error": "No AI service available", "verdict": "Uncertain", "confidence": 0}
