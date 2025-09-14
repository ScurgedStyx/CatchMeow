// Audio Analysis Integration
class AudioAnalysisManager {
    constructor() {
        this.analysisEndpoint = '/analyze_audio'; // You'll need to set up a backend endpoint
        this.currentAnalysis = null;
        this.setupFileInput();
    }

    setupFileInput() {
        // Create file input for audio files
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.multiple = true;
        fileInput.accept = '.wav,.mp3,.m4a';
        fileInput.style.display = 'none';
        fileInput.id = 'audioFileInput';
        document.body.appendChild(fileInput);

        // Add upload button to leaderboard controls
        const uploadBtn = document.createElement('button');
        uploadBtn.className = 'control-btn upload-btn';
        uploadBtn.textContent = 'Upload Audio Files';
        uploadBtn.onclick = () => fileInput.click();
        
        const controls = document.querySelector('.leaderboard-controls');
        if (controls) {
            controls.appendChild(uploadBtn);
        }

        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    async handleFileUpload(event) {
        const files = Array.from(event.target.files).filter(f => 
            f.name.endsWith('.wav') || f.name.endsWith('.mp3') || f.name.endsWith('.m4a')
        );
        
        if (files.length === 0) {
            alert('Please select audio files (.wav, .mp3, or .m4a)');
            return;
        }

        console.log(`Processing ${files.length} audio files...`);
        this.showAnalysisProgress();

        try {
            // Try real backend first, fall back to demo mode
            let results;
            if (this.isBackendAvailable()) {
                results = await this.sendFilesToBackend(files);
            } else {
                console.log('Backend not available, using demo mode');
                results = await this.simulateAudioAnalysis(files);
            }
            
            this.updateGUIWithResults(results);
        } catch (error) {
            console.error('Audio analysis failed:', error);
            alert('Audio analysis failed: ' + error.message);
        } finally {
            this.hideAnalysisProgress();
        }
    }

    async isBackendAvailable() {
        try {
            const response = await fetch('/health', { method: 'GET', timeout: 2000 });
            return response.ok;
        } catch {
            return false;
        }
    }

    async sendFilesToBackend(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch('/analyze_audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async simulateAudioAnalysis(files) {
        // Simulate the Python audio analysis pipeline
        // In production, replace this with actual API calls
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Generate realistic results based on your algorithm
        const numFiles = files.length;
        let analysisResults;

        if (numFiles === 5) {
            // Full session analysis with baselines
            analysisResults = this.generateFullSessionResults(files);
        } else if (numFiles === 1) {
            // Single file analysis
            analysisResults = this.generateSingleFileResults(files[0]);
        } else {
            // Multiple files - analyze the last one
            analysisResults = this.generateSingleFileResults(files[files.length - 1]);
        }

        return analysisResults;
    }

    generateFullSessionResults(files) {
        // Simulate advanced baseline comparison results
        const baseScore = 20 + Math.random() * 60; // 20-80 range
        const confidence = 0.7 + Math.random() * 0.25; // 0.7-0.95 range
        
        const reasons = [
            "Pause patterns differ from conversational baseline",
            "Pitch variation exceeds reading baseline",
            "Energy levels show stress indicators",
            "Speech rhythm changes detected"
        ];
        
        // Select 2-3 random reasons
        const selectedReasons = reasons.sort(() => 0.5 - Math.random()).slice(0, 2 + Math.floor(Math.random() * 2));
        
        return {
            success: true,
            bluff_score: Math.round(baseScore * 10) / 10,
            confidence: Math.round(confidence * 100) / 100,
            reasons: selectedReasons,
            metrics: {
                pause_ratio: Math.round((0.05 + Math.random() * 0.3) * 1000) / 10, // 0.5-3.5%
                pause_count: Math.floor(3 + Math.random() * 20), // 3-23 pauses
                mean_f0: Math.round(120 + Math.random() * 80), // 120-200 Hz
                mean_energy: Math.round(30 + Math.random() * 50), // 30-80%
                max_energy: Math.round(50 + Math.random() * 40)   // 50-90%
            },
            analysis_type: 'full_session_baseline',
            files_analyzed: files.length
        };
    }

    generateSingleFileResults(file) {
        // Simulate simple single-file analysis
        const baseScore = 10 + Math.random() * 70; // 10-80 range
        const confidence = 0.6 + Math.random() * 0.2; // 0.6-0.8 range
        
        const reasons = [
            "High pause ratio detected",
            "Frequent pausing detected",
            "Unusual pitch patterns",
            "Energy levels indicate stress",
            "Speech patterns appear normal"
        ];
        
        const selectedReasons = reasons.sort(() => 0.5 - Math.random()).slice(0, 1 + Math.floor(Math.random() * 2));
        
        return {
            success: true,
            bluff_score: Math.round(baseScore * 10) / 10,
            confidence: Math.round(confidence * 100) / 100,
            reasons: selectedReasons,
            metrics: {
                pause_ratio: Math.round((0.02 + Math.random() * 0.25) * 1000) / 10,
                pause_count: Math.floor(1 + Math.random() * 15),
                mean_f0: Math.round(100 + Math.random() * 100),
                mean_energy: Math.round(20 + Math.random() * 60),
                max_energy: Math.round(40 + Math.random() * 50)
            },
            analysis_type: 'single_file',
            files_analyzed: 1
        };
    }

    updateGUIWithResults(results) {
        if (!results.success) {
            console.error('Analysis failed:', results.error);
            return;
        }

        // Update the main score display
        this.updateFinalScore(results.bluff_score);
        
        // Update the metric boxes
        this.updateMetricBoxes(results.metrics);
        
        // Update leaderboard with new player
        const playerName = `Player_${Date.now()}`;
        this.addPlayerToLeaderboard(playerName, results.bluff_score);
        
        // Show analysis details
        this.showAnalysisResults(results);
        
        // Store current analysis
        this.currentAnalysis = results;
        
        console.log('GUI updated with analysis results:', results);
    }

    updateFinalScore(score) {
        const scoreElement = document.getElementById('finalScore');
        if (scoreElement) {
            scoreElement.textContent = Math.round(score);
            
            // Add color class based on score
            scoreElement.className = 'score-value';
            if (score < 30) {
                scoreElement.classList.add('score-low');
            } else if (score < 70) {
                scoreElement.classList.add('score-medium');
            } else {
                scoreElement.classList.add('score-high');
            }
        }
    }

    updateMetricBoxes(metrics) {
        const metricMapping = {
            'pause-ratio': 'pause_ratio',
            'pause-count': 'pause_count', 
            'mean-f0': 'mean_f0',
            'mean-energy': 'mean_energy',
            'max-energy': 'max_energy'
        };

        for (const [cssClass, metricKey] of Object.entries(metricMapping)) {
            const value = metrics[metricKey] || 0;
            this.updateMetricBox(cssClass, value, metricKey);
        }
    }

    updateMetricBox(cssClass, value, metricType) {
        const containers = document.querySelectorAll('.feature-box');
        
        for (const container of containers) {
            const title = container.querySelector('h3');
            if (!title) continue;
            
            const titleText = title.textContent.toLowerCase().replace(' ', '-');
            if (titleText === cssClass.replace('-', ' ').toLowerCase()) {
                
                // Calculate percentage for progress bar
                let percentage;
                switch(metricType) {
                    case 'pause_ratio':
                        percentage = Math.min(100, value * 10); // Convert 0.0-10.0 to 0-100%
                        break;
                    case 'pause_count':
                        percentage = Math.min(100, (value / 30) * 100); // Assume max 30 pauses
                        break;
                    case 'mean_f0':
                        percentage = Math.min(100, Math.max(0, ((value - 50) / 300) * 100)); // 50-350 Hz range
                        break;
                    case 'mean_energy':
                    case 'max_energy':
                        percentage = Math.min(100, Math.max(0, value)); // Already 0-100%
                        break;
                    default:
                        percentage = Math.min(100, Math.max(0, value));
                }
                
                // Update progress bar
                const progressBar = container.querySelector('.progress-bar');
                const percentageSpan = container.querySelector('.percentage');
                
                if (progressBar) {
                    progressBar.style.width = percentage + '%';
                    progressBar.setAttribute('data-percentage', Math.round(percentage));
                    
                    // Update color based on metric type and value
                    const colorClass = getMetricColor(cssClass, value, percentage);
                    progressBar.className = 'progress-bar ' + colorClass;
                }
                
                if (percentageSpan) {
                    if (metricType === 'mean_f0') {
                        percentageSpan.textContent = Math.round(value) + ' Hz';
                    } else if (metricType === 'pause_count') {
                        percentageSpan.textContent = Math.round(value) + ' pauses';
                    } else {
                        percentageSpan.textContent = Math.round(percentage) + '%';
                    }
                }
                
                break;
            }
        }
    }

    addPlayerToLeaderboard(playerName, score) {
        const leaderboardList = document.querySelector('.leaderboard-list');
        if (!leaderboardList) return;

        // Create new player item
        const playerItem = document.createElement('div');
        playerItem.className = 'player-item';
        
        // Get current rank (number of existing players + 1)
        const currentPlayers = leaderboardList.querySelectorAll('.player-item').length;
        const rank = currentPlayers + 1;
        
        playerItem.innerHTML = `
            <span class="rank">${rank}.</span>
            <span class="player-name">${playerName}</span>
            <span class="player-score">${Math.round(score)}</span>
        `;
        
        // Add to leaderboard
        leaderboardList.appendChild(playerItem);
        
        // Sort leaderboard by score (highest first)
        this.sortLeaderboard();
    }

    sortLeaderboard() {
        const leaderboardList = document.querySelector('.leaderboard-list');
        if (!leaderboardList) return;
        
        const players = Array.from(leaderboardList.querySelectorAll('.player-item'));
        players.sort((a, b) => {
            const scoreA = parseInt(a.querySelector('.player-score').textContent);
            const scoreB = parseInt(b.querySelector('.player-score').textContent);
            return scoreB - scoreA; // Sort highest to lowest
        });
        
        // Update ranks and re-add to DOM
        leaderboardList.innerHTML = '';
        players.forEach((player, index) => {
            player.querySelector('.rank').textContent = `${index + 1}.`;
            leaderboardList.appendChild(player);
        });
    }

    showAnalysisProgress() {
        // Create or show progress indicator
        let progressDiv = document.getElementById('analysisProgress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.id = 'analysisProgress';
            progressDiv.className = 'analysis-progress';
            progressDiv.innerHTML = `
                <div class="progress-content">
                    <div class="spinner"></div>
                    <p>Analyzing audio files...</p>
                </div>
            `;
            document.body.appendChild(progressDiv);
        }
        progressDiv.style.display = 'flex';
    }

    hideAnalysisProgress() {
        const progressDiv = document.getElementById('analysisProgress');
        if (progressDiv) {
            progressDiv.style.display = 'none';
        }
    }

    showAnalysisResults(results) {
        // Show a popup or modal with detailed results
        const modal = document.createElement('div');
        modal.className = 'results-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>🎯 Bluff Analysis Results</h2>
                    <button class="close-btn" onclick="this.closest('.results-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="score-section">
                        <div class="main-score">
                            <span class="score-label">Bluff Score</span>
                            <span class="score-value">${results.bluff_score}</span>
                        </div>
                        <div class="confidence">
                            <span>Confidence: ${(results.confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    <div class="reasons-section">
                        <h3>Analysis Reasons:</h3>
                        <ul>
                            ${results.reasons.map(reason => `<li>${reason}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="metrics-section">
                        <h3>Voice Metrics:</h3>
                        <div class="metrics-grid">
                            <div>Pause Ratio: ${results.metrics.pause_ratio}%</div>
                            <div>Pause Count: ${results.metrics.pause_count}</div>
                            <div>Mean F0: ${results.metrics.mean_f0} Hz</div>
                            <div>Mean Energy: ${results.metrics.mean_energy}%</div>
                            <div>Max Energy: ${results.metrics.max_energy}%</div>
                        </div>
                    </div>
                    <div class="analysis-info">
                        <p><strong>Analysis Type:</strong> ${results.analysis_type}</p>
                        <p><strong>Files Analyzed:</strong> ${results.files_analyzed}</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 10000);
    }
}

// Initialize audio analysis when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.audioAnalysisManager = new AudioAnalysisManager();
    console.log('Audio Analysis Manager initialized');
});

// Metric-Based Progress Bar Color Management
function getMetricColor(metricType, value, percentage) {
    switch(metricType) {
        case 'pause-ratio':
            // Lower pause ratio is better (0-40% range)
            if (percentage <= 10) return 'pause-ratio-excellent';
            if (percentage <= 20) return 'pause-ratio-good';
            if (percentage <= 30) return 'pause-ratio-fair';
            if (percentage <= 40) return 'pause-ratio-poor';
            return 'pause-ratio-bad';
            
        case 'pause-count':
            // Lower pause count is better (assuming 0-50 count range)
            if (value <= 5) return 'pause-count-excellent';
            if (value <= 15) return 'pause-count-good';
            if (value <= 25) return 'pause-count-fair';
            if (value <= 35) return 'pause-count-poor';
            return 'pause-count-bad';
            
        case 'mean-f0':
            // Normal speaking frequency ranges (Hz)
            if (value < 80) return 'mean-f0-low';
            if (value <= 120) return 'mean-f0-normal-low';
            if (value <= 180) return 'mean-f0-normal-mid';
            if (value <= 250) return 'mean-f0-normal-high';
            return 'mean-f0-high';
            
        case 'mean-energy':
            // Energy levels (assuming normalized 0-100 scale)
            if (value < 10) return 'mean-energy-very-low';
            if (value < 30) return 'mean-energy-low';
            if (value <= 70) return 'mean-energy-optimal';
            if (value <= 85) return 'mean-energy-high';
            return 'mean-energy-very-high';
            
        case 'max-energy':
            // Max energy levels (peak intensity - assuming normalized 0-100 scale)
            if (value < 15) return 'max-energy-very-low';
            if (value < 35) return 'max-energy-low';
            if (value <= 75) return 'max-energy-normal';
            if (value <= 90) return 'max-energy-high';
            return 'max-energy-very-high';
            
        default:
            return 'pause-ratio-good'; // Fallback
    }
}

// Initialize Progress Bars with Metric-Based Colors
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    const featureBoxes = document.querySelectorAll('.feature-box');
    
    // Define metric types and sample values for demonstration
    const metrics = [
        { type: 'pause-ratio', value: 15, percentage: 15 },
        { type: 'pause-count', value: 12, percentage: 35 },
        { type: 'mean-f0', value: 145, percentage: 55 },
        { type: 'mean-energy', value: 65, percentage: 75 },
        { type: 'max-energy', value: 82, percentage: 85 }
    ];
    
    progressBars.forEach((bar, index) => {
        if (index < metrics.length) {
            const metric = metrics[index];
            const colorClass = getMetricColor(metric.type, metric.value, metric.percentage);
            
            // Store metric type for future updates
            bar.dataset.metricType = metric.type;
            bar.dataset.metricValue = metric.value;
            
            // Add color class
            bar.classList.add(colorClass);
            
            // Set width with animation delay
            setTimeout(() => {
                bar.style.width = metric.percentage + '%';
            }, 100);
        }
    });
}

// Update Progress Bar with Metric-Based Colors
function updateProgressBar(index, newValue, newPercentage) {
    const progressBars = document.querySelectorAll('.progress-bar');
    const percentageSpans = document.querySelectorAll('.percentage');
    
    if (index >= 0 && index < progressBars.length) {
        const bar = progressBars[index];
        const span = percentageSpans[index];
        const metricType = bar.dataset.metricType;
        
        // Remove old color classes
        bar.className = 'progress-bar';
        
        // Add new metric-based color class
        const colorClass = getMetricColor(metricType, newValue, newPercentage);
        bar.classList.add(colorClass);
        
        // Update stored value
        bar.dataset.metricValue = newValue;
        
        // Update width and text
        bar.style.width = newPercentage + '%';
        span.textContent = newPercentage + '%';
        
        // Update dataset
        bar.dataset.percentage = newPercentage;
    }
}

// Helper function to update metrics with real values
function updateMetrics(metricsData) {
    /* 
    Example usage:
    updateMetrics({
        pauseRatio: 0.15,     // 15% pause ratio
        pauseCount: 8,        // 8 total pauses
        meanF0: 142.5,        // 142.5 Hz fundamental frequency
        meanEnergy: 62.3,     // 62.3% normalized energy
        maxEnergy: 88.7       // 88.7% maximum energy peak
    });
    */
    
    if (metricsData.pauseRatio !== undefined) {
        const percentage = Math.min(metricsData.pauseRatio * 100, 100);
        updateProgressBar(0, metricsData.pauseRatio, percentage);
    }
    
    if (metricsData.pauseCount !== undefined) {
        // Normalize pause count to percentage (assuming max 50 pauses = 100%)
        const percentage = Math.min((metricsData.pauseCount / 50) * 100, 100);
        updateProgressBar(1, metricsData.pauseCount, percentage);
    }
    
    if (metricsData.meanF0 !== undefined) {
        // Normalize F0 to percentage (assuming 50-300Hz range = 0-100%)
        const percentage = Math.min(Math.max(((metricsData.meanF0 - 50) / 250) * 100, 0), 100);
        updateProgressBar(2, metricsData.meanF0, percentage);
    }
    
    if (metricsData.meanEnergy !== undefined) {
        // Energy is already in percentage format typically
        const percentage = Math.min(metricsData.meanEnergy, 100);
        updateProgressBar(3, metricsData.meanEnergy, percentage);
    }
    
    if (metricsData.maxEnergy !== undefined) {
        // Max energy is already in percentage format typically
        const percentage = Math.min(metricsData.maxEnergy, 100);
        updateProgressBar(4, metricsData.maxEnergy, percentage);
    }
}

// Leaderboard Management
let leaderboardData = [
    { name: 'Alice', score: 92 },
    { name: 'Bob', score: 87 },
    { name: 'Charlie', score: 81 },
    { name: 'Diana', score: 76 }
];

function renderLeaderboard() {
    const leaderboardList = document.querySelector('.leaderboard-list');
    leaderboardList.innerHTML = '';
    
    // Sort by score descending
    leaderboardData.sort((a, b) => b.score - a.score);
    
    leaderboardData.forEach((player, index) => {
        const playerItem = document.createElement('div');
        playerItem.className = 'player-item';
        playerItem.innerHTML = `
            <span class="rank">${index + 1}.</span>
            <span class="player-name">${player.name}</span>
            <span class="player-score">${player.score}</span>
        `;
        leaderboardList.appendChild(playerItem);
    });
}

// Add New Player (placeholder function)
function addNewPlayer() {
    // For now, just generate a random player
    const names = ['Emma', 'James', 'Sophie', 'Michael', 'Lisa', 'David', 'Sarah', 'John'];
    const randomName = names[Math.floor(Math.random() * names.length)];
    const randomScore = Math.floor(Math.random() * 100);
    
    leaderboardData.push({ name: randomName, score: randomScore });
    renderLeaderboard();
    
    console.log(`Added new player: ${randomName} with score: ${randomScore}`);
}

// Remove Last Player (placeholder function)
function removeLastPlayer() {
    if (leaderboardData.length > 0) {
        const removedPlayer = leaderboardData.pop();
        renderLeaderboard();
        console.log(`Removed player: ${removedPlayer.name}`);
    } else {
        console.log('No players to remove');
    }
}

// Final Score Management
function updateFinalScore(newScore) {
    const scoreElement = document.getElementById('finalScore');
    if (scoreElement) {
        scoreElement.textContent = newScore;
        
        // Add a pulse effect when score updates
        scoreElement.style.animation = 'none';
        setTimeout(() => {
            scoreElement.style.animation = 'pulse 2s infinite';
        }, 50);
    }
}

// Demo Functions for Testing
function runDemo() {
    console.log('Running demo...');
    
    // Simulate progress bar updates every 3 seconds
    let demoIndex = 0;
    setInterval(() => {
        const randomIndex = Math.floor(Math.random() * 10);
        const randomPercentage = Math.floor(Math.random() * 101);
        updateProgressBar(randomIndex, randomPercentage);
        
        demoIndex++;
        if (demoIndex % 5 === 0) {
            // Update final score occasionally
            const newFinalScore = Math.floor(Math.random() * 100);
            updateFinalScore(newFinalScore);
        }
    }, 3000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('Bluff Score Dashboard Loaded');
    
    // Initialize the UI
    initializeProgressBars();
    renderLeaderboard();
    
    // Add event listeners for buttons
    const addButton = document.querySelector('.add-btn');
    const removeButton = document.querySelector('.remove-btn');
    
    if (addButton) {
        addButton.addEventListener('click', addNewPlayer);
    }
    
    if (removeButton) {
        removeButton.addEventListener('click', removeLastPlayer);
    }
    
    // Optional: Run demo mode (uncomment to enable)
    // runDemo();
});

// Utility Functions
function generateRandomScores() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach((bar, index) => {
        const randomPercentage = Math.floor(Math.random() * 101);
        updateProgressBar(index, randomPercentage);
    });
    
    // Also update final score
    const finalScore = Math.floor(Math.random() * 100);
    updateFinalScore(finalScore);
}

// Export functions for external use
window.BluffDashboard = {
    updateProgressBar,
    updateFinalScore,
    addNewPlayer,
    removeLastPlayer,
    generateRandomScores,
    runDemo
};

// Console commands for testing
console.log('Available commands:');
console.log('- BluffDashboard.generateRandomScores() - Generate random scores');
console.log('- BluffDashboard.updateProgressBar(index, percentage) - Update specific progress bar');
console.log('- BluffDashboard.updateFinalScore(score) - Update final cat score');
console.log('- BluffDashboard.runDemo() - Start automatic demo mode');