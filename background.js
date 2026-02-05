// Veritas Background Service Worker

// Scira AI API Configuration (Placeholder)
const SCIRA_API_CONFIG = {
    baseUrl: 'https://api.scira.ai/v1',
    apiKey: '', // User will configure this in options
    endpoints: {
        search: '/search',
        factCheck: '/agents/web'
    }
};

// Cache for analysis results
const resultsCache = new Map();
const CACHE_DURATION = 0; // Disabled for testing/debugging

// Feedback storage
let feedbackData = {
    total: 0,
    accurate: 0,
    inaccurate: 0,
    reports: []
};

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
    console.log('Veritas installed');

    chrome.contextMenus.create({
        id: 'analyzeSelection',
        title: 'Check for Fake News',
        contexts: ['selection']
    });

    // Load saved feedback data
    loadFeedbackData();
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'analyzeSelection') {
        analyzeTextSelection(info.selectionText, tab);
    }
});

// Message handler
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleMessage(request, sender).then(sendResponse);
    return true; // Keep channel open for async response
});

async function handleMessage(request, sender) {
    switch (request.action) {
        case 'analyze':
            return await performFullAnalysis(request.tabId, request.url, request.title);

        case 'getCachedResults':
            return getCachedResults(request.url);

        case 'cacheResults':
            cacheResults(request.url, request.results);
            return { success: true };

        case 'submitFeedback':
            return submitFeedback(request);

        case 'getFeedbackStats':
            return getFeedbackStats();

        case 'getApiKey':
            return await getApiKey();

        case 'setApiKey':
            return await setApiKey(request.apiKey);

        default:
            return { error: 'Unknown action' };
    }
}

// Main analysis function
async function performFullAnalysis(tabId, url, title) {
    try {
        // Get page content from content script
        const pageContent = await getPageContent(tabId);

        // Perform fake news analysis
        const fakeNewsResult = await analyzeFakeNews(pageContent, url, title);

        return {
            fakeNews: fakeNewsResult,
            timestamp: Date.now(),
            url: url
        };
    } catch (error) {
        console.error('Analysis error:', error);
        return { error: error.message };
    }
}

async function getPageContent(tabId) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: extractPageContent
        });

        return results[0]?.result || { text: '', images: [], title: '' };
    } catch (error) {
        console.error('Error getting page content:', error);
        return { text: '', images: [], title: '' };
    }
}

