/**
 * Welcome Animations Module
 * Handles time-based greetings and animated welcome messages
 */

export class WelcomeAnimations {
    constructor() {
        this.greetings = {
            morning: {
                text: "Good morning",
                emoji: "☀️",
                timeRange: [5, 12]
            },
            afternoon: {
                text: "Good afternoon", 
                emoji: "🌤️",
                timeRange: [12, 17]
            },
            evening: {
                text: "Good evening",
                emoji: "🌅", 
                timeRange: [17, 21]
            },
            night: {
                text: "Good evening",
                emoji: "🌙",
                timeRange: [21, 5]
            }
        };
    }

    /**
     * Get current time-based greeting
     */
    getTimeBasedGreeting() {
        const hour = new Date().getHours();
        
        if (hour >= 5 && hour < 12) {
            return this.greetings.morning;
        } else if (hour >= 12 && hour < 17) {
            return this.greetings.afternoon;
        } else if (hour >= 17 && hour < 21) {
            return this.greetings.evening;
        } else {
            return this.greetings.night;
        }
    }

    /**
     * Generate animated welcome message HTML
     */
    generateWelcomeMessage() {
        const greeting = this.getTimeBasedGreeting();
        
        const welcomeHTML = `
            <div class="welcome-message-content animated simple">
                <div class="greeting-line fade-in">
                    <span class="greeting-text">${greeting.text}!</span>
                    <span class="greeting-emoji">${greeting.emoji}</span>
                </div>
                
                <h2 class="main-heading fade-in-delayed">
                    Where should we begin with your malaria risk analysis?
                </h2>
                
                <div class="action-buttons fade-in-delayed">
                    <button class="welcome-action-btn primary" onclick="window.chatManager.promptDataUpload()">
                        <i class="fas fa-upload"></i> Get Started
                    </button>
                    <button class="welcome-action-btn secondary" onclick="window.chatManager.loadSampleData()">
                        <i class="fas fa-database"></i> Try Sample Data
                    </button>
                </div>
            </div>
        `;
        
        return welcomeHTML;
    }

    /**
     * Add hover animations to interactive elements
     */
    initializeInteractions() {
        // Add hover effects to emojis
        setTimeout(() => {
            const emojis = document.querySelectorAll('.feature-emoji, .mosquito-icon, .shield-icon');
            emojis.forEach(emoji => {
                emoji.addEventListener('mouseenter', function() {
                    this.classList.add('bounce');
                });
                emoji.addEventListener('animationend', function() {
                    this.classList.remove('bounce');
                });
            });
            
            // Add hover effects to feature items
            const features = document.querySelectorAll('.feature-item');
            features.forEach(feature => {
                feature.addEventListener('mouseenter', function() {
                    this.classList.add('hover-glow');
                });
                feature.addEventListener('mouseleave', function() {
                    this.classList.remove('hover-glow');
                });
            });
        }, 1000); // Wait for animations to complete
    }
}

// Create singleton instance
const welcomeAnimations = new WelcomeAnimations();
export default welcomeAnimations;