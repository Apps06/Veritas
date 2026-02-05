// Veritas Popup Script

class FakeBusterPopup {
  constructor() {
    this.isAnalyzing = false;
    this.currentResults = null;
    this.init();
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      this.bindElements();
      this.bindEvents();
      this.loadPreviousResults();
      this.loadFeedbackStats();
    });
  }

  bindElements() {
    // Buttons
    this.analyzeBtn = document.getElementById('analyzeBtn');
    this.settingsBtn = document.getElementById('settingsBtn');
    this.accurateBtn = document.getElementById('accurateBtn');
    this.inaccurateBtn = document.getElementById('inaccurateBtn');
    this.viewHistoryLink = document.getElementById('viewHistoryLink');

    // Status
    this.statusBar = document.getElementById('statusBar');
    this.statusText = document.getElementById('statusText');

    // Sections
    this.resultsSection = document.getElementById('resultsSection');
    this.feedbackSection = document.getElementById('feedbackSection');

    // Fake News Elements
    this.fakeNewsBar = document.getElementById('fakeNewsBar');
    this.fakeNewsPercent = document.getElementById('fakeNewsPercent');
    this.fakeNewsLabel = document.getElementById('fakeNewsLabel');
    this.sourceCredibility = document.getElementById('sourceCredibility');
    this.sensationalism = document.getElementById('sensationalism');
    this.factCheck = document.getElementById('factCheck');

    // Sources Elements
    this.sourcesCard = document.getElementById('sourcesCard');
    this.sourcesList = document.getElementById('sourcesList');

    // Feedback
    this.totalFeedback = document.getElementById('totalFeedback');
  }

  bindEvents() {
    this.analyzeBtn.addEventListener('click', () => this.startAnalysis());
    this.settingsBtn.addEventListener('click', () => this.openSettings());
    this.accurateBtn.addEventListener('click', () => this.submitFeedback(true));
    this.inaccurateBtn.addEventListener('click', () => this.submitFeedback(false));
    this.viewHistoryLink.addEventListener('click', (e) => {
      e.preventDefault();
      this.viewHistory();
    });
  }

  async startAnalysis() {
    if (this.isAnalyzing) return;

    this.isAnalyzing = true;
    this.analyzeBtn.classList.add('analyzing');
    this.analyzeBtn.querySelector('span').textContent = 'Analyzing...';
    this.updateStatus('Extracting page content...', 'analyzing');

    try {
      // Get current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab) {
        throw new Error('No active tab found');
      }

      // Send message to background script to analyze
      const results = await chrome.runtime.sendMessage({
        action: 'analyze',
        tabId: tab.id,
        url: tab.url,
        title: tab.title
      });

      if (results.error) {
        throw new Error(results.error);
      }

      this.currentResults = results;
      this.displayResults(results);
      this.saveResults(tab.url, results);
      this.updateStatus('Analysis complete', 'complete');

    } catch (error) {
      console.error('Analysis error:', error);
      this.updateStatus(`Error: ${error.message}`, 'error');
    } finally {
      this.isAnalyzing = false;
      this.analyzeBtn.classList.remove('analyzing');
      this.analyzeBtn.querySelector('span').textContent = 'Analyze Current Page';
    }
  }

  displayResults(results) {
    // Show results sections
    this.resultsSection.style.display = 'flex';
    this.feedbackSection.style.display = 'block';

    // Animate fake news results
    const fakeNewsScore = results.fakeNews.score;
    setTimeout(() => {
      this.animateConfidence(this.fakeNewsBar, this.fakeNewsPercent, fakeNewsScore);
      this.fakeNewsLabel.textContent = this.getLabel(fakeNewsScore);
      this.fakeNewsLabel.className = 'result-label ' + this.getLabelClass(fakeNewsScore);
    }, 100);

    // Update fake news details
    this.sourceCredibility.textContent = results.fakeNews.sourceCredibility;
    this.sourceCredibility.className = 'detail-value ' + this.getValueClass(results.fakeNews.sourceScore);

    this.sensationalism.textContent = results.fakeNews.sensationalism;
    this.sensationalism.className = 'detail-value ' + this.getValueClass(100 - results.fakeNews.sensationalismScore);

    this.factCheck.textContent = results.fakeNews.factCheck;
    this.factCheck.className = 'detail-value ' + this.getValueClass(results.fakeNews.factCheckScore);

    // Render Credible Sources
    this.renderSources(results.fakeNews.credibleSources);
  }

  renderSources(sources) {
    this.sourcesCard.style.display = 'block';

    if (!sources || sources.length === 0) {
      this.sourcesList.innerHTML = `
        <div class="detail-item" style="padding: 10px; color: var(--text-muted); font-size: 11px; text-align: center;">
          No direct credible sources found for this analysis. 
          The score is based on local analysis and metadata.
        </div>
      `;
      return;
    }

    this.sourcesList.innerHTML = sources.map(source => `
      <a href="${source.url}" target="_blank" class="source-item">
        <div class="source-header">
          <span class="source-title">${source.title}</span>
          ${source.isTrusted ? '<span class="source-badge">Trusted Source</span>' : (source.isFallback ? '<span class="source-badge" style="background: rgba(99, 102, 241, 0.15); color: var(--accent-primary);">Click to Verify</span>' : '')}
        </div>
        <div class="source-url">${new URL(source.url).hostname}</div>
      </a>
    `).join('');
  }

  animateConfidence(bar, percentEl, targetValue) {
    let current = 0;
    const increment = targetValue / 50;

    const animate = () => {
      current += increment;
      if (current >= targetValue) {
        current = targetValue;
        bar.style.width = `${current}%`;
        percentEl.textContent = `${Math.round(current)}%`;
        bar.className = 'confidence-fill ' + this.getBarClass(current);
        return;
      }
      bar.style.width = `${current}%`;
      percentEl.textContent = `${Math.round(current)}%`;
      requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }

  getLabel(score) {
    if (score < 30) return 'Likely Authentic';
    if (score < 60) return 'Uncertain';
    return 'Likely Fake';
  }

  getLabelClass(score) {
    if (score < 30) return 'safe';
    if (score < 60) return 'warning';
    return 'danger';
  }

  getBarClass(score) {
    if (score < 30) return 'low';
    if (score < 60) return 'medium';
    return 'high';
  }

  getValueClass(score) {
    if (score >= 70) return 'good';
    if (score >= 40) return 'moderate';
    return 'bad';
  }

  updateStatus(text, type) {
    this.statusText.textContent = text;
    const dot = this.statusBar.querySelector('.pulse-dot');
    const ring = this.statusBar.querySelector('.pulse-ring');

    switch (type) {
      case 'analyzing':
        dot.style.background = 'var(--warning)';
        ring.style.borderColor = 'var(--warning)';
        break;
      case 'complete':
        dot.style.background = 'var(--success)';
        ring.style.borderColor = 'var(--success)';
        break;
      case 'error':
        dot.style.background = 'var(--danger)';
        ring.style.borderColor = 'var(--danger)';
        break;
      default:
        dot.style.background = 'var(--accent-primary)';
        ring.style.borderColor = 'var(--accent-primary)';
    }
  }

  async submitFeedback(isAccurate) {
    if (!this.currentResults) return;

    // Visual feedback
    if (isAccurate) {
      this.accurateBtn.classList.add('selected');
      this.inaccurateBtn.disabled = true;
    } else {
      this.inaccurateBtn.classList.add('selected');
      this.accurateBtn.disabled = true;
    }

    // Get current tab URL
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Send feedback to background
    await chrome.runtime.sendMessage({
      action: 'submitFeedback',
      url: tab.url,
      isAccurate: isAccurate,
      results: this.currentResults,
      timestamp: Date.now()
    });

    // Update stats
    this.loadFeedbackStats();
  }

  async loadFeedbackStats() {
    const stats = await chrome.runtime.sendMessage({ action: 'getFeedbackStats' });
    if (stats) {
      this.totalFeedback.textContent = `${stats.total} total reports (${stats.accurate} accurate, ${stats.inaccurate} inaccurate)`;
    }
  }

  async loadPreviousResults() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const results = await chrome.runtime.sendMessage({
      action: 'getCachedResults',
      url: tab.url
    });

    if (results) {
      this.currentResults = results;
      this.displayResults(results);
      this.updateStatus('Previous analysis loaded', 'complete');
    }
  }

  async saveResults(url, results) {
    await chrome.runtime.sendMessage({
      action: 'cacheResults',
      url: url,
      results: results
    });
  }

  openSettings() {
    chrome.runtime.openOptionsPage();
  }

  viewHistory() {
    chrome.tabs.create({ url: 'history.html' });
  }
}

// Initialize popup
new FakeBusterPopup();
