"""
OpenAI Analysis Service for TruthGuard
Uses GPT-4 Vision for primary text and image analysis
"""
import os
import base64
import json
import traceback
from openai import OpenAI


class OpenAIAnalyzer:
    """Primary analyzer using OpenAI GPT-4 for text and image analysis"""
    
    def __init__(self):
        self.client = None
        self.has_openai = False
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and "your_" not in api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                # Quick validation test
                self.has_openai = True
                print("✓ OpenAI API initialized (GPT-4)")
            except Exception as e:
                print(f"⚠️  Could not initialize OpenAI: {e}")
    
    def analyze_text(self, text):
        """
        Use GPT-4 to analyze text for misinformation/fake news indicators.
        Returns AI analysis score and reasoning.
        """
        if not self.has_openai:
            print("OpenAI not available for text analysis")
            return None
        
        try:
            print(f"OpenAI: Analyzing text: '{text[:50]}...'")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # More reliable and cheaper
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
            
            content = response.choices[0].message.content.strip()
            print(f"OpenAI response: {content[:100]}...")
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            result["source"] = "OpenAI GPT-4"
            print(f"OpenAI: Successfully parsed - verdict: {result.get('verdict')}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"OpenAI JSON parse error: {e}")
            print(f"Raw content: {content}")
            return {"error": "JSON parse error", "raw": content, "source": "OpenAI"}
        except Exception as e:
            print(f"OpenAI text analysis error: {e}")
            traceback.print_exc()
            return None
    
    def analyze_image(self, image_base64):
        """
        Use GPT-4 Vision to analyze image for AI generation/manipulation.
        Returns AI analysis score and reasoning.
        """
        if not self.has_openai:
            print("OpenAI not available for image analysis")
            return None
        
        try:
            print("OpenAI: Analyzing image with GPT-4 Vision...")
            
            # Ensure proper base64 format
            if not image_base64.startswith("data:"):
                image_base64 = f"data:image/jpeg;base64,{image_base64}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Supports vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image for signs of AI generation or manipulation.
Look for: AI patterns (Midjourney, DALL-E, Stable Diffusion), deepfakes, photoshop.
Respond ONLY with JSON: {"ai_generated_score": 0-100, "verdict": "AI Generated|Likely Authentic|Manipulated|Uncertain", "confidence": 0-100, "reasoning": "brief explanation"}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_base64, "detail": "low"}
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            print(f"OpenAI Vision response: {content[:100]}...")
            
            # Parse JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            result["source"] = "OpenAI GPT-4 Vision"
            print(f"OpenAI: Image verdict: {result.get('verdict')}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"OpenAI image JSON parse error: {e}")
            return {"error": "JSON parse error", "source": "OpenAI"}
        except Exception as e:
            print(f"OpenAI image analysis error: {e}")
            traceback.print_exc()
            return None
    
    def analyze_claim_with_sources(self, claim, sources):
        """
        Use GPT-4 to analyze if the fetched sources support or contradict the claim.
        This is the key verification step - AI analyzes the evidence.
        """
        if not self.has_openai:
            print("OpenAI not available for source analysis")
            return None
        
        if not sources:
            return None
            
        try:
            # Format sources for the prompt
            sources_text = ""
            for i, src in enumerate(sources[:5], 1):  # Limit to 5 sources
                title = src.get('title', 'No title')
                excerpt = src.get('excerpt', '')[:200]
                sources_text += f"{i}. {title}: {excerpt}\n"
            
            print(f"OpenAI: Analyzing claim against {len(sources)} sources")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
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
            print(f"OpenAI source analysis: {content[:100]}...")
            
            # Parse JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            result["source"] = "OpenAI Source Analysis"
            return result
            
        except json.JSONDecodeError as e:
            print(f"OpenAI source analysis JSON error: {e}")
            return {"error": "JSON parse error", "source": "OpenAI"}
        except Exception as e:
            print(f"OpenAI source analysis error: {e}")
            traceback.print_exc()
            return None
