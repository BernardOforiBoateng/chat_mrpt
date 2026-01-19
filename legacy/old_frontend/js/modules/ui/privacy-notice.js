/**
 * Privacy Notice Manager
 * Handles the display and acceptance of privacy notice
 */

export class PrivacyNoticeManager {
    constructor() {
        this.STORAGE_KEY = 'chatmrpt_privacy_accepted';
        this.modal = null;
        this.modalInstance = null;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Get modal element
        this.modal = document.getElementById('privacyModal');
        if (!this.modal) {
            console.error('Privacy modal not found');
            return;
        }

        // Initialize Bootstrap modal
        if (window.bootstrap) {
            this.modalInstance = new bootstrap.Modal(this.modal, {
                backdrop: 'static',
                keyboard: false
            });
        }

        // Setup event handlers
        this.setupEventHandlers();

        // Check if we need to show the privacy notice
        this.checkAndShowPrivacyNotice();
    }

    setupEventHandlers() {
        // Accept button - Remove any existing listeners first
        const acceptBtn = document.getElementById('privacy-accept');
        if (acceptBtn) {
            // Clone to remove all existing event listeners
            const newAcceptBtn = acceptBtn.cloneNode(true);
            acceptBtn.parentNode.replaceChild(newAcceptBtn, acceptBtn);
            
            // Add fresh event listener
            newAcceptBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.acceptPrivacy();
            });
        }

        // Learn more button
        const learnMoreBtn = document.getElementById('privacy-learn-more');
        if (learnMoreBtn) {
            learnMoreBtn.addEventListener('click', () => this.showFullPolicy());
        }
    }

    checkAndShowPrivacyNotice() {
        const accepted = this.getAcceptanceStatus();
        
        if (!accepted) {
            // Show the modal after a brief delay to ensure page is loaded
            setTimeout(() => {
                if (this.modalInstance) {
                    this.modalInstance.show();
                }
            }, 500);
        }
    }

    getAcceptanceStatus() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (!stored) return false;
            
            const data = JSON.parse(stored);
            // Check if acceptance is still valid (e.g., within last 365 days)
            const acceptanceDate = new Date(data.timestamp);
            const now = new Date();
            const daysSinceAcceptance = (now - acceptanceDate) / (1000 * 60 * 60 * 24);
            
            // Re-show notice after 365 days
            return daysSinceAcceptance < 365;
        } catch (error) {
            console.error('Error checking privacy acceptance:', error);
            return false;
        }
    }

    acceptPrivacy() {
        try {
            // Store acceptance with timestamp
            const acceptanceData = {
                accepted: true,
                timestamp: new Date().toISOString(),
                version: '1.0' // Version of privacy policy
            };
            
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(acceptanceData));
            
            // Hide the modal
            if (this.modalInstance) {
                this.modalInstance.hide();
            }
            
            // Dispatch event for other modules
            document.dispatchEvent(new CustomEvent('privacyAccepted', {
                detail: acceptanceData
            }));
            
            console.log('Privacy notice accepted');
        } catch (error) {
            console.error('Error saving privacy acceptance:', error);
        }
    }

    showFullPolicy() {
        // For now, just open all accordion items
        const accordionButtons = this.modal.querySelectorAll('.accordion-button');
        accordionButtons.forEach(button => {
            if (button.classList.contains('collapsed')) {
                button.click();
            }
        });
    }

    // Method to programmatically show the privacy notice
    showPrivacyNotice() {
        if (this.modalInstance) {
            // Re-setup event handlers when showing manually
            this.setupEventHandlers();
            this.modalInstance.show();
        }
    }

    // Method to reset acceptance (for testing or user request)
    resetAcceptance() {
        localStorage.removeItem(this.STORAGE_KEY);
        console.log('Privacy acceptance reset');
    }
}

// Create and export singleton instance
const privacyNoticeManager = new PrivacyNoticeManager();
export default privacyNoticeManager;