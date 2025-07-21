// Test script for new hamburger navigation
// Run this in browser console after page loads

console.log('=== Testing Hamburger Navigation ===');

// Check if elements exist
const hamburger = document.getElementById('hamburger-menu');
const nav = document.getElementById('vertical-nav');
const overlay = document.getElementById('nav-overlay');

console.log('Hamburger button exists:', !!hamburger);
console.log('Navigation sidebar exists:', !!nav);
console.log('Overlay exists:', !!overlay);

// Check if hamburger is visible
if (hamburger) {
    const styles = window.getComputedStyle(hamburger);
    console.log('Hamburger visible:', styles.display !== 'none');
    console.log('Hamburger position:', styles.position);
    console.log('Hamburger z-index:', styles.zIndex);
}

// Check if nav is hidden by default
if (nav) {
    const styles = window.getComputedStyle(nav);
    console.log('Nav left position:', styles.left);
    console.log('Nav has active class:', nav.classList.contains('active'));
}

// Test clicking hamburger
if (hamburger) {
    console.log('\nClicking hamburger...');
    hamburger.click();
    
    setTimeout(() => {
        console.log('After click:');
        console.log('Nav has active class:', nav.classList.contains('active'));
        console.log('Overlay has active class:', overlay.classList.contains('active'));
        
        // Check if nav items are visible
        const navItems = nav.querySelectorAll('.nav-item');
        console.log('Number of nav items found:', navItems.length);
        navItems.forEach((item, index) => {
            console.log(`Nav item ${index}: ${item.textContent.trim()}`);
        });
    }, 500);
}