// Injected function to extract page content
function extractPageContent() {
    // Get main text content
    const article = document.querySelector('article') || document.body;
    const paragraphs = article.querySelectorAll('p, h1, h2, h3');
    let text = '';
    paragraphs.forEach(p => {
        text += p.textContent + ' ';
    });

    // Get title
    const title = document.title || document.querySelector('h1')?.textContent || '';

    // Get images
    const images = [];
    document.querySelectorAll('img').forEach(img => {
        if (img.naturalWidth > 100 && img.naturalHeight > 100) {
            images.push({
                src: img.src,
                alt: img.alt,
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        }
    });

    return { text: text.slice(0, 5000), title, images };
}

// Fake News Analysis
async function analyzeFakeNews(pageContent, url, title) {
    const combinedText = (title + ' ' + pageContent.text).toLowerCase();

    // 1. Source credibility analysis
    const sourceResult = analyzeSourceCredibility(url);

    // 2. Sensationalism detection
    const sensationalismResult = detectSensationalism(combinedText, title);

    // 3. Writing style analysis
    const styleResult = analyzeWritingStyle(combinedText);

    // 4. Fact-check via Scira AI
    const factCheckResult = await performFactCheck(combinedText, title);

    // Calculate combined score (higher = more likely fake)
    let weightedScore = (
        (100 - sourceResult.score) * 0.20 +
        sensationalismResult.score * 0.25 +
        (100 - styleResult.score) * 0.15 +
        (100 - factCheckResult.score) * 0.40
    );

    // Decisively handle satire and unreliable sources
    if (sourceResult.label === 'Satire/Parody') {
        weightedScore = Math.max(98, weightedScore);
    } else if (sourceResult.label === 'Questionable') {
        weightedScore = Math.max(80, weightedScore);
    }

    return {
        score: Math.round(Math.min(100, Math.max(0, weightedScore))),
        sourceCredibility: sourceResult.label,
        sourceScore: sourceResult.score,
        sensationalism: sensationalismResult.label,
        sensationalismScore: sensationalismResult.score,
        writeStyle: styleResult.label,
        styleScore: styleResult.score,
        factCheck: factCheckResult.label,
        factCheckScore: factCheckResult.score,
        credibleSources: factCheckResult.sources || []
    };
}

function analyzeSourceCredibility(url) {
    const domain = new URL(url).hostname.replace('www.', '');

    // Known reliable sources (simplified list)
    const reliableSources = [
        'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk',
        'nytimes.com', 'washingtonpost.com', 'theguardian.com',
        'npr.org', 'economist.com', 'wsj.com', 'ft.com',
        'cnn.com', 'abcnews.go.com', 'nbcnews.com', 'cbsnews.com',
        // Indian news sources
        'timesnownews.com', 'ndtv.com', 'indiatoday.in', 'thehindu.com',
        'hindustantimes.com', 'indianexpress.com', 'news18.com',
        'zeenews.india.com', 'aajtak.in', 'theprint.in', 'scroll.in'
    ];

    // Known questionable sources
    const questionableSources = [
        'infowars.com', 'naturalnews.com', 'beforeitsnews.com',
        'worldnewsdailyreport.com', 'yournewswire.com'
    ];

    // Satire sources
    const satireSources = [
        'theonion.com', 'babylonbee.com', 'clickhole.com',
        'neworder.com', 'theborowitzreport.com', 'thehardtimes.net'
    ];

    if (satireSources.some(s => domain.includes(s))) {
        return { score: 10, label: 'Satire/Parody' };
    } else if (reliableSources.some(s => domain.includes(s))) {
        return { score: 90, label: 'Highly Reliable' };
    } else if (questionableSources.some(s => domain.includes(s))) {
        return { score: 15, label: 'Questionable' };
    } else if (domain.includes('.gov') || domain.includes('.edu')) {
        return { score: 85, label: 'Generally Reliable' };
    } else {
        return { score: 50, label: 'Unknown Source' };
    }
}

function detectSensationalism(text, title) {
    const sensationalPatterns = [
        /breaking/i, /exclusive/i, /shocking/i, /unbelievable/i,
        /you won't believe/i, /mind-blowing/i, /insane/i,
        /doctors hate/i, /secret/i, /they don't want you to know/i,
        /miracle/i, /cure/i, /exposed/i, /bombshell/i,
        /urgent/i, /warning/i, /alert/i, /confirmed/i,
        /100%/i, /guaranteed/i, /scientifically proven/i
    ];

    const clickbaitPatterns = [
        /\d+ (things|ways|reasons|facts|tips)/i,
        /you'll never guess/i, /what happened next/i,
        /gone wrong/i, /gone viral/i, /blew up the internet/i
    ];

    let sensationalismCount = 0;
    let clickbaitCount = 0;

    sensationalPatterns.forEach(pattern => {
        if (pattern.test(text)) sensationalismCount++;
        if (pattern.test(title)) sensationalismCount += 2; // Title weight higher
    });

    clickbaitPatterns.forEach(pattern => {
        if (pattern.test(text)) clickbaitCount++;
        if (pattern.test(title)) clickbaitCount += 2;
    });

    // Check for excessive punctuation
    const exclamations = (text.match(/!/g) || []).length;
    const questions = (text.match(/\?/g) || []).length;
    const allCaps = (text.match(/\b[A-Z]{4,}\b/g) || []).length;

    const totalScore = Math.min(100,
        sensationalismCount * 8 +
        clickbaitCount * 10 +
        exclamations * 2 +
        allCaps * 3
    );

    let label = 'Low';
    if (totalScore > 60) label = 'High';
    else if (totalScore > 30) label = 'Moderate';

    return { score: totalScore, label };
}

function analyzeWritingStyle(text) {
    // Check for professional writing indicators
    const wordCount = text.split(/\s+/).length;
    const avgSentenceLength = text.split(/[.!?]+/).length > 0
        ? wordCount / text.split(/[.!?]+/).length
        : 0;

    // Professional articles typically have varied sentence lengths
    // and proper grammar indicators

    // Check for quotes and attributions
    const hasQuotes = /"[^"]+"/g.test(text);
    const hasAttribution = /according to|said|stated|reported|announced|confirmed by/i.test(text);

    // Check for multiple sources
    const sourceIndicators = text.match(/sources?|officials?|experts?|researchers?|scientists?|spokesperson/gi) || [];

    let score = 50; // Base score

    if (avgSentenceLength > 10 && avgSentenceLength < 30) score += 15;
    if (hasQuotes) score += 15;
    if (hasAttribution) score += 10;
    if (sourceIndicators.length >= 2) score += 10;
    if (wordCount > 200) score += 10;

    score = Math.min(100, score);

    let label = 'Poor';
    if (score >= 70) label = 'Professional';
    else if (score >= 50) label = 'Average';

    return { score, label };
}

async function performFactCheck(text, title) {
    // Try to use Scira AI if API key is configured
    const apiKey = await getStoredApiKey();

    let result = { score: 50, label: 'Unverified', sources: [] };

    if (apiKey) {
        try {
            result = await callSciraAPI(text, apiKey);
        } catch (error) {
            console.error('Scira API error:', error);
            result = simulateFactCheck(text);
        }
    } else {
        result = simulateFactCheck(text);
    }

    // Always ensure we have some "Credible Context" links as fallback
    if (!result.sources || result.sources.length === 0) {
        const query = encodeURIComponent(title || text.slice(0, 100));
        result.sources = [
            {
                title: `Search Google for: "${title.slice(0, 50)}..."`,
                url: `https://www.google.com/search?q=${query}+fact+check`,
                isTrusted: false,
                isFallback: true
            },
            {
                title: "Check on Snopes.com",
                url: `https://www.snopes.com/?s=${query}`,
                isTrusted: true,
                isFallback: true
            },
            {
                title: "Check on Politifact.com",
                url: `https://www.politifact.com/search/?q=${query}`,
                isTrusted: true,
                isFallback: true
            }
        ];
    }

    return result;
}

async function callSciraAPI(text, apiKey) {
    // Extract key claims from text (first 500 chars)
    const claims = text.slice(0, 500);

    try {
        const response = await fetch(`${SCIRA_API_CONFIG.baseUrl}${SCIRA_API_CONFIG.endpoints.factCheck}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey
            },
            body: JSON.stringify({
                query: `Is the following claim true, false, or satire? Fact check it and provide credible sources to debunk or confirm: "${claims}"`,
                search_depth: 'advanced',
                max_results: 8
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed with status: ${response.status}`);
        }

        const data = await response.json();
        const sources = [];

        // Process Scira response
        if (data.results && data.results.length > 0) {
            // Extract sources regardless of reliability (we will score them)
            data.results.forEach(r => {
                if (r.url && r.title) {
                    sources.push({
                        title: r.title,
                        url: r.url,
                        snippet: r.snippet || '',
                        isTrusted: isTrustedSource(r.url)
                    });
                }
            });

            const reliableResults = sources.filter(s => s.isTrusted);

            // Score based on trustworthy sources found
            let score = 40; // Default uncertain
            if (reliableResults.length >= 3) score = 90;
            else if (reliableResults.length >= 2) score = 80;
            else if (reliableResults.length >= 1) score = 65;

            // Boost score if the title specifically mentions fact-check words
            const factCheckMatch = data.results.some(r =>
                /fact check|verified|debunked|misleading|false/i.test(r.title + ' ' + (r.snippet || ''))
            );
            if (factCheckMatch) score = Math.max(score, 70);

            return {
                score,
                label: score >= 80 ? 'Verified' : score >= 60 ? 'Likely Reliable' : 'Needs Verification',
                sources: sources.slice(0, 4) // Return top 4 sources
            };
        }

        return { score: 50, label: 'No Data Found', sources: [] };
    } catch (error) {
        console.error('Scira API call failed:', error);
        return { ...simulateFactCheck(text), sources: [] };
    }
}

