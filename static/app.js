/**
 * Football Statistics Agent & Chatbot — Client-side Application
 * Handles UI state, API calls, message rendering, and conversation management.
 */

// ─── State ────────────────────────────────────────────────────────────
const state = {
    currentMode: 'chatbot',              // 'chatbot' | 'agent'
    currentConversationId: null,
    conversations: [],
    suggestions: [],
    isLoading: false,
};

// ─── DOM References ───────────────────────────────────────────────────
const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const DOM = {
    sidebar:           () => $('#sidebar'),
    overlay:           () => $('#sidebar-overlay'),
    convList:          () => $('#conversation-list'),
    convListEmpty:     () => $('#conv-list-empty'),
    chatArea:          () => $('#chat-area'),
    emptyState:        () => $('#empty-state'),
    messagesContainer: () => $('#messages-container'),
    loadingIndicator:  () => $('#loading-indicator'),
    loadingText:       () => $('#loading-status-text'),
    messageInput:      () => $('#message-input'),
    btnSend:           () => $('#btn-send'),
    modelName:         () => $('#model-name'),
    providerLabel:     () => $('#provider-label'),
    suggestionsGrid:   () => $('#suggestions-grid'),
    inputSuggestions:  () => $('#input-suggestions'),
};


// ─── Init ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    await loadModelInfo();
    await loadSuggestions();
    await loadConversations();
    renderSuggestionsGrid();
});

// ─── Theme ────────────────────────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    const btn = $('#theme-toggle');
    if (saved === 'light') {
        document.documentElement.classList.add('light-mode');
        if (btn) btn.textContent = '🌙';
    } else {
        if (btn) btn.textContent = '☀️';
    }
}

function toggleTheme() {
    const root = document.documentElement;
    const isLight = root.classList.toggle('light-mode');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    const btn = $('#theme-toggle');
    if (btn) btn.textContent = isLight ? '🌙' : '☀️';
}

// ─── API Helpers ──────────────────────────────────────────────────────
async function api(url, options = {}) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: res.statusText }));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        return res.json();
    } catch (e) {
        showToast(e.message, 'error');
        throw e;
    }
}


// ─── Model Info ───────────────────────────────────────────────────────
async function loadModelInfo() {
    try {
        const data = await api('/api/model-info');
        DOM.modelName().textContent = data.model;
        DOM.providerLabel().textContent = `(${data.provider})`;
    } catch { /* fallback stays */ }
}


// ─── Suggestions ──────────────────────────────────────────────────────
async function loadSuggestions() {
    try {
        const data = await api('/api/suggestions');
        state.suggestions = data.suggestions || [];
    } catch { /* use empty */ }
}

function renderSuggestionsGrid() {
    const grid = DOM.suggestionsGrid();
    if (!grid) return;
    // Show 4 random suggestions
    const shuffled = [...state.suggestions].sort(() => 0.5 - Math.random());
    const pick = shuffled.slice(0, 4);
    grid.innerHTML = pick.map(q => `
        <button class="suggestion-card" onclick="useSuggestion('${escapeHtml(q)}')">
            <span class="sugg-icon">💡</span>
            ${escapeHtml(q)}
        </button>
    `).join('');
}

function renderInputSuggestions() {
    const container = DOM.inputSuggestions();
    if (!container) return;
    const shuffled = [...state.suggestions].sort(() => 0.5 - Math.random());
    const pick = shuffled.slice(0, 5);
    container.innerHTML = pick.map(q => `
        <button class="input-suggestion-chip" onmousedown="useSuggestion('${escapeHtml(q)}')">${escapeHtml(q.length > 40 ? q.slice(0, 40) + '...' : q)}</button>
    `).join('');
}

function showInputSuggestions() {
    const container = DOM.inputSuggestions();
    const input = DOM.messageInput();
    if (container && !input.value.trim()) {
        renderInputSuggestions();
        container.classList.add('show');
    }
}

function hideInputSuggestions() {
    setTimeout(() => {
        const container = DOM.inputSuggestions();
        if (container) container.classList.remove('show');
    }, 200);
}

function useSuggestion(text) {
    DOM.messageInput().value = text;
    DOM.messageInput().focus();
    hideInputSuggestions();
    autoResizeTextarea(DOM.messageInput());
}


// ─── Conversations ────────────────────────────────────────────────────
async function loadConversations() {
    try {
        const data = await api('/api/conversations');
        state.conversations = data.conversations || [];
        renderConversationList();
    } catch { /* keep old */ }
}

