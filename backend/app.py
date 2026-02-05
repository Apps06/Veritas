from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from news_analyzer import NewsAnalyzer
from feedback_manager import FeedbackManager
from news_analyzer import NewsAnalyzer
from feedback_manager import FeedbackManager
from openai_service import OpenAIAnalyzer
from scira_service import SciraService
from staged_analyzer import StagedAnalyzer

app = Flask(__name__)
CORS(app)

# Load configuration and validate API keys
print("\n" + "="*50)
print("Veritas Backend v7.0 Starting...")
print("="*50)
Config.validate()

# Initialize Services
news_analyzer = NewsAnalyzer()
feedback_manager = FeedbackManager()
openai_analyzer = OpenAIAnalyzer()
scira_service = SciraService()

# Initialize 3-Stage Analyzer
staged_analyzer = StagedAnalyzer(
    news_analyzer=news_analyzer,
    openai_analyzer=openai_analyzer,
    scira_service=scira_service,
    social_service=news_analyzer.social_service
)

print("✓ Services initialized (3-Stage Pipeline: Exa+Tavily → Scira → OpenAI → Scira → X)\n")


@app.route("/analyze-staged", methods=["POST"])
def analyze_staged():
    """
    NEW: 3-Stage Verification Pipeline
    Stage 1: Exa + Tavily (source discovery)
    Bridge 1: Scira (aggregation)
    Stage 2: OpenAI GPT-4 (analysis)
    Bridge 2: Scira (enhancement)
    Stage 3: X/Twitter (social verification)
    """
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"verdict": "No text provided", "color": "gray"})
    
    # Run the 3-stage analysis
    result = staged_analyzer.analyze(text)
    
    # Get community stats
    stats = feedback_manager.get_stats()
    result["community_accuracy"] = stats["accuracy"]
    result["total_reports"] = stats["total_reports"]
    
    return jsonify(result)


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    New Pipeline: ((OpenAI + Exa + Tavily) + (Scira + X))
    Prioritizes OpenAI for analysis and Real-time Search for verification.
    """
    data = request.json
    text = data.get("text", "")
    include_realtime = data.get("include_realtime", True)

    if not text:
        return jsonify({"verdict": "No text provided", "color": "gray"})

    # Run ALL analyses CONCURRENTLY
    openai_result = None
    realtime_data = None
    scira_result = None
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        
        # 1. OpenAI Analysis (The new "Foundation Model")
        if openai_analyzer.has_openai:
            futures['openai'] = executor.submit(openai_analyzer.analyze_text, text)
        
        # 2. Real-time News Verification (Exa + Tavily + existing Social)
        if include_realtime:
            futures['realtime'] = executor.submit(news_analyzer.analyze_news, text)
            
        # 3. Scira Search (New Social/Search Layer)
        if scira_service.has_scira:
            futures['scira'] = executor.submit(scira_service.search, text)
        
        # Collect results
        for key, future in futures.items():
            try:
                result = future.result(timeout=20)
                if key == 'openai':
                    openai_result = result
                elif key == 'realtime':
                    realtime_data = result
                elif key == 'scira':
                    scira_result = result
            except Exception as e:
                print(f"Analysis {key} failed or timed out: {e}")
    
    # Merge Scira results into Realtime Data if available
    if scira_result and realtime_data:
        print(f"Scira result: {scira_result}")
    
    # --- NEW: Use OpenAI to ANALYZE the sources ---
    source_analysis = None
    if realtime_data and realtime_data.get("sources") and openai_analyzer.has_openai:
        # Pass claim + sources to OpenAI for intelligent analysis
        source_analysis = openai_analyzer.analyze_claim_with_sources(
            text, 
            realtime_data.get("sources", [])
        )
        print(f"Source analysis result: {source_analysis}")
    
    # --- VERDICT LOGIC ---
    
    # Default State
    verdict = "Uncertain"
    confidence = 0
    reason = "Could not analyze text."
    color = "#f39c12"
    
    # 1. PRIORITY: OpenAI Source Analysis (AI analyzes the evidence)
    if source_analysis and not source_analysis.get("error"):
        ai_verdict = source_analysis.get("verdict", "")
        confidence = source_analysis.get("confidence", 50)
        reason = source_analysis.get("reasoning", "Based on source analysis.")
        
        if "True" in ai_verdict or "Support" in ai_verdict:
            verdict = "Verified Real"
            color = "#2ecc71"
        elif "False" in ai_verdict or "Contradict" in ai_verdict:
            verdict = "Likely Fake"
            color = "#e74c3c"
        elif "Partially" in ai_verdict:
            verdict = "Partially True"
            color = "#f39c12"
        else:
            verdict = "Unverifiable"
            color = "#f39c12"
    
    # 2. Fallback: Direct OpenAI analysis (if no sources or source analysis failed)
    elif openai_result and not openai_result.get("error"):
        ai_verdict = openai_result.get("verdict", "Uncertain")
        confidence = openai_result.get("confidence", 50)
        reason = openai_result.get("reasoning", "OpenAI analysis.")
        
        if "True" in ai_verdict:
            verdict = "Likely Real"
            color = "#2ecc71"
        elif "False" in ai_verdict or "Misleading" in ai_verdict:
            verdict = "Likely Fake"
            color = "#e74c3c"
        else:
            verdict = "Uncertain"
            color = "#f39c12"
    
    # 3. Last Resort: If we have sources but no AI analysis
    elif realtime_data and realtime_data.get("total_sources", 0) > 0:
        verdict = "Sources Found - Review Needed"
        confidence = 40
        reason = f"Found {realtime_data.get('total_sources')} sources but AI analysis unavailable."
        color = "#f39c12"
    else:
        reason = "No sources found and AI unavailable."

    # Stats
    stats = feedback_manager.get_stats()
    
    return jsonify({
        "verdict": verdict,
        "reason": reason,
        "color": color,
        "confidence": confidence,
        "ai_analysis": openai_result,
        "source_analysis": source_analysis,  # NEW: Source-based analysis
        "realtime": realtime_data,
        "community_accuracy": stats["accuracy"],
        "total_reports": stats["total_reports"]
    })




@app.route("/report", methods=["POST"])
def report():
    """Endpoint for users to report incorrect/correct verdicts"""
    data = request.json
    text = data.get("text", "Image Analysis")
    system_verdict = data.get("verdict")
    user_feedback = data.get("feedback")
    confidence = data.get("confidence")
    
    feedback_manager.add_report(text, system_verdict, user_feedback, confidence)
    return jsonify({"status": "success", "stats": feedback_manager.get_stats()})


@app.route("/stats", methods=["GET"])
def get_stats():
    """Get system accuracy statistics"""
    return jsonify(feedback_manager.get_stats())


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify API status"""
    return jsonify({
        "status": "running",
        "version": "6.0",
        "openai_available": openai_analyzer.has_openai,
        "exa_available": news_analyzer.has_exa,
        "tavily_available": news_analyzer.has_tavily,
        "parallel_available": news_analyzer.has_parallel,
        "twitter_available": news_analyzer.has_twitter,
        "reddit_available": news_analyzer.has_reddit,
        "bert_loaded": True
    })


if __name__ == "__main__":
    print("="*50)
    print("Server ready at http://127.0.0.1:5001")
    print("="*50 + "\n")
    app.run(port=5001, debug=True)
