"""
Veritas Desktop - Simplified (No pystray issues)
Background clipboard monitor + hotkey (Alt+Shift+C)
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keyboard
import pyperclip

from config import Config
from news_analyzer import NewsAnalyzer
from openai_service import OpenAIAnalyzer

COLORS = {
    "bg": "#0a0e14",
    "card": "#14181f",
    "input": "#1a1f29",
    "text": "#e6edf3",
    "text_dim": "#8b949e",
    "green": "#3fb950",
    "red": "#f85149",
    "orange": "#d29922",
    "blue": "#58a6ff",
}


class VeritasSimple:
    def __init__(self):
        self.last_result = None
        self.is_analyzing = False
        self.control_window = None
        
        print("\n" + "="*50)
        print("Veritas Desktop - Background Mode")
        print("="*50)
        
        try:
            Config.validate()
            self.news = NewsAnalyzer()
            self.ai = OpenAIAnalyzer()
            print("✓ Services ready")
        except Exception as e:
            print(f"Error: {e}")
            self.news = None
            self.ai = None
    
    def analyze_clipboard(self):
        if self.is_analyzing:
            return
        
        try:
            print("[DEBUG] Hotkey triggered! Reading clipboard...")
            text = pyperclip.paste()
            if not text or len(text.strip()) < 10:
                print(f"[DEBUG] Selection too short or empty: '{text}'")
                self.show_mini_notification("Copy text first!")
                return
            
            print(f"[DEBUG] Analyzing text: {text[:50]}...")
            
            self.is_analyzing = True
            self.show_mini_notification("Analyzing...")
            
            thread = threading.Thread(target=self._analyze, args=(text,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"Error: {e}")
    
    def _analyze(self, text):
        try:
            print(f"\nAnalyzing: {text[:80]}...")
            
            # Get sources
            sources = []
            if self.news and self.news.has_tavily:
                try:
                    sources = self.news.search_with_tavily(text, 6)
                    print(f"✓ {len(sources)} sources")
                except Exception as e:
                    print(f"Search error: {e}")
            
            # Try AI
            ai_verdict = None
            ai_reasoning = None
            
            if self.ai and self.ai.has_openai:
                try:
                    result = self.ai.analyze_text(text)
                    if result and not result.get("error"):
                        ai_verdict = result.get("verdict", "")
                        ai_reasoning = result.get("reasoning", "")
                except Exception as e:
                    print(f"AI error: {e}")
            
            # Smart fallback
            if not ai_verdict and sources:
                verdict, confidence, reasoning = self._smart_analysis(text, sources)
            elif ai_verdict:
                verdict, confidence, reasoning = self._interpret_ai(ai_verdict, ai_reasoning)
            else:
                verdict = "UNABLE TO VERIFY"
                confidence = 20
                reasoning = "No sources found."
            
            self.last_result = {
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": reasoning,
                "sources": sources,
                "claim": text
            }
            
            # Show result window
            self.show_result_window()
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_analyzing = False
    
    def _smart_analysis(self, claim, sources):
        satire_kw = ['onion', 'babylon bee', 'satirical', 'parody']
        
        for src in sources:
            title = src.get('title', '').lower()
            url = src.get('url', '').lower()
            
            if any(kw in title or kw in url for kw in satire_kw):
                return "LIKELY SATIRE/FAKE", 80, "Sources indicate satirical/parody content."
        
        if len(sources) >= 3:
            return "LIKELY REAL", 65, f"Found {len(sources)} credible sources."
        return "PARTIALLY VERIFIED", 50, f"Found {len(sources)} source(s)."
    
    def _interpret_ai(self, verdict, reasoning):
        if "False" in verdict or "Misleading" in verdict:
            return "LIKELY FAKE", 75, reasoning or "AI detected misinformation."
        elif "True" in verdict:
            return "LIKELY REAL", 75, reasoning or "AI verified claim."
        return "UNCERTAIN", 50, reasoning or "AI inconclusive."
    
    def show_mini_notification(self, message):
        """Show a tiny popup notification"""
        def show():
            popup = tk.Tk()
            popup.title("Veritas")
            popup.geometry("250x80+{}+{}".format(
                popup.winfo_screenwidth() - 270,
                50
            ))
            popup.configure(bg=COLORS["card"])
            popup.overrideredirect(True)
            popup.attributes('-topmost', True)
            
            tk.Label(popup, text="🛡️ Veritas", font=("Segoe UI", 10, "bold"), 
                    fg=COLORS["blue"], bg=COLORS["card"]).pack(pady=(10, 5))
            tk.Label(popup, text=message, font=("Segoe UI", 9), 
                    fg=COLORS["text"], bg=COLORS["card"]).pack()
            
            popup.after(2000, popup.destroy)
            popup.mainloop()
        
        thread = threading.Thread(target=show)
        thread.daemon = True
        thread.start()
    
    def show_result_window(self):
        if not self.last_result:
            return
        
        def create():
            result = self.last_result
            
            root = tk.Tk()
            root.title("Veritas Analysis")
            root.geometry("750x700")
            root.configure(bg=COLORS["bg"])
            root.attributes('-topmost', True)
            
            container = tk.Frame(root, bg=COLORS["bg"])
            container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
            
            # Verdict
            verdict = result.get("verdict", "UNKNOWN")
            confidence = result.get("confidence", 0)
            
            if "FAKE" in verdict or "SATIRE" in verdict:
                accent = COLORS["red"]
                icon = "⚠️"
            elif "REAL" in verdict:
                accent = COLORS["green"]
                icon = "✓"
            else:
                accent = COLORS["orange"]
                icon = "?"
            
            # Header
            tk.Label(container, text="Veritas Analysis", font=("Segoe UI", 14), 
                    fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 20))
            
            # Verdict banner
            verdict_card = tk.Frame(container, bg=accent)
            verdict_card.pack(fill=tk.X, pady=(0, 20))
            
            verdict_inner = tk.Frame(verdict_card, bg=accent, padx=25, pady=20)
            verdict_inner.pack(fill=tk.BOTH)
            
            tk.Label(verdict_inner, text=icon, font=("Segoe UI", 32), 
                    fg="white", bg=accent).pack(side=tk.LEFT, padx=(0, 15))
            
            text_stack = tk.Frame(verdict_inner, bg=accent)
            text_stack.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            tk.Label(text_stack, text=verdict, font=("Segoe UI", 24, "bold"), 
                    fg="white", bg=accent, anchor="w").pack(fill=tk.X)
            tk.Label(text_stack, text=f"{confidence}% Confidence", font=("Segoe UI", 12), 
                    fg="white", bg=accent, anchor="w").pack(fill=tk.X, pady=(5, 0))
            
            # Claim
            claim_card = tk.Frame(container, bg=COLORS["card"])
            claim_card.pack(fill=tk.X, pady=(0, 15))
            
            claim_inner = tk.Frame(claim_card, bg=COLORS["card"], padx=20, pady=15)
            claim_inner.pack(fill=tk.BOTH)
            
            tk.Label(claim_inner, text="CLAIM", font=("Segoe UI", 9, "bold"), 
                    fg=COLORS["text_dim"], bg=COLORS["card"]).pack(anchor="w")
            tk.Label(claim_inner, text=result.get("claim", "")[:250], font=("Segoe UI", 11), 
                    fg=COLORS["text"], bg=COLORS["card"], wraplength=680, justify="left").pack(anchor="w", pady=(8, 0))
            
            # Analysis
            analysis_card = tk.Frame(container, bg=COLORS["card"])
            analysis_card.pack(fill=tk.X, pady=(0, 15))
            
            analysis_inner = tk.Frame(analysis_card, bg=COLORS["card"], padx=20, pady=15)
            analysis_inner.pack(fill=tk.BOTH)
            
            tk.Label(analysis_inner, text="ANALYSIS", font=("Segoe UI", 9, "bold"), 
                    fg=COLORS["text_dim"], bg=COLORS["card"]).pack(anchor="w")
            tk.Label(analysis_inner, text=result.get("reasoning", ""), font=("Segoe UI", 11), 
                    fg=COLORS["text"], bg=COLORS["card"], wraplength=680, justify="left").pack(anchor="w", pady=(8, 0))
            
            # Sources
            sources = result.get("sources", [])
            if sources:
                sources_card = tk.Frame(container, bg=COLORS["card"])
                sources_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                
                sources_inner = tk.Frame(sources_card, bg=COLORS["card"], padx=20, pady=15)
                sources_inner.pack(fill=tk.BOTH, expand=True)
                
                tk.Label(sources_inner, text=f"SOURCES ({len(sources)})", font=("Segoe UI", 9, "bold"), 
                        fg=COLORS["text_dim"], bg=COLORS["card"]).pack(anchor="w", pady=(0, 10))
                
                canvas = tk.Canvas(sources_inner, bg=COLORS["card"], highlightthickness=0, height=150)
                scrollbar = tk.Scrollbar(sources_inner, orient="vertical", command=canvas.yview)
                scrollable = tk.Frame(canvas, bg=COLORS["card"])
                
                scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.create_window((0, 0), window=scrollable, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                for src in sources:
                    src_row = tk.Frame(scrollable, bg=COLORS["input"], cursor="hand2")
                    src_row.pack(fill=tk.X, pady=3)
                    
                    src_inner = tk.Frame(src_row, bg=COLORS["input"], padx=15, pady=10)
                    src_inner.pack(fill=tk.BOTH)
                    
                    title = src.get("title", "Unknown")[:90]
                    url = src.get("url", "")
                    
                    tk.Label(src_inner, text=f"• {title}", font=("Segoe UI", 10), 
                            fg=COLORS["text"], bg=COLORS["input"], anchor="w", justify="left", 
                            wraplength=600).pack(fill=tk.X)
                    
                    if url:
                        src_row.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            
            # Close button
            tk.Button(container, text="Close", font=("Segoe UI", 11), bg=COLORS["input"], 
                     fg=COLORS["text"], relief=tk.FLAT, padx=30, pady=10, 
                     cursor="hand2", command=root.destroy).pack(pady=(10, 0))
            
            root.mainloop()
        
        thread = threading.Thread(target=create)
        thread.daemon = True
        thread.start()
    
    def show_control_panel(self):
        """Show a small control panel window"""
        if self.control_window and self.control_window.winfo_exists():
            return
        
        self.control_window = tk.Tk()
        self.control_window.title("Veritas")
        self.control_window.geometry("300x200")
        self.control_window.configure(bg=COLORS["bg"])
        
        tk.Label(self.control_window, text="🛡️ Veritas", font=("Segoe UI", 18, "bold"), 
                fg=COLORS["green"], bg=COLORS["bg"]).pack(pady=20)
        
        tk.Label(self.control_window, text="Background monitor active", font=("Segoe UI", 10), 
                fg=COLORS["text_dim"], bg=COLORS["bg"]).pack()
        
        tk.Label(self.control_window, text="\nPress Alt+Shift+C\nto analyze clipboard", 
                font=("Segoe UI", 11), fg=COLORS["text"], bg=COLORS["bg"]).pack(pady=10)
        
        btn_frame = tk.Frame(self.control_window, bg=COLORS["bg"])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Analyze Now", font=("Segoe UI", 10), bg=COLORS["green"], 
                 fg="white", relief=tk.FLAT, padx=20, pady=8, 
                 command=self.analyze_clipboard).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Exit", font=("Segoe UI", 10), bg=COLORS["red"], 
                 fg="white", relief=tk.FLAT, padx=20, pady=8, 
                 command=self.quit).pack(side=tk.LEFT, padx=5)
        
        self.control_window.protocol("WM_DELETE_WINDOW", self.control_window.withdraw)
        self.control_window.mainloop()
    
    def setup_hotkey(self):
        try:
            keyboard.add_hotkey('alt+shift+c', self.analyze_clipboard)
            print("✓ Hotkey: Alt+Shift+C")
            return True
        except Exception as e:
            print(f"Hotkey error: {e}")
            return False
    
    def quit(self):
        try:
            keyboard.unhook_all()
        except:
            pass
        os._exit(0)
    
    def run(self):
        print("\n" + "="*50)
        print("Veritas Desktop Running")
        print("• Background clipboard monitor")
        print("• Press Alt+Shift+C to analyze")
        print("="*50 + "\n")
        
        if not self.setup_hotkey():
            print("Failed to register hotkey")
            return
        
        # Show control panel
        self.show_control_panel()


if __name__ == "__main__":
    app = VeritasSimple()
    app.run()
