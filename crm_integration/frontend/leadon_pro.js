// Global State
let contacts = [];
let filteredContacts = [];
let selectedContactIds = new Set();
let campaigns = [];
let currentView = 'dashboard';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    showView('dashboard');
    refreshContacts();
    loadCampaigns();
});

// View Management
function showView(viewName) {
    // Hide all views
    document.querySelectorAll('.view-container').forEach(el => el.classList.add('hidden'));
    
    // Show selected view
    document.getElementById(`view-${viewName}`).classList.remove('hidden');
    
    // Update nav buttons
    document.querySelectorAll('[id^="nav-"]').forEach(btn => {
        btn.classList.remove('bg-white/20');
    });
    document.getElementById(`nav-${viewName}`).classList.add('bg-white/20');
    
    currentView = viewName;
    
    // Refresh data for the view
    if (viewName === 'dashboard') {
        updateDashboard();
    } else if (viewName === 'contacts') {
        renderContacts();
    } else if (viewName === 'campaigns') {
        renderCampaigns();
    }
}

// Search Functionality
function toggleJobEnrichment() {
    const checkbox = document.getElementById('enrich-jobs');
    const container = document.getElementById('product-desc-container');
    container.classList.toggle('hidden', !checkbox.checked);
}

async function performSearch() {
    const searchInput = document.getElementById('search-input');
    const websiteInput = document.getElementById('website-input');
    const enrichJobs = document.getElementById('enrich-jobs');
    const productDesc = document.getElementById('product-description');
    const maxContacts = document.getElementById('max-contacts');
    const searchBtn = document.getElementById('search-btn');
    const resultsDiv = document.getElementById('search-results');

    const message = searchInput.value.trim();
    if (!message) {
        alert('Please enter a search query');
        return;
    }

    // Show loading
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<div class="spinner inline-block"></div>';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                website_url: websiteInput.value.trim() || null,
                enrich_with_jobs: enrichJobs.checked,
                product_description: productDesc.value.trim() || null,
                max_contacts: parseInt(maxContacts.value) || 25
            })
        });

        const data = await response.json();

        // Show results
        document.getElementById('search-response-text').textContent = data.response;
        document.getElementById('search-contacts-found').textContent = data.contacts_found;
        document.getElementById('search-contacts-added').textContent = data.contacts_added;
        resultsDiv.classList.remove('hidden');

        // Add to recent activity
        addRecentActivity(`Found ${data.contacts_found} contacts: ${message}`);

        // Refresh contacts
        await refreshContacts();

        // Clear input
        searchInput.value = '';

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fas fa-search mr-2"></i>Search';
    }
}

// Contacts Management
async function refreshContacts() {
    try {
        const response = await fetch('/api/contacts?limit=1000');
        const data = await response.json();
        contacts = data.contacts;
        filteredContacts = [...contacts];
        renderContacts();
        updateDashboard();
    } catch (error) {
        console.error('Error fetching contacts:', error);
    }
}

function filterContacts() {
    const filterInput = document.getElementById('filter-input');
    const query = filterInput.value.toLowerCase();
    
    if (!query) {
        filteredContacts = [...contacts];
    } else {
        filteredContacts = contacts.filter(contact => 
            contact.name.toLowerCase().includes(query) ||
            (contact.email && contact.email.toLowerCase().includes(query)) ||
            (contact.company && contact.company.toLowerCase().includes(query)) ||
            (contact.title && contact.title.toLowerCase().includes(query))
        );
    }
    
    renderContacts();
}

