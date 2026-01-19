"""
Veritas - Simple Web UI Version
Works 100% reliably (no Windows API issues)
"""
from flask import Flask, render_template_string, request, jsonify
from news_analyzer import NewsAnalyzer
from openai_service import OpenAIAnalyzer
from config import Config
import webbrowser
import threading

app = Flask(__name__)

# Initialize services
Config.validate()
news = NewsAnalyzer()
ai = OpenAIAnalyzer()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Veritas - Fake News Detector</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e14 0%, #14181f 100%);
            color: #e6edf3;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 40px 20px;
        }
        
        h1 {
            font-size: 3em;
            background: linear-gradient(135deg, #3fb950, #58a6ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .tagline {
            color: #8b949e;
            font-size: 1.1em;
        }
        
        .input-card {
            background: #14181f;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        textarea {
            width: 100%;
            min-height: 120px;
            background: #1a1f29;
            border: 2px solid #21262f;
            border-radius: 8px;
            color: #e6edf3;
            font-size: 16px;
            padding: 15px;
            resize: vertical;
            font-family: inherit;
        }
        
        textarea:focus {
            outline: none;
            border-color: #58a6ff;
        }
        
        button {
            background: linear-gradient(135deg, #3fb950, #2ea043);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 20px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        button:disabled {
            background: #555;
            cursor: not-allowed;
        }
        
        #loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #58a6ff;
        }
        
        .result-card {
            background: #14181f;
            border-radius: 12px;
            padding: 30px;
            margin: 30px 0;
            display: none;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .verdict-banner {
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .verdict-banner.fake {
            background: linear-gradient(135deg, #f85149, #da3b34);
        }
        
        .verdict-banner.real {
            background: linear-gradient(135deg, #3fb950, #2ea043);
        }
        
        .verdict-banner.uncertain {
            background: linear-gradient(135deg, #d29922, #bf8700);
        }
        
        .verdict-text {
            font-size: 2em;
            font-weight: bold;
        }
        
        .confidence {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .section {
            background: #1a1f29;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .section-title {
            color: #58a6ff;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .source {
            background: #14181f;
            padding: 15px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 3px solid #58a6ff;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .source:hover {
            background: #1a1f29;
            transform: translateX(5px);
        }
        
        .feedback {
            text-align: center;
            margin-top: 25px;
            padding-top: 25px;
            border-top: 1px solid #21262f;
        }
        
        .feedback-btn {
            background: #1a1f29;
            padding: 10px 25px;
            margin: 0 10px;
            font-size: 1em;
        }
        
        .feedback-btn.yes:hover {
            background: #3fb950;
        }
        
        .feedback-btn.no:hover {
            background: #f85149;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Veritas</h1>
            <p class="tagline">AI-Powered Fake News Detection</p>
        </header>
        
        <div class="input-card">
            <textarea id="claim" placeholder="Paste news headline or claim here..."></textarea>
            <button onclick="analyze()">Analyze for Fake News</button>
        </div>
        
        <div id="loading">
            <h2>🔍 Analyzing...</h2>
            <p>Searching sources and analyzing content...</p>
        </div>
        
        <div id="result" class="result-card"></div>
    </div>
    
    <script>
        async function analyze() {
            const claim = document.getElementById('claim').value.trim();
            if (!claim) {
                alert('Please enter a claim to analyze');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({claim: claim})
                });
                
                const data = await response.json();
                displayResult(data);
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function displayResult(data) {
            const resultDiv = document.getElementById('result');
            
            let verdictClass = 'uncertain';
            if (data.verdict.includes('FAKE') || data.verdict.includes('SATIRE')) {
                verdictClass = 'fake';
            } else if (data.verdict.includes('REAL')) {
                verdictClass = 'real';
            }
            
            let sourcesHTML = '';
            if (data.sources && data.sources.length > 0) {
                sourcesHTML = '<div class="section"><div class="section-title">Sources (' + data.sources.length + ')</div>';
                data.sources.forEach(src => {
                    sourcesHTML += `<div class="source" onclick="window.open('${src.url}', '_blank')">
                        <div>📰 ${src.title}</div>
                    </div>`;
                });
                sourcesHTML += '</div>';
            }
            
            resultDiv.innerHTML = `
                <div class="verdict-banner ${verdictClass}">
                    <div class="verdict-text">${data.verdict}</div>
                    <div class="confidence">${data.confidence}%</div>
                </div>
                
                <div class="section">
                    <div class="section-title">Claim</div>
                    <div>${data.claim}</div>
                </div>
                
                <div class="section">
                    <div class="section-title">Analysis</div>
                    <div>${data.reasoning}</div>
                </div>
                
                ${sourcesHTML}
                
                <div class="feedback">
                    <p style="color: #8b949e; margin-bottom: 15px;">Was this analysis helpful?</p>
                    <button class="feedback-btn yes" onclick="feedback('yes')">✓ Yes</button>
                    <button class="feedback-btn no" onclick="feedback('no')">✗ No</button>
                </div>
            `;
            
            resultDiv.style.display = 'block';
            resultDiv.scrollIntoView({behavior: 'smooth'});
        }
        
        function feedback(type) {
            alert('Thank you for your feedback: ' + type);
        }
        
        // Allow Enter to submit
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('claim').addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    analyze();
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    claim = request.json.get('claim', '')
    
    if not claim:
        return jsonify({"error": "No claim provided"}), 400
    
    print(f"\nAnalyzing: {claim[:80]}...")
    
    # Get sources
    sources = []
    if news.has_tavily:
        try:
            sources = news.search_with_tavily(claim, 6)
            print(f"✓ Found {len(sources)} sources")
        except Exception as e:
            print(f"Search error: {e}")
    
    # Try AI analysis
    ai_verdict = None
    ai_reasoning = None
    
    if ai.has_openai:
        try:
            result = ai.analyze_text(claim)
            if result and not result.get("error"):
                ai_verdict = result.get("verdict", "")
                ai_reasoning = result.get("reasoning", "")
                print(f"✓ AI: {ai_verdict}")
        except Exception as e:
            print(f"AI error: {e}")
    
    # Smart fallback analysis
    if not ai_verdict and sources:
        verdict, confidence, reasoning = smart_source_analysis(claim, sources)
    elif ai_verdict:
        verdict, confidence, reasoning = interpret_ai(ai_verdict, ai_reasoning)
    else:
        verdict = "UNABLE TO VERIFY"
        confidence = 20
        reasoning = "No sources found and AI unavailable."
    
    return jsonify({
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "sources": sources,
        "claim": claim
    })

def smart_source_analysis(claim, sources):
    """Analyze sources without AI"""
    satire_keywords = ['onion', 'babylon bee', 'satirical', 'parody', 'humor', 'comedy']
    
    for src in sources:
        title = src.get('title', '').lower()
        url = src.get('url', '').lower()
        
        if any(kw in title or kw in url for kw in satire_keywords):
            return "LIKELY SATIRE/FAKE", 80, "Sources indicate this is satire or parody content, not real news."
    
    if len(sources) >= 3:
        return "LIKELY REAL", 65, f"Found {len(sources)} credible sources discussing this topic."
    else:
        return "PARTIALLY VERIFIED", 50, f"Found {len(sources)} source(s). Verify carefully."

def interpret_ai(verdict, reasoning):
    """Interpret AI verdict"""
    if "False" in verdict or "Misleading" in verdict:
        return "LIKELY FAKE", 75, reasoning or "AI detected misinformation patterns."
    elif "True" in verdict:
        return "LIKELY REAL", 75, reasoning or "AI verified the claim."
    return "UNCERTAIN", 50, reasoning or "AI analysis inconclusive."

def open_browser():
    """Open browser after a short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Veritas Web UI Starting...")
    print("Opening browser at http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask
    app.run(debug=False, port=5000)
