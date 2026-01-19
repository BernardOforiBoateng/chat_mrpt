/**
 * Vertical Navigation Module
 * Handles vertical sidebar navigation functionality
 */

import DOMHelpers from '../utils/dom-helpers.js';
import { SessionDataManager } from '../utils/storage.js';

export class VerticalNavManager {
    constructor() {
        this.nav = null;
        this.navToggle = null;
        this.mobileToggle = null;
        this.navOverlay = null;
        this.navItems = [];
        this.isCollapsed = false;
        this.isMobileOpen = false;
        
        this.init();
    }

    /**
     * Initialize vertical navigation
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeElements());
        } else {
            this.initializeElements();
        }
    }
    
    initializeElements() {
        this.nav = DOMHelpers.getElementById('vertical-nav');
        this.navToggle = DOMHelpers.getElementById('nav-collapse-toggle');
        this.mobileToggle = DOMHelpers.getElementById('mobile-nav-toggle');
        this.navOverlay = DOMHelpers.getElementById('nav-overlay');
        
        console.log('Vertical nav initialized:', {
            nav: !!this.nav,
            navToggle: !!this.navToggle,
            mobileToggle: !!this.mobileToggle
        });
        
        if (!this.nav) {
            console.warn('Vertical navigation element not found');
            return;
        }
        
        this.setupEventListeners();
        this.loadSavedState();
        this.setupNavigationItems();
        this.setupPreferences();
        this.setActiveNavItem();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Desktop collapse toggle
        if (this.navToggle) {
            this.navToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleCollapse();
            });
        }

        // Mobile menu toggle
        if (this.mobileToggle) {
            this.mobileToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }

        // Close mobile menu on overlay click
        if (this.navOverlay) {
            this.navOverlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Close mobile menu on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isMobileOpen) {
                this.closeMobileMenu();
            }
        });
    }

    /**
     * Setup navigation item click handlers
     */
    setupNavigationItems() {
        this.navItems = this.nav.querySelectorAll('.nav-item');
        
        this.navItems.forEach(item => {
            // Skip external links
            if (item.href && !item.href.startsWith('#')) {
                return;
            }
            
            item.addEventListener('click', (e) => {
                const itemId = item.id;
                
                switch(itemId) {
                    case 'nav-chat':
                        e.preventDefault();
                        this.setActiveNavItem('nav-chat');
                        // Already on chat page
                        if (this.isMobileOpen) {
                            this.closeMobileMenu();
                        }
                        break;
                        
                    case 'nav-upload':
                        e.preventDefault();
                        this.setActiveNavItem('nav-upload');
                        // Trigger upload modal
                        const uploadBtn = document.getElementById('upload-button');
                        if (uploadBtn) {
                            uploadBtn.click();
                        }
                        if (this.isMobileOpen) {
                            this.closeMobileMenu();
                        }
                        break;
                        
                    case 'nav-settings':
                        e.preventDefault();
                        this.setActiveNavItem('nav-settings');
                        // Show about modal or info
                        this.showAboutInfo();
                        if (this.isMobileOpen) {
                            this.closeMobileMenu();
                        }
                        break;
                        
                    case 'nav-reports':
                    case 'nav-admin':
                        // These have hrefs, let them navigate normally
                        if (this.isMobileOpen) {
                            this.closeMobileMenu();
                        }
                        break;
                }
            });
        });
    }

    /**
     * Toggle collapse state (desktop only)
     */
    toggleCollapse() {
        console.log('Toggle collapse called, current state:', this.isCollapsed);
        this.isCollapsed = !this.isCollapsed;
        
        if (this.isCollapsed) {
            DOMHelpers.addClass(this.nav, 'collapsed');
            this.navToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
        } else {
            DOMHelpers.removeClass(this.nav, 'collapsed');
            this.navToggle.innerHTML = '<i class="fas fa-chevron-left"></i>';
        }
        
        console.log('New collapsed state:', this.isCollapsed);
        
        // Save state
        SessionDataManager.updateSettings({ navCollapsed: this.isCollapsed });
        
        // Dispatch event for other modules
        document.dispatchEvent(new CustomEvent('navToggled', {
            detail: { collapsed: this.isCollapsed }
        }));
        
        // Update main interface for browsers without :has() support
        const mainInterface = document.querySelector('.main-chat-interface');
        if (mainInterface) {
            if (this.isCollapsed) {
                mainInterface.style.marginLeft = '60px';
                mainInterface.style.width = 'calc(100vw - 60px)';
            } else {
                mainInterface.style.marginLeft = '240px';
                mainInterface.style.width = 'calc(100vw - 240px)';
            }
        }
    }

