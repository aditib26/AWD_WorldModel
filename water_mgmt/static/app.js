// Rice Assistant — 3-Screen Architecture
const API_BASE = '';

// ─── State ───────────────────────────────────────────────
let currentFarmId = null;
let currentTheme  = 'light';
let authMode      = 'login';
let authToken     = localStorage.getItem('rice_auth_token') || null;
let authUserEmail = localStorage.getItem('rice_auth_email') || null;
let conversationHistory = [];
let latestAdvice  = null;

// ─── DOM shorthand ───────────────────────────────────────
const $ = id => document.getElementById(id);

// Screens
const authScreen = $('authScreen');
const dashScreen = $('dashScreen');
const appScreen  = $('appScreen');

// Auth screen
const tabLogin      = $('tabLogin');
const tabSignup     = $('tabSignup');
const authForm      = $('authForm');
const authEmail     = $('authEmail');
const authPassword  = $('authPassword');
const authError     = $('authError');
const authSubmitBtn = $('authSubmitBtn');

// Dashboard screen
const dashUserEmail  = $('dashUserEmail');
const dashLogoutBtn  = $('dashLogoutBtn');
const dashFarmGrid   = $('dashFarmGrid');
const dashNewFarmBtn = $('dashNewFarmBtn');

// App screen
const sidebar        = $('sidebar');
const sidebarToggle  = $('sidebarToggle');
const newFarmBtn     = $('newFarmBtn');
const themeToggle    = $('themeToggle');
const backToDashBtn  = $('backToDashBtn');
const logoutBtn      = $('logoutBtn');
const statusFarmName = $('statusFarmName');
const statusRegime   = $('statusRegime');
const statusDas      = $('statusDas');
const chatMessages   = $('chatMessages');
const chatInput      = $('chatInput');
const sendBtn        = $('sendBtn');
const profileModal   = $('profileModal');
const profileForm    = $('profileForm');
const closeProfileModal = $('closeProfileModal');
const cancelProfile  = $('cancelProfile');
const checkinModal   = $('checkinModal');
const checkinForm    = $('checkinForm');
const dailyCheckinBtn = $('dailyCheckinBtn');
const closeCheckinModal = $('closeCheckinModal');
const cancelCheckin  = $('cancelCheckin');
const worldModelModal = $('worldModelModal');
const worldModelBtn  = $('worldModelBtn');
const closeWorldModelModal = $('closeWorldModelModal');
const loadingOverlay = $('loadingOverlay');

// ─── Utility ─────────────────────────────────────────────
function showLoading() { if (loadingOverlay) loadingOverlay.style.display = 'flex'; }
function hideLoading() { if (loadingOverlay) loadingOverlay.style.display = 'none'; }

async function apiCall(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const headers = { ...options.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    if (options.body) headers['Content-Type'] = 'application/json';
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
        let detail = 'Request failed';
        try { const err = await res.json(); detail = err.detail || detail; } catch(e) {}
        throw new Error(detail);
    }
    return res.json();
}

// ─── Screen Navigation ──────────────────────────────────
function showScreen(name) {
    authScreen.style.display = name === 'auth' ? 'flex' : 'none';
    dashScreen.style.display = name === 'dash' ? 'flex' : 'none';
    appScreen.style.display  = name === 'app'  ? 'flex' : 'none';
}

// ─── Auth State ──────────────────────────────────────────
function setAuth(token, email) {
    authToken = token;
    authUserEmail = email;
    token ? localStorage.setItem('rice_auth_token', token) : localStorage.removeItem('rice_auth_token');
    email ? localStorage.setItem('rice_auth_email', email) : localStorage.removeItem('rice_auth_email');
}

function logout() {
    setAuth(null, null);
    currentFarmId = null;
    conversationHistory = [];
    showScreen('auth');
}

// ─── Auth Screen ─────────────────────────────────────────
tabLogin?.addEventListener('click', () => {
    authMode = 'login';
    tabLogin.classList.add('active');
    tabSignup.classList.remove('active');
    authSubmitBtn.textContent = 'Log in';
});

tabSignup?.addEventListener('click', () => {
    authMode = 'register';
    tabSignup.classList.add('active');
    tabLogin.classList.remove('active');
    authSubmitBtn.textContent = 'Sign up';
});

authForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (authError) { authError.style.display = 'none'; authError.textContent = ''; }

    const email = (authEmail?.value || '').trim();
    const password = authPassword?.value || '';
    if (!email || !email.includes('@')) { showAuthErr('Enter a valid email.'); return; }
    if (password.length < 8) { showAuthErr('Password must be at least 8 characters.'); return; }

    showLoading();
    try {
        const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
        const res = await apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        setAuth(res.token, res.user?.email || email);
        authForm.reset();
        showDashboard();
    } catch (err) {
        showAuthErr(err.message || 'Authentication failed.');
    } finally {
        hideLoading();
    }
});

function showAuthErr(msg) {
    if (!authError) return;
    authError.textContent = msg;
    authError.style.display = 'block';
}

// ─── Dashboard Screen ────────────────────────────────────
function showDashboard() {
    if (dashUserEmail) dashUserEmail.textContent = authUserEmail || '';
    showScreen('dash');
    loadFarmList();
}

