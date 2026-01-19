import json
import os
from datetime import datetime

class FeedbackManager:
    """Manages user reports and community accuracy statistics"""
    
    def __init__(self, feedback_file="feedback.json"):
        self.feedback_file = feedback_file
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w') as f:
                json.dump([], f)
                
    def add_report(self, text, system_verdict, user_feedback, confidence):
        """
        Add a user report
        user_feedback: 'correct' or 'incorrect'
        """
        report = {
            "text": text,
            "system_verdict": system_verdict,
            "user_feedback": user_feedback,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.feedback_file, 'r+') as f:
            data = json.load(f)
            data.append(report)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            
    def get_stats(self):
        """Calculate community accuracy statistics"""
        with open(self.feedback_file, 'r') as f:
            data = json.load(f)
            
        if not data:
            return {"accuracy": 100, "total_reports": 0}
            
        correct_count = sum(1 for r in data if r['user_feedback'] == 'correct')
        total = len(data)
        accuracy = round((correct_count / total) * 100, 1)
        
        return {
            "accuracy": accuracy,
            "total_reports": total,
            "incorrect_reports": total - correct_count
        }
