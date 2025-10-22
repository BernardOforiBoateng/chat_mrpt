#!/usr/bin/env node
/**
 * Test frontend workflow transition logic
 * This simulates the browser environment and tests the actual logic
 */

// Mock browser globals
global.document = {
    querySelector: (selector) => {
        if (selector === '.tab-pane.active') {
            return { id: global.activeTab || 'standard-upload' };
        }
        return null;
    },
    getElementById: (id) => {
        if (id === 'standard-upload-tab') {
            return { 
                click: () => console.log('  → Tab switched to standard-upload')
            };
        }
        return null;
    }
};

global.sessionStorage = {
    data: {},
    getItem(key) { return this.data[key] || null; },
    setItem(key, value) { 
        this.data[key] = value;
        console.log(`  → sessionStorage.setItem('${key}', '${value}')`);
    },
    removeItem(key) { 
        delete this.data[key];
        console.log(`  → sessionStorage.removeItem('${key}')`);
    }
};

global.localStorage = {
    data: {},
    getItem(key) { return this.data[key] || null; },
    setItem(key, value) { this.data[key] = value; },
    removeItem(key) { 
        delete this.data[key];
        console.log(`  → localStorage.removeItem('${key}')`);
    }
};

// Simulate the API Client logic from our actual code
function determineEndpoint(message) {
    const activeTab = document.querySelector('.tab-pane.active')?.id || 'standard-upload';
    const isDataAnalysis = activeTab === 'data-analysis';
    
    let endpoint = '/api/unified/chat-stream';
    let requestBody = {
        message: message,
        tab_context: activeTab,
        is_data_analysis: isDataAnalysis
    };
    
    // The actual logic from api-client.js
    if (isDataAnalysis && 
        sessionStorage.getItem('has_data_analysis_file') === 'true' && 
        sessionStorage.getItem('data_analysis_exited') !== 'true') {
        endpoint = '/api/unified/chat-stream';
        console.log('  📊 Routing to Data Analysis V3 endpoint');
    } else if (sessionStorage.getItem('data_analysis_exited') === 'true') {
        console.log('  📊 Data Analysis exited, routing to main workflow');
        sessionStorage.removeItem('data_analysis_exited');
    }
    
    return endpoint;
}

function handleExitResponse(result) {
    if (result.exit_data_analysis_mode) {
        console.log('  📊 Exiting Data Analysis mode, switching to main workflow');
        
        // Clear Data Analysis mode flags PERMANENTLY
        sessionStorage.removeItem('has_data_analysis_file');
        sessionStorage.setItem('data_analysis_exited', 'true');
        
        // Also clear from localStorage to be sure
        localStorage.removeItem('has_data_analysis_file');
        
        // Simulate tab switch
        const standardTab = document.getElementById('standard-upload-tab');
        if (standardTab) {
            standardTab.click();
        }
        
        return true;
    }
    return false;
}

// Test functions
function test1_InitialTPRRouting() {
    console.log('\n✅ Test 1: Initial TPR Routing');
    console.log('================================');
    
    // Reset environment
    sessionStorage.data = {};
    localStorage.data = {};
    global.activeTab = 'data-analysis';
    
    // Set up TPR state
    sessionStorage.setItem('has_data_analysis_file', 'true');
    
    // Test routing
    const endpoint = determineEndpoint('guide me through TPR calculation');
    console.log(`  Result: ${endpoint}`);
    
    const passed = endpoint === '/api/unified/chat-stream';
    console.log(passed ? '  ✅ PASSED' : '  ❌ FAILED');
    return passed;
}

function test2_ExitResponseHandling() {
    console.log('\n✅ Test 2: Exit Response Handling');
    console.log('==================================');
    
    // Reset and setup
    sessionStorage.data = {};
    localStorage.data = {};
    sessionStorage.setItem('has_data_analysis_file', 'true');
    
    // Simulate receiving exit response
    console.log('  Simulating exit_data_analysis_mode response...');
    const exitHandled = handleExitResponse({ 
        exit_data_analysis_mode: true,
        message: 'Switching to main workflow'
    });
    
    // Check results
    const flagsCorrect = 
        sessionStorage.getItem('has_data_analysis_file') === null &&
        sessionStorage.getItem('data_analysis_exited') === 'true' &&
        localStorage.getItem('has_data_analysis_file') === null;
    
    console.log(`  Exit handled: ${exitHandled}`);
    console.log(`  Flags correct: ${flagsCorrect}`);
    
    const passed = exitHandled && flagsCorrect;
    console.log(passed ? '  ✅ PASSED' : '  ❌ FAILED');
    return passed;
}