function isTrustedSource(url) {
    if (!url) return false;
    const domain = new URL(url).hostname.replace('www.', '');
    const trusted = [
        'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk',
        'nytimes.com', 'washingtonpost.com', 'theguardian.com',
        'npr.org', 'economist.com', 'wsj.com', 'ft.com',
        'factcheck.org', 'snopes.com', 'politifact.com',
        'poynter.org', 'fullfact.org', 'afp.com'
    ];
    return trusted.some(t => domain.includes(t)) || domain.endsWith('.gov') || domain.endsWith('.edu');
}

function simulateFactCheck(text) {
    // Simulate fact-checking based on content characteristics
    // This is a placeholder - real fact-checking requires API integration

    // Check for verifiable elements
    const hasDate = /\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b/i.test(text);
    const hasLocation = /\b(city|country|state|province|washington|london|new york|los angeles)\b/i.test(text);
    const hasNumbers = /\d+%|\$\d+|\d+ (million|billion|thousand)/i.test(text);
    const hasOrganization = /\b(government|company|organization|university|institute|department)\b/i.test(text);

    let score = 40;
    if (hasDate) score += 15;
    if (hasLocation) score += 15;
    if (hasNumbers) score += 10;
    if (hasOrganization) score += 10;

    score = Math.min(90, score);

    let label = 'Unverified';
    if (score >= 70) label = 'Likely Accurate';
    else if (score >= 50) label = 'Needs Verification';

    return { score, label };
}