function renderConversationList() {
    const list = DOM.convList();
    const empty = DOM.convListEmpty();

    // Remove old items (keep the empty placeholder)
    list.querySelectorAll('.conv-item').forEach(el => el.remove());

    if (state.conversations.length === 0) {
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    state.conversations.forEach(conv => {
        const el = document.createElement('div');
        el.className = `conv-item ${conv.id === state.currentConversationId ? 'active' : ''}`;
        el.onclick = () => selectConversation(conv.id);
        el.innerHTML = `
            <div class="conv-icon ${conv.mode === 'agent' ? 'agent-icon' : 'chatbot-icon'}">
                ${conv.mode === 'agent' ? '🤖' : '💬'}
            </div>
            <div class="conv-info">
                <div class="conv-title">${escapeHtml(conv.title)}</div>
                <div class="conv-meta">${conv.mode === 'agent' ? 'Agent' : 'Chatbot'} · ${formatDate(conv.updated_at)}</div>
            </div>
            <button class="conv-delete" onclick="event.stopPropagation(); deleteConversation(${conv.id})" title="Delete">✕</button>
        `;
        list.appendChild(el);
    });
}

async function createNewConversation() {
    try {
        const data = await api('/api/conversations', {
            method: 'POST',
            body: JSON.stringify({ mode: state.currentMode }),
        });
        state.currentConversationId = data.conversation.id;
        await loadConversations();
        showChatView([]);
        DOM.messageInput().focus();
        closeSidebar();
    } catch { /* toast shown by api() */ }
}

async function selectConversation(convId) {
    state.currentConversationId = convId;
    renderConversationList();

    // Load messages
    try {
        const data = await api(`/api/conversations/${convId}/messages`);
        // Determine mode from conversation
        const conv = state.conversations.find(c => c.id === convId);
        if (conv) {
            switchModeUI(conv.mode);
        }
        showChatView(data.messages || []);
    } catch { /* fallback */ }

    closeSidebar();
}

async function deleteConversation(convId) {
    try {
        await api(`/api/conversations/${convId}`, { method: 'DELETE' });
        if (state.currentConversationId === convId) {
            state.currentConversationId = null;
            showEmptyState();
        }
        await loadConversations();
        showToast('Conversation deleted', 'success');
    } catch { /* toast shown */ }
}


// ─── Mode Switching ───────────────────────────────────────────────────
function switchMode(mode) {
    state.currentMode = mode;
    switchModeUI(mode);

    // If no active conversation, create one
    if (!state.currentConversationId) {
        // just update the UI, conversation created on first message
    }
}

function switchModeUI(mode) {
    state.currentMode = mode;
    $$('.mode-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });
}


// ─── Chat View ────────────────────────────────────────────────────────
function showEmptyState() {
    DOM.emptyState().classList.remove('hidden');
    DOM.messagesContainer().innerHTML = '';
    DOM.loadingIndicator().classList.add('hidden');
    renderSuggestionsGrid();
}

function showChatView(messages) {
    DOM.emptyState().classList.add('hidden');
    DOM.messagesContainer().innerHTML = '';
    messages.forEach(msg => appendMessage(msg));
    scrollToBottom();
}

function appendMessage(msg) {
    const container = DOM.messagesContainer();
    const div = document.createElement('div');
    div.className = `message ${msg.role}`;

    if (msg.role === 'user') {
        div.innerHTML = `
            <div class="bubble">${formatContent(msg.content)}</div>
            <div class="avatar">👤</div>
        `;
    } else {
        let traceHTML = '';
        if (msg.reasoning_trace && msg.reasoning_trace.length > 0) {
            const traceId = `trace-${msg.id || Date.now()}`;
            traceHTML = `
                <button class="reasoning-toggle" onclick="toggleReasoning('${traceId}', this)">
                    <span class="toggle-arrow">▶</span> Show Reasoning (${msg.reasoning_trace.length} steps)
                </button>
                <div class="reasoning-trace" id="${traceId}">
                    ${renderReasoningSteps(msg.reasoning_trace)}
                </div>
            `;
        }

        let metaHTML = '';
        if (msg.latency_ms || msg.token_usage) {
            const parts = [];
            if (msg.latency_ms) parts.push(`⏱ ${(msg.latency_ms / 1000).toFixed(1)}s`);
            if (msg.token_usage && msg.token_usage.total_tokens) parts.push(`📊 ${msg.token_usage.total_tokens} tokens`);
            metaHTML = `<div class="message-meta">${parts.join(' · ')}</div>`;
        }

        div.innerHTML = `
            <div class="avatar">🤖</div>
            <div>
                <div class="bubble">${formatContent(msg.content)}</div>
                ${traceHTML}
                ${metaHTML}
            </div>
        `;
    }

    container.appendChild(div);
}

function renderReasoningSteps(steps) {
    return steps.map((step, i) => {
        if (step.type === 'step') {
            return `
                <div class="reasoning-step">
                    ${step.thought ? `<div class="step-label thought">💭 Thought</div><div class="step-content">${escapeHtml(step.thought)}</div>` : ''}
                    <div class="step-label action">⚡ Action: ${escapeHtml(step.tool)}(${escapeHtml(step.args)})</div>
                    <div class="step-label observation">👁 Observation</div>
                    <div class="step-content">${escapeHtml(step.observation || '')}</div>
                </div>
            `;
        } else if (step.type === 'thought') {
            return `
                <div class="reasoning-step">
                    <div class="step-label thought">💭 Thought</div>
                    <div class="step-content">${escapeHtml(step.content)}</div>
                </div>
            `;
        } else if (step.type === 'error') {
            return `
                <div class="reasoning-step">
                    <div class="step-label error">⚠ Error</div>
                    <div class="step-content">${escapeHtml(step.content)}</div>
                </div>
            `;
        }
        return '';
    }).join('');
}

function toggleReasoning(traceId, btn) {
    const trace = document.getElementById(traceId);
    if (!trace) return;
    trace.classList.toggle('show');
    btn.classList.toggle('open');
    const arrow = btn.querySelector('.toggle-arrow');
    const isOpen = trace.classList.contains('show');
    btn.innerHTML = `<span class="toggle-arrow">${isOpen ? '▼' : '▶'}</span> ${isOpen ? 'Hide' : 'Show'} Reasoning`;
}


// ─── Sending Messages ─────────────────────────────────────────────────
async function sendMessage() {
    const input = DOM.messageInput();
    const message = input.value.trim();
    if (!message || state.isLoading) return;

    // Create conversation if needed
    if (!state.currentConversationId) {
        try {
            const data = await api('/api/conversations', {
                method: 'POST',
                body: JSON.stringify({ mode: state.currentMode, title: message.slice(0, 50) }),
            });
            state.currentConversationId = data.conversation.id;
            await loadConversations();
            DOM.emptyState().classList.add('hidden');
        } catch { return; }
    }

    // Show user message immediately
    appendMessage({ role: 'user', content: message });
    input.value = '';
    autoResizeTextarea(input);
    scrollToBottom();

    // Show loading
    setLoading(true);

    try {
        const data = await api('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                conversation_id: state.currentConversationId,
                message: message,
                mode: state.currentMode,
            }),
        });

        // Append assistant response
        appendMessage({
            role: 'assistant',
            content: data.reply,
            reasoning_trace: data.reasoning_trace,
            latency_ms: data.latency_ms,
            token_usage: data.usage,
            id: Date.now(),
        });

        // Refresh conversation list (title may have updated)
        await loadConversations();
    } catch (e) {
        appendMessage({
            role: 'assistant',
            content: 'Sorry, there was an error processing your request. Please try again.',
        });
    } finally {
        setLoading(false);
        scrollToBottom();
    }
}