async function loadFarmList() {
    if (!dashFarmGrid) return;
    dashFarmGrid.innerHTML = '<p style="color:var(--text-secondary);font-size:14px;">Loading farms...</p>';

    let farms = [];
    try {
        const res = await apiCall('/farms');
        farms = res.farms || [];
    } catch (e) {
        // Fallback to localStorage if server unavailable
        farms = JSON.parse(localStorage.getItem('rice_farms_' + authUserEmail) || '[]');
    }

    // Sync to localStorage as cache
    if (farms.length > 0) {
        localStorage.setItem('rice_farms_' + authUserEmail, JSON.stringify(farms));
    }

    dashFarmGrid.innerHTML = '';
    if (farms.length === 0) {
        dashFarmGrid.innerHTML = '<p style="color:var(--text-secondary);font-size:14px;">No farms yet. Create your first farm below.</p>';
    } else {
        farms.forEach(farmId => {
            const card = document.createElement('button');
            card.className = 'dash-farm-card';
            card.innerHTML = `<span class="dash-farm-icon">🌾</span><span class="dash-farm-name">${farmId}</span>`;
            card.addEventListener('click', () => openFarm(farmId));
            dashFarmGrid.appendChild(card);
        });
    }
}

function saveFarmLocally(farmId) {
    const key = 'rice_farms_' + authUserEmail;
    const farms = JSON.parse(localStorage.getItem(key) || '[]');
    if (!farms.includes(farmId)) {
        farms.push(farmId);
        localStorage.setItem(key, JSON.stringify(farms));
    }
}

dashLogoutBtn?.addEventListener('click', logout);
dashNewFarmBtn?.addEventListener('click', () => {
    showScreen('app');
    profileModal.style.display = 'flex';
});

// ─── App Screen ──────────────────────────────────────────

// Sidebar buttons
backToDashBtn?.addEventListener('click', () => showDashboard());
logoutBtn?.addEventListener('click', logout);
newFarmBtn?.addEventListener('click', () => { profileModal.style.display = 'flex'; });
themeToggle?.addEventListener('click', () => {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
});
sidebarToggle?.addEventListener('click', () => sidebar?.classList.toggle('open'));

// Profile (Create Farm) Modal
closeProfileModal?.addEventListener('click', () => { profileModal.style.display = 'none'; });
cancelProfile?.addEventListener('click', () => {
    profileModal.style.display = 'none';
    // If no farm selected yet, go back to dashboard
    if (!currentFarmId) showDashboard();
});

profileForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const farmIdVal = $('farmIdCreate')?.value;
    if (!farmIdVal) { alert('Please enter a Farm ID.'); return; }

    showLoading();
    try {
        await apiCall('/profile', {
            method: 'POST',
            body: JSON.stringify({
                farmer_id: $('farmerId')?.value,
                farm_id: farmIdVal,
                province: $('province')?.value,
                soil_type: $('soilType')?.value,
                irrigation_access: $('irrigationAccess')?.checked,
                awd_tube_available: $('awdTube')?.checked,
                sowing_date: $('sowingDate')?.value || null
            })
        });
        profileModal.style.display = 'none';
        saveFarmLocally(farmIdVal);
        await openFarm(farmIdVal);
    } catch (error) {
        alert(`Failed to create farm: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Open a farm → show chat
async function openFarm(farmId) {
    showScreen('app');
    showLoading();
    try {
        await apiCall(`/profile/${farmId}`);
        let state = null;
        try { state = await apiCall(`/state/${farmId}`); } catch(e) {}

        currentFarmId = farmId;
        conversationHistory = [];

        // Clear previous chat messages and show fresh welcome
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="assistant-avatar"><span>🌾</span></div>
                <div class="message-content">
                    <div class="message-header">Rice Assistant</div>
                    <p>Hello! I'm your intelligent irrigation advisor for <strong>${farmId}</strong>. Tell me about your field conditions or ask me anything about water management.</p>
                    <div class="suggested-prompts">
                        <button class="prompt-suggestion">Water table is 16 cm below surface</button>
                        <button class="prompt-suggestion">I see small cracks in my field</button>
                        <button class="prompt-suggestion">Should I irrigate today?</button>
                    </div>
                </div>
            </div>`;
        // Re-bind prompt suggestion clicks
        chatMessages.querySelectorAll('.prompt-suggestion').forEach(btn => {
            btn.addEventListener('click', () => {
                chatInput.value = btn.textContent;
                chatInput.focus();
                updateSendButton();
            });
        });

        statusFarmName.textContent = farmId;
        statusRegime.textContent = state?.regime || 'AUTO';
        statusDas.textContent = state?.das ? `${state.das} DAS` : 'New';

        saveFarmLocally(farmId);
        addFarmToSidebar(farmId);
        hideLoading();
    } catch (error) {
        hideLoading();
        alert(`Failed to load farm: ${error.message}`);
        showDashboard();
    }
}

function addFarmToSidebar(farmId) {
    const farmList = document.getElementById('farmList');
    
    // Remove existing
    const existing = farmList.querySelector(`[data-farm="${farmId}"]`);
    if (existing) {
        existing.remove();
    }
    
    const farmItem = document.createElement('div');
    farmItem.className = 'farm-item active';
    farmItem.dataset.farm = farmId;
    farmItem.textContent = farmId;
    farmItem.addEventListener('click', () => openFarm(farmId));
    
    // Remove active from others
    farmList.querySelectorAll('.farm-item').forEach(item => {
        item.classList.remove('active');
    });
    
    farmList.prepend(farmItem);
}

// Chat Input
chatInput.addEventListener('input', updateSendButton);

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

