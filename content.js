// Veritas Content Script
// Runs on every page to extract content and provide visual indicators

(function () {
  'use strict';

  // Prevent multiple injections
  if (window.fakeBusterInitialized) return;
  window.fakeBusterInitialized = true;

  // Configuration
  const CONFIG = {
    indicatorClass: 'fakebuster-indicator',
    badgeClass: 'fakebuster-badge',
    tooltipClass: 'fakebuster-tooltip'
  };

  // Store analysis results
  let pageAnalysis = null;

  // Initialize content script
  function init() {
    // Listen for messages from popup/background
    chrome.runtime.onMessage.addListener(handleMessage);

    // Check if page already analyzed
    checkCachedAnalysis();
  }

  function handleMessage(request, sender, sendResponse) {
    switch (request.action) {
      case 'getPageContent':
        sendResponse(extractPageContent());
        break;

      case 'showIndicator':
        showAnalysisIndicator(request.results);
        sendResponse({ success: true });
        break;

      case 'highlightSuspicious':
        highlightSuspiciousElements(request.elements);
        sendResponse({ success: true });
        break;

      default:
        sendResponse({ error: 'Unknown action' });
    }
    return true;
  }

  // Extract page content for analysis
  function extractPageContent() {
    const content = {
      title: document.title,
      url: window.location.href,
      text: '',
      images: [],
      metadata: {}
    };

    // Get main content
    const article = findMainContent();
    const textElements = article.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li');

    textElements.forEach(el => {
      const text = el.textContent.trim();
      if (text.length > 20) {
        content.text += text + ' ';
      }
    });

    // Get headline
    const headline = document.querySelector('h1') || document.querySelector('[class*="headline"]');
    content.headline = headline ? headline.textContent.trim() : '';

    // Get images
    document.querySelectorAll('img').forEach(img => {
      if (img.naturalWidth > 100 && img.naturalHeight > 100) {
        content.images.push({
          src: img.src,
          alt: img.alt || '',
          width: img.naturalWidth,
          height: img.naturalHeight,
          element: getElementPath(img)
        });
      }
    });

    // Get metadata
    content.metadata = extractMetadata();

    // Limit text length
    content.text = content.text.slice(0, 10000);

    return content;
  }

  function findMainContent() {
    // Try common content containers
    const selectors = [
      'article',
      '[role="main"]',
      '.article-content',
      '.post-content',
      '.entry-content',
      '.content',
      'main',
      '#content'
    ];

    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.length > 500) {
        return el;
      }
    }

    return document.body;
  }

  function extractMetadata() {
    const metadata = {};

    // Author
    const authorMeta = document.querySelector('meta[name="author"]');
    const authorEl = document.querySelector('[class*="author"], [rel="author"]');
    metadata.author = authorMeta?.content || authorEl?.textContent?.trim() || '';

    // Publish date
    const dateMeta = document.querySelector('meta[property="article:published_time"]');
    const dateEl = document.querySelector('time, [class*="date"], [class*="published"]');
    metadata.publishDate = dateMeta?.content || dateEl?.getAttribute('datetime') || dateEl?.textContent?.trim() || '';

    // Publisher
    const publisherMeta = document.querySelector('meta[property="og:site_name"]');
    metadata.publisher = publisherMeta?.content || window.location.hostname;

    return metadata;
  }

  function getElementPath(element) {
    const path = [];
    let current = element;

    while (current && current !== document.body) {
      let selector = current.tagName.toLowerCase();
      if (current.id) {
        selector += '#' + current.id;
      } else if (current.className) {
        selector += '.' + current.className.split(' ').join('.');
      }
      path.unshift(selector);
      current = current.parentElement;
    }

    return path.join(' > ');
  }

  // Visual indicators
  function showAnalysisIndicator(results) {
    pageAnalysis = results;

    // Remove existing indicator
    removeIndicator();

    // Create floating indicator
    const indicator = document.createElement('div');
    indicator.id = 'fakebuster-floating-indicator';
    indicator.className = CONFIG.indicatorClass;

    const score = results.fakeNews?.score || 0;
    const colorClass = score < 30 ? 'safe' : score < 60 ? 'warning' : 'danger';

    indicator.innerHTML = `
      <div class="fakebuster-header">
        <svg class="fakebuster-icon" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L3 7V12C3 17.55 6.84 22.74 12 24C17.16 22.74 21 17.55 21 12V7L12 2Z" fill="currentColor"/>
          <path d="M10 17L6 13L7.41 11.59L10 14.17L16.59 7.58L18 9L10 17Z" fill="white"/>
        </svg>
        <span>Veritas</span>
        <button class="fakebuster-close" onclick="this.closest('#fakebuster-floating-indicator').remove()">×</button>
      </div>
      <div class="fakebuster-scores">
        <div class="fakebuster-score-item ${colorClass}">
          <span class="label">Fake News Risk</span>
          <span class="value">${results.fakeNews?.score || 0}%</span>
        </div>
      </div>
      <div class="fakebuster-verdict ${colorClass}">
        ${getVerdict(score)}
      </div>
    `;

    document.body.appendChild(indicator);

    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (indicator.parentNode) {
        indicator.style.opacity = '0';
        setTimeout(() => indicator.remove(), 300);
      }
    }, 10000);
  }

  function getVerdict(score) {
    if (score < 30) return '✓ Content appears authentic';
    if (score < 60) return '⚠ Exercise caution';
    return '⚠ High risk of misinformation';
  }

  function removeIndicator() {
    const existing = document.getElementById('fakebuster-floating-indicator');
    if (existing) existing.remove();
  }

  function highlightSuspiciousElements(elements) {
    elements.forEach(element => {
      const el = document.querySelector(element.selector);
      if (el) {
        el.classList.add('fakebuster-suspicious');

        // Add tooltip
        const tooltip = document.createElement('div');
        tooltip.className = CONFIG.tooltipClass;
        tooltip.textContent = element.reason;
        el.appendChild(tooltip);
      }
    });
  }

  async function checkCachedAnalysis() {
    try {
      const results = await chrome.runtime.sendMessage({
        action: 'getCachedResults',
        url: window.location.href
      });

      if (results) {
        pageAnalysis = results;
      }
    } catch (error) {
      console.log('Veritas: No cached analysis available');
    }
  }

  // Inject styles
  function injectStyles() {
    if (document.getElementById('fakebuster-styles')) return;

    const style = document.createElement('style');
    style.id = 'fakebuster-styles';
    style.textContent = `
      #fakebuster-floating-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 260px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #fff;
        z-index: 999999;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        animation: fakebuster-slideIn 0.3s ease;
        transition: opacity 0.3s ease;
      }

      @keyframes fakebuster-slideIn {
        from {
          transform: translateY(20px);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      .fakebuster-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }

      .fakebuster-icon {
        width: 24px;
        height: 24px;
        color: #6366f1;
      }

      .fakebuster-header span {
        flex: 1;
        font-weight: 600;
        font-size: 14px;
      }

      .fakebuster-close {
        width: 24px;
        height: 24px;
        border: none;
        background: rgba(255, 255, 255, 0.1);
        color: #999;
        border-radius: 50%;
        cursor: pointer;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .fakebuster-close:hover {
        background: rgba(255, 255, 255, 0.2);
        color: #fff;
      }

      .fakebuster-scores {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 10px;
      }

      .fakebuster-score-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        font-size: 12px;
      }

      .fakebuster-score-item .label {
        color: #a0a0b2;
      }

      .fakebuster-score-item .value {
        font-weight: 600;
      }

      .fakebuster-score-item.safe .value {
        color: #10b981;
      }

      .fakebuster-score-item.warning .value {
        color: #f59e0b;
      }

      .fakebuster-score-item.danger .value {
        color: #ef4444;
      }

      .fakebuster-verdict {
        text-align: center;
        padding: 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
      }

      .fakebuster-verdict.safe {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
      }

      .fakebuster-verdict.warning {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
      }

      .fakebuster-verdict.danger {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
      }

      .fakebuster-suspicious {
        outline: 2px dashed #f59e0b !important;
        outline-offset: 2px;
        position: relative;
      }

      .fakebuster-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1a2e;
        color: #fff;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 11px;
        white-space: nowrap;
        z-index: 999998;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s;
      }

      .fakebuster-suspicious:hover .fakebuster-tooltip {
        opacity: 1;
      }
    `;

    document.head.appendChild(style);
  }

  // Initialize
  injectStyles();
  init();
})();
