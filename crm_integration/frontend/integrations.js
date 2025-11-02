// Integrations Page JavaScript
const API_BASE = 'http://localhost:8000';

let integrations = {
    all: []
};

document.addEventListener('DOMContentLoaded', () => {
    loadIntegrations();
});

async function loadIntegrations() {
    try {
        const response = await fetch(`${API_BASE}/api/integrations`);
        const data = await response.json();

        // Store all integrations
        integrations.all = data.integrations || [];

        // Render accounts list
        renderAccountsList();

        document.getElementById('loading').classList.add('hidden');
        document.getElementById('integrations-container').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading integrations:', error);
        document.getElementById('loading').innerHTML = '<p class="text-red-500">Error loading integrations</p>';
    }
}

function renderAccountsList() {
    const accountsList = document.getElementById('accounts-list');
    const noAccounts = document.getElementById('no-accounts');

    // Clear existing content
    accountsList.innerHTML = '';

    if (integrations.all.length === 0) {
        noAccounts.classList.remove('hidden');
        return;
    }

    noAccounts.classList.add('hidden');

    // Render each account
    integrations.all.forEach(account => {
        const accountCard = createAccountCard(account);
        accountsList.appendChild(accountCard);
    });
}

function createAccountCard(account) {
    const div = document.createElement('div');
    div.className = 'p-6 hover:bg-gray-50 transition-colors';

    const platformIcon = account.platform === 'linkedin'
        ? '<i class="fab fa-linkedin-in text-blue-600 text-2xl"></i>'
        : '<i class="fab fa-telegram-plane text-blue-500 text-2xl"></i>';

    const platformColor = account.platform === 'linkedin' ? 'blue' : 'blue';

    const statusBadge = account.status === 'connected'
        ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><i class="fas fa-circle mr-1 text-green-500"></i>Active</span>'
        : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"><i class="fas fa-circle mr-1 text-gray-400"></i>Inactive</span>';

    div.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex items-start space-x-4 flex-1">
                <div class="w-12 h-12 bg-${platformColor}-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    ${platformIcon}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-3 mb-2">
                        <h3 class="text-lg font-semibold text-gray-900 capitalize">${account.platform}</h3>
                        ${statusBadge}
                    </div>
                    <p class="text-sm text-gray-600 mb-3">
                        <strong>Account:</strong> ${account.account_name || account.account_email || account.account_id || '—'}
                    </p>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <p class="text-gray-500">Connected</p>
                            <p class="font-medium text-gray-900">${formatDate(account.connected_at)}</p>
                        </div>
                        <div>
                            <p class="text-gray-500">Messages Sent</p>
                            <p class="font-medium text-gray-900">${account.messages_sent || 0}</p>
                        </div>
                        ${account.platform === 'linkedin' ? `
                        <div>
                            <p class="text-gray-500">Connections Made</p>
                            <p class="font-medium text-gray-900">${account.connections_made || 0}</p>
                        </div>
                        ` : ''}
                        <div>
                            <p class="text-gray-500">Last Used</p>
                            <p class="font-medium text-gray-900">${account.last_used_at ? formatDate(account.last_used_at) : 'Never'}</p>
                        </div>
                    </div>
                </div>
            </div>
            <button onclick="disconnectIntegration('${account.platform}', ${account.id})"
                    class="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex-shrink-0">
                <i class="fas fa-unlink mr-2"></i>Disconnect
            </button>
        </div>
    `;

    return div;
}

// LinkedIn Connection
function connectLinkedIn() {
    document.getElementById('linkedin-modal').classList.remove('hidden');
}

function closeLinkedInModal() {
    document.getElementById('linkedin-modal').classList.add('hidden');
    document.getElementById('linkedin-email').value = '';
    document.getElementById('linkedin-password').value = '';
}

async function saveLinkedInConnection() {
    const email = document.getElementById('linkedin-email').value.trim();
    const password = document.getElementById('linkedin-password').value.trim();
    
    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/integrations/linkedin/connect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('LinkedIn connected successfully!');
            closeLinkedInModal();
            loadIntegrations(); // Reload to show updated status
        } else {
            const error = await response.json();
            alert(`Failed to connect LinkedIn: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error connecting LinkedIn:', error);
        alert('Error connecting LinkedIn');
    }
}

// Telegram Connection
function connectTelegram() {
    document.getElementById('telegram-modal').classList.remove('hidden');
}

function closeTelegramModal() {
    document.getElementById('telegram-modal').classList.add('hidden');
    document.getElementById('telegram-api-id').value = '';
    document.getElementById('telegram-api-hash').value = '';
    document.getElementById('telegram-phone').value = '';
}

async function saveTelegramConnection() {
    const apiId = document.getElementById('telegram-api-id').value.trim();
    const apiHash = document.getElementById('telegram-api-hash').value.trim();
    const phone = document.getElementById('telegram-phone').value.trim();

    if (!apiId || !apiHash || !phone) {
        alert('Please fill in all fields (API ID, API Hash, and Phone Number)');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/integrations/telegram/connect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_id: apiId,
                api_hash: apiHash,
                phone: phone
            })
        });

        if (response.ok) {
            const data = await response.json();
            alert('Telegram User API connected successfully!');
            closeTelegramModal();
            loadIntegrations(); // Reload to show updated status
        } else {
            const error = await response.json();
            alert(`Failed to connect Telegram: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error connecting Telegram:', error);
        alert('Error connecting Telegram');
    }
}

// Disconnect Integration
async function disconnectIntegration(platform, integrationId) {
    if (!confirm(`Are you sure you want to disconnect this ${platform} account?`)) {
        return;
    }

    try {
        const url = integrationId
            ? `${API_BASE}/api/integrations/${platform}/disconnect?integration_id=${integrationId}`
            : `${API_BASE}/api/integrations/${platform}/disconnect`;

        const response = await fetch(url, {
            method: 'POST'
        });

        if (response.ok) {
            alert(`${platform} disconnected successfully`);
            loadIntegrations(); // Reload to show updated status
        } else {
            const error = await response.json();
            alert(`Failed to disconnect: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error disconnecting:', error);
        alert('Error disconnecting integration');
    }
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