function updateSendButton() {
    const hasText = chatInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
    
    // Auto-resize
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || !currentFarmId) return;
    
    // Add user message to UI
    addMessage(message, 'user');
    chatInput.value = '';
    updateSendButton();
    
    // Add to conversation history
    conversationHistory.push({ role: 'user', content: message });
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
        // Single unified endpoint - world model handles everything
        const response = await apiCall('/chat', {
            method: 'POST',
            body: JSON.stringify({
                farm_id: currentFarmId,
                message: message,
                conversation_history: conversationHistory.slice(-10)
            })
        });
        
        removeTypingIndicator(typingId);
        
        // Always display the conversational response
        addMessage(response.response, 'assistant');
        
        // Add to history
        conversationHistory.push({ role: 'assistant', content: response.response });
        
        // If state changed, show a subtle state update indicator
        if (response.state_changed && response.state_updates) {
            showStateUpdate(response.state_updates);
        }
        
        // If planner generated new advice, show compact advice card
        if (response.advice) {
            displayCompactAdvice(response.advice);
            latestAdvice = response.advice;
        }
        
        // Update status bar from returned state
        if (response.state) {
            statusRegime.textContent = response.state.regime || 'AUTO';
            statusDas.textContent = response.state.das ? `${response.state.das} DAS` : 'New';
        }
        
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant');
    }
}

