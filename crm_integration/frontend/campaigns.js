// Campaigns Page JavaScript
const API_BASE = 'http://localhost:8000';

let campaigns = [];

document.addEventListener('DOMContentLoaded', () => {
    loadCampaigns();
});

async function loadCampaigns() {
    try {
        const response = await fetch(`${API_BASE}/api/campaigns`);
        const data = await response.json();
        
        campaigns = data.campaigns || [];
        
        document.getElementById('loading').classList.add('hidden');
        
        if (campaigns.length === 0) {
            document.getElementById('empty-state').classList.remove('hidden');
        } else {
            renderCampaigns();
            updateStats();
        }
    } catch (error) {
        console.error('Error loading campaigns:', error);
        document.getElementById('loading').innerHTML = '<p class="text-red-500">Error loading campaigns</p>';
    }
}

function renderCampaigns() {
    const grid = document.getElementById('campaigns-grid');
    
    grid.innerHTML = campaigns.map(campaign => `
        <div class="campaign-card bg-white rounded-lg shadow p-6">
            <div class="flex items-start justify-between mb-4">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">${escapeHtml(campaign.name)}</h3>
                    <p class="text-sm text-gray-500 mt-1">${escapeHtml(campaign.description || '')}</p>
                </div>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(campaign.status)}">
                    ${campaign.status}
                </span>
            </div>
            
            <div class="space-y-3">
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500">Contacts</span>
                    <span class="font-medium text-gray-900">${campaign.contact_count || 0}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500">Sent</span>
                    <span class="font-medium text-gray-900">${campaign.sent_count || 0}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500">Replied</span>
                    <span class="font-medium text-green-600">${campaign.replied_count || 0}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-500">Response Rate</span>
                    <span class="font-medium text-gray-900">${calculateResponseRate(campaign)}%</span>
                </div>
            </div>
            
            <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
                <span class="text-xs text-gray-500">Created ${formatDate(campaign.created_at)}</span>
                <div class="flex items-center space-x-2">
                    <button onclick="viewCampaign('${campaign.id}')" class="text-indigo-600 hover:text-indigo-800 text-sm">
                        <i class="fas fa-eye mr-1"></i>View
                    </button>
                    <button onclick="editCampaign('${campaign.id}')" class="text-gray-600 hover:text-gray-800 text-sm">
                        <i class="fas fa-edit mr-1"></i>Edit
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function updateStats() {
    const total = campaigns.length;
    const active = campaigns.filter(c => c.status === 'active').length;
    const totalContacts = campaigns.reduce((sum, c) => sum + (c.contact_count || 0), 0);
    const totalSent = campaigns.reduce((sum, c) => sum + (c.sent_count || 0), 0);
    const totalReplied = campaigns.reduce((sum, c) => sum + (c.replied_count || 0), 0);
    const responseRate = totalSent > 0 ? Math.round((totalReplied / totalSent) * 100) : 0;
    
    document.getElementById('total-campaigns').textContent = total;
    document.getElementById('active-campaigns').textContent = active;
    document.getElementById('total-contacts').textContent = totalContacts;
    document.getElementById('response-rate').textContent = responseRate + '%';
}

function getStatusColor(status) {
    const colors = {
        'active': 'bg-green-100 text-green-800',
        'paused': 'bg-yellow-100 text-yellow-800',
        'completed': 'bg-blue-100 text-blue-800',
        'draft': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

function calculateResponseRate(campaign) {
    if (!campaign.sent_count || campaign.sent_count === 0) return 0;
    return Math.round((campaign.replied_count || 0) / campaign.sent_count * 100);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function showCreateCampaignModal() {
    alert('Create Campaign feature coming soon! This will allow you to:\n\n• Select contacts for outreach\n• Define LinkedIn automation sequence\n• Set timing and delays\n• Track responses and engagement');
}

function viewCampaign(id) {
    alert(`View campaign ${id} - Coming soon!`);
}

function editCampaign(id) {
    alert(`Edit campaign ${id} - Coming soon!`);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

