/* ─────────────────────────────────────────────────────────────────────────────
   Gojo Sentinel — app.js
   AI fraud detection frontend for Nigerian transactions with admin security.
───────────────────────────────────────────────────────────────────────────── */

const API_ROOT   = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.port === '5500' || window.location.port === '8000')
                    ? 'http://localhost:8000/api/v1'
                    : '/api/v1';
const API_URL    = `${API_ROOT}/predict`;
const HEALTH_URL = `${API_ROOT}/health`;

console.log("🛠️ Gojo Sentinel API Root:", API_ROOT);

const NIGERIAN_BANKS = [
    'GTBank','Zenith Bank','Access Bank','UBA','First Bank',
    'Opay','Moniepoint','Kuda','Fidelity Bank','Sterling Bank'
];

let sessionScored = 0;
let sessionFraud  = 0;
let history       = [];
let sessionToken  = localStorage.getItem('gojo_token');
let sessionUser   = JSON.parse(localStorage.getItem('gojo_user') || 'null');
let currentTheme  = localStorage.getItem('gojo_theme') || 'dark';
let riskChartInstance = null;

function randNuban() {
    return String(Math.floor(1000000000 + Math.random() * 9000000000));
}

function randTxnId() {
    return 'TXN' + String(Math.floor(Math.random() * 1e8)).padStart(8, '0');
}

function randFrom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function getAuthHeaders() {
    return sessionToken ? { 'Authorization': `Bearer ${sessionToken}` } : {};
}

function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('gojo_theme', theme);
    const themeIconTop = document.getElementById('themeIconTop');
    if (themeIconTop) themeIconTop.textContent = theme === 'light' ? 'Light' : 'Dark';
    const themeCheckbox = document.getElementById('themeToggleCheckbox');
    if (themeCheckbox) themeCheckbox.checked = (theme === 'light');
}

function setAuth(token, user) {
    sessionToken = token;
    sessionUser = user;
    if (token) {
        localStorage.setItem('gojo_token', token);
        localStorage.setItem('gojo_user', JSON.stringify(user));
    } else {
        localStorage.removeItem('gojo_token');
        localStorage.removeItem('gojo_user');
    }
    renderAuthState();
}

function renderAuthState() {
    const profileCard = document.getElementById('profileCard');
    const loginWrapper = document.getElementById('loginWrapper');
    const profileName = document.getElementById('profileName');
    const profileRole = document.getElementById('profileRole');
    const ruleNote = document.getElementById('ruleNote');
    const transactionNote = document.getElementById('transactionNote');
    const appLayout = document.getElementById('appLayout');
    const loginModal = document.getElementById('loginModal');

    if (sessionUser) {
        if (profileName) profileName.textContent = sessionUser.full_name || sessionUser.username;
        if (profileRole) profileRole.textContent = `Role: ${sessionUser.role}`;
        if (loginWrapper) loginWrapper.classList.add('hidden');
        if (profileCard) profileCard.classList.remove('hidden');
        if (ruleNote) ruleNote.textContent = 'Manage rules from this admin panel.';
        if (transactionNote) transactionNote.textContent = 'Backend history is shown when authenticated.';
        if (loginModal) loginModal.classList.add('hidden');
        if (appLayout) appLayout.classList.remove('hidden');
        
        const navUsers = document.getElementById('nav-users');
        if (navUsers) {
            navUsers.classList.toggle('hidden', sessionUser.role !== 'admin');
        }
    } else {
        if (loginWrapper) loginWrapper.classList.remove('hidden');
        if (profileCard) profileCard.classList.add('hidden');
        if (ruleNote) ruleNote.textContent = 'Login as admin to manage rules.';
        if (transactionNote) transactionNote.textContent = 'Login to view backend transaction history.';
        if (loginModal) loginModal.classList.remove('hidden');
        if (appLayout) appLayout.classList.add('hidden');
    }
}

function showPage(page) {
    if (page === 'settings') page = 'dashboard';
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
        link.classList.toggle('active', link.dataset.page === page);
    });
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.toggle('hidden', section.id !== `page-${page}`);
    });

    if (page === 'transactions') loadTransactions();
    if (page === 'rules') loadRules();
    if (page === 'users') loadUsers();
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const text = await response.text();
    let payload = null;
    try { payload = text ? JSON.parse(text) : null; } catch (e) { payload = null; }
    if (!response.ok) {
        const message = payload?.detail || payload?.message || response.statusText || 'Request failed';
        throw new Error(message);
    }
    return payload;
}

