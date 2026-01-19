/**
 * Pre-Post Test JavaScript Handler
 * Manages the complete test flow including phone verification,
 * question display, time tracking, and response submission
 */

class PrePostTestHandler {
    constructor() {
        this.phoneNumber = null;
        this.sessionId = null;
        this.testType = null;  // 'pre' or 'post'
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.responses = {};
        this.testStartTime = null;
        this.questionStartTime = null;
        this.timerInterval = null;
        this.backgroundData = {};

        this.init();
    }

    init() {
        console.log('[PrePost] Initializing handler');
        // Phone input validation
        const phoneInput = document.getElementById('phoneInput');
        if (phoneInput) {
            phoneInput.addEventListener('input', this.validatePhoneInput.bind(this));
            phoneInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.checkPhoneAndStart();
                }
            });
        }

        // Attempt to resume saved state on refresh
        try {
            const saved = localStorage.getItem('prepost_state');
            if (saved) {
                const state = JSON.parse(saved);
                if (state && state.status === 'in_progress' && Array.isArray(state.questions)) {
                    console.log('[PrePost] Resuming saved state');
                    this.phoneNumber = state.phoneNumber || null;
                    this.sessionId = state.sessionId || null;
                    this.testType = state.testType || null;
                    this.questions = state.questions || [];
                    this.currentQuestionIndex = Math.min(Math.max(state.currentQuestionIndex || 0, 0), this.questions.length - 1);
                    this.responses = state.responses || {};
                    this.testStartTime = state.testStartTime || Date.now();
                    this.backgroundData = state.backgroundData || {};

                    // Jump straight to questions view
                    this.showQuestion(this.currentQuestionIndex);
                    this.showSection('questionSection');
                }
            }
        } catch (e) {
            console.warn('[PrePost] Failed to resume saved state:', e);
        }
    }

    validatePhoneInput(event) {
        const input = event.target;
        // Only allow digits
        input.value = input.value.replace(/[^0-9]/g, '');

        // Auto-check when 4 digits entered
        if (input.value.length === 4) {
            this.checkPhone(input.value);
        }
    }

    async checkPhone(phone) {
        try {
            const response = await fetch('/prepost/api/check-phone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_last4: phone })
            });

            const data = await response.json();

            if (data.success) {
                const messageEl = document.getElementById('testTypeMessage');
                messageEl.textContent = data.message;
                messageEl.classList.add('show');
                this.testType = data.test_type;
            }

        } catch (error) {
            console.error('[PrePost] Error checking phone:', error);
        }
    }

    async checkPhoneAndStart() {
        const phoneInput = document.getElementById('phoneInput');
        const phone = phoneInput.value.trim();

        // Validate phone number
        if (phone.length !== 4 || !/^\d{4}$/.test(phone)) {
            alert('Please enter exactly 4 digits');
            phoneInput.focus();
            return;
        }

        this.phoneNumber = phone;

        try {
            // Show loading
            this.showSection('loadingSection');

            // Check phone and start test
            const checkResponse = await fetch('/prepost/api/check-phone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_last4: phone })
            });

            const checkData = await checkResponse.json();

            if (!checkData.success) {
                throw new Error(checkData.error || 'Failed to verify phone number');
            }

            this.testType = checkData.test_type;

            // Start test session
            const startResponse = await fetch('/prepost/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone_last4: phone,
                    test_type: this.testType
                })
            });

            const startData = await startResponse.json();

            if (!startData.success) {
                throw new Error(startData.error || 'Failed to start test');
            }

            this.sessionId = startData.session_id;
            this.questions = startData.questions;
            this.testStartTime = Date.now();

            console.log(`[PrePost] Started ${this.testType} test with ${this.questions.length} questions`);

            // Persist and show first question
            this.persistState();
            this.showQuestion(0);
            this.showSection('questionSection');

        } catch (error) {
            console.error('[PrePost] Error starting test:', error);
            this.showError(error.message);
        }
    }

    showQuestion(index) {
        if (index < 0 || index >= this.questions.length) {
            console.error('[PrePost] Invalid question index:', index);
            return;
        }

        this.currentQuestionIndex = index;
        this.questionStartTime = Date.now();

        const question = this.questions[index];
        console.log('[PrePost] Showing question:', question.id);

        // Update progress
        this.updateProgress();

        // Update section badge
        const badgeEl = document.getElementById('sectionBadge');
        if (question.section === 'background') {
            badgeEl.textContent = 'Background Information';
            badgeEl.className = 'section-badge';
        } else {
            badgeEl.textContent = 'Concept Assessment';
            badgeEl.className = 'section-badge concepts';
        }

        // Show/hide timer (only for concepts section)
        const timerEl = document.getElementById('timer');
        if (question.section === 'concepts') {
            timerEl.style.display = 'inline-block';
            this.startTimer();
        } else {
            timerEl.style.display = 'none';
            this.stopTimer();
        }

        // Update question number
        document.getElementById('questionNumber').textContent =
            `Question ${index + 1} of ${this.questions.length}`;

        // Render question
        const questionHTML = this.renderQuestion(question);
        document.getElementById('questionContent').innerHTML = questionHTML;

        // Load saved response if exists
        if (this.responses[question.id]) {
            this.loadSavedResponse(question.id, this.responses[question.id]);
        }

        // Update navigation buttons
        this.updateNavigation();

        // Persist progress
        this.persistState();
    }

    renderQuestion(question) {
        console.log('[PrePost] renderQuestion called for:', question.id, 'type:', question.type);
        let html = '';

        // Section header type - special rendering
        if (question.type === 'section_header') {
            html += `<div class="section-header-container">
                        <h2 class="section-header-title">${question.text}</h2>`;
            if (question.instruction) {
                html += `<p class="section-header-instruction">${question.instruction}</p>`;
            }
            html += `</div>`;
            return html;
        }

        // Question text
        html += `<div class="question-text">${question.text}</div>`;

        // Instruction if exists
        if (question.instruction) {
            html += `<div class="question-instruction">${question.instruction}</div>`;
        }

        // Map link if exists
        if (question.has_map_link && question.map_link) {
            html += `<a href="${question.map_link}" target="_blank" class="map-link">
                🗺️ View Vulnerability Map
            </a>`;
        }

        // Render based on type
        switch (question.type) {
            case 'text':
                html += `<input type="text"
                               class="input-text"
                               id="response_${question.id}"
                               placeholder="Type your answer here..."
                               ${question.maxlength ? `maxlength="${question.maxlength}"` : ''}
                               ${question.pattern ? `pattern="${question.pattern}"` : ''}
                               ${question.required ? 'required' : ''}>`;
                break;

            case 'number':
                html += `<input type="number"
                               class="input-number"
                               id="response_${question.id}"
                               min="${question.min || 0}"
                               max="${question.max || 100}"
                               ${question.required ? 'required' : ''}>`;
                break;

            case 'textarea':
                html += `<textarea class="input-textarea"
                                  id="response_${question.id}"
                                  placeholder="Type your answer here..."
                                  ${question.required ? 'required' : ''}></textarea>`;
                break;

            case 'radio':
                html += '<div class="radio-options">';
                question.options.forEach((option, i) => {
                    html += `
                        <div class="radio-option" onclick="prepostHandler.selectRadio('${question.id}', ${i})">
                            <input type="radio"
                                   name="response_${question.id}"
                                   id="response_${question.id}_${i}"
                                   value="${i}"
                                   ${question.required ? 'required' : ''}>
                            <label for="response_${question.id}_${i}">${option}</label>
                        </div>
                    `;
                });
                html += '</div>';
                break;

            case 'scale':
                const minVal = question.min || 1;
                const maxVal = question.max || 5;

                html += '<div class="scale-container">';
                html += '<div class="scale-options">';
                for (let i = minVal; i <= maxVal; i++) {
                    html += `
                        <div class="scale-option"
                             id="scale_${question.id}_${i}"
                             onclick="prepostHandler.selectScale('${question.id}', ${i})">
                            ${i}
                        </div>
                    `;
                }
                html += '</div>';

                // Show labels if provided
                if (question.labels && question.labels.length > 0) {
                    html += '<div class="scale-labels">';
                    question.labels.forEach(label => {
                        html += `<span>${label}</span>`;
                    });
                    html += '</div>';
                }
                html += '</div>';
                break;

            case 'checkbox':
                // Ensure options exist (defensive fallback for production cache mismatches)
                let options = Array.isArray(question.options) ? question.options : null;
                if (!options) {
                    // Fallback for known question IDs if options missing in payload
                    if (question.id === 'bg_resource_access') {
                        options = [
                            'Laptop or desktop',
                            'Smartphone or tablet',
                            'Stable internet',
                            'Stable electricity'
                        ];
                        console.warn('[PrePost] Fallback applied: using default options for bg_resource_access');
                    }
                }

                console.log('[PrePost] Rendering checkbox question:', question.id, 'with options:', options);
                html += '<div class="checkbox-options">';
                if (options) {
                    options.forEach((option, i) => {
                        html += `
                            <div class="checkbox-option">
                                <input type="checkbox"
                                       name="response_${question.id}"
                                       id="response_${question.id}_${i}"
                                       value="${i}"
                                       onchange="prepostHandler.updateCheckboxSelection('${question.id}')">
                                <label for="response_${question.id}_${i}">${option}</label>
                            </div>
                        `;
                    });
                } else {
                    console.error('[PrePost] No options found for checkbox question:', question.id);
                    html += '<p style="color: red;">Options are unavailable. Please refresh and try again.</p>';
                }
                html += '</div>';
                break;
        }

        return html;
    }

    selectRadio(questionId, optionIndex) {
        const radio = document.getElementById(`response_${questionId}_${optionIndex}`);
        if (radio) {
            radio.checked = true;
            // Update visual selection
            document.querySelectorAll('.radio-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            radio.closest('.radio-option').classList.add('selected');

            // Save response
            this.responses[questionId] = optionIndex;
        }
    }

    selectScale(questionId, value) {
        // Clear previous selection
        document.querySelectorAll('.scale-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        // Add selection
        const selected = document.getElementById(`scale_${questionId}_${value}`);
        if (selected) {
            selected.classList.add('selected');
            this.responses[questionId] = value;
        }
    }

    updateCheckboxSelection(questionId) {
        // Get all checked checkboxes for this question
        const checkboxes = document.querySelectorAll(`input[name="response_${questionId}"]:checked`);
        const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.value));

        // Save to responses
        this.responses[questionId] = selectedIndices;
    }

    loadSavedResponse(questionId, response) {
        const question = this.questions.find(q => q.id === questionId);
        if (!question) return;

        switch (question.type) {
            case 'text':
            case 'number':
            case 'textarea':
                const input = document.getElementById(`response_${questionId}`);
                if (input) input.value = response;
                break;

            case 'radio':
                const radio = document.getElementById(`response_${questionId}_${response}`);
                if (radio) {
                    radio.checked = true;
                    radio.closest('.radio-option').classList.add('selected');
                }
                break;

            case 'scale':
                this.selectScale(questionId, response);
                break;

            case 'checkbox':
                if (Array.isArray(response)) {
                    response.forEach(index => {
                        const checkbox = document.getElementById(`response_${questionId}_${index}`);
                        if (checkbox) checkbox.checked = true;
                    });
                }
                break;
        }
    }

    getCurrentResponse() {
        const question = this.questions[this.currentQuestionIndex];
        let response = null;

        switch (question.type) {
            case 'text':
            case 'number':
            case 'textarea':
                const input = document.getElementById(`response_${question.id}`);
                response = input ? input.value.trim() : '';
                break;

            case 'radio':
                const selected = document.querySelector(`input[name="response_${question.id}"]:checked`);
                response = selected ? parseInt(selected.value) : null;
                break;

            case 'scale':
                response = this.responses[question.id] || null;
                break;

            case 'checkbox':
                const checkboxes = document.querySelectorAll(`input[name="response_${question.id}"]:checked`);
                response = Array.from(checkboxes).map(cb => parseInt(cb.value));
                break;
        }

        return response;
    }

    async saveCurrentResponse() {
        const question = this.questions[this.currentQuestionIndex];

        // Skip saving for section headers (just display them)
        if (question.type === 'section_header') {
            return true;
        }

        const response = this.getCurrentResponse();

        // Validate required questions
        if (question.required) {
            if (question.type === 'checkbox') {
                // For checkbox, check if at least one option is selected
                if (!Array.isArray(response) || response.length === 0) {
                    alert('Please select at least one option before proceeding.');
                    return false;
                }
            } else if (response === null || response === '') {
                alert('Please answer this question before proceeding.');
                return false;
            }
        }

        // Calculate time spent
        const timeSpent = Math.floor((Date.now() - this.questionStartTime) / 1000);

        // Save response locally
        this.responses[question.id] = response;

        // Persist after capturing response locally
        this.persistState();

        // If background question, save to backgroundData
        if (question.section === 'background' && question.id !== 'bg_phone') {
            const fieldName = question.id.replace('bg_', '');
            this.backgroundData[fieldName] = response;
        }

        // Submit to server
        try {
            await fetch('/prepost/api/submit-response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    question_id: question.id,
                    section: question.section,
                    response: response,
                    time_spent: timeSpent
                })
            });

            return true;
        } catch (error) {
            console.error('[PrePost] Error saving response:', error);
            // Continue anyway - responses saved locally
            return true;
        }
    }

    async nextQuestion() {
        // Save current response
        if (!await this.saveCurrentResponse()) {
            return;
        }

        // Move to next question
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.showQuestion(this.currentQuestionIndex + 1);
        }
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.showQuestion(this.currentQuestionIndex - 1);
        }
    }

    async submitTest() {
        // Save current response
        if (!await this.saveCurrentResponse()) {
            return;
        }

        // Save background data if pre-test
        if (this.testType === 'pre' && Object.keys(this.backgroundData).length > 0) {
            try {
                await fetch('/prepost/api/save-background', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone_last4: this.phoneNumber,
                        background_data: this.backgroundData
                    })
                });
            } catch (error) {
                console.error('[PrePost] Error saving background data:', error);
            }
        }

        // Complete test
        try {
            this.showSection('loadingSection');

            const response = await fetch('/prepost/api/complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showCompletion(data.score);
            } else {
                throw new Error(data.error || 'Failed to complete test');
            }

        } catch (error) {
            console.error('[PrePost] Error completing test:', error);
            this.showError(error.message);
        }
    }

    showCompletion(score) {
        // Simple completion message without scoring
        // Since there are no embedded correct answers, scoring is not applicable

        // Create simple stats grid showing only participation
        const statsHTML = `
            <div class="stat-item">
                <div class="stat-value">${this.questions.length}</div>
                <div class="stat-label">Questions Answered</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">✓</div>
                <div class="stat-label">Test Completed</div>
            </div>
        `;
        document.getElementById('statsGrid').innerHTML = statsHTML;

        // Hide score display if it exists
        const scoreElement = document.getElementById('scoreNumber');
        if (scoreElement) {
            scoreElement.textContent = 'Complete';
        }

        this.showSection('completionSection');
        // Clear saved state when completed
        this.clearState();
    }

    updateProgress() {
        const progress = ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
        document.getElementById('progressBar').style.width = `${progress}%`;
        document.getElementById('progressText').textContent =
            `Question ${this.currentQuestionIndex + 1} of ${this.questions.length}`;
    }

    updateNavigation() {
        const prevBtn = document.getElementById('btnPrevious');
        const nextBtn = document.getElementById('btnNext');
        const submitBtn = document.getElementById('btnSubmit');

        // Previous button
        prevBtn.style.display = this.currentQuestionIndex > 0 ? 'block' : 'none';

        // Next/Submit buttons
        if (this.currentQuestionIndex === this.questions.length - 1) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'block';
        } else {
            nextBtn.style.display = 'block';
            submitBtn.style.display = 'none';
        }
    }

    startTimer() {
        this.stopTimer(); // Clear any existing timer

        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.questionStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('timer').textContent =
                `⏱️ ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    showSection(sectionId) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.showSection('errorSection');
    }

    persistState() {
        try {
            const state = {
                status: 'in_progress',
                phoneNumber: this.phoneNumber,
                sessionId: this.sessionId,
                testType: this.testType,
                questions: this.questions,
                currentQuestionIndex: this.currentQuestionIndex,
                responses: this.responses,
                testStartTime: this.testStartTime,
                backgroundData: this.backgroundData
            };
            localStorage.setItem('prepost_state', JSON.stringify(state));
        } catch (e) {
            console.warn('[PrePost] Failed to persist state:', e);
        }
    }

    clearState() {
        try {
            localStorage.removeItem('prepost_state');
        } catch (e) {
            console.warn('[PrePost] Failed to clear state:', e);
        }
    }
}

// Initialize handler
let prepostHandler;
document.addEventListener('DOMContentLoaded', () => {
    console.log('[PrePost] DOM loaded, initializing handler');
    prepostHandler = new PrePostTestHandler();
});

// Global functions for HTML onclick handlers
function checkPhoneAndStart() {
    prepostHandler.checkPhoneAndStart();
}

function nextQuestion() {
    prepostHandler.nextQuestion();
}

function previousQuestion() {
    prepostHandler.previousQuestion();
}

function submitTest() {
    if (confirm('Are you sure you want to submit your test? You cannot change your answers after submission.')) {
        prepostHandler.submitTest();
    }
}
