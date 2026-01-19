"""
Fakebuster Integration Service
CNN-LSTM model with GloVe embeddings for fake news detection
Based on: https://github.com/Shubhang-Kuber/Fakebuster
"""
import os
import numpy as np
import pickle

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class FakebusterService:
    """
    CNN-LSTM model for fake news detection using GloVe embeddings.
    Falls back gracefully if TensorFlow is not available.
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.has_model = False
        self.max_length = 54
        self.padding_type = 'post'
        self.trunc_type = 'post'
        
        self._init_model()
    
    def _init_model(self):
        """Initialize the Fakebuster model"""
        try:
            import tensorflow as tf
            from tensorflow.keras.preprocessing.sequence import pad_sequences
            
            model_path = os.path.join(os.path.dirname(__file__), 'model', 'fakebuster_model.h5')
            tokenizer_path = os.path.join(os.path.dirname(__file__), 'model', 'fakebuster_tokenizer.pkl')
            
            if os.path.exists(model_path) and os.path.exists(tokenizer_path):
                # Load pre-trained model
                self.model = tf.keras.models.load_model(model_path)
                with open(tokenizer_path, 'rb') as f:
                    self.tokenizer = pickle.load(f)
                self.has_model = True
                print("✓ Fakebuster CNN-LSTM model loaded")
            else:
                print("⚠️ Fakebuster model not found. Run train_fakebuster.py to train it.")
                print(f"   Expected: {model_path}")
                
        except ImportError:
            print("⚠️ TensorFlow not available for Fakebuster model")
        except Exception as e:
            print(f"⚠️ Could not load Fakebuster model: {e}")
    
    def predict(self, text):
        """
        Predict if news text is True or Fake.
        
        Returns:
            dict with 'label' (True/Fake), 'confidence' (0-100), 'source'
        """
        if not self.has_model:
            return None
        
        try:
            from tensorflow.keras.preprocessing.sequence import pad_sequences
            
            # Tokenize and pad
            sequences = self.tokenizer.texts_to_sequences([text])
            padded = pad_sequences(sequences, maxlen=self.max_length, 
                                   padding=self.padding_type, 
                                   truncating=self.trunc_type)
            
            # Predict
            prediction = self.model.predict(padded, verbose=0)[0][0]
            
            # Interpret result
            is_true = prediction >= 0.5
            confidence = prediction * 100 if is_true else (1 - prediction) * 100
            
            return {
                "label": "True" if is_true else "Fake",
                "confidence": round(float(confidence), 2),
                "raw_score": float(prediction),
                "source": "Fakebuster CNN-LSTM"
            }
            
        except Exception as e:
            print(f"Fakebuster prediction error: {e}")
            return None