function renderContacts() {
    const container = document.getElementById('contacts-container');
    const countEl = document.getElementById('contacts-count');
    
    countEl.textContent = `(${filteredContacts.length})`;

    if (filteredContacts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <i class="fas fa-inbox text-6xl mb-4 text-gray-300"></i>
                <p class="text-lg">No contacts found</p>
                <p class="text-sm">Try adjusting your filters or search for new contacts</p>
            </div>
        `;
        return;
    }

    const html = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left">
                        <input type="checkbox" onchange="toggleSelectAll(this)" class="w-4 h-4 text-purple-600 rounded">
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${filteredContacts.map(contact => `
                    <tr class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4">
                            <input 
                                type="checkbox" 
                                class="w-4 h-4 text-purple-600 rounded contact-checkbox"
                                data-id="${contact.email || contact.linkedin_url}"
                                onchange="toggleContactSelection('${contact.email || contact.linkedin_url}')"
                                ${selectedContactIds.has(contact.email || contact.linkedin_url) ? 'checked' : ''}
                            >
                        </td>
                        <td class="px-6 py-4">
                            <div class="flex items-center">
                                <div class="flex-shrink-0 h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                                    <span class="text-purple-600 font-semibold">${contact.name.charAt(0).toUpperCase()}</span>
                                </div>
                                <div class="ml-4">
                                    <div class="text-sm font-medium text-gray-900">${contact.name}</div>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-500">${contact.title || '-'}</td>
                        <td class="px-6 py-4 text-sm text-gray-500">${contact.company || '-'}</td>
                        <td class="px-6 py-4 text-sm text-gray-500">${contact.email || '-'}</td>
                        <td class="px-6 py-4 text-sm text-gray-500">${formatLocation(contact)}</td>
                        <td class="px-6 py-4 text-sm font-medium space-x-2">
                            <button onclick='showContactDetail(${JSON.stringify(contact)})' class="text-purple-600 hover:text-purple-900">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${contact.linkedin_url ? `
                                <a href="${contact.linkedin_url}" target="_blank" class="text-blue-600 hover:text-blue-900">
                                    <i class="fab fa-linkedin"></i>
                                </a>
                            ` : ''}
                            ${contact.email ? `
                                <a href="mailto:${contact.email}" class="text-green-600 hover:text-green-900">
                                    <i class="fas fa-envelope"></i>
                                </a>
                            ` : ''}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

function formatLocation(contact) {
    const parts = [contact.city, contact.state, contact.country].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : '-';
}

function toggleContactSelection(id) {
    if (selectedContactIds.has(id)) {
        selectedContactIds.delete(id);
    } else {
        selectedContactIds.add(id);
    }
    updateCampaignContactCount();
}

function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.contact-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const id = cb.dataset.id;
        if (checkbox.checked) {
            selectedContactIds.add(id);
        } else {
            selectedContactIds.delete(id);
        }
    });
    updateCampaignContactCount();
}

function selectAllContacts() {
    filteredContacts.forEach(contact => {
        selectedContactIds.add(contact.email || contact.linkedin_url);
    });
    renderContacts();
    updateCampaignContactCount();
}

function updateCampaignContactCount() {
    const countEl = document.getElementById('campaign-contact-count');
    if (countEl) {
        countEl.textContent = selectedContactIds.size;
    }
}