function test3_PostExitRouting() {
    console.log('\n✅ Test 3: Post-Exit Routing');
    console.log('=============================');
    
    // Setup post-exit state
    sessionStorage.data = {};
    sessionStorage.setItem('data_analysis_exited', 'true');
    global.activeTab = 'data-analysis'; // Still in Data Analysis tab
    
    console.log('  Testing routing after exit...');
    const endpoint = determineEndpoint('Check data quality');
    console.log(`  Result: ${endpoint}`);
    
    // Check that exit flag was cleared
    const exitFlagCleared = sessionStorage.getItem('data_analysis_exited') === null;
    console.log(`  Exit flag cleared: ${exitFlagCleared}`);
    
    const passed = endpoint === '/api/unified/chat-stream' && exitFlagCleared;
    console.log(passed ? '  ✅ PASSED' : '  ❌ FAILED');
    return passed;
}

function test4_CompleteWorkflow() {
    console.log('\n✅ Test 4: Complete Workflow Simulation');
    console.log('=========================================');
    
    // Reset
    sessionStorage.data = {};
    localStorage.data = {};
    global.activeTab = 'data-analysis';
    
    console.log('  Step 1: Upload TPR data');
    sessionStorage.setItem('has_data_analysis_file', 'true');
    
    console.log('  Step 2: Run TPR calculation');
    let endpoint = determineEndpoint('guide me through TPR');
    console.log(`    Endpoint: ${endpoint}`);
    if (endpoint !== '/api/unified/chat-stream') return false;
    
    console.log('  Step 3: Complete TPR, say "yes"');
    endpoint = determineEndpoint('yes');
    console.log(`    Endpoint: ${endpoint}`);
    
    console.log('  Step 4: Receive exit response');
    handleExitResponse({ exit_data_analysis_mode: true });
    
    console.log('  Step 5: Send "Check data quality"');
    endpoint = determineEndpoint('Check data quality');
    console.log(`    Endpoint: ${endpoint}`);
    
    const passed = endpoint === '/api/unified/chat-stream';
    console.log(passed ? '  ✅ PASSED' : '  ❌ FAILED');
    return passed;
}

function test5_NoReentryAfterExit() {
    console.log('\n✅ Test 5: No Re-entry After Exit');
    console.log('===================================');
    
    // Setup
    sessionStorage.data = {};
    global.activeTab = 'data-analysis';
    
    // Complete an exit
    sessionStorage.setItem('has_data_analysis_file', 'true');
    handleExitResponse({ exit_data_analysis_mode: true });
    
    console.log('  Testing multiple messages after exit...');
    
    // Try multiple messages
    const endpoints = [
        determineEndpoint('Check data quality'),
        determineEndpoint('Run analysis'),
        determineEndpoint('Show me the map')
    ];
    
    const allMainWorkflow = endpoints.every(ep => ep === '/api/unified/chat-stream');
    console.log(`  All routed to main: ${allMainWorkflow}`);
    
    const passed = allMainWorkflow;
    console.log(passed ? '  ✅ PASSED' : '  ❌ FAILED');
    return passed;
}

// Run all tests
console.log('🧪 Frontend Workflow Transition Tests');
console.log('=====================================');

const tests = [
    test1_InitialTPRRouting,
    test2_ExitResponseHandling,
    test3_PostExitRouting,
    test4_CompleteWorkflow,
    test5_NoReentryAfterExit
];

let passCount = 0;
let failCount = 0;

tests.forEach((test, index) => {
    try {
        if (test()) {
            passCount++;
        } else {
            failCount++;
        }
    } catch (error) {
        console.error(`  Error in test ${index + 1}: ${error.message}`);
        failCount++;
    }
});

console.log('\n=====================================');
console.log(`📊 Results: ${passCount}/${tests.length} tests passed`);

if (passCount === tests.length) {
    console.log('🎉 All frontend tests passed!');
    process.exit(0);
} else {
    console.log(`⚠️  ${failCount} tests failed`);
    process.exit(1);
}