function showStateUpdate(updates) {
    if (!updates || Object.keys(updates).length === 0) return;
    const stateDiv = document.createElement('div');
    stateDiv.className = 'state-update-bar';
    
    const labels = {
        water_table_depth_cm: ['💧', 'Water table', 'cm'],
        ponded_water_cm: ['🌊', 'Ponded', 'cm'],
        soil_cracks: ['🔍', 'Cracks', ''],
        das: ['📅', 'DAS', ''],
        growth_stage: ['🌱', 'Stage', ''],
    };
    
    const chips = Object.entries(updates).map(([key, val]) => {
        const [icon, label, unit] = labels[key] || ['📊', key, ''];
        return `<span class="su-chip">${icon} ${label}: ${val}${unit ? ' ' + unit : ''}</span>`;
    });
    
    stateDiv.innerHTML = `<span class="su-label">✅ Updated</span><span class="su-chips">${chips.join('')}</span>`;
    chatMessages.appendChild(stateDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function displayCompactAdvice(advice) {
    const adviceDiv = document.createElement('div');
    adviceDiv.className = 'message-assistant';
    
    const avatar = document.createElement('div');
    avatar.className = 'assistant-avatar';
    avatar.innerHTML = '<span>🌾</span>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const box = document.createElement('div');
    box.className = 'advice-box';
    
    const actionClass = advice.recommended_action === 'IRRIGATE' ? 'action-irrigate' : 
                        advice.recommended_action === 'HOLD' ? 'action-hold' : 'action-drain';
    
    box.innerHTML = `
        <div class="advice-header">
            <div class="advice-action ${actionClass}">${advice.recommended_action}</div>
            <div class="advice-confidence confidence-${advice.confidence}">${advice.confidence.toUpperCase()}</div>
        </div>
        ${advice.target_description ? `<div class="advice-target">${advice.target_description}</div>` : ''}
        ${(advice.rationale && advice.rationale.length) ? `<div class="advice-rationale-list">
            <div class="advice-rationale-title">Handbook rationale</div>
            ${advice.rationale.map(r => `<div class="rationale-item"><span class="rationale-text">${r.text}</span><span class="source-tag source-${r.source_type.toLowerCase()}">${r.source_type}</span></div>`).join('')}
        </div>` : ''}
    `;
    
    content.appendChild(box);
    adviceDiv.appendChild(avatar);
    adviceDiv.appendChild(content);
    
    chatMessages.appendChild(adviceDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingId = `typing-${Date.now()}`;
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'message-assistant typing-indicator-msg';
    
    const avatar = document.createElement('div');
    avatar.className = 'assistant-avatar';
    avatar.innerHTML = '<span>🌾</span>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    
    content.appendChild(typingIndicator);
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(content);
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingElement = document.getElementById(typingId);
    if (typingElement) {
        typingElement.remove();
    }
}

function simpleMarkdown(text) {
    // Convert **bold** to <strong>
    let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert *italic* to <em>
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Convert \n to <br>
    html = html.replace(/\n/g, '<br>');
    // Convert • to list-like items
    html = html.replace(/•\s?(.*?)(<br>|$)/g, '<span style="display:block;padding-left:12px;">• $1</span>');
    // Convert ✓ items
    html = html.replace(/✓\s?(.*?)(<br>|$)/g, '<span style="display:block;padding-left:12px;color:var(--success-color);">✓ $1</span>');
    return html;
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'message-user' : 'message-assistant';
    
    const avatar = document.createElement('div');
    avatar.className = sender === 'user' ? 'user-avatar' : 'assistant-avatar';
    avatar.innerHTML = sender === 'user' ? '<span>👤</span>' : '<span>🌾</span>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    if (sender === 'assistant') {
        const header = document.createElement('div');
        header.className = 'message-header';
        header.textContent = 'Rice Assistant';
        content.appendChild(header);
    }
    
    const p = document.createElement('div');
    p.style.lineHeight = '1.6';
    if (sender === 'assistant') {
        p.innerHTML = simpleMarkdown(text);
    } else {
        p.textContent = text;
    }
    content.appendChild(p);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function displayAdviceInChat(advice) {
    // Store for World Model display
    latestAdvice = advice;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-assistant';
    
    const avatar = document.createElement('div');
    avatar.className = 'assistant-avatar';
    avatar.innerHTML = '<span>🌾</span>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = 'Rice Assistant';
    content.appendChild(header);
    
    const adviceBox = document.createElement('div');
    adviceBox.className = 'advice-box';
    
    const action = document.createElement('div');
    action.className = 'advice-action';
    action.textContent = advice.recommended_action;
    adviceBox.appendChild(action);
    
    if (advice.target_description) {
        const target = document.createElement('div');
        target.className = 'advice-target';
        target.textContent = advice.target_description;
        adviceBox.appendChild(target);
    }
    
    const confidence = document.createElement('div');
    confidence.className = `advice-confidence confidence-${advice.confidence}`;
    confidence.textContent = `${advice.confidence.toUpperCase()} CONFIDENCE`;
    adviceBox.appendChild(confidence);
    
    const rationaleTitle = document.createElement('div');
    rationaleTitle.textContent = 'Why this recommendation:';
    rationaleTitle.style.fontWeight = '600';
    rationaleTitle.style.marginTop = '16px';
    rationaleTitle.style.marginBottom = '8px';
    adviceBox.appendChild(rationaleTitle);
    
    advice.rationale.forEach(item => {
        const rationaleItem = document.createElement('div');
        rationaleItem.className = 'rationale-item';
        rationaleItem.innerHTML = `
            ${item.text}
            <span class="source-tag source-${item.source_type.toLowerCase()}">[${item.source_type}]</span>
        `;
        adviceBox.appendChild(rationaleItem);
    });
    
    if (advice.risk_warnings && advice.risk_warnings.length > 0) {
        const warningTitle = document.createElement('div');
        warningTitle.textContent = '⚠️ Important Warnings:';
        warningTitle.style.fontWeight = '600';
        warningTitle.style.marginTop = '16px';
        warningTitle.style.marginBottom = '8px';
        adviceBox.appendChild(warningTitle);
        
        advice.risk_warnings.forEach(warning => {
            const warningItem = document.createElement('div');
            warningItem.className = 'rationale-item';
            warningItem.textContent = warning;
            adviceBox.appendChild(warningItem);
        });
    }
    
    content.appendChild(adviceBox);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Suggested Prompts
document.querySelectorAll('.prompt-suggestion').forEach(btn => {
    btn.addEventListener('click', () => {
        chatInput.value = btn.textContent;
        chatInput.focus();
        updateSendButton();
    });
});

// World Model
worldModelBtn.addEventListener('click', async () => {
    await loadWorldModel();
    worldModelModal.style.display = 'flex';
});

closeWorldModelModal.addEventListener('click', () => {
    worldModelModal.style.display = 'none';
});

// Certificate modal
document.getElementById('closeCertModal').addEventListener('click', () => {
    document.getElementById('certModal').style.display = 'none';
});

async function loadWorldModel() {
    if (!currentFarmId) return;
    
    showLoading();
    try {
        console.log('[WM] Fetching world model for', currentFarmId);
        const wm = await apiCall(`/worldmodel/${currentFarmId}`);
        
        const state = wm.state || {};
        const rules = wm.awd_rules || {};
        const prov = state.field_provenance || {};
        
        function reported(field, val, fallback = 'Not reported') {
            return prov[field] ? val : fallback;
        }
        
        // Update state cards
        const wmDas = document.getElementById('wmDas');
        const wmStage = document.getElementById('wmStage');
        const wmPonded = document.getElementById('wmPonded');
        const wmWaterTable = document.getElementById('wmWaterTable');
        const wmSoilMoisture = document.getElementById('wmSoilMoisture');
        const wmRegime = document.getElementById('wmRegime');
        
        if (wmDas) wmDas.textContent = state.das != null ? state.das : '-';
        if (wmStage) wmStage.textContent = formatGrowthStage(state.growth_stage);
        if (wmPonded) wmPonded.textContent = reported('ponded_water_cm',
            state.ponded_water_cm != null ? `${Number(state.ponded_water_cm).toFixed(1)} cm` : '- cm', '- cm');
        if (wmWaterTable) wmWaterTable.textContent = reported('water_table_depth_cm',
            state.water_table_depth_cm != null ? `${Number(state.water_table_depth_cm).toFixed(1)} cm below` : 'Not measured', 'Not measured');
        if (wmSoilMoisture) wmSoilMoisture.textContent = reported('soil_cracks',
            (state.soil_cracks && state.soil_cracks !== 'unknown') ? state.soil_cracks : 'Not reported');
        if (wmRegime) wmRegime.textContent = state.regime || 'AUTO';
        
        // Handbook params
        const paramET = document.getElementById('paramET');
        const paramPerc = document.getElementById('paramPerc');
        const paramFC = document.getElementById('paramFC');
        const paramKsat = document.getElementById('paramKsat');
        if (paramET) paramET.textContent = `${rules.trigger_depth_cm || 15} cm`;
        if (paramPerc) paramPerc.textContent = `${rules.refill_min_cm || 3}-${rules.refill_max_cm || 5} cm`;
        if (paramFC) paramFC.textContent = state.soil_type || 'unknown';
        if (paramKsat) paramKsat.textContent = state.regime || 'AUTO';
        
        // Weather
        const wx = wm.weather || {};
        const wmTemp = document.getElementById('wmTemp');
        const wmRain24 = document.getElementById('wmRain24');
        const wmRain3d = document.getElementById('wmRain3d');
        const wmET0 = document.getElementById('wmET0');
        if (wmTemp) wmTemp.textContent = wx.temperature_c != null ? `${wx.temperature_c}°C` : '-';
        if (wmRain24) wmRain24.textContent = wx.rain_last_24h_mm != null ? `${wx.rain_last_24h_mm} mm` : '-';
        if (wmRain3d) {
            const r3 = wx.rain_next_3d_mm || 0;
            wmRain3d.textContent = `${r3} mm`;
            if (r3 >= 20) wmRain3d.style.color = '#2563eb';
        }
        if (wmET0) wmET0.textContent = wx.et0_mm_day != null ? `${wx.et0_mm_day} mm/day` : '-';
        
        const forecastBar = document.getElementById('wmForecastBar');
        if (forecastBar && wx.daily_forecast && wx.daily_forecast.length > 0) {
            forecastBar.innerHTML = `<div style="display:flex;gap:6px;justify-content:space-between;">
                ${wx.daily_forecast.map(d => `<div style="flex:1;text-align:center;padding:6px 4px;background:var(--bg-tertiary);border-radius:6px;font-size:0.8em;">
                    <div style="opacity:0.7;">Day ${d.day}</div><div style="font-weight:600;">${d.rain_mm > 0 ? '🌧️' : '☀️'}</div>
                    <div>${d.rain_mm}mm</div><div style="opacity:0.7;">${d.temp_c || '-'}°</div></div>`).join('')}
            </div>`;
        }
        
        // Provenance tags
        const provDiv = document.getElementById('wmProvenance');
        if (provDiv && prov) {
            const sources = new Set();
            Object.values(prov).forEach(p => { if (p && p.source) sources.add(p.source); });
            const sourceLabels = {
                'profile': ['FARMER PROFILE', 'profile'],
                'chat': ['CHAT CONVERSATION', 'observation'],
                'checkin': ['DAILY CHECK-IN', 'observation'],
                'derived': ['AUTO-CALCULATED', 'derived'],
            };
            let tags = '<span class="prov-tag handbook">AWD HANDBOOK</span>';
            sources.forEach(s => {
                const [label, cls] = sourceLabels[s] || [s.toUpperCase(), 'observation'];
                tags += `<span class="prov-tag ${cls}">${label}</span>`;
            });
            if (wx.temperature_c != null) tags += '<span class="prov-tag weather">LIVE WEATHER</span>';
            provDiv.innerHTML = tags;
        }
        
        // AWD assessment
        displayHandbookAssessment(wm.awd_assessment, rules, state.das);
        
        // AWD Progress (fetch separately)
        await loadAWDProgress(currentFarmId);
        
        // Observation timeline
        await loadObservationTimeline(currentFarmId);
        
        console.log('[WM] World model loaded successfully');
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Failed to load world model:', error.message, error.stack);
    }
}

// ─── AWD Progress ────────────────────────────────────────

async function loadAWDProgress(farmId) {
    try {
        const data = await apiCall(`/awd-progress/${farmId}`);
        const prog = data.progress || {};
        const schedule = data.schedule || [];
        const criteria = data.criteria || [];
        const regime = (data.regime || 'AUTO').toUpperCase();
        const isAWD = regime === 'AWD';
        
        // Update modal title and explainer based on regime
        const modalTitle = document.getElementById('wmModalTitle');
        const explainer = document.getElementById('wmExplainerText');
        if (modalTitle) {
            modalTitle.textContent = isAWD
                ? '🌾 AWD World Model — 3 Wet-Dry Cycles'
                : `🌾 Rice Season World Model — ${regime}`;
        }
        if (explainer) {
            explainer.innerHTML = isAWD
                ? '<strong>Alternate Wetting & Drying (AWD)</strong><p>Your field goes through 10 phases with 3 wet-dry cycles. Complete all cycles to earn your AWD Certificate — reducing water use and emissions while maintaining yield.</p>'
                : `<strong>${regime} Water Management</strong><p>Track your rice season through ${schedule.length} growth phases. Your current phase and progress are shown below.</p>`;
        }
        
        renderProgressBar(prog, regime);
        renderPhaseSchedule(schedule, prog, regime);
        
        // AWD-specific sections
        const verifySection = document.getElementById('awdVerification')?.closest('.wm-section');
        const certSection = document.getElementById('awdCertificateSection');
        if (isAWD) {
            if (verifySection) verifySection.style.display = '';
            renderVerificationCriteria(criteria, prog);
            renderCertificateArea(prog, farmId);
        } else {
            if (verifySection) verifySection.style.display = 'none';
            if (certSection) certSection.style.display = 'none';
        }
    } catch (err) {
        console.error('Failed to load AWD progress:', err);
    }
}

function renderProgressBar(prog, regime) {
    const container = document.getElementById('awdProgressContainer');
    if (!container) return;
    
    const pct = prog.percent_complete || 0;
    const das = prog.current_das;
    const cycles = prog.cycles_completed || 0;
    const eligible = prog.certificate_eligible;
    const isAWD = regime === 'AWD';
    
    // AWD: show cycle milestones; Generic: show growth stage milestones
    let milestonesHTML = '';
    if (isAWD) {
        const milestones = [
            { day: 20,  label: 'C1', done: cycles >= 1 },
            { day: 34,  label: 'C2', done: cycles >= 2 },
            { day: 56,  label: 'C3', done: cycles >= 3 },
        ];
        milestonesHTML = milestones.map(m => {
            const pos = (m.day / 115 * 100).toFixed(1);
            return `<div class="bar-milestone ${m.done ? 'done' : ''}" style="left:${pos}%">
                <div class="milestone-dot">${m.done ? '✓' : ''}</div>
                <div class="milestone-label">${m.label}</div>
            </div>`;
        }).join('');
    } else {
        const milestones = [
            { day: 35,  label: 'Veg', done: das > 35 },
            { day: 65,  label: 'PI', done: das > 65 },
            { day: 100, label: 'Fill', done: das > 100 },
        ];
        milestonesHTML = milestones.map(m => {
            const pos = (m.day / 115 * 100).toFixed(1);
            return `<div class="bar-milestone ${m.done ? 'done' : ''}" style="left:${pos}%">
                <div class="milestone-dot">${m.done ? '✓' : ''}</div>
                <div class="milestone-label">${m.label}</div>
            </div>`;
        }).join('');
    }
    
    const cursorPos = Math.min(pct, 100).toFixed(1);
    
    // Third stat: AWD shows cycles, others show regime name
    const thirdStat = isAWD
        ? `<div class="awd-stat"><div class="awd-stat-value">${cycles}/3</div><div class="awd-stat-label">Cycles</div></div>`
        : `<div class="awd-stat"><div class="awd-stat-value">${regime}</div><div class="awd-stat-label">Regime</div></div>`;
    
    const certStat = (isAWD && eligible)
        ? '<div class="awd-stat cert-ready"><div class="awd-stat-value">🏆</div><div class="awd-stat-label">Ready!</div></div>'
        : '';
    
    container.innerHTML = `
        <div class="awd-stats-row">
            <div class="awd-stat">
                <div class="awd-stat-value">${Math.round(pct)}%</div>
                <div class="awd-stat-label">Complete</div>
            </div>
            <div class="awd-stat">
                <div class="awd-stat-value">Day ${das ?? '—'}</div>
                <div class="awd-stat-label">of ~115</div>
            </div>
            ${thirdStat}
            ${certStat}
        </div>
        <div class="awd-track-area">
            <div class="awd-track">
                <div class="awd-track-fill" style="width:${pct}%"></div>
                <div class="awd-track-cursor" style="left:${cursorPos}%"></div>
                ${milestonesHTML}
            </div>
            <div class="awd-track-labels">
                <span>Day 1</span>
                <span>Day 60</span>
                <span>Day 115</span>
            </div>
        </div>
    `;
}

function renderPhaseSchedule(schedule, prog, regime) {
    const container = document.getElementById('awdPhaseSchedule');
    if (!container) return;
    
    const isAWD = regime === 'AWD';
    const das = prog.current_das;
    const completed = prog.phases_completed || [];
    
    // Update section heading based on regime
    const heading = container.closest('.wm-section')?.querySelector('h3');
    if (heading) {
        heading.textContent = isAWD
            ? '🗓️ 10-Phase AWD Schedule'
            : `🗓️ ${schedule.length}-Phase Rice Season`;
    }
    const desc = container.closest('.wm-section')?.querySelector('.section-desc');
    if (desc) {
        desc.textContent = isAWD
            ? 'Three wet-dry cycles highlighted in amber. Your current phase is highlighted.'
            : `Season phases for ${regime} water management. Your current phase is highlighted.`;
    }
    
    const phaseCards = schedule.map(p => {
        const isCurrent = p.id === prog.current_phase_id;
        const isDone = completed.includes(p.id);
        const isDrying = p.is_drying;
        
        let statusClass = '';
        if (isCurrent) statusClass = 'phase-current';
        else if (isDone) statusClass = 'phase-done';
        else statusClass = 'phase-future';
        
        let cycleTag = '';
        if (p.cycle) cycleTag = `<span class="phase-cycle-tag">CYCLE ${p.cycle}</span>`;
        
        const statusIcon = isDone ? '✅' : isCurrent ? `<span class="phase-current-pip"></span>` : `<span class="phase-num-text">${p.id}</span>`;
        return `
        <div class="awd-phase-card ${statusClass} ${isDrying ? 'phase-drying' : ''}">
            <div class="phase-icon-col">${statusIcon}</div>
            <div class="phase-info-col">
                <div class="phase-name-row">
                    <span class="phase-emoji-inline">${p.icon}</span>
                    <span class="phase-name">${p.name}</span>
                    ${cycleTag}
                    ${isCurrent ? '<span class="phase-here-tag">NOW</span>' : ''}
                </div>
                <div class="phase-days">${p.day_range}</div>
                <div class="phase-rule">${p.rule}</div>
            </div>
        </div>`;
    }).join('');
    
    container.innerHTML = `<div class="awd-phase-list">${phaseCards}</div>`;
}

function renderVerificationCriteria(criteria, prog) {
    const container = document.getElementById('awdVerification');
    if (!container) return;
    
    const met = prog.criteria_met || {};
    const total = criteria.length;
    const done = Object.values(met).filter(v => v).length;
    
    const items = criteria.map(c => {
        const passed = met[c.id];
        return `
        <div class="awd-verify-item ${passed ? 'verified' : ''}">
            <div class="verify-check">${passed ? '✅' : '⬜'}</div>
            <div class="verify-info">
                <div class="verify-label">${c.icon} ${c.label}</div>
                <div class="verify-desc">${c.description}</div>
            </div>
        </div>`;
    }).join('');
    
    container.innerHTML = `
        <div class="awd-verify-header">
            <div class="verify-progress-ring">
                <span class="verify-count">${done}/${total}</span>
            </div>
            <span class="verify-summary">${done === total ? '🎉 All criteria met!' : `${total - done} remaining`}</span>
        </div>
        <div class="awd-verify-list">${items}</div>
    `;
}

function renderCertificateArea(prog, farmId) {
    const section = document.getElementById('awdCertificateSection');
    const area = document.getElementById('awdCertificateArea');
    if (!section || !area) return;
    
    if (prog.certificate_eligible) {
        section.style.display = 'block';
        area.innerHTML = `
        <div class="awd-cert-banner">
            <div class="cert-banner-icon">🏆</div>
            <div class="cert-banner-text">
                <strong>Congratulations!</strong>
                <p>You have completed all 3 AWD wet-dry cycles and met all verification criteria. You are eligible for your AWD Completion Certificate.</p>
            </div>
            <button class="btn-primary cert-view-btn" onclick="viewCertificate('${farmId}')">View Certificate</button>
        </div>`;
    } else {
        section.style.display = 'none';
    }
}

async function viewCertificate(farmId) {
    try {
        showLoading();
        const data = await apiCall(`/awd-certificate/${farmId}`);
        hideLoading();
        
        if (!data.eligible) {
            alert('Certificate not yet available. Complete all verification criteria first.');
            return;
        }
        
        const cert = data.certificate;
        const content = document.getElementById('certContent');
        content.innerHTML = `
        <div class="awd-certificate">
            <div class="cert-header">
                <div class="cert-emblem">🌾</div>
                <h1 class="cert-title">AWD Completion Certificate</h1>
                <p class="cert-subtitle">Alternate Wetting & Drying — Three Wet-Dry Cycles</p>
                <div class="cert-divider"></div>
            </div>
            <div class="cert-body">
                <p class="cert-preamble">This is to certify that</p>
                <p class="cert-farmer">${cert.farmer_id}</p>
                <p class="cert-preamble">has successfully implemented AWD irrigation with<br><strong>${cert.cycles_completed} wet-dry cycles</strong> on farm <strong>${cert.farm_id}</strong></p>
                <div class="cert-details">
                    <div class="cert-detail-row"><span>Province</span><span>${cert.province || '-'}</span></div>
                    <div class="cert-detail-row"><span>District</span><span>${cert.district || '-'}</span></div>
                    <div class="cert-detail-row"><span>Sowing Date</span><span>${cert.sowing_date || '-'}</span></div>
                    <div class="cert-detail-row"><span>Completion Date</span><span>${cert.completion_date}</span></div>
                    <div class="cert-detail-row"><span>Days After Sowing</span><span>${cert.das_at_completion}</span></div>
                </div>
                <div class="cert-verification">
                    <strong>Verification Summary</strong>
                    <p>${cert.verification_summary}</p>
                    <div class="cert-checks">
                        ${Object.entries(cert.criteria_met).map(([k, v]) => 
                            `<span class="cert-check ${v ? 'pass' : 'fail'}">${v ? '✅' : '❌'} ${k.replace(/_/g, ' ')}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
            <div class="cert-footer">
                <div class="cert-seal">🏆</div>
                <p>1 Million Hectare Programme — AWD Water-Saving Irrigation</p>
            </div>
            <div style="text-align:center;margin-top:24px;">
                <button class="btn-primary" onclick="window.print()">🖨️ Print Certificate</button>
            </div>
        </div>`;
        
        document.getElementById('certModal').style.display = 'flex';
    } catch (err) {
        hideLoading();
        console.error('Failed to load certificate:', err);
    }
}

// ─── Observation Timeline ────────────────────────────────

async function loadObservationTimeline(farmId) {
    const container = document.getElementById('wmObservations');
    if (!container) return;
    
    try {
        const data = await apiCall(`/state/${farmId}/observations?limit=20`);
        const obs = data.observations || [];
        
        if (obs.length === 0) {
            container.innerHTML = '<div style="opacity:0.6;font-size:0.9em;padding:12px;">No observations recorded yet. Chat with the assistant to start building your field state.</div>';
            return;
        }
        
        const sourceIcons = { 'chat': '💬', 'checkin': '📋', 'weather': '🌤️', 'derived': '⚙️', 'profile': '👤', 'system': '🔧' };
        const sourceColors = { 'chat': '#10b981', 'checkin': '#3b82f6', 'weather': '#f59e0b', 'derived': '#8b5cf6', 'profile': '#6366f1', 'system': '#64748b' };
        
        const items = obs.map(o => {
            const icon = sourceIcons[o.source] || '📝';
            const color = sourceColors[o.source] || '#64748b';
            const time = o.created_at ? new Date(o.created_at + 'Z').toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}) : '';
            const oldVal = o.old_value != null ? o.old_value : '-';
            const newVal = o.new_value != null ? o.new_value : '-';
            const field = o.field_name.replace(/_/g, ' ');
            const conf = o.confidence != null ? `${Math.round(o.confidence * 100)}%` : '';
            return `<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">
                <div style="flex-shrink:0;width:28px;text-align:center;font-size:1.1em;">${icon}</div>
                <div style="flex:1;min-width:0;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;">
                        <span style="font-weight:600;text-transform:capitalize;">${field}</span>
                        <span style="font-size:0.75em;opacity:0.6;">${time}</span>
                    </div>
                    <div style="font-size:0.85em;margin-top:2px;">
                        <span style="opacity:0.5;">${oldVal}</span> <span style="margin:0 4px;">→</span>
                        <span style="font-weight:600;color:${color};">${newVal}</span>
                        ${conf ? `<span style="margin-left:6px;opacity:0.5;font-size:0.85em;">(${conf})</span>` : ''}
                    </div>
                </div>
            </div>`;
        }).join('');
        
        container.innerHTML = `<div style="max-height:300px;overflow-y:auto;">${items}</div>`;
    } catch (err) {
        console.error('Failed to load observations:', err);
        container.innerHTML = '<div style="opacity:0.5;font-size:0.9em;">Could not load observations</div>';
    }
}

// ─── Assessment Display ──────────────────────────────────

function formatGrowthStage(stage) {
    if (!stage) return '-';
    return stage.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function displayHandbookAssessment(assessment, rules, das) {
    const trajectoryViz = document.getElementById('trajectoryViz');
    trajectoryViz.innerHTML = '';
    
    if (!assessment) {
        trajectoryViz.innerHTML = '<div class="loading-placeholder">Chat with the assistant to build your field state</div>';
        return;
    }
    
    const irrigateColor = assessment.should_irrigate ? '#dc2626' : '#16a34a';
    const irrigateIcon = assessment.should_irrigate ? '🔴 IRRIGATE NOW' : '🟢 NO IRRIGATION NEEDED';
    
    trajectoryViz.innerHTML = `
        <div style="padding:16px;border-radius:8px;background:var(--bg-tertiary);border-left:4px solid ${irrigateColor};margin-bottom:16px;">
            <div style="font-size:1.1em;font-weight:700;margin-bottom:8px;">${irrigateIcon}</div>
            <div style="margin-bottom:8px;">${assessment.reason || 'No water table data yet. Tell the assistant your measurements.'}</div>
            ${assessment.das_phase ? `<div style="opacity:0.8;font-size:0.9em;">📅 ${assessment.das_phase}</div>` : ''}
            ${assessment.is_sensitive_stage ? `<div style="color:#dc2626;font-weight:600;margin-top:8px;">⚠️ Sensitive growth stage — maintain shallow ponding</div>` : ''}
        </div>
        <div style="padding:10px;background:var(--bg-tertiary);border-radius:6px;font-size:0.85em;">
            <strong>AWD Trigger:</strong> Irrigate when water table ≥ ${rules.trigger_depth_cm || 15}cm below surface OR soil cracks appear<br>
            <strong>Refill target:</strong> ${rules.refill_min_cm || 3}–${rules.refill_max_cm || 5}cm shallow ponding
        </div>`;
}

// Daily Check-In
dailyCheckinBtn.addEventListener('click', () => {
    checkinModal.style.display = 'flex';
});

closeCheckinModal.addEventListener('click', () => {
    checkinModal.style.display = 'none';
});

cancelCheckin.addEventListener('click', () => {
    checkinModal.style.display = 'none';
});

// Measurement mode switching
document.querySelectorAll('input[name="measurementMode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const mode = e.target.value;
        document.getElementById('awdTubeFields').style.display = mode === 'awd_tube' ? 'block' : 'none';
        document.getElementById('bucketFields').style.display = mode === 'standing_water_bucket' ? 'block' : 'none';
    });
});

// Soil cracks button group
document.querySelectorAll('.btn-option').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('checkinSoilCracks').value = btn.dataset.value;
    });
});

// Check-in form submission
checkinForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentFarmId) {
        alert('No farm selected');
        return;
    }
    
    const measurementMode = document.querySelector('input[name="measurementMode"]:checked').value;
    const soilCracks = document.getElementById('checkinSoilCracks').value;
    
    const checkinData = {
        farm_id: currentFarmId,
        checkin_date: new Date().toISOString().split('T')[0],
        measurement_mode: measurementMode,
        soil_cracks: soilCracks
    };
    
    if (measurementMode === 'awd_tube') {
        const depth = document.getElementById('checkinWaterTableDepth').value;
        if (depth) {
            checkinData.water_table_depth_cm = parseFloat(depth);
        }
    } else if (measurementMode === 'standing_water_bucket') {
        const bucket = document.getElementById('checkinPondedBucket').value;
        if (bucket) {
            checkinData.ponded_bucket = bucket;
        }
    }
    
    checkinModal.style.display = 'none';
    showLoading();
    
    try {
        const response = await apiCall('/checkin', {
            method: 'POST',
            body: JSON.stringify(checkinData)
        });
        
        // Display advice in chat
        displayAdviceInChat(response);
        
        // Update status bar
        try {
            const state = await apiCall(`/state/${currentFarmId}`);
            statusRegime.textContent = state.regime;
            statusDas.textContent = state.das ? `${state.das} DAS` : 'New';
        } catch (error) {
            console.error('Failed to update status:', error);
        }
        
        hideLoading();
    } catch (error) {
        hideLoading();
        alert(`Failed to submit check-in: ${error.message}`);
    }
});

// ─── Initialize ──────────────────────────────────────────
if (authToken) {
    showDashboard();
} else {
    showScreen('auth');
}
console.log('🌾 Rice Assistant loaded');
