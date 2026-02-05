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
import base64

app = Flask(__name__)

# Initialize services
Config.validate()
news = NewsAnalyzer()
ai = OpenAIAnalyzer()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veritas - AI Truth Detector</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0e14;
            --card-bg: #14181f;
            --text-primary: #ffffff;
            --text-secondary: #8b949e;
            --accent-purple: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            --success: #3fb950;
            --danger: #f85149;
            --warning: #d29922;
            --toggle-bg: #21262d;
            --toggle-hover: #30363d;
            --input-bg: #0d1117;
            --input-border: #30363d;
        }

        body.light-theme {
            --bg-color: #f6f8fa;
            --card-bg: #ffffff;
            --text-primary: #1f2328;
            --text-secondary: #636c76;
            --accent-purple: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            --success: #1a7f37;
            --danger: #d1242f;
            --warning: #9a6700;
            --toggle-bg: #ebeff2;
            --toggle-hover: #d0d7de;
            --input-bg: #ffffff;
            --input-border: #d0d7de;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 450px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            font-size: 28px;
            color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .app-info {
            display: flex;
            flex-direction: column;
        }

        .app-name {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(90deg, #8b5cf6, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .app-desc {
            font-size: 11px;
            color: #4b5563;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .theme-toggle {
            color: var(--text-secondary);
            cursor: pointer;
            width: 36px;
            height: 36px;
            background: var(--toggle-bg); 
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }

        .theme-toggle:hover {
            background: var(--toggle-hover);
            color: var(--text-primary);
        }

        /* Status Bar */
        .status-bar {
            background: var(--card-bg);
            padding: 16px 24px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            color: var(--text-secondary);
            border: 1px solid rgba(48, 54, 61, 0.5);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(63, 185, 80, 0.4);
        }

        /* Main Action Button */
        .analyze-btn {
            background: var(--accent-gradient);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 18px;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            cursor: pointer;
            transition: box-shadow 0.2s, transform 0.2s;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25);
            width: 100%;
        }

        .analyze-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 25px rgba(99, 102, 241, 0.35);
        }
        
        .analyze-btn:active {
            transform: translateY(0);
        }

        /* Cards */
        .result-card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(48, 54, 61, 0.5);
            margin-bottom: 20px;
            display: none; /* Hidden by default */
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }

        .card-icon {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }

        .icon-fake { background: rgba(248, 81, 73, 0.1); color: var(--danger); }
        .icon-real { background: rgba(63, 185, 80, 0.1); color: var(--success); }
        .icon-uncertain { background: rgba(210, 153, 34, 0.1); color: var(--warning); }

        .card-title-group {
            flex: 1;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 4px;
        }

        .verdict-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            background: rgba(248, 81, 73, 0.15);
            color: var(--danger);
        }
        
        .badge-real { background: rgba(63, 185, 80, 0.15); color: var(--success); }
        .badge-uncertain { background: rgba(210, 153, 34, 0.15); color: var(--warning); }

        /* Progress Bar */
        .progress-container {
            margin: 10px 0 24px 0;
        }
        
        .progress-track {
            height: 8px;
            background: #21262d;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .progress-labels {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 8px;
            font-weight: 500;
        }

        .progress-value-overlay {
            color: white;
            font-weight: 700;
            text-align: center;
            margin-top: 5px;
            font-size: 12px;
        }

         /* Metrics */
        .metrics-grid {
            border-top: 1px solid #21262d;
            padding-top: 20px;
            display: grid;
            gap: 12px;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        .metric-label {
            color: var(--text-secondary);
        }
        
        .metric-value {
            font-weight: 600;
        }

        .val-danger { color: var(--danger); }
        .val-success { color: var(--success); }
        .val-warning { color: var(--warning); }
        .val-neutral { color: var(--text-primary); }

        /* Input Card */
        .input-card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(48, 54, 61, 0.5);
            margin-bottom: 20px;
        }

        .input-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #21262d;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 8px;
            transition: 0.2s;
        }

        .tab-btn.active {
            background: rgba(99, 102, 241, 0.1);
            color: #6366f1;
        }

        textarea {
            width: 100%;
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 12px;
            color: var(--text-primary);
            padding: 12px;
            min-height: 100px;
            font-family: inherit;
            resize: vertical;
        }

        textarea:focus {
            outline: none;
            border-color: #6366f1;
        }
        
        /* Dropzone */
        .drop-zone {
            border: 2px dashed #30363d;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: 0.2s;
        }
        
        .drop-zone:hover {
            border-color: #6366f1;
            background: rgba(99, 102, 241, 0.05);
        }

        .hidden { display: none !important; }
        
        /* Loading */
        .loading-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: var(--bg-color);
            opacity: 0.9;
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            flex-direction: column;
            gap: 15px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(99, 102, 241, 0.3);
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }

    </style>
</head>
<body>

