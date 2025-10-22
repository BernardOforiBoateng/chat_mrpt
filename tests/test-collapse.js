// Test script to verify vertical nav collapse functionality
// Run this in the browser console after the page loads

// Test 1: Check if vertical nav elements exist
console.log('=== Vertical Nav Test ===');
console.log('Nav element exists:', !!document.getElementById('vertical-nav'));
console.log('Collapse button exists:', !!document.getElementById('nav-collapse-toggle'));

// Test 2: Check if the module is initialized
console.log('Vertical nav manager exists:', !!window.app?.modules?.verticalNav);

// Test 3: Manually trigger collapse
if (window.app?.modules?.verticalNav) {
    console.log('Testing collapse toggle...');
    window.app.modules.verticalNav.toggleCollapse();
    console.log('Collapse triggered - check if nav is collapsed');
} else {
    console.log('ERROR: Vertical nav module not found!');
}

// Test 4: Check CSS classes
const nav = document.getElementById('vertical-nav');
if (nav) {
    console.log('Nav has collapsed class:', nav.classList.contains('collapsed'));
}

// Test 5: Direct button click test
const button = document.getElementById('nav-collapse-toggle');
if (button) {
    console.log('Clicking collapse button directly...');
    button.click();
    console.log('Button clicked - check visual changes');
}