function setLoading(loading) {
    state.isLoading = loading;
    const indicator = DOM.loadingIndicator();
    const btn = DOM.btnSend();
    const text = DOM.loadingText();

    if (loading) {
        indicator.classList.remove('hidden');
        btn.disabled = true;
        text.textContent = state.currentMode === 'agent'
            ? 'Agent is reasoning through tools...'
            : 'Chatbot is thinking...';
        scrollToBottom();
    } else {
        indicator.classList.add('hidden');
        btn.disabled = false;
    }
}

async function clearConversation() {
    if (!state.currentConversationId) return;

    if (confirm('Clear this conversation? This will delete all messages.')) {
        await deleteConversation(state.currentConversationId);
    }
}


// ─── Input Handling ───────────────────────────────────────────────────
function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}


// ─── Sidebar ──────────────────────────────────────────────────────────
function toggleSidebar() {
    const sidebar = DOM.sidebar();
    const overlay = DOM.overlay();
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

function closeSidebar() {
    DOM.sidebar().classList.remove('open');
    DOM.overlay().classList.remove('show');
}


// ─── Helpers ──────────────────────────────────────────────────────────
function scrollToBottom() {
    const area = DOM.chatArea();
    requestAnimationFrame(() => {
        area.scrollTop = area.scrollHeight;
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatContent(text) {
    if (!text) return '';
    // Convert markdown-like formatting to HTML
    let html = escapeHtml(text);

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    html = html.replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

    // Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Unordered lists: - item
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');

    return html;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr + 'Z');
        const now = new Date();
        const diff = now - d;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return dateStr;
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
