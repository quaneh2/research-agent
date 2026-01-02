/**
 * Research Assistant Frontend
 * Handles SSE streaming and UI updates
 */

// Elements
const questionInput = document.getElementById('question');
const researchBtn = document.getElementById('research-btn');
const loadingDiv = document.getElementById('loading');
const thinkingSection = document.getElementById('thinking-section');
const thinkingLog = document.getElementById('thinking-log');
const answerSection = document.getElementById('answer-section');
const answerText = document.getElementById('answer-text');
const sourcesDiv = document.getElementById('sources');
const stepCountSpan = document.getElementById('step-count');

// Example question buttons
const exampleBtns = document.querySelectorAll('.example-btn');
exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.dataset.question;
        questionInput.value = question;
        startResearch();
    });
});

// Research button click
researchBtn.addEventListener('click', startResearch);

// Enter key in textarea
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        startResearch();
    }
});

/**
 * Start the research process
 */
function startResearch() {
    const question = questionInput.value.trim();

    if (!question) {
        alert('Please enter a research question');
        return;
    }

    // Reset UI
    showLoading();
    clearPreviousResults();
    showThinkingSection();

    // Start SSE connection
    startResearchWithSSE(question);
}

/**
 * Start research with proper SSE handling
 */
async function startResearchWithSSE(question) {
    try {
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            throw new Error('Request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const messages = buffer.split('\n\n');
            buffer = messages.pop(); // Keep incomplete message in buffer

            for (const message of messages) {
                if (message.trim()) {
                    processSSEMessage(message);
                }
            }
        }

    } catch (error) {
        console.error('Research error:', error);
        displayError('Failed to complete research. Please try again.');
        hideLoading();
    }
}

/**
 * Process a Server-Sent Event message
 */
function processSSEMessage(message) {
    const lines = message.split('\n');
    let eventType = 'message';
    let eventData = '';

    for (const line of lines) {
        if (line.startsWith('event: ')) {
            eventType = line.substring(7);
        } else if (line.startsWith('data: ')) {
            eventData = line.substring(6);
        }
    }

    if (!eventData) return;

    try {
        const data = JSON.parse(eventData);
        handleAgentEvent(eventType, data);
    } catch (e) {
        console.error('Failed to parse SSE data:', e);
    }
}

/**
 * Handle different types of agent events
 */
function handleAgentEvent(type, data) {
    switch (type) {
        case 'thinking':
            addThinkingStep('thinking', data.content);
            break;

        case 'tool_use':
            const toolLabel = `${data.tool}: ${JSON.stringify(data.input)}`;
            addThinkingStep('tool_use', toolLabel);
            break;

        case 'tool_result':
            addThinkingStep('tool_result', data.summary);
            break;

        case 'complete':
            hideLoading();
            displayFinalAnswer(data);
            break;

        case 'error':
            hideLoading();
            displayError(data.error || 'An error occurred');
            break;
    }
}

/**
 * Add a step to the thinking log
 */
function addThinkingStep(type, content) {
    const stepDiv = document.createElement('div');
    stepDiv.className = `thinking-step step-${type}`;

    let icon = '';
    switch (type) {
        case 'thinking':
            icon = '💭';
            break;
        case 'tool_use':
            icon = '🔧';
            break;
        case 'tool_result':
            icon = '✅';
            break;
    }

    stepDiv.innerHTML = `
        <span class="step-icon">${icon}</span>
        <span class="step-content">${escapeHtml(content)}</span>
    `;

    thinkingLog.appendChild(stepDiv);

    // Auto-scroll to bottom
    thinkingLog.scrollTop = thinkingLog.scrollHeight;
}

/**
 * Display the final answer
 */
function displayFinalAnswer(result) {
    // Show answer
    answerText.textContent = result.answer;

    // Show sources
    if (result.sources && result.sources.length > 0) {
        sourcesDiv.innerHTML = result.sources.map(source => `
            <div class="source-item">
                <a href="${source.url}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(source.url)}
                </a>
            </div>
        `).join('');
    } else {
        sourcesDiv.innerHTML = '<p>No sources available</p>';
    }

    // Show stats
    stepCountSpan.textContent = result.iterations || 0;

    // Show answer section
    answerSection.classList.remove('hidden');
}

/**
 * Display an error message
 */
function displayError(message) {
    answerText.innerHTML = `<p class="error">Error: ${escapeHtml(message)}</p>`;
    answerSection.classList.remove('hidden');
}

/**
 * UI Helper Functions
 */
function showLoading() {
    loadingDiv.classList.remove('hidden');
    researchBtn.disabled = true;
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
    researchBtn.disabled = false;
}

function showThinkingSection() {
    thinkingSection.classList.remove('hidden');
}

function clearPreviousResults() {
    thinkingLog.innerHTML = '';
    answerText.textContent = '';
    sourcesDiv.innerHTML = '';
    stepCountSpan.textContent = '0';
    answerSection.classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
