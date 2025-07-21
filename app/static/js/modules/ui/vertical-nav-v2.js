/**
 * Vertical Navigation v2 - Simplified Hamburger Menu
 */

export class VerticalNavV2 {
    constructor() {
        this.hamburger = null;
        this.nav = null;
        this.overlay = null;
        this.closeBtn = null;
        this.isOpen = false;
        
        this.init();
    }

    init() {
        // Wait for DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Get elements
        this.hamburger = document.getElementById('hamburger-menu');
        this.nav = document.getElementById('vertical-nav');
        this.overlay = document.getElementById('nav-overlay');
        this.closeBtn = document.getElementById('nav-collapse-toggle');
        
        if (!this.hamburger || !this.nav) {
            console.error('Vertical nav elements not found');
            return;
        }
        
        // Setup event listeners
        this.hamburger.addEventListener('click', () => this.open());
        
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }
        
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.close());
        }
        
        // Setup preferences
        this.setupPreferences();
        
        // Setup navigation clicks
        this.setupNavItems();
    }

    open() {
        this.isOpen = true;
        this.nav.classList.add('active');
        this.overlay?.classList.add('active');
        document.body.classList.add('nav-open');
    }

    close() {
        this.isOpen = false;
        this.nav.classList.remove('active');
        this.overlay?.classList.remove('active');
        document.body.classList.remove('nav-open');
    }

    setupPreferences() {
        // Dark mode toggle
        const themeToggle = document.getElementById('nav-theme-toggle');
        if (themeToggle) {
            const savedTheme = localStorage.getItem('chatmrpt-theme') || 'light';
            themeToggle.checked = savedTheme === 'dark';
            
            themeToggle.addEventListener('change', (e) => {
                const theme = e.target.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('chatmrpt-theme', theme);
            });
        }
        
        // Language selector
        const langSelect = document.getElementById('nav-language-selector');
        if (langSelect) {
            const savedLang = localStorage.getItem('chatmrpt-language') || 'en';
            langSelect.value = savedLang;
            
            langSelect.addEventListener('change', (e) => {
                localStorage.setItem('chatmrpt-language', e.target.value);
                console.log('Language changed to:', e.target.value);
            });
        }
    }

    setupNavItems() {
        // Chat link
        const chatLink = document.getElementById('nav-chat');
        if (chatLink) {
            chatLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
            });
        }
        
        // Privacy link
        const privacyLink = document.getElementById('nav-privacy');
        if (privacyLink) {
            privacyLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
                // Use the privacy notice manager to show the modal
                if (window.privacyNoticeManager) {
                    window.privacyNoticeManager.showPrivacyNotice();
                } else {
                    // Fallback if manager not available
                    const privacyModal = document.getElementById('privacyModal');
                    if (privacyModal && window.bootstrap) {
                        const modal = new bootstrap.Modal(privacyModal);
                        modal.show();
                    }
                }
            });
        }
        
        // About link
        const aboutLink = document.getElementById('nav-settings');
        if (aboutLink) {
            aboutLink.addEventListener('click', (e) => {
                e.preventDefault();
                alert('ChatMRPT v2.0\nMalaria Risk Prioritization Tool\n\nHelps identify high-risk malaria areas for targeted interventions.');
                this.close();
            });
        }
    }
}

// Create instance
const verticalNav = new VerticalNavV2();
export default verticalNav;