async function loadMe() {
    if (!sessionToken) return setAuth(null, null);
    try {
        const data = await fetchJson(`${API_ROOT}/auth/me`, { headers: getAuthHeaders() });
        setAuth(sessionToken, data);
    } catch {
        setAuth(null, null);
    }
}

async function loginAdmin(username, password) {
    const data = await fetchJson(`${API_ROOT}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    setAuth(data.token, data);
    return data;
}

async function logoutAdmin() {
    if (!sessionToken) return;
    try {
        await fetchJson(`${API_ROOT}/auth/logout`, { method: 'POST', headers: getAuthHeaders() });
    } catch (e) {
        console.warn('Logout error', e);
    }
    setAuth(null, null);
}

async function loadTransactions() {
    const body = document.getElementById('transactionHistoryBody');
    const note = document.getElementById('transactionNote');
    if (!sessionToken) {
        if (body) body.innerHTML = '<tr class="empty-row"><td colspan="7">Login to view stored transaction history.</td></tr>';
        if (note) note.textContent = 'Login to view backend transaction history.';
        return;
    }

    try {
        const rows = await fetchJson(`${API_ROOT}/transactions/history`, { headers: getAuthHeaders() });
        if (!rows.length) {
            body.innerHTML = '<tr class="empty-row"><td colspan="7">No transactions recorded yet.</td></tr>';
            return;
        }
        body.innerHTML = rows.map(r => {
            const rec = (r.recommendation || 'APPROVE').toLowerCase();
            return `
                <tr>
                    <td>${r.id}</td>
                    <td>${r.transaction_id}</td>
                    <td>₦${fmt(r.amount_ngn)}</td>
                    <td>${r.channel}</td>
                    <td><span class="risk-badge ${r.risk_level.toLowerCase()}">${r.risk_level}</span></td>
                    <td><span class="decision-badge ${rec}">${r.recommendation}</span></td>
                    <td>${new Date(r.scored_at).toLocaleString()}</td>
                </tr>`;
        }).join('');
    } catch (e) {
        console.error(e);
        body.innerHTML = `<tr class="empty-row"><td colspan="7">${e.message}</td></tr>`;
    }
}

async function loadRules() {
    const list = document.getElementById('ruleList');
    const note = document.getElementById('ruleNote');
    if (!sessionToken) {
        if (list) list.innerHTML = '<tr class="empty-row"><td colspan="6">Login as admin to manage rules.</td></tr>';
        if (note) note.textContent = 'Login as admin to manage rules.';
        return;
    }

    try {
        const rules = await fetchJson(`${API_ROOT}/rules`, { headers: getAuthHeaders() });
        if (!rules.length) {
            list.innerHTML = '<tr class="empty-row"><td colspan="6">No rules available.</td></tr>';
            return;
        }
        list.innerHTML = rules.map(rule => `
                <tr>
                    <td>${rule.name}</td>
                    <td>${rule.type}</td>
                    <td>${rule.value}</td>
                    <td>${rule.action}</td>
                    <td>${rule.enabled ? 'Yes' : 'No'}</td>
                    <td><button class="btn btn-ghost" data-rule-id="${rule.id}">Delete</button></td>
                </tr>`).join('');
        list.querySelectorAll('button[data-rule-id]').forEach(btn => {
            btn.addEventListener('click', () => deleteRule(btn.dataset.ruleId));
        });
    } catch (e) {
        console.error(e);
        list.innerHTML = `<tr class="empty-row"><td colspan="6">${e.message}</td></tr>`;
    }
}



async function loadUsers() {
    const list = document.getElementById('userList');
    if (!sessionToken || sessionUser.role !== 'admin') {
        if (list) list.innerHTML = '<tr class="empty-row"><td colspan="6">Admin access required.</td></tr>';
        return;
    }

    try {
        const users = await fetchJson(`${API_ROOT}/users`, { headers: getAuthHeaders() });
        if (!users.length) {
            list.innerHTML = '<tr class="empty-row"><td colspan="6">No users found.</td></tr>';
            return;
        }
        list.innerHTML = users.map(u => `
                <tr>
                    <td><strong>${u.username}</strong></td>
                    <td>${u.full_name || '-'}</td>
                    <td><span class="role-badge ${u.role}">${u.role}</span></td>
                    <td>${u.is_active ? '<span class="status-active">Active</span>' : '<span class="status-inactive">Disabled</span>'}</td>
                    <td>${u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}</td>
                    <td>
                        <button class="btn btn-ghost text-danger" data-delete-user-id="${u.id}" ${u.id === sessionUser.id ? 'disabled' : ''}>Delete</button>
                    </td>
                </tr>`).join('');
        
        list.querySelectorAll('button[data-delete-user-id]').forEach(btn => {
            btn.addEventListener('click', () => deleteUser(btn.dataset.deleteUserId));
        });
    } catch (e) {
        console.error(e);
        list.innerHTML = `<tr class="empty-row"><td colspan="6">${e.message}</td></tr>`;
    }
}

async function createUser(form) {
    const username = document.getElementById('userUsername').value.trim();
    const password = document.getElementById('userPassword').value;
    const full_name = document.getElementById('userFullName').value.trim();
    const email = document.getElementById('userEmail').value.trim();
    const role = document.getElementById('userRole').value;
    const msg = document.getElementById('userMessage');

    try {
        await fetchJson(`${API_ROOT}/users`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, full_name, email, role }),
        });
        form.reset();
        msg.textContent = 'User account created successfully.';
        msg.style.color = 'var(--accent)';
        await loadUsers();
    } catch (e) {
        msg.textContent = `Failed: ${e.message}`;
        msg.style.color = '#ef4444';
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
        await fetchJson(`${API_ROOT}/users/${userId}`, { method: 'DELETE', headers: getAuthHeaders() });
        await loadUsers();
    } catch (e) {
        alert(`Delete failed: ${e.message}`);
    }
}

async function deleteRule(ruleId) {
    try {
        await fetchJson(`${API_ROOT}/rules/${ruleId}`, { method: 'DELETE', headers: getAuthHeaders() });
        await loadRules();
    } catch (e) {
        document.getElementById('ruleMessage').textContent = `Rule delete failed: ${e.message}`;
    }
}

async function createRule(form) {
    const name = document.getElementById('ruleName').value.trim();
    const type = document.getElementById('ruleType').value;
    const value = document.getElementById('ruleValue').value.trim();
    const action = document.getElementById('ruleAction').value;
    const description = document.getElementById('ruleDescription').value.trim();
    const enabled = document.getElementById('ruleEnabled').checked;
    try {
        await fetchJson(`${API_ROOT}/rules`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, value, action, description, enabled }),
        });
        form.reset();
        document.getElementById('ruleEnabled').checked = true;
        document.getElementById('ruleMessage').textContent = 'Rule created successfully.';
        await loadRules();
    } catch (e) {
        document.getElementById('ruleMessage').textContent = `Failed to create rule: ${e.message}`;
    }
}

function riskColor(risk) {
    return { LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#ef4444', CRITICAL: '#dc2626' }[risk] || '#10b981';
}
function riskClass(risk) {
    return { LOW: '', MEDIUM: 'warning', HIGH: 'fraud', CRITICAL: 'critical' }[risk] || '';
}
function riskEmoji(risk) {
    return '';
}
function riskLabel(risk) {
    return { LOW: 'Safe Transaction', MEDIUM: 'Elevated Risk', HIGH: 'High Risk Detected', CRITICAL: 'Critical Block Immediately' }[risk] || 'Safe Transaction';
}

function fmt(n) {
    return Number(n).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function animateCount(el, from, to, dur, format) {
    let start = null;
    function step(ts) {
        if (!start) start = ts;
        const p = Math.min((ts - start) / dur, 1);
        const ease = p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p;
        el.textContent = format(from + (to - from) * ease);
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function showState(name) {
    const initialState = document.getElementById('initialState');
    const loadingState = document.getElementById('loadingState');
    const resultState = document.getElementById('resultState');
    initialState.classList.add('hidden');
    loadingState.classList.add('hidden');
    resultState.classList.add('hidden');
    if (name === 'initial') initialState.classList.remove('hidden');
    if (name === 'loading') loadingState.classList.remove('hidden');
    if (name === 'result') resultState.classList.remove('hidden');
}

function displayResult(data, payload) {
    showState('result');
    const gaugePath = document.getElementById('gaugePath');
    const scoreValue = document.getElementById('scoreValue');
    const verdictBadge = document.getElementById('verdictBadge');
    const verdictIcon = document.getElementById('verdictIcon');
    const verdictText = document.getElementById('verdictText');
    const decisionText = document.getElementById('decisionText');
    const riskLevelText = document.getElementById('riskLevelText');
    const resTxnId = document.getElementById('resTxnId');
    const probText = document.getElementById('probText');
    const riskList = document.getElementById('riskList');

    const pct = (data.fraud_probability * 100).toFixed(1);
    const fraud = data.is_fraud;
    const risk = data.risk_level;
    const rec = data.recommendation;
    // Circular gauge circumference is 339.292
    const offset = 339.292 - (pct / 100) * 339.292;
    const proGaugePath = document.getElementById('proGaugePath');
    if (proGaugePath) {
        proGaugePath.style.strokeDashoffset = 339.292;
        proGaugePath.style.stroke = riskColor(risk);
        requestAnimationFrame(() => {
            setTimeout(() => { proGaugePath.style.strokeDashoffset = offset; }, 50);
        });
    }
    animateCount(scoreValue, 0, parseFloat(pct), 1200, v => v.toFixed(1) + '%');
    scoreValue.style.fill = riskColor(risk);
    verdictBadge.className = 'verdict-badge ' + riskClass(risk);
    verdictIcon.textContent = riskEmoji(risk);
    verdictText.textContent = riskLabel(risk);
    decisionText.textContent = rec;
    decisionText.style.color = riskColor(risk);
    riskLevelText.textContent = risk;
    riskLevelText.style.color = riskColor(risk);
    resTxnId.textContent = data.transaction_id;
    probText.textContent = pct + '%';
    buildRiskFactors(payload, data);
    sessionScored++;
    if (fraud) sessionFraud++;
    document.getElementById('sessionsScored').textContent = sessionScored;
    document.getElementById('fraudCaught').textContent = sessionFraud;
}

function buildRiskFactors(p, data) {
    const riskList = document.getElementById('riskList');
    const items = [];
    const amt = p.amount_ngn;
    if (amt >= 500000) items.push({ text: `Large amount: ₦${fmt(amt)} — above typical transfer threshold`, cls: 'bad' });
    else items.push({ text: `Amount ₦${fmt(amt)} within normal range`, cls: 'ok' });
    if (p.bvn_match == 0) items.push({ text: 'BVN name mismatch detected — possible account takeover', cls: 'bad' });
    else items.push({ text: 'BVN names verified and matched', cls: 'ok' });
    const fintechs = ['Opay','Moniepoint','Kuda'];
    if (fintechs.includes(p.receiver_bank)) items.push({ text: `Receiver is ${p.receiver_bank} — common fraud cashout channel`, cls: 'bad' });
    else items.push({ text: `Receiver bank (${p.receiver_bank}) is low-risk`, cls: 'ok' });
    if (['USSD','Web'].includes(p.channel)) items.push({ text: `${p.channel} channel — elevated risk for unauthorized access`, cls: 'bad' });
    else items.push({ text: `${p.channel} channel — lower-risk payment method`, cls: 'ok' });
    const h = new Date(p.timestamp.replace('T',' ')).getHours();
    if (h >= 0 && h <= 4) items.push({ text: `Late-night transaction (${h}:xx AM) — fraud-correlated time window`, cls: 'bad' });
    else items.push({ text: 'Transaction during normal banking hours', cls: 'ok' });
    riskList.innerHTML = items.map(i => `<li class="${i.cls}">${i.text}</li>`).join('');
}

function addToHistory(data, payload) {
    history.unshift({ data, payload, time: new Date() });
    renderHistory();
}

function renderHistory() {
    const historyBody = document.getElementById('historyBody');
    if (!history.length) {
        historyBody.innerHTML = '<tr class="empty-row"><td colspan="7">No transactions scored yet.</td></tr>';
        updateChart();
        return;
    }
    historyBody.innerHTML = history.map(h => {
        const pct = (h.data.fraud_probability * 100).toFixed(1);
        const rl = (h.data.risk_level || 'LOW').toLowerCase();
        const rec = (h.data.recommendation || 'APPROVE').toLowerCase();
        return `
            <tr>
                <td>${h.data.transaction_id}</td>
                <td>₦${fmt(h.payload.amount_ngn)}</td>
                <td>${h.payload.channel}</td>
                <td>${h.payload.receiver_bank}</td>
                <td><span class="risk-badge ${rl}">${pct}%</span></td>
                <td><span class="decision-badge ${rec}">${h.data.recommendation}</span></td>
                <td>${h.time.toLocaleTimeString()}</td>
            </tr>`;
    }).join('');
    updateChart();
}

function updateChart() {
    if (!riskChartInstance) return;
    
    // Group history by date or just show counts of recent
    // For the 30-day chart, we typically show counts
    // Since we only have a few transactions in memory usually, we'll update the last day
    const fraudCount = history.filter(h => h.data.is_fraud).length;
    const goodCount = history.length - fraudCount;

    const goodDataset = riskChartInstance.data.datasets[0].data;
    const fraudDataset = riskChartInstance.data.datasets[1].data;

    // In a real app we'd group by day, here we just show the dynamic nature
    goodDataset[goodDataset.length - 1] = 10 + (goodCount * 5) + Math.random() * 5;
    fraudDataset[fraudDataset.length - 1] = 5 + (fraudCount * 8) + Math.random() * 3;

    riskChartInstance.update();
}

function setChannel(ch) {
    document.querySelectorAll('.channel-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.channel === ch);
    });
    document.getElementById('channel').value = ch;
}

function flashForm(type) {
    const form = document.getElementById('transactionForm');
    form.style.transition = 'box-shadow 0.3s';
    form.style.boxShadow = type === 'fraud'
        ? '0 0 0 2px rgba(239,68,68,0.5)'
        : '0 0 0 2px rgba(16,185,129,0.5)';
    setTimeout(() => { form.style.boxShadow = ''; }, 600);
}

async function handleSubmitTransaction(e) {
    e.preventDefault();
    
    const apiToggle = document.getElementById('apiToggleCheckbox');
    if (apiToggle && !apiToggle.checked) {
        alert("System Paused: API connection is disabled.");
        return;
    }

    showState('loading');

    const tsRaw = document.getElementById('timestamp').value;
    const ts = tsRaw.includes(':00', tsRaw.length - 3) ? tsRaw : tsRaw + ':00';

    const payload = {
        transaction_id: document.getElementById('transaction_id').value,
        user_id:        document.getElementById('user_id').value,
        amount_ngn:     parseFloat(document.getElementById('amount_ngn').value),
        sender_bank:    document.getElementById('sender_bank').value,
        receiver_bank:  document.getElementById('receiver_bank').value,
        channel:        document.getElementById('channel').value,
        sender_nuban:   document.getElementById('sender_nuban').value,
        receiver_nuban: document.getElementById('receiver_nuban').value,
        bvn_match:      parseInt(document.getElementById('bvn_match').value),
        txn_count_1h:   0,
        txn_count_24h:  0,
        amt_sum_24h:    0.0,
        timestamp:      ts,
    };

    const scoreBtn = document.getElementById('scoreBtn');
    scoreBtn.disabled = true;

    try {
        const resp = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        const data = await resp.json();

        setTimeout(() => {
            displayResult(data, payload);
            addToHistory(data, payload);
        }, 700);

    } catch (err) {
        console.error(err);
        showState('initial');
        alert(`❌ Error: ${err.message}\n\nMake sure the Gojo Sentinel server is running.`);
    } finally {
        scoreBtn.disabled = false;
    }
}

async function checkHealth() {
    const statusDot = document.getElementById('apiStatus');
    const label = statusDot.querySelector('.status-label');
    try {
        const data = await fetchJson(HEALTH_URL);
        if (data.status === 'healthy') {
            statusDot.classList.add('online');
            label.textContent = 'Gojo API Online';
        } else {
            statusDot.classList.remove('online');
            label.textContent = 'Degraded';
        }
    } catch {
        statusDot.classList.remove('online');
        label.textContent = 'Offline';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('timestamp').value = now.toISOString().slice(0, 16);
    document.getElementById('sender_nuban').value   = randNuban();
    document.getElementById('receiver_nuban').value = randNuban();
    document.getElementById('transaction_id').value = randTxnId();

    document.getElementById('transactionForm').addEventListener('submit', handleSubmitTransaction);
    document.querySelectorAll('.channel-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setChannel(btn.dataset.channel);
        });
    });
    document.getElementById('fillFraudBtn').addEventListener('click', () => {
        document.getElementById('transaction_id').value = randTxnId();
        document.getElementById('amount_ngn').value = (500000 + Math.random() * 4500000).toFixed(2);
        document.getElementById('bvn_match').value = '0';
        document.getElementById('sender_bank').value = randFrom(['GTBank','Zenith Bank','First Bank','Access Bank']);
        document.getElementById('receiver_bank').value = randFrom(['Opay','Moniepoint','Kuda']);
        setChannel(randFrom(['USSD','Web']));
        document.getElementById('sender_nuban').value   = randNuban();
        document.getElementById('receiver_nuban').value = randNuban();
        const d = new Date();
        d.setHours(1 + Math.floor(Math.random() * 3), Math.floor(Math.random() * 60));
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        document.getElementById('timestamp').value = d.toISOString().slice(0, 16);
        flashForm('fraud');
    });
    document.getElementById('fillLegitBtn').addEventListener('click', () => {
        document.getElementById('transaction_id').value = randTxnId();
        document.getElementById('amount_ngn').value = (100 + Math.random() * 49900).toFixed(2);
        document.getElementById('bvn_match').value = '1';
        document.getElementById('sender_bank').value   = randFrom(NIGERIAN_BANKS);
        document.getElementById('receiver_bank').value = randFrom(NIGERIAN_BANKS);
        setChannel(randFrom(['NIP','POS']));
        document.getElementById('sender_nuban').value   = randNuban();
        document.getElementById('receiver_nuban').value = randNuban();
        const d = new Date();
        d.setHours(9 + Math.floor(Math.random() * 8), Math.floor(Math.random() * 60));
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        document.getElementById('timestamp').value = d.toISOString().slice(0, 16);
        flashForm('legit');
    });
    const themeCheckbox = document.getElementById('themeToggleCheckbox');
    if (themeCheckbox) {
        themeCheckbox.addEventListener('change', (e) => {
            applyTheme(e.target.checked ? 'light' : 'dark');
        });
    }
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const page = link.dataset.page;
            if (page) {
                localStorage.setItem('gojo_page', page);
                showPage(page);
            }
        });
    });
    document.getElementById('createRuleForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        await createRule(event.target);
    });
    document.getElementById('loginForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const message = document.getElementById('loginMessage');
        try {
            await loginAdmin(username, password);
            message.textContent = 'Login successful.';
            await loadRules();
        } catch (e) {
            message.textContent = `Login failed: ${e.message}`;
        }
    });

    const loginModal = document.getElementById('loginModal');
    if (loginModal) {
        const openBtn = document.getElementById('openLoginBtn');
        if (openBtn) {
            openBtn.addEventListener('click', () => {
                loginModal.classList.remove('hidden');
                document.getElementById('loginMessage').textContent = '';
            });
        }
    }

    document.getElementById('logoutBtn').addEventListener('click', async () => {
        await logoutAdmin();
    });
    
    const toggleChartBtn = document.getElementById('toggleChartBtn');
    const predictionSection = document.getElementById('predictionSection');
    if (toggleChartBtn && predictionSection) {
        toggleChartBtn.addEventListener('click', () => {
            predictionSection.classList.toggle('hidden');
            if (!predictionSection.classList.contains('hidden') && !riskChartInstance) {
                init30DayChart();
            }
        });
    }

    document.getElementById('reloadTransactions').addEventListener('click', loadTransactions);
    document.getElementById('reloadRules').addEventListener('click', loadRules);
    document.getElementById('reloadUsers').addEventListener('click', loadUsers);
    
    document.getElementById('createUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createUser(e.target);
    });

    document.getElementById('clearHistory').addEventListener('click', () => {
        history = [];
        sessionScored = 0;
        sessionFraud  = 0;
        document.getElementById('sessionsScored').textContent = 0;
        document.getElementById('fraudCaught').textContent = 0;
        renderHistory();
    });
    applyTheme(currentTheme);
    await loadMe();
    renderAuthState();

    // Logo Logout Trigger
    const logo = document.querySelector('.logo');
    if (logo) {
        logo.style.cursor = 'pointer';
        logo.addEventListener('click', () => {
            if (sessionToken) {
                if (confirm('Are you sure you want to logout from Gojo Sentinel?')) {
                    logoutAdmin();
                }
            }
        });
    }

    const storedPage = localStorage.getItem('gojo_page') || 'dashboard';
    showPage(storedPage);

    // Initialize Chart (30-Day Activity)
    const ctx = document.getElementById('riskChart');
    if (ctx) {
        const labels = [];
        const goodPoints = [];
        const badPoints = [];
        let now = new Date();
        for(let i = 29; i >= 0; i--) {
            let d = new Date(now);
            d.setDate(d.getDate() - i);
            labels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            
            // Mock data for 30 days
            let mockGood = 10 + Math.sin(i * 0.5) * 5 + Math.random() * 5;
            let mockBad = 3 + Math.cos(i * 0.5) * 3 + Math.random() * 2;
            goodPoints.push(mockGood.toFixed(1));
            badPoints.push(mockBad.toFixed(1));
        }

        riskChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Legitimate',
                        data: goodPoints,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Fraudulent',
                        data: badPoints,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#64748b', maxTicksLimit: 7, font: { size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#64748b', font: { size: 10 } },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#94a3b8',
                            boxWidth: 10,
                            padding: 20,
                            font: { size: 11, weight: '600' }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    // Sidebar Toggle Logic
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.classList.toggle('collapsed');
        });
    }

    // Batch Drag & Drop + File Selector Listeners
    const dropzone = document.getElementById('batchDropzone');
    const batchInput = document.getElementById('batchCsvInput');
    const selectBtn = document.getElementById('selectBatchCsvBtn');

    if (dropzone && batchInput) {
        selectBtn.addEventListener('click', () => batchInput.click());
        batchInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleBatchFileUpload(e.target.files[0]);
            }
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.style.background = 'rgba(6, 182, 212, 0.1)';
        });
        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropzone.style.background = 'rgba(6, 182, 212, 0.03)';
        });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.background = 'rgba(6, 182, 212, 0.03)';
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleBatchFileUpload(e.dataTransfer.files[0]);
            }
        });
    }

    const exportBtn = document.getElementById('exportBatchCsvBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportBatchResultsCsv);
    }

    // Initial health check and interval
    checkHealth();
    setInterval(checkHealth, 10000);
});

// ─── Batch Dataset Scanner Functions ──────────────────────────────────────────
let batchData = null;
let batchPieChartInstance = null;

async function handleBatchFileUpload(file) {
    if (!file) return;
    const dropzone = document.getElementById('batchDropzone');
    const loading = document.getElementById('batchLoading');
    const resultsView = document.getElementById('batchResultsView');
    
    if (dropzone) dropzone.classList.add('hidden');
    if (loading) loading.classList.remove('hidden');
    if (resultsView) resultsView.classList.add('hidden');

    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_ROOT}/batch-predict`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Batch processing failed.');
        }
        
        batchData = await response.json();
        renderBatchResults(batchData);
    } catch (e) {
        alert(`Batch Upload Error: ${e.message}`);
    } finally {
        if (loading) loading.classList.add('hidden');
        if (dropzone) dropzone.classList.remove('hidden');
    }
}

