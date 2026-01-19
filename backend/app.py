from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from news_analyzer import NewsAnalyzer
from feedback_manager import FeedbackManager
from image_analyzer import ImageAnalyzer
from openai_service import OpenAIAnalyzer
from scira_service import SciraService
from fakebuster_service import FakebusterService
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
image_analyzer = ImageAnalyzer()
openai_analyzer = OpenAIAnalyzer()
scira_service = SciraService()
fakebuster = FakebusterService()  # CNN-LSTM fallback model

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
    
    # 3. Fakebuster CNN-LSTM Fallback (when OpenAI unavailable)
    elif fakebuster.has_model:
        fb_result = fakebuster.predict(text)
        if fb_result:
            fb_label = fb_result.get("label", "")
            confidence = fb_result.get("confidence", 50)
            
            if fb_label == "True":
                verdict = "Likely Real"
                color = "#2ecc71"
                reason = f"Fakebuster CNN-LSTM: Classified as credible ({confidence}% confidence)"
            else:
                verdict = "Likely Fake"
                color = "#e74c3c"
                reason = f"Fakebuster CNN-LSTM: Detected misinformation patterns ({confidence}% confidence)"
    
    # 4. Last Resort: If we have sources but no AI analysis
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


@app.route("/analyze-image", methods=["POST"])
def analyze_image_endpoint():
    """
    Comprehensive image analysis:
    1. Deepfake/AI detection (OpenAI + Local models)
    2. OCR text extraction
    3. Fake news verification of extracted text
    """
    data = request.json
    image_base64 = data.get("image")
    
    if not image_base64:
        return jsonify({"error": "No image data provided"})
    
    # Run analyses CONCURRENTLY
    openai_result = None
    local_result = None
    text_analysis = None
    
    print(f"Image analysis starting: OpenAI={openai_analyzer.has_openai}, LocalDetector={image_analyzer.has_detector}")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        
        # Submit OpenAI Vision analysis
        if openai_analyzer.has_openai:
            futures['openai'] = executor.submit(openai_analyzer.analyze_image, image_base64)
        
        # Submit local model analysis (includes OCR)
        if image_analyzer.has_detector:
            futures['local'] = executor.submit(image_analyzer.analyze_image, image_base64)
        
        # Collect results with timeout
        for key, future in futures.items():
            try:
                result = future.result(timeout=30)  # Longer timeout for OCR
                if key == 'openai':
                    openai_result = result
                elif key == 'local':
                    local_result = result
            except Exception as e:
                print(f"Image analysis {key} failed or timed out: {e}")
    
    # Check if we extracted text from the image
    extracted_text = ""
    if local_result and local_result.get("extracted_text"):
        extracted_text = local_result.get("extracted_text", "")
        
        # If significant text found, verify it for fake news
        if len(extracted_text) > 20:
            print(f"Running fake news check on extracted text: '{extracted_text[:50]}...'")
            try:
                # Run BERT + Realtime analysis on extracted text
                bert_result = pipe(extracted_text[:512])[0]
                realtime_result = news_analyzer.analyze_news(extracted_text)
                
                text_analysis = {
                    "extracted_text": extracted_text,
                    "bert_label": bert_result["label"],
                    "bert_score": round(bert_result["score"] * 100, 2),
                    "is_fake": bert_result["label"] == "LABEL_0",
                    "realtime": realtime_result
                }
            except Exception as e:
                print(f"Text analysis failed: {e}")
                text_analysis = {"extracted_text": extracted_text, "error": str(e)}
    
    # Initialize with defaults
    verdict = "Uncertain"
    confidence = 50
    reason = "Analysis could not be completed"
    color = "#f39c12"
    
    # Combine results
    openai_valid = openai_result and isinstance(openai_result, dict) and not openai_result.get("error") and openai_result.get("verdict")
    local_valid = local_result and isinstance(local_result, dict) and not local_result.get("error") and local_result.get("verdict")
    
    # Determine image verdict (deepfake detection)
    if openai_valid:
        verdict = openai_result.get("verdict", "Uncertain")
        confidence = openai_result.get("confidence", 50)
        reason = openai_result.get("reasoning", "GPT-4 Vision analysis")
        color = "#e74c3c" if "AI" in verdict or "Manipulated" in verdict else "#2ecc71"
        if verdict == "Uncertain":
            color = "#f39c12"
    elif local_valid:
        verdict = local_result.get("verdict", "Uncertain")
        confidence = local_result.get("confidence", 50)
        reason = local_result.get("reason", "Local model analysis")
        color = local_result.get("color", "#f39c12")
    
    # If text was found, add text verification to the verdict
    if text_analysis and not text_analysis.get("error"):
        if text_analysis.get("is_fake"):
            # Text in image is likely fake news
            reason += f" | ⚠️ TEXT IN IMAGE: Likely Fake News ({text_analysis['bert_score']}% confidence)"
            if "Authentic" in verdict or "Real" in verdict:
                verdict = "Contains Fake News Text"
                color = "#e74c3c"
        else:
            # Text appears credible
            if text_analysis.get("realtime", {}).get("credibility_score", 0) > 60:
                reason += f" | ✓ Text verified by {text_analysis['realtime'].get('matching_reputable_sources', 0)} sources"
    
    stats = feedback_manager.get_stats()
    
    print(f"Final image verdict: {verdict}, confidence: {confidence}")
    
    return jsonify({
        "verdict": verdict,
        "confidence": confidence,
        "color": color,
        "reason": reason,
        "ai_analysis": openai_result,
        "local_analysis": local_result,
        "text_analysis": text_analysis,  # NEW: OCR + fake news verification
        "community_accuracy": stats["accuracy"]
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
        "image_detector_available": image_analyzer.has_detector,
        "bert_loaded": True
    })


if __name__ == "__main__":
    print("="*50)
    print("Server ready at http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(port=5000, debug=True)
