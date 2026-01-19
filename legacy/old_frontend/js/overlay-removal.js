/**
 * Emergency Overlay Removal Script
 * Removes any blocking overlay that prevents user interaction
 */

(function() {
    'use strict';
    
    console.log('🔧 Overlay removal script loaded');
    
    function removeBlockingOverlays() {
        // Find and remove any blocking overlays
        const selectors = [
            // Common overlay patterns
            '.loading-overlay',
            '.spinner-overlay',
            '.overlay-container',
            '.modal-backdrop',
            
            // React root overlays
            '#root > div:empty',
            '#root > div[style*="position: fixed"]',
            '#root > div[style*="position: absolute"]',
            
            // Circular overlays
            'div[style*="border-radius: 50%"][style*="position: fixed"]',
            'div[style*="border-radius: 50%"][style*="position: absolute"]',
            
            // High z-index blockers
            '*[style*="z-index: 9999"]',
            '*[style*="z-index: 99999"]'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                // Check if element is blocking
                const style = window.getComputedStyle(el);
                const isBlocking = (
                    (style.position === 'fixed' || style.position === 'absolute') &&
                    (style.width === '100%' || parseInt(style.width) > window.innerWidth * 0.8) &&
                    (style.height === '100%' || parseInt(style.height) > window.innerHeight * 0.8)
                );
                
                if (isBlocking) {
                    console.log('🗑️ Removing blocking overlay:', el);
                    el.remove();
                }
            });
        });
        
        // Check for black circular elements in center of screen
        const allDivs = document.querySelectorAll('div');
        allDivs.forEach(div => {
            const style = window.getComputedStyle(div);
            const rect = div.getBoundingClientRect();
            
            // Check if it's a centered circular element
            const isCentered = (
                Math.abs(rect.left + rect.width/2 - window.innerWidth/2) < 100 &&
                Math.abs(rect.top + rect.height/2 - window.innerHeight/2) < 100
            );
            
            const isCircular = style.borderRadius === '50%' || style.borderRadius.includes('50%');
            const isBlack = style.backgroundColor.includes('0, 0, 0') || 
                           style.backgroundColor === 'black' ||
                           style.backgroundColor === 'rgb(0, 0, 0)';
            
            if (isCentered && isCircular && (isBlack || style.position === 'fixed')) {
                console.log('🗑️ Removing centered circular overlay:', div);
                div.remove();
            }
        });
        
        // Ensure main app is interactive
        const mainElements = [
            '.main-chat-interface',
            '.chat-container',
            'main',
            '#chat-messages',
            '.chat-input-container'
        ];
        
        mainElements.forEach(selector => {
            const el = document.querySelector(selector);
            if (el) {
                el.style.pointerEvents = 'auto';
                el.style.position = 'relative';
                el.style.zIndex = '1';
            }
        });
    }
    
    // Run immediately
    removeBlockingOverlays();
    
    // Run after DOM is fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeBlockingOverlays);
    }
    
    // Run after a short delay to catch dynamically created overlays
    setTimeout(removeBlockingOverlays, 100);
    setTimeout(removeBlockingOverlays, 500);
    setTimeout(removeBlockingOverlays, 1000);
    
    // Watch for new overlays being added
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        const style = window.getComputedStyle(node);
                        if ((style.position === 'fixed' || style.position === 'absolute') &&
                            (style.borderRadius === '50%' || style.borderRadius.includes('50%'))) {
                            console.log('🔍 Detected potential overlay, checking...');
                            setTimeout(removeBlockingOverlays, 10);
                        }
                    }
                });
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('✅ Overlay removal script active');
})();