function renderBatchResults(data) {
    const resultsView = document.getElementById('batchResultsView');
    if (!resultsView || !data) return;
    resultsView.classList.remove('hidden');

    // Stats Cards
    const totalEl = document.getElementById('batchTotalCount');
    const appVolEl = document.getElementById('batchApprovedVol');
    const revEl = document.getElementById('batchReviewCount');
    const blkEl = document.getElementById('batchBlockedCount');

    if (totalEl) totalEl.textContent = data.total_transactions.toLocaleString();
    if (appVolEl) appVolEl.textContent = '₦' + fmt(data.approved_volume_ngn);
    if (revEl) revEl.textContent = data.review_count.toLocaleString();
    if (blkEl) blkEl.textContent = data.blocked_count.toLocaleString();

    // Pie Chart
    renderBatchPieChart(data.risk_distribution);

    // Top Rule Violations
    const listEl = document.getElementById('topViolationsList');
    if (listEl) {
        if (!data.top_violations || data.top_violations.length === 0) {
            listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem; font-style: italic;">No rule violations detected in this batch.</div>';
        } else {
            listEl.innerHTML = data.top_violations.map(v => `
                <div style="background: var(--bg-input); padding: 0.65rem 0.9rem; border-radius: var(--radius-sm); border: 1px solid var(--border-soft); display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
                    <span style="color: var(--text-primary); font-weight: 500; display:flex; align-items:center; gap:0.4rem;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--yellow)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        ${v.rule}
                    </span>
                    <span style="background: var(--red-soft); color: var(--red); padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">${v.count} breaches</span>
                </div>
            `).join('');
        }
    }

    // Populate Batch Table
    renderBatchTable(data.records, 'ALL');

    // Risk Filter Listener
    const filterSelect = document.getElementById('batchFilterRisk');
    if (filterSelect) {
        filterSelect.onchange = (e) => {
            renderBatchTable(data.records, e.target.value);
        };
    }

    // Scroll to results smooth
    resultsView.scrollIntoView({ behavior: 'smooth' });
}

