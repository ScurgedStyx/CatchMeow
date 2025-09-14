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