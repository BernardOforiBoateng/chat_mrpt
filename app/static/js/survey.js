/**
 * Survey JavaScript Handler
 * Manages survey interactions, question navigation, and response submission
 */

class SurveyHandler {
    constructor() {
        this.sessionId = null;
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.responses = {};
        this.startTime = null;
        this.questionStartTime = null;
        this.config = window.surveyConfig || {};

        this.init();
    }

    async init() {
        // Show context information
        this.showContextInfo();

        // Check for saved draft
        this.loadDraft();

        // Set up auto-save
        setInterval(() => this.saveDraft(), 30000); // Auto-save every 30 seconds
    }

    showContextInfo() {
        const contextDiv = document.getElementById('contextInfo');
        if (this.config.context && typeof this.config.context === 'object') {
            let contextHtml = '<div class="context-details"><h4>Survey Context:</h4><ul>';

            if (this.config.context.trigger_type) {
                contextHtml += `<li>Activity: ${this.formatTriggerType(this.config.context.trigger_type)}</li>`;
            }
            if (this.config.context.models) {
                contextHtml += `<li>Models compared: ${this.config.context.models.join(', ')}</li>`;
            }

            contextHtml += '</ul></div>';
            contextDiv.innerHTML = contextHtml;
        }
    }

    formatTriggerType(trigger) {
        const triggerNames = {
            'arena_comparison': 'Arena Mode Comparison',
            'risk_analysis_complete': 'Risk Analysis',
            'itn_distribution_generated': 'ITN Distribution',
            'tpr_analysis_complete': 'TPR Analysis'
        };
        return triggerNames[trigger] || trigger;
    }

    async startSurvey() {
        try {
            this.showSection('loadingScreen');

            // Start survey session
            const response = await fetch('/survey/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chatmrpt_session_id: this.config.chatmrptSession,
                    trigger_type: this.config.trigger || 'general_usability',
                    context: this.config.context
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to start survey');
            }

            this.sessionId = data.session_id;
            this.questions = data.questions;
            this.startTime = Date.now();

            // Show first question
            this.showQuestion(0);
            this.showSection('questionContainer');
            document.getElementById('navigation').style.display = 'flex';

        } catch (error) {
            this.showError(error.message);
        }
    }

    showQuestion(index) {
        if (index < 0 || index >= this.questions.length) return;

        this.currentQuestionIndex = index;
        this.questionStartTime = Date.now();

        const question = this.questions[index];
        const container = document.getElementById('questionContent');

        // Update question number
        document.getElementById('questionNumber').textContent =
            `Question ${index + 1} of ${this.questions.length}`;

        // Update progress bar
        this.updateProgress();

        // Render question based on type
        container.innerHTML = this.renderQuestion(question);

        // Load saved response if exists
        if (this.responses[question.id]) {
            this.loadSavedResponse(question.id, this.responses[question.id]);
        }

        // Update navigation buttons
        this.updateNavigation();

        // Start time tracking
        this.startTimeTracking();
    }

    renderQuestion(question) {
        let html = '';

        switch (question.type) {
            case 'text':
                html = `
                    <div class="question-text">${question.text}</div>
                    <input type="text"
                           class="input-text"
                           id="response_${question.id}"
                           placeholder="Type your answer here..."
                           ${question.required ? 'required' : ''}>
                `;
                break;

            case 'textarea':
                html = `
                    <div class="question-text">${question.text}</div>
                    <textarea class="input-textarea"
                              id="response_${question.id}"
                              rows="5"
                              placeholder="Type your answer here..."
                              ${question.required ? 'required' : ''}></textarea>
                `;
                break;

            case 'radio':
                html = `
                    <div class="question-text">${question.text}</div>
                    <div class="radio-options">
                `;
                question.options.forEach((option, i) => {
                    html += `
                        <div class="radio-option" onclick="surveyHandler.selectRadio('${question.id}', ${i})">
                            <input type="radio"
                                   name="response_${question.id}"
                                   id="response_${question.id}_${i}"
                                   value="${option}"
                                   ${question.required ? 'required' : ''}>
                            <label for="response_${question.id}_${i}">${option}</label>
                        </div>
                    `;
                });
                html += '</div>';

                // Add follow-up if exists
                if (question.follow_up) {
                    html += `
                        <div class="follow-up-question" style="margin-top: 1.5rem;">
                            <div class="question-text">${question.follow_up}</div>
                            ${question.follow_up_type === 'textarea' ?
                                `<textarea class="input-textarea"
                                          id="follow_up_${question.id}"
                                          rows="3"
                                          placeholder="Please explain..."></textarea>` :
                                `<input type="text"
                                        class="input-text"
                                        id="follow_up_${question.id}"
                                        placeholder="Please explain...">`
                            }
                        </div>
                    `;
                }
                break;

            case 'scale':
                html = `
                    <div class="question-text">${question.text}</div>
                    <div class="scale-container">
                        <div class="scale-labels">
                            ${question.labels ? question.labels.map(label =>
                                `<span>${label}</span>`).join('') : ''}
                        </div>
                        <div class="scale-options">
                `;
                for (let i = question.min; i <= question.max; i++) {
                    html += `
                        <div class="scale-option"
                             onclick="surveyHandler.selectScale('${question.id}', ${i})"
                             id="scale_${question.id}_${i}">
                            ${i}
                        </div>
                    `;
                }
                html += `
                        </div>
                    </div>
                `;
                break;

            case 'rating_matrix':
                html = `
                    <div class="question-text">${question.text}</div>
                    <div class="matrix-container">
                        <table class="rating-matrix">
                            <thead>
                                <tr>
                                    <th></th>
                `;
                // Add column headers (rating values)
                const firstRow = Object.values(question.options)[0];
                firstRow.forEach(value => {
                    html += `<th>${value}</th>`;
                });
                html += `
                                </tr>
                            </thead>
                            <tbody>
                `;
                // Add rows
                Object.entries(question.options).forEach(([rowLabel, values]) => {
                    html += `<tr><th>${rowLabel}</th>`;
                    values.forEach(value => {
                        html += `
                            <td>
                                <input type="radio"
                                       name="matrix_${question.id}_${rowLabel}"
                                       value="${value}"
                                       onclick="surveyHandler.selectMatrix('${question.id}', '${rowLabel}', ${value})">
                            </td>
                        `;
                    });
                    html += '</tr>';
                });
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
                if (question.labels) {
                    html += `<div class="scale-labels" style="margin-top: 1rem;">`;
                    question.labels.forEach((label, i) => {
                        html += `<span>${i + 1}: ${label}</span> `;
                    });
                    html += `</div>`;
                }
                break;
        }

        return html;
    }