function renderBatchTable(records, filterRisk) {
    const tbody = document.getElementById('batchTableBody');
    if (!tbody || !records) return;

    let filtered = records;
    if (filterRisk !== 'ALL') {
        filtered = records.filter(r => r.risk_level === filterRisk);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="9">No records match the selected risk filter.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(r => {
        const recLower = (r.recommendation || 'APPROVE').toLowerCase();
        const vBadges = (r.violations && r.violations.length) 
            ? r.violations.map(v => `<span style="display:inline-block; margin:2px; padding:2px 6px; background:var(--red-soft); color:var(--red); border-radius:4px; font-size:0.7rem; font-weight:600;">${v}</span>`).join('')
            : '<span style="color:var(--text-muted); font-size:0.75rem;">None</span>';

        return `
            <tr>
                <td>${r.id}</td>
                <td><strong>${r.transaction_id}</strong></td>
                <td>₦${fmt(r.amount_ngn)}</td>
                <td><span style="font-weight:600;">${r.channel}</span></td>
                <td>${r.sender_bank}</td>
                <td>${r.receiver_bank}</td>
                <td><strong>${(r.fraud_probability * 100).toFixed(1)}%</strong></td>
                <td><span class="decision-badge ${recLower}">${r.recommendation}</span></td>
                <td>${vBadges}</td>
            </tr>
        `;
    }).join('');
}

function renderBatchPieChart(dist) {
    const ctx = document.getElementById('batchPieChart');
    if (!ctx) return;

    if (batchPieChartInstance) {
        batchPieChartInstance.destroy();
    }

    batchPieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk (Safe)', 'Medium Risk', 'High Risk', 'Critical (Blocked)'],
            datasets: [{
                data: [dist.LOW || 0, dist.MEDIUM || 0, dist.HIGH || 0, dist.CRITICAL || 0],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#dc2626'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#94a3b8', font: { size: 11 } }
                }
            }
        }
    });
}

function exportBatchResultsCsv() {
    if (!batchData || !batchData.records || !batchData.records.length) {
        alert('No batch data to export.');
        return;
    }

    const headers = ["ID", "Transaction ID", "User ID", "Amount NGN", "Sender Bank", "Receiver Bank", "Channel", "Fraud Probability", "Risk Level", "Recommendation", "Violations"];
    const rows = batchData.records.map(r => [
        r.id,
        r.transaction_id,
        r.user_id,
        r.amount_ngn,
        `"${r.sender_bank}"`,
        `"${r.receiver_bank}"`,
        r.channel,
        r.fraud_probability,
        r.risk_level,
        r.recommendation,
        `"${(r.violations || []).join('; ')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
        + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Gojo_Sentinel_Batch_Audit_${batchData.file_name || 'report'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
