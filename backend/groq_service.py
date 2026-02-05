"""
Groq Analysis Service for TruthGuard
Fallback analyzer for when OpenAI is unavailable
"""
import os
import json
import traceback
from groq import Groq

class GroqAnalyzer:
    """Fallback analyzer using Groq for text and source analysis"""
    
    def __init__(self):
        self.client = None
        self.has_groq = False
        
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and "your_" not in api_key:
            try:
                self.client = Groq(api_key=api_key)
                self.has_groq = True
                print("✓ Groq API initialized (Llama-3)")
            except Exception as e:
                print(f"⚠️  Could not initialize Groq: {e}")
        else:
            print(f"⚠️ Groq API key missing or invalid: '{api_key[:5] if api_key else 'None'}...'")
    
    def analyze_text(self, text):
        """Analyze text using Groq's Llama-3 models"""
        if not self.has_groq:
            return None
        
        try:
            print(f"Groq: Analyzing text: '{text[:50]}...'")
            
            print(f"Groq: Calling API with model 'llama-3.3-70b-versatile'...")
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a fact-checking expert. Analyze the claim for misinformation.
Respond ONLY with valid JSON:
{"misinformation_score": 0-100, "verdict": "Likely True|Likely False|Unverifiable|Misleading", "confidence": 0-100, "reasoning": "brief explanation"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this claim: {text}"
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            print("Groq: API call returned successfully.")
            
            content = response.choices[0].message.content.strip()
            
            # Handle markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            result["source"] = "Groq Llama-3"
            return result
            
        except Exception as e:
            print(f"Groq text analysis error: {e}")
            return None

    def analyze_image(self, image_base64):
        """Groq currently doesn't support vision in the same way, return None"""
        # Alternatively, if there's a vision model supported by Groq, use it.
        # llama-3.2-11b-vision-preview is available.
        if not self.has_groq:
            return None
        
        try:
            # Groq supports vision now with llama-3.2
            response = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this image for signs of AI generation or manipulation. Respond ONLY with JSON: {\"ai_generated_score\": 0-100, \"verdict\": \"AI Generated|Likely Authentic|Manipulated|Uncertain\", \"confidence\": 0-100, \"reasoning\": \"brief explanation\"}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ]
            )
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            result["source"] = "Groq Vision"
            return result
        except Exception as e:
            print(f"Groq vision error: {e}")
            return None

    def analyze_claim_with_sources(self, claim, sources):
        if not self.has_groq:
            return None
            
        try:
            sources_text = ""
            for i, src in enumerate(sources[:5], 1):
                title = src.get('title', 'No title')
                excerpt = src.get('excerpt', '')[:200]
                sources_text += f"{i}. {title}: {excerpt}\n"
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a fact-checker. Compare the CLAIM to the NEWS SOURCES provided.
Determine if the sources SUPPORT, CONTRADICT, or are UNRELATED to the claim.
Respond ONLY with valid JSON:
{"verdict": "Verified True|Verified False|Unverifiable|Partially True", "confidence": 0-100, "reasoning": "brief explanation based on sources"}"""
                    },
                    {
                        "role": "user",
                        "content": f"CLAIM: {claim}\n\nNEWS SOURCES:\n{sources_text}"
                    }
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            result["source"] = "Groq Source Analysis"
            return result
        except Exception as e:
            print(f"Groq source analysis error: {e}")
            return None