    selectRadio(questionId, optionIndex) {
        const radio = document.getElementById(`response_${questionId}_${optionIndex}`);
        if (radio) {
            radio.checked = true;
            // Update visual selection
            document.querySelectorAll(`.radio-option`).forEach(opt => {
                opt.classList.remove('selected');
            });
            radio.closest('.radio-option').classList.add('selected');
        }
    }

    selectScale(questionId, value) {
        // Clear previous selection
        document.querySelectorAll(`.scale-option`).forEach(opt => {
            opt.classList.remove('selected');
        });
        // Add selection
        const selected = document.getElementById(`scale_${questionId}_${value}`);
        if (selected) {
            selected.classList.add('selected');
            this.responses[questionId] = value;
        }
    }

    selectMatrix(questionId, rowLabel, value) {
        if (!this.responses[questionId]) {
            this.responses[questionId] = {};
        }
        this.responses[questionId][rowLabel] = value;
    }

    async nextQuestion() {
        // Save current response
        if (!await this.saveCurrentResponse()) {
            return;
        }

        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.showQuestion(this.currentQuestionIndex + 1);
        }
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.showQuestion(this.currentQuestionIndex - 1);
        }
    }

    async saveCurrentResponse() {
        const question = this.questions[this.currentQuestionIndex];
        let response = this.getQuestionResponse(question);

        // Validate required questions
        if (question.required && !response) {
            alert('Please answer this question before proceeding.');
            return false;
        }

        // Calculate time spent
        const timeSpent = Math.floor((Date.now() - this.questionStartTime) / 1000);

        // Save response
        this.responses[question.id] = response;

        // Submit to server
        try {
            await fetch('/survey/api/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    question_id: question.id,
                    response: response,
                    time_spent: timeSpent,
                    metadata: {
                        question_index: this.currentQuestionIndex,
                        total_questions: this.questions.length
                    }
                })
            });

            return true;
        } catch (error) {
            console.error('Failed to save response:', error);
            // Continue anyway - responses are saved locally
            return true;
        }
    }

    getQuestionResponse(question) {
        switch (question.type) {
            case 'text':
            case 'textarea':
                const input = document.getElementById(`response_${question.id}`);
                const response = input ? input.value.trim() : '';

                // Include follow-up if exists
                if (question.follow_up) {
                    const followUp = document.getElementById(`follow_up_${question.id}`);
                    if (followUp && followUp.value.trim()) {
                        return {
                            main: response,
                            follow_up: followUp.value.trim()
                        };
                    }
                }
                return response;

            case 'radio':
                const selected = document.querySelector(`input[name="response_${question.id}"]:checked`);
                const value = selected ? selected.value : '';

                // Include follow-up if exists
                if (question.follow_up) {
                    const followUp = document.getElementById(`follow_up_${question.id}`);
                    if (followUp && followUp.value.trim()) {
                        return {
                            main: value,
                            follow_up: followUp.value.trim()
                        };
                    }
                }
                return value;

            case 'scale':
                return this.responses[question.id] || '';

            case 'rating_matrix':
                return this.responses[question.id] || {};
        }
    }

    loadSavedResponse(questionId, response) {
        const question = this.questions.find(q => q.id === questionId);
        if (!question) return;

        switch (question.type) {
            case 'text':
            case 'textarea':
                const input = document.getElementById(`response_${questionId}`);
                if (input) {
                    if (typeof response === 'object' && response.main) {
                        input.value = response.main;
                        const followUp = document.getElementById(`follow_up_${questionId}`);
                        if (followUp && response.follow_up) {
                            followUp.value = response.follow_up;
                        }
                    } else {
                        input.value = response;
                    }
                }
                break;

            case 'radio':
                if (typeof response === 'object' && response.main) {
                    const radio = document.querySelector(`input[name="response_${questionId}"][value="${response.main}"]`);
                    if (radio) {
                        radio.checked = true;
                        radio.closest('.radio-option').classList.add('selected');
                    }
                    const followUp = document.getElementById(`follow_up_${questionId}`);
                    if (followUp && response.follow_up) {
                        followUp.value = response.follow_up;
                    }
                } else {
                    const radio = document.querySelector(`input[name="response_${questionId}"][value="${response}"]`);
                    if (radio) {
                        radio.checked = true;
                        radio.closest('.radio-option').classList.add('selected');
                    }
                }
                break;

            case 'scale':
                this.selectScale(questionId, response);
                break;

            case 'rating_matrix':
                if (typeof response === 'object') {
                    Object.entries(response).forEach(([rowLabel, value]) => {
                        const radio = document.querySelector(`input[name="matrix_${questionId}_${rowLabel}"][value="${value}"]`);
                        if (radio) radio.checked = true;
                    });
                }
                break;
        }
    }

    updateProgress() {
        const progress = ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
        document.documentElement.style.setProperty('--progress', `${progress}%`);
        document.getElementById('progressText').textContent =
            `${this.currentQuestionIndex + 1} / ${this.questions.length}`;
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

    startTimeTracking() {
        // Update time display every second
        if (this.timeInterval) clearInterval(this.timeInterval);

        this.timeInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.questionStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('timeSpent').textContent =
                `Time on question: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    async submitSurvey() {
        // Save current response
        if (!await this.saveCurrentResponse()) {
            return;
        }

        try {
            // Mark survey as complete
            await fetch(`/survey/api/complete/${this.sessionId}`, {
                method: 'POST'
            });

            // Show completion screen
            this.showCompletion();

        } catch (error) {
            this.showError('Failed to complete survey. Your responses have been saved.');
        }
    }

    showCompletion() {
        const totalTime = Math.floor((Date.now() - this.startTime) / 1000);
        const minutes = Math.floor(totalTime / 60);
        const seconds = totalTime % 60;

        const stats = `
            <p>Questions answered: ${Object.keys(this.responses).length} / ${this.questions.length}</p>
            <p>Time taken: ${minutes} minutes ${seconds} seconds</p>
            <p>Session ID: ${this.sessionId}</p>
        `;

        document.getElementById('completionStats').innerHTML = stats;
        this.showSection('completionScreen');

        // Clear draft
        this.clearDraft();
    }

    saveDraft() {
        if (!this.sessionId) return;

        const draft = {
            sessionId: this.sessionId,
            responses: this.responses,
            currentQuestionIndex: this.currentQuestionIndex,
            timestamp: Date.now()
        };

        localStorage.setItem(`survey_draft_${this.config.chatmrptSession}`, JSON.stringify(draft));
    }

    loadDraft() {
        const draftKey = `survey_draft_${this.config.chatmrptSession}`;
        const draft = localStorage.getItem(draftKey);

        if (draft) {
            try {
                const data = JSON.parse(draft);
                // Check if draft is less than 24 hours old
                if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
                    this.responses = data.responses || {};
                    // Optionally restore question index
                    // this.currentQuestionIndex = data.currentQuestionIndex || 0;
                }
            } catch (error) {
                console.error('Failed to load draft:', error);
            }
        }
    }

    clearDraft() {
        localStorage.removeItem(`survey_draft_${this.config.chatmrptSession}`);
    }

    async downloadResponses() {
        try {
            const response = await fetch(`/survey/api/export/${this.sessionId}`);
            const data = await response.json();

            // Create download
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `survey_responses_${this.sessionId}.json`;
            a.click();
            URL.revokeObjectURL(url);

        } catch (error) {
            alert('Failed to download responses');
        }
    }

    showSection(sectionId) {
        document.querySelectorAll('.survey-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.showSection('errorScreen');
    }
}

// Initialize handler
let surveyHandler;
document.addEventListener('DOMContentLoaded', () => {
    surveyHandler = new SurveyHandler();
});

// Global functions for HTML onclick handlers
function startSurvey() {
    surveyHandler.startSurvey();
}

function nextQuestion() {
    surveyHandler.nextQuestion();
}

function previousQuestion() {
    surveyHandler.previousQuestion();
}

function saveDraft() {
    surveyHandler.saveDraft();
    alert('Draft saved successfully!');
}

function submitSurvey() {
    if (confirm('Are you sure you want to submit your survey responses?')) {
        surveyHandler.submitSurvey();
    }
}

function downloadResponses() {
    surveyHandler.downloadResponses();
}

function showPrivacy() {
    alert('Your survey responses are confidential and will only be used to improve ChatMRPT. No personally identifiable information is collected.');
}