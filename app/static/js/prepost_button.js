/**
 * Pre-Post Test Button Integration for ChatMRPT
 * Adds a pre/post test button to the existing React interface
 */

(function() {
    'use strict';

    class PrePostButton {
        constructor() {
            console.log('🟢 PrePostButton: Constructor called');
            this.init();
        }

        init() {
            console.log('🟢 PrePostButton: Init called');
            // Wait for page to fully load
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                this.setup();
            }
        }

        setup() {
            console.log('🟢 PrePostButton: Setup called');
            // Create and inject pre-post test button
            this.createPrePostButton();
        }

        createPrePostButton() {
            console.log('🟢 PrePostButton: CreatePrePostButton called');
            let attempts = 0;
            const maxAttempts = 10;

            const tryCreateButton = () => {
                attempts++;
                console.log(`🟢 PrePostButton: Attempt ${attempts}/${maxAttempts} to find nav bar`);

                // Find the navigation bar (same logic as survey_button.js)
                let navBar = document.querySelector('header') ||
                            document.querySelector('[class*="navbar"]') ||
                            document.querySelector('[class*="nav-bar"]') ||
                            document.querySelector('[class*="header"]') ||
                            document.querySelector('nav');

                // Find both Clear and Export buttons to locate the navbar correctly
                const clearButton = Array.from(document.querySelectorAll('button')).find(btn =>
                    btn.textContent.includes('Clear')
                );
                const exportButton = Array.from(document.querySelectorAll('button')).find(btn =>
                    btn.textContent.includes('Export')
                );

                console.log('🟢 PrePostButton: Found navBar?', !!navBar, 'Found Clear?', !!clearButton, 'Found Export?', !!exportButton);

                // Use the common parent of Clear and Export buttons as the navbar
                if (clearButton && exportButton) {
                    let commonParent = exportButton.parentElement;
                    while (commonParent && !commonParent.contains(clearButton)) {
                        commonParent = commonParent.parentElement;
                    }
                    if (commonParent) {
                        navBar = commonParent;
                    }
                } else if (exportButton) {
                    navBar = exportButton.parentElement;
                }

                // If still no nav bar found and we've tried enough times, create our own
                if (!navBar && attempts >= maxAttempts) {
                    navBar = document.createElement('div');
                    navBar.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 60px;
                        background: #ffffff;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                        align-items: center;
                        justify-content: flex-end;
                        padding: 0 20px;
                        z-index: 9998;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    `;
                    document.body.appendChild(navBar);
                    document.body.style.paddingTop = '60px';
                } else if (!navBar) {
                    // Try again in 500ms if we haven't reached max attempts
                    setTimeout(tryCreateButton, 500);
                    return;
                }

                // Check if button already exists to avoid duplicates
                if (document.getElementById('prepost-button')) {
                    return;
                }

                this.insertPrePostButton(navBar);
            };

            // Start trying to create the button
            tryCreateButton();
        }

        insertPrePostButton(navBar) {
            // Create button container for top nav
            const buttonContainer = document.createElement('div');
            buttonContainer.id = 'prepost-button-container';
            buttonContainer.style.cssText = `
                display: inline-flex;
                align-items: center;
                margin-left: 20px;
                margin-right: 10px;
            `;

            // Create button with a design that fits in the nav bar
            const button = document.createElement('button');
            button.id = 'prepost-button';
            button.className = 'prepost-btn';
            button.style.cssText = `
                background: transparent;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s ease;
            `;

            button.innerHTML = `
                <span style="font-size: 16px;">📝</span>
                <span>Pre/Post Test</span>
            `;

            button.onmouseover = () => {
                button.style.background = '#10b981';
                button.style.color = 'white';
                button.style.borderColor = '#10b981';
            };

            button.onmouseout = () => {
                button.style.background = 'transparent';
                button.style.color = '#374151';
                button.style.borderColor = '#e5e7eb';
            };

            button.onclick = () => this.openPrePostTest();

            // Add a subtle separator before the button
            const separator = document.createElement('span');
            separator.style.cssText = `
                display: inline-block;
                width: 1px;
                height: 24px;
                background: #e5e7eb;
                margin-right: 15px;
                vertical-align: middle;
            `;
            buttonContainer.appendChild(separator);
            buttonContainer.appendChild(button);

            // Add to nav bar - insert at the END after all existing buttons
            const allButtons = Array.from(navBar.querySelectorAll('button'));

            if (allButtons.length > 0) {
                // Get the last button
                const lastButton = allButtons[allButtons.length - 1];

                // Insert after the last button
                if (lastButton.nextSibling) {
                    lastButton.parentElement.insertBefore(buttonContainer, lastButton.nextSibling);
                } else {
                    lastButton.parentElement.appendChild(buttonContainer);
                }
            } else {
                // No buttons found, just append to nav bar
                navBar.appendChild(buttonContainer);
            }

            console.log('🟢 PrePostButton: Button inserted successfully');
        }

        openPrePostTest() {
            console.log('🟢 PrePostButton: Opening pre/post test');
            // Open pre/post test in new tab
            window.open('/prepost', '_blank');
        }
    }

    // Initialize pre-post test button
    console.log('🟢 PrePostButton: Script loaded, creating instance');
    window.prepostButton = new PrePostButton();
    console.log('🟢 PrePostButton: Instance created:', !!window.prepostButton);
})();
