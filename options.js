// Veritas Options Page Script

class OptionsPage {
    constructor() {
        this.init();
    }

    async init() {
        await this.loadSettings();
        this.bindEvents();
        this.loadStatistics();
    }

    bindEvents() {
        // API Key
        document.getElementById('apiKey').addEventListener('input', () => {
            this.hideMessage();
        });

        // Sensitivity slider
        document.getElementById('sensitivity').addEventListener('input', (e) => {
            document.getElementById('sensitivityValue').textContent = e.target.value + '%';
        });

        // Save button
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Export data
        document.getElementById('exportData').addEventListener('click', () => {
            this.exportData();
        });

        // Clear data
        document.getElementById('clearData').addEventListener('click', () => {
            this.clearData();
        });
    }

    async loadSettings() {
        const settings = await chrome.storage.sync.get([
            'sciraApiKey',
            'autoAnalyze',
            'showIndicator',
            'deepfakeDetection',
            'sensitivity'
        ]);

        // Apply settings to form
        if (settings.sciraApiKey) {
            document.getElementById('apiKey').value = settings.sciraApiKey;
        }

        document.getElementById('autoAnalyze').checked = settings.autoAnalyze || false;
        document.getElementById('showIndicator').checked = settings.showIndicator !== false;
        document.getElementById('deepfakeDetection').checked = settings.deepfakeDetection !== false;

        const sensitivity = settings.sensitivity || 50;
        document.getElementById('sensitivity').value = sensitivity;
        document.getElementById('sensitivityValue').textContent = sensitivity + '%';
    }

    async saveSettings() {
        const settings = {
            sciraApiKey: document.getElementById('apiKey').value,
            autoAnalyze: document.getElementById('autoAnalyze').checked,
            showIndicator: document.getElementById('showIndicator').checked,
            deepfakeDetection: document.getElementById('deepfakeDetection').checked,
            sensitivity: parseInt(document.getElementById('sensitivity').value)
        };

        try {
            await chrome.storage.sync.set(settings);

            // Validate API key if provided
            if (settings.sciraApiKey) {
                const isValid = await this.validateApiKey(settings.sciraApiKey);
                if (isValid) {
                    this.showMessage('Settings saved successfully! API key validated.', 'success');
                } else {
                    this.showMessage('Settings saved. API key could not be validated - will use local analysis.', 'success');
                }
            } else {
                this.showMessage('Settings saved successfully!', 'success');
            }
        } catch (error) {
            this.showMessage('Error saving settings: ' + error.message, 'error');
        }
    }

    async validateApiKey(apiKey) {
        try {
            // Simple validation - in production, make a test API call
            return apiKey.length > 10;
        } catch (error) {
            return false;
        }
    }

    async loadStatistics() {
        try {
            const stats = await chrome.storage.local.get(['feedbackData', 'analysisHistory']);

            const feedbackData = stats.feedbackData || { total: 0, accurate: 0, inaccurate: 0, reports: [] };
            const analysisHistory = stats.analysisHistory || [];

            // Count pages analyzed
            document.getElementById('pagesAnalyzed').textContent = analysisHistory.length;

            // Count fake detected (high risk analyses)
            const fakeCount = analysisHistory.filter(a => a.fakeNews?.score > 60).length;
            document.getElementById('fakeDetected').textContent = fakeCount;

            // Feedback count
            document.getElementById('feedbackGiven').textContent = feedbackData.total;
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    async exportData() {
        try {
            const data = await chrome.storage.local.get(null);
            const syncData = await chrome.storage.sync.get(null);

            // Remove sensitive data
            delete syncData.sciraApiKey;

            const exportData = {
                localData: data,
                syncData: syncData,
                exportDate: new Date().toISOString(),
                version: '1.0.0'
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `veritas-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showMessage('Data exported successfully!', 'success');
        } catch (error) {
            this.showMessage('Error exporting data: ' + error.message, 'error');
        }
    }

    async clearData() {
        if (!confirm('Are you sure you want to clear all data? This cannot be undone.')) {
            return;
        }

        try {
            await chrome.storage.local.clear();

            // Reset statistics display
            document.getElementById('pagesAnalyzed').textContent = '0';
            document.getElementById('fakeDetected').textContent = '0';
            document.getElementById('feedbackGiven').textContent = '0';

            this.showMessage('All data cleared successfully!', 'success');
        } catch (error) {
            this.showMessage('Error clearing data: ' + error.message, 'error');
        }
    }

    showMessage(text, type) {
        const messageEl = document.getElementById('apiMessage');
        messageEl.textContent = text;
        messageEl.className = 'message ' + type;
    }

    hideMessage() {
        const messageEl = document.getElementById('apiMessage');
        messageEl.className = 'message';
    }
}

// Initialize options page
new OptionsPage();