// Caching functions
function getCachedResults(url) {
    const cached = resultsCache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached.results;
    }
    return null;
}

function cacheResults(url, results) {
    resultsCache.set(url, {
        results: results,
        timestamp: Date.now()
    });
}

// API Key management
async function getStoredApiKey() {
    const result = await chrome.storage.sync.get(['sciraApiKey']);
    return result.sciraApiKey || '';
}

async function getApiKey() {
    return { apiKey: await getStoredApiKey() };
}

async function setApiKey(apiKey) {
    await chrome.storage.sync.set({ sciraApiKey: apiKey });
    SCIRA_API_CONFIG.apiKey = apiKey;
    return { success: true };
}

// Feedback functions
async function loadFeedbackData() {
    const result = await chrome.storage.local.get(['feedbackData']);
    if (result.feedbackData) {
        feedbackData = result.feedbackData;
    }
}

async function saveFeedbackData() {
    await chrome.storage.local.set({ feedbackData: feedbackData });
}

function submitFeedback(request) {
    feedbackData.total++;
    if (request.isAccurate) {
        feedbackData.accurate++;
    } else {
        feedbackData.inaccurate++;
    }

    feedbackData.reports.push({
        url: request.url,
        isAccurate: request.isAccurate,
        results: request.results,
        timestamp: request.timestamp
    });

    // Keep only last 100 reports
    if (feedbackData.reports.length > 100) {
        feedbackData.reports = feedbackData.reports.slice(-100);
    }

    saveFeedbackData();

    return { success: true };
}

function getFeedbackStats() {
    return {
        total: feedbackData.total,
        accurate: feedbackData.accurate,
        inaccurate: feedbackData.inaccurate
    };
}


async function analyzeTextSelection(text, tab) {
    // Quick fact-check for selected text
    const result = await simulateFactCheck(text);

    await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (text, result) => {
            alert(`Veritas Fact Check:\n\n"${text.slice(0, 100)}..."\n\nResult: ${result.label}\nConfidence: ${result.score}%`);
        },
        args: [text, result]
    });
}