<div class="container">
    <header>
        <div class="logo-section">
            <div class="logo-icon">
                <i class="fas fa-shield-alt"></i>
            </div>
            <div class="app-info">
                <span class="app-name">Veritas</span>
                <span class="app-desc">AI-Powered Truth Detector</span>
            </div>
        </div>
        <div class="theme-toggle" onclick="toggleTheme()">
            <i class="fas fa-moon" id="theme-icon"></i>
        </div>
    </header>

    <div class="status-bar">
        <div class="status-dot"></div>
        <span>Analysis complete</span>
    </div>

    <!-- Input Section -->
    <div class="input-card" id="input-section">
        <div id="tab-text">
            <textarea id="claim-input" placeholder="Paste text or URL to analyze..."></textarea>
        </div>
    </div>

    <button class="analyze-btn" onclick="runAnalysis()">
        <i class="fas fa-search"></i>
        Analyze Current Page
    </button>

    <!-- Card 1: Fake News Detection -->
    <div id="card-news" class="result-card">
        <div class="card-header">
            <div class="card-icon icon-fake" id="news-icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="card-title-group">
                <div class="card-title">Fake News Detection</div>
                <div class="verdict-badge" id="news-badge">Likely Fake</div>
            </div>
        </div>

        <div class="progress-container">
            <div class="progress-track">
                <div class="progress-fill" id="news-progress" style="width: 0%; background: var(--danger);"></div>
            </div>
            <div class="progress-labels">
                <span>Likely Real</span>
                <span id="news-percent">98%</span>
                <span>Likely Fake</span>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-row">
                <span class="metric-label">Source Credibility:</span>
                <span class="metric-value val-danger" id="news-source">Satire/Parody</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Sensationalism:</span>
                <span class="metric-value val-success" id="news-sensation">Low</span>
            </div>
             <div class="metric-row">
                <span class="metric-label">Fact Check:</span>
                <span class="metric-value val-success" id="news-factcheck">Likely Accurate</span>
            </div>
        </div>
    </div>


</div>

<div id="loading" class="loading-overlay hidden">
    <div class="spinner"></div>
    <div style="color: white; font-weight: 600;">Analyzing...</div>
</div>

<script>
    async function runAnalysis() {
        const loading = document.getElementById('loading');
        const newsCard = document.getElementById('card-news');
        
        loading.classList.remove('hidden');
        newsCard.style.display = 'none';

        try {
            const text = document.getElementById('claim-input').value;
            if (!text) throw new Error("Please enter text");
            
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({claim: text})
            });
            const data = await res.json();
            renderTextResult(data);
        } catch (e) {
            alert(e.message);
        } finally {
            loading.classList.add('hidden');
        }
    }

    function renderTextResult(data) {
        // Show Fake News Card
        const card = document.getElementById('card-news');
        const badge = document.getElementById('news-badge');
        const progress = document.getElementById('news-progress');
        const icon = document.getElementById('news-icon');
        
        // Map Verdict
        const v = data.verdict.toUpperCase();
        let color = 'var(--warning)';
        let w = '50%';
        let badgeText = 'Uncertain';
        let bgClass = 'badge-uncertain';
        let iconClass = 'icon-uncertain';
        
        const confidence = data.confidence || 50;
        
        if (v.includes('FAKE') || v.includes('SATIRE')) {
            color = 'var(--danger)';
            w = `${confidence}%`;
            progress.style.marginLeft = 'auto'; // Fill from right (towards center)
            progress.style.marginRight = '0';
            badgeText = 'Likely Fake';
            bgClass = 'verdict-badge'; 
            iconClass = 'icon-fake';
        } else if (v.includes('REAL')) {
            color = 'var(--success)';
            w = `${confidence}%`;
            progress.style.marginLeft = '0'; // Fill from left (towards center)
            progress.style.marginRight = 'auto';
            badgeText = 'Likely Real';
            bgClass = 'badge-real';
            iconClass = 'icon-real';
        }

        badge.className = `verdict-badge ${bgClass}`;
        badge.innerText = badgeText;
        progress.style.background = color;
        progress.style.width = w;
        icon.className = `card-icon ${iconClass}`;
        
        document.getElementById('news-percent').innerText = `${data.confidence}%`;

        // Update Metrics
        document.getElementById('news-source').innerText = data.sources.length + ' Sources';
        document.getElementById('news-source').className = 'metric-value val-neutral';
        
        document.getElementById('news-factcheck').innerText = data.verdict;
        document.getElementById('news-factcheck').style.color = color;
        
        card.style.display = 'block';
    }

    function toggleTheme() {
        const body = document.body;
        const icon = document.getElementById('theme-icon');
        
        body.classList.toggle('light-theme');
        const isLight = body.classList.contains('light-theme');
        
        icon.className = isLight ? 'fas fa-sun' : 'fas fa-moon';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    }

    // Load saved theme
    (function() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
            document.getElementById('theme-icon').className = 'fas fa-sun';
        }
    })();

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