// Contact Detail Modal
function showContactDetail(contact) {
    const modal = document.getElementById('contact-modal');
    const content = document.getElementById('contact-modal-content');
    
    content.innerHTML = `
        <div class="space-y-6">
            <div class="flex items-center space-x-4">
                <div class="flex-shrink-0 h-20 w-20 bg-purple-100 rounded-full flex items-center justify-center">
                    <span class="text-purple-600 font-bold text-3xl">${contact.name.charAt(0).toUpperCase()}</span>
                </div>
                <div>
                    <h3 class="text-2xl font-bold text-gray-800">${contact.name}</h3>
                    <p class="text-gray-600">${contact.title || 'No title'}</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Company</p>
                    <p class="text-gray-800">${contact.company || '-'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Email</p>
                    <p class="text-gray-800">${contact.email || '-'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Phone</p>
                    <p class="text-gray-800">${contact.phone || '-'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Location</p>
                    <p class="text-gray-800">${formatLocation(contact)}</p>
                </div>
            </div>
            
            <div class="flex gap-3 pt-4">
                ${contact.linkedin_url ? `
                    <a href="${contact.linkedin_url}" target="_blank" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-center hover:bg-blue-700 transition">
                        <i class="fab fa-linkedin mr-2"></i>View LinkedIn
                    </a>
                ` : ''}
                ${contact.email ? `
                    <a href="mailto:${contact.email}" class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg text-center hover:bg-green-700 transition">
                        <i class="fas fa-envelope mr-2"></i>Send Email
                    </a>
                ` : ''}
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

function closeContactModal() {
    document.getElementById('contact-modal').classList.add('hidden');
}

// Campaign Management
function showCampaignModal() {
    if (selectedContactIds.size === 0) {
        alert('Please select at least one contact first');
        return;
    }
    updateCampaignContactCount();
    document.getElementById('campaign-modal').classList.remove('hidden');
}

function closeCampaignModal() {
    document.getElementById('campaign-modal').classList.add('hidden');
}

function createCampaign() {
    const name = document.getElementById('campaign-name').value.trim();
    const message = document.getElementById('campaign-message').value.trim();
    
    if (!name || !message) {
        alert('Please fill in all fields');
        return;
    }
    
    const campaign = {
        id: Date.now(),
        name: name,
        message: message,
        contacts: Array.from(selectedContactIds),
        created: new Date().toISOString(),
        status: 'active'
    };
    
    campaigns.push(campaign);
    saveCampaigns();
    
    addRecentActivity(`Created campaign: ${name} with ${selectedContactIds.size} contacts`);
    
    alert(`Campaign "${name}" created successfully!\n\n${selectedContactIds.size} contacts will be contacted.`);
    
    closeCampaignModal();
    selectedContactIds.clear();
    renderContacts();
    updateDashboard();
}

function loadCampaigns() {
    const saved = localStorage.getItem('leadon_campaigns');
    if (saved) {
        campaigns = JSON.parse(saved);
    }
}

function saveCampaigns() {
    localStorage.setItem('leadon_campaigns', JSON.stringify(campaigns));
}

function renderCampaigns() {
    const container = document.getElementById('campaigns-container');
    
    if (campaigns.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <i class="fas fa-bullhorn text-6xl mb-4 text-gray-300"></i>
                <p class="text-lg">No campaigns yet</p>
                <p class="text-sm">Create your first campaign to start reaching out</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = campaigns.map(campaign => `
        <div class="bg-white border-2 border-gray-200 rounded-lg p-6 mb-4 hover-lift">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-xl font-bold text-gray-800">${campaign.name}</h3>
                    <p class="text-gray-600 mt-2">${campaign.message.substring(0, 100)}...</p>
                    <div class="flex gap-4 mt-4 text-sm text-gray-500">
                        <span><i class="fas fa-users mr-1"></i>${campaign.contacts.length} contacts</span>
                        <span><i class="fas fa-calendar mr-1"></i>${new Date(campaign.created).toLocaleDateString()}</span>
                        <span class="px-2 py-1 bg-green-100 text-green-700 rounded">${campaign.status}</span>
                    </div>
                </div>
                <button onclick="deleteCampaign(${campaign.id})" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function deleteCampaign(id) {
    if (confirm('Are you sure you want to delete this campaign?')) {
        campaigns = campaigns.filter(c => c.id !== id);
        saveCampaigns();
        renderCampaigns();
        updateDashboard();
    }
}

// Dashboard
function updateDashboard() {
    document.getElementById('stat-total-contacts').textContent = contacts.length;
    
    const uniqueCompanies = new Set(contacts.map(c => c.company).filter(Boolean));
    document.getElementById('stat-companies').textContent = uniqueCompanies.size;
    
    document.getElementById('stat-campaigns').textContent = campaigns.length;
}

function addRecentActivity(text) {
    const container = document.getElementById('recent-activity');
    const activity = document.createElement('div');
    activity.className = 'flex items-start space-x-3 p-3 bg-gray-50 rounded-lg animate-slide-in';
    activity.innerHTML = `
        <i class="fas fa-circle text-purple-600 text-xs mt-1"></i>
        <div class="flex-1">
            <p class="text-sm text-gray-800">${text}</p>
            <p class="text-xs text-gray-500 mt-1">${new Date().toLocaleString()}</p>
        </div>
    `;
    
    if (container.querySelector('.text-center')) {
        container.innerHTML = '';
    }
    
    container.insertBefore(activity, container.firstChild);
    
    // Keep only last 10 activities
    while (container.children.length > 10) {
        container.removeChild(container.lastChild);
    }
}

// Export
function exportContacts() {
    if (selectedContactIds.size === 0) {
        alert('Please select contacts to export');
        return;
    }
    
    const selectedContacts = contacts.filter(c => 
        selectedContactIds.has(c.email || c.linkedin_url)
    );
    
    const csv = [
        ['Name', 'Title', 'Company', 'Email', 'Phone', 'LinkedIn', 'City', 'State', 'Country'],
        ...selectedContacts.map(c => [
            c.name,
            c.title || '',
            c.company || '',
            c.email || '',
            c.phone || '',
            c.linkedin_url || '',
            c.city || '',
            c.state || '',
            c.country || ''
        ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leadon_contacts_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    addRecentActivity(`Exported ${selectedContacts.length} contacts to CSV`);
}

