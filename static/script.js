// API base URL
const API_BASE = '';

// State
let logRefreshInterval = null;
let sessionRefreshInterval = null;
let allLogs = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    loadLogs();
    
    // Auto-refresh
    sessionRefreshInterval = setInterval(loadSessions, 5000);
    logRefreshInterval = setInterval(loadLogs, 2000);
});

// Join Meeting Form
document.getElementById('joinForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = {
        meeting_id: formData.get('meeting_id'),
        meeting_url: formData.get('meeting_url'),
        platform: formData.get('platform'),
        start_time: new Date().toISOString()
    };

    const btn = e.target.querySelector('button[type="submit"]');
    const msgDiv = document.getElementById('joinMessage');
    
    btn.disabled = true;
    msgDiv.className = 'message';
    msgDiv.textContent = 'Starting bot session...';

    try {
        const response = await fetch(`${API_BASE}/join-meeting`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            msgDiv.className = 'message success';
            msgDiv.textContent = `✅ Session started! ID: ${data.session_id}`;
            e.target.reset();
            setTimeout(() => { msgDiv.className = 'message'; }, 5000);
            loadSessions();
        } else {
            msgDiv.className = 'message error';
            msgDiv.textContent = `❌ Error: ${data.error || data.detail || 'Unknown error'}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `❌ Failed to start session: ${error.message}`;
    } finally {
        btn.disabled = false;
    }
});

// Load Sessions
async function loadSessions() {
    try {
        const response = await fetch(`${API_BASE}/sessions`);
        const sessions = await response.json();
        renderSessions(sessions);
    } catch (error) {
        console.error('Failed to load sessions:', error);
        document.getElementById('sessionsList').innerHTML = 
            '<div class="error">Failed to load sessions</div>';
    }
}

function renderSessions(sessions) {
    const container = document.getElementById('sessionsList');
    
    if (sessions.length === 0) {
        container.innerHTML = '<div class="empty">No active sessions</div>';
        return;
    }

    container.innerHTML = sessions.map(session => {
        const statusClass = session.status.toLowerCase();
        const started = session.started_at ? new Date(session.started_at).toLocaleString() : 'Not started';
        const ended = session.ended_at ? new Date(session.ended_at).toLocaleString() : '-';
        
        return `
            <div class="session-card ${statusClass}">
                <h3>${session.meeting_id}</h3>
                <div class="session-id">${session.session_id}</div>
                <div>
                    <span class="session-badge ${statusClass}">${session.status}</span>
                    <span style="margin-left: 8px; color: var(--text-light);">${session.platform}</span>
                </div>
                <div class="session-meta">
                    <div>Started: ${started}</div>
                    ${session.ended_at ? `<div>Ended: ${ended}</div>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Load Logs
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs`);
        const logs = await response.json();
        allLogs = logs;
        filterLogs();
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

function filterLogs() {
    const levelFilter = document.getElementById('logLevelFilter').value;
    const searchTerm = document.getElementById('logSearch').value.toLowerCase();
    
    let filtered = allLogs;
    
    if (levelFilter) {
        filtered = filtered.filter(log => log.level === levelFilter);
    }
    
    if (searchTerm) {
        filtered = filtered.filter(log => {
            const message = (log.message || '').toLowerCase();
            const meetingId = (log.meeting_id || '').toLowerCase();
            const sessionId = (log.session_id || '').toLowerCase();
            return message.includes(searchTerm) || meetingId.includes(searchTerm) || sessionId.includes(searchTerm);
        });
    }
    
    renderLogs(filtered);
}

function renderLogs(logs) {
    const container = document.getElementById('logsContainer');
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="empty">No logs to display</div>';
        return;
    }
    
    // Show last 200 logs (oldest at top, newest at bottom)
    const recentLogs = logs.slice(-200);
    
    container.innerHTML = recentLogs.map(log => {
        const timestamp = new Date(log.timestamp).toLocaleTimeString();
        const level = log.level || 'INFO';
        let message = log.message || '';
        if (log.error) {
            message += ` — ${log.error}`;
        }
        
        let metaHtml = '';
        if (log.meeting_id || log.session_id || log.event) {
            metaHtml = '<div class="log-meta">';
            if (log.meeting_id) metaHtml += `Meeting: ${log.meeting_id} `;
            if (log.session_id) metaHtml += `Session: ${log.session_id.substring(0, 8)}... `;
            if (log.event) metaHtml += `Event: ${log.event}`;
            metaHtml += '</div>';
        }
        
        return `
            <div class="log-entry ${level}">
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level ${level}">${level}</span>
                <span class="log-message">${escapeHtml(message)}</span>
                ${metaHtml}
            </div>
        `;
    }).join('');
    
    // Do not force scroll; let the user control scroll position
}

async function clearLogs() {
    if (confirm('Clear all logs?')) {
        try {
            await fetch(`${API_BASE}/logs/clear`, { method: 'POST' });
            allLogs = [];
            renderLogs([]);
        } catch (error) {
            console.error('Failed to clear logs:', error);
        }
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}



