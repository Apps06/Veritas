"""
Veritas Desktop - UI Update
Background clipboard monitor + hotkey (Alt+Shift+C)
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, font
import webbrowser
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keyboard
import pyperclip

from config import Config
from news_analyzer import NewsAnalyzer
from ai_service import UnifiedAIAnalyzer
import base64

# --- THEME CONFIGURATION ---
# --- THEME CONFIGURATION (Matches web_app.py) ---
THEME = {
    "bg": "#0b0e14",
    "card": "#14181f", 
    "input": "#0d1117",
    "text": "#ffffff",
    "text_dim": "#8b949e",
    "purple": "#8b5cf6",
    "purple_dark": "#6366f1",
    "green": "#3fb950",
    "red": "#f85149",
    "orange": "#d29922",
    "border": "#30363d",
    "success_bg": "rgba(63, 185, 80, 0.15)",
    "danger_bg": "rgba(248, 81, 73, 0.15)",
    "warning_bg": "rgba(210, 153, 34, 0.15)"
}

class VeritasDesktop:
    def __init__(self):
        self.last_result = None
        self.is_analyzing = False
        self.root = tk.Tk()
        self.root.withdraw() # Hide the main root window
        self.control_window = None
        self.loading_win = None
        self.result_win = None
        
        print("\n" + "="*50)
        print("Veritas Desktop - UI Enhanced (Thread Safe)")
        print("="*50)
        
        try:
            Config.validate()
            self.news = NewsAnalyzer()
            self.ai = UnifiedAIAnalyzer()
            print("✓ Services ready")
        except Exception as e:
            print(f"Error: {e}")
            self.news = None
            self.ai = None
    
    def analyze_clipboard(self):
        if self.is_analyzing:
            return
        
        try:
            print("[DEBUG] Hotkey triggered! Checking clipboard...")
            
            # 2. Check for Text
            text = pyperclip.paste()
            if not text or len(text.strip()) < 5:
                self.show_toast("No content found in clipboard!")
                return
            
            print(f"[DEBUG] Analyzing text: {text[:50]}...")
            
            self.is_analyzing = True
            # Call show_loading on main thread
            self.root.after(0, lambda: self.show_loading("Analyzing Text..."))
            
            thread = threading.Thread(target=self._analyze_text, args=(text,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"Error: {e}")
            self.is_analyzing = False
    
    def _analyze_text(self, text):
        try:
            # Sources
            sources = []
            if self.news and self.news.has_tavily:
                try:
                    sources = self.news.search_with_tavily(text, 5)
                except: pass
            
            # AI
            ai_verdict = None
            ai_reasoning = None
            source_name = "Sources"
            
            if self.ai and self.ai.has_ai:
                try:
                    # UnifiedAIAnalyzer handles fallback internally
                    res = self.ai.analyze_text(text)
                    if res: 
                        ai_verdict = res.get("verdict")
                        ai_reasoning = res.get("reasoning")
                        source_name = res.get("source", "AI")
                except: pass
            
            # Smart Logic (Matches web_app.py)
            verdict = "UNABLE TO VERIFY"
            confidence = 20
            reasoning = "No sources found and AI unavailable."
            
            if not ai_verdict and sources:
                verdict, confidence, reasoning = self.smart_source_analysis(text, sources)
            elif ai_verdict:
                verdict, confidence, reasoning = self.interpret_ai(ai_verdict, ai_reasoning)
                
            # Determine Color
            color = THEME["orange"]
            if "FAKE" in verdict or "SATIRE" in verdict:
                color = THEME["red"]
            elif "REAL" in verdict or "VERIFIED" in verdict and "PARTIALLY" not in verdict:
                color = THEME["green"]
            
            self.last_result = {
                "type": "text",
                "verdict": verdict,
                "confidence": confidence,
                "color": color,
                "claim": text,
                "sources": sources,
                "reason": reasoning,
                "ai_source": source_name,
                "metrics": {
                    "Source Credibility": "High" if len(sources) > 3 else "Low",
                    "Sensationalism": "Low", 
                    "Fact Check": verdict
                }
            }
            # Show result on main thread
            self.root.after(0, self.show_result_window)
            
        except Exception as e:
            print(f"Analysis error: {e}")
        finally:
            self.is_analyzing = False

    def smart_source_analysis(self, claim, sources):
        """Analyze sources without AI"""
        # Keywords that suggest the source is criticizing or debunking
        satire_keywords = ['onion', 'babylon bee', 'satirical', 'parody', 'humor', 'comedy']
        debunk_keywords = ['fact check', 'false', 'debunk', 'hoax', 'fake', 'rumor', 'myth', 'scam']
        
        satire_count = 0
        debunk_count = 0
        
        for src in sources:
            title = src.get('title', '').lower()
            url = src.get('url', '').lower()
            
            if any(kw in title or kw in url for kw in satire_keywords):
                satire_count += 1
            if any(kw in title for kw in debunk_keywords):
                debunk_count += 1
                
        if satire_count > 0:
            return "LIKELY SATIRE/FAKE", 80, "Sources indicate this is satire or parody content."
            
        if debunk_count > 0:
            return "LIKELY FAKE (Fact Checked)", 70, "Sources appear to be fact-checking or debunking this claim."
        
        if len(sources) >= 4:
            return "LIKELY REAL", 65, f"Found {len(sources)} sources. No obvious debunking found."
        elif len(sources) >= 1:
            return "PARTIALLY VERIFIED", 50, f"Found {len(sources)} source(s). Verify carefully."
        else:
            return "UNVERIFIED", 20, "No sources found."

    def interpret_ai(self, verdict, reasoning):
        """Interpret AI verdict"""
        if "False" in verdict or "Misleading" in verdict:
            return "LIKELY FAKE", 75, reasoning or "AI detected misinformation patterns."
        elif "True" in verdict:
            return "LIKELY REAL", 75, reasoning or "AI verified the claim."
        return "UNCERTAIN", 50, reasoning or "AI analysis inconclusive."


    def show_toast(self, msg):
        print(f"Toast: {msg}")

    def show_loading(self, msg):
        if self.loading_win:
            try: self.loading_win.destroy()
            except: pass
            
        self.loading_win = tk.Toplevel(self.root)
        self.loading_win.overrideredirect(True)
        self.loading_win.geometry(f"300x100+{self.loading_win.winfo_screenwidth()-320}+50")
        self.loading_win.configure(bg=THEME["bg"])
        self.loading_win.attributes('-topmost', True)
        
        tk.Label(self.loading_win, text="🛡️ Veritas", font=("Segoe UI", 12, "bold"),
                fg=THEME["purple"], bg=THEME["bg"]).pack(pady=(20,5))
        tk.Label(self.loading_win, text=msg, font=("Segoe UI", 10),
                fg=THEME["text"], bg=THEME["bg"]).pack()
        
        self.loading_win.update()

    def show_result_window(self):
        if self.loading_win:
            try: self.loading_win.destroy()
            except: pass
            self.loading_win = None
            
        if not self.last_result: return
        
        if self.result_win:
            try: self.result_win.destroy()
            except: pass
        
        data = self.last_result
        
        self.result_win = tk.Toplevel(self.root)
        self.result_win.title("Veritas Analysis")
        self.result_win.geometry("480x750") # Taller for new design
        self.result_win.configure(bg=THEME["bg"])
        self.result_win.attributes('-topmost', True)
        
        # --- STYLES ---
        # Fonts
        F_TITLE = ("Segoe UI", 18, "bold")
        F_HEAD = ("Segoe UI", 12, "bold")
        F_BODY = ("Segoe UI", 10)
        F_BADGE = ("Segoe UI", 9, "bold")
        F_SMALL = ("Segoe UI", 9)
        
        # --- HEADER ---
        header = tk.Frame(self.result_win, bg=THEME["bg"], pady=20, padx=25)
        header.pack(fill=tk.X)
        
        # Icon placeholder (Label)
        tk.Label(header, text="🛡️", font=("Segoe UI", 24), bg=THEME["bg"], fg=THEME["purple"]).pack(side=tk.LEFT)
        
        info = tk.Frame(header, bg=THEME["bg"], padx=15)
        info.pack(side=tk.LEFT)
        tk.Label(info, text="Veritas", font=F_TITLE, fg=THEME["text"], bg=THEME["bg"]).pack(anchor="w")
        tk.Label(info, text=f"Source: {data.get('ai_source', 'AI')}", font=F_SMALL, fg=THEME["text_dim"], bg=THEME["bg"]).pack(anchor="w")

        # --- STATUS BAR ---
        status = tk.Frame(self.result_win, bg=THEME["card"], padx=20, pady=12)
        status.pack(fill=tk.X, padx=25, pady=(0, 25))
        
        # Status Dot
        dot_canvas = tk.Canvas(status, width=10, height=10, bg=THEME["card"], highlightthickness=0)
        dot_canvas.pack(side=tk.LEFT)
        dot_canvas.create_oval(0, 0, 10, 10, fill=THEME["green"], outline="")
        
        tk.Label(status, text="Analysis complete", font=F_BODY, fg=THEME["text_dim"], bg=THEME["card"], padx=10).pack(side=tk.LEFT)

        # --- RESULT CARD ---
        card = tk.Frame(self.result_win, bg=THEME["card"], padx=25, pady=25)
        card.pack(fill=tk.BOTH, expand=False, padx=25, pady=(0, 20))
        
        # Header Row: Icon + Title + Badge
        head_row = tk.Frame(card, bg=THEME["card"])
        head_row.pack(fill=tk.X, pady=(0, 20))
        
        # Icon Box (Simulating rounded icon with background)
        icon_bg = data["color"]
        # Use simple label for icon for now, Tkinter doesn't do rounded rects easily without canvas
        icon_char = "!" if "Fake" in data["verdict"] else "✓" if "Real" in data["verdict"] else "?"
        if "Fake" in data["verdict"]: icon_bg = THEME["red"]
        elif "Real" in data["verdict"]: icon_bg = THEME["green"]
        else: icon_bg = THEME["orange"]
        
        tk.Label(head_row, text=icon_char, font=("Segoe UI", 16, "bold"), 
                 fg=icon_bg, bg=THEME["card"], width=3).pack(side=tk.LEFT)
        
        # Title Group
        title_grp = tk.Frame(head_row, bg=THEME["card"], padx=10)
        title_grp.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        display_title = "Fake News Detection"
        tk.Label(title_grp, text=display_title, font=F_HEAD, fg=THEME["text"], bg=THEME["card"]).pack(anchor="w")
        
        # Badge
        val_bg = THEME["card"] # Fallback
        val_fg = data["color"]
        if "Fake" in data["verdict"]: val_bg = THEME["danger_bg"]
        elif "Real" in data["verdict"]: val_bg = THEME["success_bg"]
        else: val_bg = THEME["warning_bg"]
        
        # Note: Tkinter Label doesn't support alpha bg easily, using fg color mainly
        tk.Label(title_grp, text=data["verdict"].upper(), font=F_BADGE, fg=val_fg, bg=THEME["card"]).pack(anchor="w")

        # Progress Bar
        conf = data["confidence"]
        prog_cnt = tk.Frame(card, bg=THEME["card"])
        prog_cnt.pack(fill=tk.X, pady=(0, 20))
        
        # Track
        prog_track = tk.Frame(prog_cnt, bg=THEME["border"], height=8)
        prog_track.pack(fill=tk.X)
        prog_track.pack_propagate(False)
        
        # Fill
        # Logic: Fake fills from right (red), Real fills from left (green)
        fill_color = data["color"]
        fill_width = int(360 * (conf/100)) # Approx width
        
        if "Fake" in data["verdict"] or "SATIRE" in data["verdict"]:
            fill = tk.Frame(prog_track, bg=THEME["red"], width=fill_width, height=8)
            fill.pack(side=tk.RIGHT)
        else:
            fill = tk.Frame(prog_track, bg=THEME["green"], width=fill_width, height=8)
            fill.pack(side=tk.LEFT)
            
        # Labels
        lbl_row = tk.Frame(prog_cnt, bg=THEME["card"], pady=5)
        lbl_row.pack(fill=tk.X)
        tk.Label(lbl_row, text="Likely Real", font=F_SMALL, fg=THEME["text_dim"], bg=THEME["card"]).pack(side=tk.LEFT)
        tk.Label(lbl_row, text=f"{conf}%", font=("Segoe UI", 10, "bold"), fg=THEME["text"], bg=THEME["card"]).pack(side=tk.LEFT, expand=True) # Center?
        tk.Label(lbl_row, text="Likely Fake", font=F_SMALL, fg=THEME["text_dim"], bg=THEME["card"]).pack(side=tk.RIGHT)

        # Metrics Grid
        met_frame = tk.Frame(card, bg=THEME["card"], pady=10)
        met_frame.pack(fill=tk.X, pady=(10, 0))
        
        metrics = data.get("metrics", {})
        # Map values to colors
        def get_val_color(v):
            if v in ["High", "Low", "Likely Accurate"]: return THEME["green"] # Context dependent in web app but simple here
            if v in ["Satire/Parody", "Likely Fake"]: return THEME["red"]
            return THEME["text"]

        for k, v in metrics.items():
            row = tk.Frame(met_frame, bg=THEME["card"], pady=4)
            row.pack(fill=tk.X)
            tk.Label(row, text=f"{k}:", font=F_SMALL, fg=THEME["text_dim"], bg=THEME["card"]).pack(side=tk.LEFT)
            tk.Label(row, text=v, font=F_SMALL, fg=get_val_color(v), bg=THEME["card"]).pack(side=tk.RIGHT)

        # --- CONTENT CARD ---
        content = tk.Frame(self.result_win, bg=THEME["card"], padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        
        tk.Label(content, text="ANALYSIS", font=F_BADGE, fg=THEME["purple"], bg=THEME["card"]).pack(anchor="w", pady=(0,8))
        
        reason = data.get("reason", "")
        tk.Label(content, text=reason, font=F_BODY, fg=THEME["text"], bg=THEME["card"], 
                wraplength=380, justify="left").pack(anchor="w")

        # --- CLOSE BUTTON ---
        btn = tk.Button(self.result_win, text="Close", command=self.result_win.destroy, 
                       bg=THEME["input"], fg=THEME["text"], 
                       font=F_BODY, relief="flat", padx=30, pady=10, 
                       activebackground=THEME["border"], activeforeground=THEME["text"])
        btn.pack(pady=10)

    def show_control_panel(self):
        if self.control_window:
            try: self.control_window.destroy()
            except: pass
            
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Veritas")
        self.control_window.geometry("280x200")
        self.control_window.configure(bg=THEME["bg"])
        
        tk.Label(self.control_window, text="🛡️ Veritas", font=("Segoe UI", 16, "bold"), 
                fg=THEME["purple"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self.control_window, text="Monitoring Clipboard...", font=("Segoe UI", 10), 
                fg=THEME["green"], bg=THEME["bg"]).pack()
                
        tk.Label(self.control_window, text="Press Alt+Shift+C to Analyze", font=("Segoe UI", 9), 
                fg=THEME["text_dim"], bg=THEME["bg"]).pack(pady=5)
        
        tk.Button(self.control_window, text="Analyze Now", command=self.analyze_clipboard,
                 bg=THEME["purple"], fg="white", relief="flat", padx=15).pack(pady=15)
                 
        self.control_window.protocol("WM_DELETE_WINDOW", lambda: self.root.quit())

    def run(self):
        if hasattr(keyboard, 'add_hotkey'):
            keyboard.add_hotkey('alt+shift+c', self.analyze_clipboard)
        self.show_control_panel()
        self.root.mainloop()

if __name__ == "__main__":
    app = VeritasDesktop()
    app.run()
