from PIL import Image
from transformers import pipeline, ViTForImageClassification, ViTImageProcessor
import io
import base64
from pathlib import Path
import torch


class ImageAnalyzer:
    """
    Analyzes images for:
    1. AI-generated/deepfake content detection
    2. OCR text extraction for fake news verification
    """
    
    def __init__(self):
        print("Loading Image Analysis Models...")
        self.custom_model = None
        self.custom_processor = None
        self.detectors = []
        self.has_detector = False
        self.using_custom = False
        self.ocr_reader = None
        self.has_ocr = False
        
        # Initialize OCR (EasyOCR)
        self._init_ocr()
        
        # Try to load custom trained model first
        custom_path = Path("models/veritas_detector/final")
        if custom_path.exists():
            try:
                self.custom_model = ViTForImageClassification.from_pretrained(str(custom_path))
                self.custom_processor = ViTImageProcessor.from_pretrained(str(custom_path))
                self.has_detector = True
                self.using_custom = True
                print("✓ Loaded CUSTOM Veritas detector")
            except Exception as e:
                print(f"⚠️  Could not load custom model: {e}")
        
        # Fallback to pre-trained models if no custom model
        if not self.using_custom:
            # Using better models for accuracy
            models_to_try = [
                ("umm-maybe/AI-image-detector", "ai_detector"),  # Better general AI detector
                ("prithivMLmods/Deep-Fake-Detector-v2-Model", "deepfake_v2"),
            ]
            
            for model_name, label in models_to_try:
                try:
                    detector = pipeline("image-classification", model=model_name)
                    self.detectors.append({"model": detector, "name": label})
                    print(f"✓ Loaded {label} detector")
                except Exception as e:
                    print(f"⚠️  Could not load {label}: {e}")
            
            if self.detectors:
                self.has_detector = True
                print(f"✓ {len(self.detectors)} detector(s) ready")

    def _init_ocr(self):
        """Initialize EasyOCR for text extraction"""
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            self.has_ocr = True
            print("✓ OCR (EasyOCR) initialized")
        except ImportError:
            print("⚠️  EasyOCR not installed. Run: pip install easyocr")
        except Exception as e:
            print(f"⚠️  Could not initialize OCR: {e}")

    def extract_text(self, image):
        """Extract text from image using OCR"""
        if not self.has_ocr:
            return ""
        
        try:
            import numpy as np
            # Convert PIL Image to numpy array for EasyOCR
            img_array = np.array(image)
            
            # Run OCR
            results = self.ocr_reader.readtext(img_array)
            
            # Combine all detected text
            extracted_text = " ".join([result[1] for result in results])
            
            print(f"OCR extracted {len(extracted_text)} characters")
            return extracted_text.strip()
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""

    def _analyze_with_custom(self, image):
        """Analyze using custom trained model"""
        inputs = self.custom_processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.custom_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
        
        # Get predictions (Label 0 = AI, Label 1 = Real)
        ai_score = probs[0][0].item()
        real_score = probs[0][1].item()
        
        return ai_score, real_score

    def _analyze_with_ensemble(self, image):
        """Analyze using ensemble of pre-trained models with weighted voting"""
        model_results = []
        
        for detector_info in self.detectors:
            try:
                preds = detector_info["model"](image)
                
                ai_score = 0
                real_score = 0
                
                for pred in preds:
                    label = pred['label'].lower()
                    score = pred['score']
                    
                    # More comprehensive label detection
                    ai_keywords = ['fake', 'artificial', 'ai', 'generated', 'deepfake', 
                                   'synthetic', 'manipulated', 'ai_generated', 'not_real']
                    real_keywords = ['real', 'authentic', 'human', 'natural', 'realism', 
                                     'genuine', 'original', 'not_ai']
                    
                    is_ai = any(kw in label for kw in ai_keywords)
                    is_real = any(kw in label for kw in real_keywords)
                    
                    if is_ai:
                        ai_score = max(ai_score, score)
                    elif is_real:
                        real_score = max(real_score, score)
                
                if ai_score > 0 or real_score > 0:
                    model_results.append({
                        "model": detector_info["name"],
                        "ai": ai_score,
                        "real": real_score
                    })
                    
            except Exception as e:
                print(f"Error with {detector_info['name']}: {e}")
        
        if not model_results:
            return 0.5, 0.5
        
        # Weighted average (first model has higher weight as it's more accurate)
        total_ai = 0
        total_real = 0
        total_weight = 0
        
        for i, result in enumerate(model_results):
            weight = 2.0 if i == 0 else 1.0  # First model weighted higher
            total_ai += result["ai"] * weight
            total_real += result["real"] * weight
            total_weight += weight
        
        avg_ai = total_ai / total_weight
        avg_real = total_real / total_weight
        
        # Normalize
        total = avg_ai + avg_real
        if total > 0:
            return avg_ai / total, avg_real / total
        return 0.5, 0.5

    def analyze_image(self, image_data_base64):
        """
        Analyze an image for:
        1. AI generation/deepfake detection
        2. Text extraction via OCR (for fake news verification)
        """
        if not self.has_detector:
            return {"error": "Image detection model not available"}
            
        try:
            # Decode base64
            if ',' in image_data_base64:
                header, encoded = image_data_base64.split(',', 1)
            else:
                encoded = image_data_base64
                
            image_bytes = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize for faster processing while maintaining quality
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            print(f"Analyzing image: size={image.size}, custom_model={self.using_custom}")
            
            # 1. Extract text via OCR
            extracted_text = self.extract_text(image)
            
            # 2. Get AI/deepfake predictions
            if self.using_custom:
                ai_score, real_score = self._analyze_with_custom(image)
                model_info = "Custom Veritas Model"
            else:
                ai_score, real_score = self._analyze_with_ensemble(image)
                model_info = f"Ensemble ({len(self.detectors)} models)"
            
            ai_percentage = round(ai_score * 100, 2)
            real_percentage = round(real_score * 100, 2)
            
            # Decision logic with stricter thresholds
            if ai_score > 0.65:
                verdict = "AI Generated"
                color = "#e74c3c"
                confidence = ai_percentage
                reason = f"High AI probability detected ({confidence:.1f}%). [{model_info}]"
            elif real_score > 0.65:
                verdict = "Likely Authentic"
                color = "#2ecc71"
                confidence = real_percentage
                reason = f"Authentic patterns detected ({confidence:.1f}%). [{model_info}]"
            elif ai_score > real_score:
                verdict = "Possibly AI Generated"
                color = "#e67e22"
                confidence = ai_percentage
                reason = f"Some AI patterns detected ({confidence:.1f}%). [{model_info}]"
            else:
                verdict = "Uncertain"
                color = "#f39c12"
                confidence = max(ai_percentage, real_percentage)
                reason = f"Mixed signals (AI: {ai_percentage:.1f}%, Real: {real_percentage:.1f}%). Review recommended."
                
            return {
                "verdict": verdict,
                "confidence": round(confidence, 2),
                "color": color,
                "reason": reason,
                "ai_score": ai_percentage,
                "real_score": real_percentage,
                "model_used": model_info,
                "using_custom_model": self.using_custom,
                "extracted_text": extracted_text,  # NEW: OCR text for fake news check
                "has_text": len(extracted_text) > 10
            }
            
        except Exception as e:
            import traceback
            print(f"Error analyzing image: {e}")
            traceback.print_exc()
            return {"error": str(e)}
