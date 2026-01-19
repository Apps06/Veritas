// 1. Create the Context Menus
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "check-news",
    title: "Verify news with Veritas",
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "check-image",
    title: "Analyze image for Deepfakes",
    contexts: ["image"]
  });
});

// Handle hotkey (Alt+Shift+C) from Chrome commands
chrome.commands.onCommand.addListener((command) => {
  if (command === "verify-news") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => window.getSelection().toString()
        }, (results) => {
          const selection = results[0]?.result;
          if (selection && selection.length > 10) {
            handleAnalysis(selection, tabs[0].id);
          } else {
            console.log("No valid selection found for hotkey analysis.");
          }
        });
      }
    });
  }
});

// 2. Listen for the Click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "check-news") {
    const selectedText = info.selectionText;
    analyzeContent("http://127.0.0.1:5000/analyze", { text: selectedText }, tab);
  } else if (info.menuItemId === "check-image") {
    const imageUrl = info.srcUrl;

    // Execute conversion on the page itself to bypass CORS 
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (url) => {
          return fetch(url)
            .then(r => r.blob())
            .then(blob => new Promise((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => resolve(reader.result);
              reader.readAsDataURL(blob);
            }));
        },
        args: [imageUrl]
      });

      const base64 = results[0].result;
      analyzeContent("http://127.0.0.1:5000/analyze-image", { image: base64 }, tab);
    } catch (e) {
      console.error("Image capture failed:", e);
    }
  }
});

function analyzeContent(url, body, tab) {
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
    .then(response => response.json())
    .then(data => {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: displayResult,
        args: [data, body.text || "Image Analysis"]
      });
    })
    .catch(error => console.error("Error:", error));
}