    /**
     * Toggle mobile menu
     */
    toggleMobileMenu() {
        if (this.isMobileOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }

    /**
     * Open mobile menu
     */
    openMobileMenu() {
        this.isMobileOpen = true;
        DOMHelpers.addClass(this.nav, 'mobile-open');
        DOMHelpers.addClass(this.navOverlay, 'show');
        DOMHelpers.addClass(document.body, 'nav-open');
        
        // Update ARIA
        this.mobileToggle.setAttribute('aria-expanded', 'true');
        this.nav.setAttribute('aria-hidden', 'false');
    }

    /**
     * Close mobile menu
     */
    closeMobileMenu() {
        this.isMobileOpen = false;
        DOMHelpers.removeClass(this.nav, 'mobile-open');
        DOMHelpers.removeClass(this.navOverlay, 'show');
        DOMHelpers.removeClass(document.body, 'nav-open');
        
        // Update ARIA
        this.mobileToggle.setAttribute('aria-expanded', 'false');
        this.nav.setAttribute('aria-hidden', 'true');
    }

    /**
     * Handle window resize
     */
    handleResize() {
        const isMobile = window.innerWidth <= 768;
        
        if (!isMobile && this.isMobileOpen) {
            // Close mobile menu when resizing to desktop
            this.closeMobileMenu();
        }
    }

    /**
     * Load saved navigation state
     */
    loadSavedState() {
        const settings = SessionDataManager.getSettings();
        
        if (settings.navCollapsed && window.innerWidth > 768) {
            this.isCollapsed = true;
            DOMHelpers.addClass(this.nav, 'collapsed');
            this.navToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
        }
    }

    /**
     * Set active navigation item
     * @param {string} itemId - ID of the nav item to activate
     */
    setActiveNavItem(itemId = null) {
        // Remove active class from all items
        this.navItems.forEach(item => {
            DOMHelpers.removeClass(item, 'active');
        });
        
        // If no itemId provided, try to determine from current page
        if (!itemId) {
            const currentPath = window.location.pathname;
            
            if (currentPath === '/' || currentPath === '') {
                itemId = 'nav-chat';
            } else if (currentPath.includes('report')) {
                itemId = 'nav-reports';
            } else if (currentPath.includes('admin')) {
                itemId = 'nav-admin';
            }
        }
        
        // Set active class on specified item
        if (itemId) {
            const activeItem = DOMHelpers.getElementById(itemId);
            if (activeItem) {
                DOMHelpers.addClass(activeItem, 'active');
            }
        }
    }

    /**
     * Get current navigation state
     * @returns {Object} Navigation state
     */
    getState() {
        return {
            isCollapsed: this.isCollapsed,
            isMobileOpen: this.isMobileOpen,
            activeItem: this.nav.querySelector('.nav-item.active')?.id || null
        };
    }

    /**
     * Setup preferences controls (theme and language)
     */
    setupPreferences() {
        // Theme toggle
        const themeToggle = DOMHelpers.getElementById('nav-theme-toggle');
        if (themeToggle) {
            // Load saved theme
            const savedTheme = localStorage.getItem('chatmrpt-theme') || 'light';
            themeToggle.checked = savedTheme === 'dark';
            if (savedTheme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            }
            
            // Handle theme toggle
            themeToggle.addEventListener('change', (e) => {
                const theme = e.target.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('chatmrpt-theme', theme);
                
                // Update moon icon color
                const moonIcon = this.nav.querySelector('.nav-pref-item .fa-moon');
                if (moonIcon) {
                    if (theme === 'dark') {
                        moonIcon.style.color = 'var(--accent-primary)';
                    } else {
                        moonIcon.style.color = '';
                    }
                }
                
                // Dispatch event for other modules
                document.dispatchEvent(new CustomEvent('themeChanged', {
                    detail: { theme }
                }));
            });
        }
        
        // Language selector
        const languageSelector = DOMHelpers.getElementById('nav-language-selector');
        if (languageSelector) {
            // Load saved language
            const savedLang = localStorage.getItem('chatmrpt-language') || 'en';
            languageSelector.value = savedLang;
            
            // Handle language change
            languageSelector.addEventListener('change', (e) => {
                const language = e.target.value;
                localStorage.setItem('chatmrpt-language', language);
                
                // Dispatch event for other modules
                document.dispatchEvent(new CustomEvent('languageChanged', {
                    detail: { language }
                }));
                
                // Show notification
                console.log(`Language changed to: ${language}`);
            });
        }
    }
    
    /**
     * Show about information
     */
    showAboutInfo() {
        // Create a simple modal or alert with about info
        const aboutMessage = `
ChatMRPT v2.0
Malaria Risk Prioritization Tool

ChatMRPT helps identify high-risk malaria areas for targeted interventions and resource allocation.

© 2024 ChatMRPT Team
        `;
        
        // For now, use alert. In production, create a proper modal
        alert(aboutMessage.trim());
    }
    
    /**
     * Update navigation based on authentication state
     * @param {boolean} isAuthenticated - Whether user is authenticated
     */
    updateAuthState(isAuthenticated) {
        const adminSection = this.nav.querySelector('.nav-section:has(#nav-admin)');
        
        if (adminSection) {
            if (isAuthenticated) {
                DOMHelpers.show(adminSection);
            } else {
                DOMHelpers.hide(adminSection);
            }
        }
    }
}

// Create and export singleton instance
const verticalNavManager = new VerticalNavManager();

export default verticalNavManager;