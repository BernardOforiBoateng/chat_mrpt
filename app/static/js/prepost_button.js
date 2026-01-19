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

                const actionGroup = document.getElementById('toolbar-action-group');
                if (actionGroup) {
                    navBar = actionGroup;
                }

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
                        gap: 12px;
                        z-index: 9998;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    `;
                    navBar.id = 'toolbar-action-group';
                    document.body.appendChild(navBar);
                    document.body.style.paddingTop = '60px';
                } else if (!navBar) {
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
            if (navBar && navBar.classList) {
                navBar.classList.add('flex');
                navBar.classList.add('items-center');
                navBar.classList.add('gap-3');
            }

            const button = document.createElement('button');
            button.id = 'prepost-button';
            button.type = 'button';
            button.className = 'toolbar-button toolbar-button--prepost';

            button.innerHTML = `
                <span class="toolbar-button-icon">📝</span>
                <span class="toolbar-button-label">Pre/Post Test</span>
            `;

            button.onclick = () => this.openPrePostTest();

            navBar.appendChild(button);

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