// This function runs inside the webpage the user is looking at
function displayResult(result, originalContent) {
  // 1. Remove existing card if it exists
  const existing = document.getElementById("truth-guard-root");
  if (existing) existing.remove();

  // 2. Create the container
  const root = document.createElement("div");
  root.id = "truth-guard-root";
  document.body.appendChild(root);

  // 3. Create Shadow Root
  const shadow = root.attachShadow({ mode: "open" });

  // 4. Modern CSS for the Card
  const style = document.createElement("style");
  style.textContent = `
    .card {
      position: fixed; top: 20px; right: 20px; width: 340px;
      background: #ffffff; border-radius: 12px; z-index: 100000;
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      overflow: hidden; border: 1px solid #eee;
      animation: slideIn 0.3s ease-out;
      display: flex; flex-direction: column;
      max-height: 80vh;
    }
    @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    .header {
      padding: 15px; color: white; font-weight: bold; font-size: 1.1em;
      background: ${result.color}; display: flex; justify-content: space-between;
      flex-shrink: 0;
    }
    .content { padding: 15px; color: #333; overflow-y: auto; }
    .verdict { font-size: 1.4em; font-weight: 800; margin-bottom: 5px; color: ${result.color}; }
    .reason { font-size: 0.9em; line-height: 1.4; color: #666; margin-bottom: 12px; }
    .meter-bg { background: #eee; height: 8px; border-radius: 4px; margin: 10px 0 5px; }
    .meter-fill { 
      background: ${result.color}; height: 100%; border-radius: 4px; 
      width: ${result.confidence || '50'}%; transition: width 1s ease-in-out;
    }
    .community-accuracy {
      font-size: 0.75em; color: #888; margin-top: 5px; font-style: italic;
      display: flex; justify-content: space-between;
    }
    .sources-title { font-size: 0.8em; font-weight: bold; text-transform: uppercase; color: #888; margin: 15px 0 8px; border-top: 1px solid #eee; padding-top: 10px; }
    .source-item { font-size: 0.85em; margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid ${result.color}; }
    .source-link { color: ${result.color}; text-decoration: none; font-weight: 600; display: block; margin-bottom: 3px; }
    .source-link:hover { text-decoration: underline; }
    .source-meta { font-size: 0.8em; color: #999; }
    .report-box { 
      display: flex; gap: 10px; margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;
    }
    .report-btn { 
      flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 6px; 
      background: white; cursor: pointer; font-size: 0.8em; font-weight: 600;
      transition: all 0.2s;
    }
    .report-btn:hover { background: #f0f0f0; }
    .report-btn.active { background: #eee; border-color: #999; }
    .close-btn { cursor: pointer; border: none; background: none; color: white; font-size: 1.2em; }
    .footer { padding: 10px 15px; background: #f9f9f9; font-size: 0.75em; color: #aaa; text-align: center; flex-shrink: 0; }
  `;

  // 5. Build Sources List
  let sourcesHtml = "";
  if (result.realtime && result.realtime.sources && result.realtime.sources.length > 0) {
    sourcesHtml = `<div class="sources-title">Supporting Sources</div>`;
    result.realtime.sources.slice(0, 3).forEach(source => {
      const url = source.url || "#";
      const title = source.title || "Untitled Article";
      const domain = url !== "#" ? new URL(url).hostname.replace('www.', '') : source.source;

      sourcesHtml += `
        <div class="source-item">
          <a href="${url}" target="_blank" class="source-link">${title}</a>
          <div class="source-meta">Via ${domain}</div>
        </div>
      `;
    });
  }

  let socialHtml = "";
  // Handle social_context being a dict (new backend) or array (legacy)
  let socialPosts = [];
  const socialCtx = result.realtime && result.realtime.social_context;

  if (socialCtx) {
    if (Array.isArray(socialCtx)) {
      socialPosts = socialCtx;
    } else if (typeof socialCtx === 'object') {
      // Combine all platform lists
      if (socialCtx.twitter) socialPosts = socialPosts.concat(socialCtx.twitter);
      if (socialCtx.reddit) socialPosts = socialPosts.concat(socialCtx.reddit);
      if (socialCtx.parallel) socialPosts = socialPosts.concat(socialCtx.parallel);
    }
  }

  if (socialPosts.length > 0) {
    socialHtml = `<div class="sources-title" style="margin-top: 20px;">Social Pulse</div>`;
    socialPosts.forEach(post => {
      const icon = post.platform === "Twitter" ? "𝕏" : "🤖";
      // Ensure snippet exists
      const snippet = post.snippet || post.text || "";
      socialHtml += `
        <div class="source-item" style="border-left-color: #55acee;">
          <a href="${post.url}" target="_blank" class="source-link" style="color: #444;">${icon} ${post.title || 'Social Post'}</a>
          <div class="source-meta">${snippet.substring(0, 100)}...</div>
        </div>`;
    });
  }

  // 6. HTML Structure
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="header">
      <span>Veritas Analysis</span>
      <button class="close-btn" id="close-card">×</button>
    </div>
    <div class="content">
      <div class="verdict">${result.verdict}</div>
      <div class="reason">${result.reason}</div>
      <div class="meter-bg"><div class="meter-fill" style="width: 0%"></div></div>
      <div class="community-accuracy">
        <span>Confidence Score: ${result.confidence}%</span>
        <span>Community Accuracy: ${result.community_accuracy}%</span>
      </div>
      ${sourcesHtml}
      ${socialHtml}
      <div class="report-box">
        <button class="report-btn" id="report-correct">✅ Correct</button>
        <button class="report-btn" id="report-incorrect">❌ Incorrect</button>
      </div>
    </div>
    <div class="footer">Veritas AI v4.0 | Social Media Pulse</div>
  `;

  shadow.appendChild(style);
  shadow.appendChild(card);

  setTimeout(() => {
    shadow.querySelector('.meter-fill').style.width = `${result.confidence}%`;
  }, 100);

  shadow.getElementById("close-card").onclick = () => root.remove();

  const report = (feedback) => {
    fetch("http://127.0.0.1:5000/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: originalContent,
        verdict: result.verdict,
        feedback: feedback,
        confidence: result.confidence
      })
    }).then(() => {
      const box = shadow.querySelector('.report-box');
      box.innerHTML = `<div style="text-align: center; width: 100%; font-size: 0.8em; color: #666;">Thanks for your feedback!</div>`;
    });
  };

  shadow.getElementById("report-correct").onclick = () => report('correct');
  shadow.getElementById("report-incorrect").onclick = () => report('incorrect');
}