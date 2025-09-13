// Progress Bar Color Management
function getProgressColor(percentage) {
    if (percentage >= 0 && percentage <= 20) {
        return 'progress-green';
    } else if (percentage > 20 && percentage <= 40) {
        return 'progress-yellow';
    } else if (percentage > 40 && percentage <= 60) {
        return 'progress-orange';
    } else if (percentage > 60 && percentage <= 80) {
        return 'progress-dark-orange';
    } else if (percentage > 80 && percentage <= 100) {
        return 'progress-red';
    }
    return 'progress-green'; // Default fallback
}

// Initialize Progress Bars
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const percentage = parseInt(bar.dataset.percentage);
        const colorClass = getProgressColor(percentage);
        
        // Add color class
        bar.classList.add(colorClass);
        
        // Set width with animation delay
        setTimeout(() => {
            bar.style.width = percentage + '%';
        }, 100);
    });
}

// Update Progress Bar
function updateProgressBar(index, newPercentage) {
    const progressBars = document.querySelectorAll('.progress-bar');
    const percentageSpans = document.querySelectorAll('.percentage');
    
    if (index >= 0 && index < progressBars.length) {
        const bar = progressBars[index];
        const span = percentageSpans[index];
        
        // Remove old color classes
        bar.className = 'progress-bar';
        
        // Add new color class
        const colorClass = getProgressColor(newPercentage);
        bar.classList.add(colorClass);
        
        // Update width and text
        bar.style.width = newPercentage + '%';
        span.textContent = newPercentage + '%';
        
        // Update dataset
        bar.dataset.percentage = newPercentage;
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