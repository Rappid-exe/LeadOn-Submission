// LeadOn CRM - Main JavaScript
const API_BASE = 'http://localhost:8000';

// State
let contacts = [];
let selectedContacts = new Set();
let currentPage = 1;
let itemsPerPage = 50;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadContacts();
    setupEventListeners();
});

function setupEventListeners() {
    // Auto-refresh every 30 seconds
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            loadContacts(true); // Silent refresh
        }
    }, 30000);
}

// ==================== Data Loading ====================

async function loadContacts(silent = false) {
    try {
        if (!silent) {
            showLoading();
        }
        
        const response = await fetch(`${API_BASE}/api/contacts`);
        const data = await response.json();
        
        contacts = data.contacts || [];
        renderContactsTable();
        updateStats();
        
    } catch (error) {
        console.error('Error loading contacts:', error);
        if (!silent) {
            showError('Failed to load contacts');
        }
    }
}

async function syncContacts() {
    showLoading('Syncing contacts...');
    await loadContacts();
}

// ==================== Table Rendering ====================

function renderContactsTable() {
    const tbody = document.getElementById('contacts-table-body');
    
    if (contacts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="px-4 py-12 text-center text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-3 text-gray-300"></i>
                    <p>No contacts found. Use AI Search to find contacts.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    // Pagination
    const startIdx = (currentPage - 1) * itemsPerPage;
    const endIdx = startIdx + itemsPerPage;
    const pageContacts = contacts.slice(startIdx, endIdx);
    
    tbody.innerHTML = pageContacts.map(contact => `
        <tr class="table-row" data-id="${contact.id}">
            <td class="px-4 py-3">
                <input 
                    type="checkbox" 
                    class="checkbox-custom contact-checkbox" 
                    data-id="${contact.id}"
                    onchange="toggleContactSelection(${contact.id})"
                    ${selectedContacts.has(contact.id) ? 'checked' : ''}
                >
            </td>
            <td class="px-4 py-3">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-semibold">
                        ${getInitials(contact.name)}
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${escapeHtml(contact.name)}</div>
                        ${contact.seniority ? `<div class="text-xs text-gray-500">${escapeHtml(contact.seniority)}</div>` : ''}
                    </div>
                </div>
            </td>
            <td class="px-4 py-3">
                ${contact.linkedin_url ? `
                    <a href="${escapeHtml(contact.linkedin_url)}" target="_blank" class="text-blue-600 hover:text-blue-800">
                        <i class="fab fa-linkedin text-lg"></i>
                    </a>
                ` : '<span class="text-gray-300">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${escapeHtml(contact.title) || '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${escapeHtml(contact.company || contact.company_name) || '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm">
                ${contact.tags && contact.tags.length > 0 ?
                    contact.tags.map(tag => `
                        <span class="inline-block bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">
                            ${escapeHtml(tag)}
                        </span>
                    `).join('')
                    : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm">
                ${formatWorkflowStage(contact.workflow_stage)}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${contact.last_action ? `
                    <div class="text-gray-900">${escapeHtml(contact.last_action)}</div>
                    <div class="text-xs text-gray-500">${formatDate(contact.last_action_date)}</div>
                ` : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${contact.next_action ? `
                    <div class="text-gray-900">${escapeHtml(contact.next_action)}</div>
                    <div class="text-xs text-gray-500">${formatDate(contact.next_action_date)}</div>
                ` : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${contact.email ? `
                    <a href="mailto:${escapeHtml(contact.email)}" class="text-blue-600 hover:underline">
                        ${escapeHtml(contact.email)}
                    </a>
                ` : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${escapeHtml(contact.phone) || '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-4 py-3 text-sm text-gray-700">
                ${formatLocation(contact)}
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">
                ${formatDate(contact.created_at)}
            </td>
            <td class="px-4 py-3 text-sm">
                <button
                    onclick="generatePitch(${contact.id})"
                    class="text-purple-600 hover:text-purple-900 mr-2"
                    title="Generate AI Sales Pitch"
                >
                    <i class="fas fa-magic"></i>
                </button>
                <button
                    onclick="editContact('${contact.id}')"
                    class="text-indigo-600 hover:text-indigo-900 mr-2"
                    title="Edit contact"
                >
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
    `).join('');

    updatePagination();
}

// ==================== Filtering ====================

let activeFilters = {
    search: '',
    workflow: '',
    company: '',
    tags: ''
};

function toggleFilterPanel() {
    const panel = document.getElementById('filter-panel');
    panel.classList.toggle('hidden');
}

function applyFilters() {
    activeFilters.search = document.getElementById('search-input').value.toLowerCase();
    activeFilters.workflow = document.getElementById('filter-workflow').value;
    activeFilters.company = document.getElementById('filter-company').value.toLowerCase();
    activeFilters.tags = document.getElementById('filter-tags').value.toLowerCase();

    filterTable();
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('filter-workflow').value = '';
    document.getElementById('filter-company').value = '';
    document.getElementById('filter-tags').value = '';

    activeFilters = {
        search: '',
        workflow: '',
        company: '',
        tags: ''
    };

    filterTable();
}

function filterTable() {
    const searchTerm = activeFilters.search || document.getElementById('search-input').value.toLowerCase();

    // Check if any filters are active
    const hasFilters = searchTerm || activeFilters.workflow || activeFilters.company || activeFilters.tags;

    if (!hasFilters) {
        renderContactsTable();
        return;
    }

    const filtered = contacts.filter(contact => {
        // Search filter
        const matchesSearch = !searchTerm || (
            contact.name?.toLowerCase().includes(searchTerm) ||
            contact.email?.toLowerCase().includes(searchTerm) ||
            (contact.company || contact.company_name)?.toLowerCase().includes(searchTerm) ||
            contact.title?.toLowerCase().includes(searchTerm)
        );

        // Workflow filter
        const matchesWorkflow = !activeFilters.workflow || contact.workflow_stage === activeFilters.workflow;

        // Company filter
        const matchesCompany = !activeFilters.company ||
            (contact.company || contact.company_name)?.toLowerCase().includes(activeFilters.company);

        // Tags filter
        const matchesTags = !activeFilters.tags ||
            (contact.tags && contact.tags.some(tag => tag.toLowerCase().includes(activeFilters.tags)));

        return matchesSearch && matchesWorkflow && matchesCompany && matchesTags;
    });

    // Temporarily replace contacts for rendering
    const originalContacts = contacts;
    contacts = filtered;
    renderContactsTable();
    contacts = originalContacts;
}

function exportAllContacts() {
    downloadCSV(contacts, 'leadon_all_contacts.csv');
}

// ==================== Selection ====================

function toggleContactSelection(id) {
    if (selectedContacts.has(id)) {
        selectedContacts.delete(id);
    } else {
        selectedContacts.add(id);
    }
    updateSelectionUI();
}

function toggleSelectAll() {
    const checkbox = document.getElementById('select-all');
    const pageContacts = contacts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
    
    if (checkbox.checked) {
        pageContacts.forEach(c => selectedContacts.add(c.id));
    } else {
        pageContacts.forEach(c => selectedContacts.delete(c.id));
    }
    
    renderContactsTable();
    updateSelectionUI();
}

function updateSelectionUI() {
    const count = selectedContacts.size;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('action-bar-count').textContent = `${count} selected`;
    
    const actionBar = document.getElementById('action-bar');
    if (count > 0) {
        actionBar.classList.remove('hidden');
    } else {
        actionBar.classList.add('hidden');
    }
}

// ==================== Chat Panel ====================

function toggleChat() {
    const panel = document.getElementById('chat-panel');
    panel.classList.toggle('open');
    
    if (panel.classList.contains('open')) {
        document.getElementById('chat-input').focus();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show loading
    const loadingId = addChatMessage('Searching...', 'assistant', true);
    
    try {
        const enrichJobs = document.getElementById('enrich-jobs-chat').checked;
        
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                max_contacts: 25,
                enrich_with_jobs: enrichJobs
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId)?.remove();
        
        // Add response
        const responseText = `✅ ${data.response}\n\n📊 Found ${data.contacts_found} contacts\n💾 Added ${data.contacts_added} to CRM`;
        addChatMessage(responseText, 'assistant');
        
        // Reload contacts
        await loadContacts();
        
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        addChatMessage('❌ Error: ' + error.message, 'assistant');
    }
}

function addChatMessage(text, sender, isLoading = false) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = sender === 'user' 
        ? 'bg-indigo-600 text-white rounded-lg p-3 ml-8' 
        : 'bg-gray-100 rounded-lg p-3 mr-8';
    
    if (isLoading) {
        messageDiv.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${text}`;
    } else {
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    return messageId;
}

// ==================== Actions ====================

async function startCampaign() {
    if (selectedContacts.size === 0) {
        alert('Please select contacts first');
        return;
    }
    
    const confirmed = confirm(
        `Start LinkedIn automation for ${selectedContacts.size} contacts?\n\n` +
        `This will:\n` +
        `1. Like 3 recent posts on their profile\n` +
        `2. Send connection request\n\n` +
        `Note: Browser will open and run automation`
    );
    
    if (!confirmed) return;

    try {
        const contactIds = Array.from(selectedContacts);
        
        console.log('Starting LinkedIn campaign for contacts:', contactIds);

        const response = await fetch('/api/linkedin/campaign/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contact_ids: contactIds,
                actions: ['like_posts', 'send_connection'],
                like_count: 3,
                headless: false  // Show browser for visibility
            })
        });

        const data = await response.json();
        console.log('Campaign response:', data);

        if (response.ok) {
            const results = data.results;
            alert(
                `✅ Campaign Complete!\n\n` +
                `Total: ${results.total}\n` +
                `Successful: ${results.successful}\n` +
                `Failed: ${results.failed}\n` +
                `Skipped: ${results.skipped}\n\n` +
                `Check contact details for automation notes.`
            );
            
            // Refresh contacts to show updated status
            await loadContacts();
            selectedContacts.clear();
            updateSelectionUI();
        } else {
            alert(`❌ Error: ${data.detail || 'Campaign failed'}`);
        }

    } catch (error) {
        console.error('Campaign error:', error);
        alert(`❌ Error starting campaign: ${error.message}`);
    }
}

function exportSelected() {
    const selected = contacts.filter(c => selectedContacts.has(c.id));
    downloadCSV(selected, 'leadon_contacts.csv');
}

function deleteSelected() {
    if (!confirm(`Delete ${selectedContacts.size} contacts?`)) return;
    
    // TODO: Implement delete API
    alert('Delete functionality coming soon!');
}

// ==================== Pagination ====================

function updatePagination() {
    const totalPages = Math.ceil(contacts.length / itemsPerPage);
    document.getElementById('current-page').textContent = currentPage;
    document.getElementById('total-pages').textContent = totalPages;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderContactsTable();
    }
}

function nextPage() {
    const totalPages = Math.ceil(contacts.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderContactsTable();
    }
}

// ==================== Edit Contact ====================

function editContact(contactId) {
    console.log('Editing contact ID:', contactId, 'Type:', typeof contactId);
    console.log('First 3 contact IDs in array:', contacts.slice(0, 3).map(c => ({ id: c.id, type: typeof c.id })));

    // Convert to string for comparison since IDs might be strings
    const contact = contacts.find(c => String(c.id) === String(contactId));
    if (!contact) {
        alert('Contact not found. ID: ' + contactId);
        console.error('Could not find contact with ID:', contactId);
        console.log('Available contacts:', contacts.length);
        return;
    }

    console.log('Found contact:', contact);

    // Pre-fill the form with contact data
    document.getElementById('contact-name').value = contact.name || '';
    document.getElementById('contact-email').value = contact.email || '';
    document.getElementById('contact-phone').value = contact.phone || '';
    document.getElementById('contact-title').value = contact.title || '';
    document.getElementById('contact-company').value = contact.company || contact.company_name || '';
    document.getElementById('contact-linkedin').value = contact.linkedin_url || '';
    document.getElementById('contact-city').value = contact.city || '';
    document.getElementById('contact-country').value = contact.country || '';
    document.getElementById('contact-tags').value = contact.tags ? contact.tags.join(', ') : '';

    // Store the contact ID for updating
    const form = document.getElementById('create-contact-form');
    form.dataset.editingId = String(contactId);
    console.log('Set editingId to:', form.dataset.editingId);

    // Change modal title and button text
    document.querySelector('#create-contact-modal h2').textContent = 'Edit Contact';
    document.getElementById('submit-contact-btn').textContent = 'Update Contact';

    // Show the modal
    document.getElementById('create-contact-modal').classList.remove('hidden');
}

// ==================== Sidebar ====================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');

    sidebar.classList.toggle('collapsed');

    if (sidebar.classList.contains('collapsed')) {
        mainContent.classList.remove('ml-60');
        mainContent.classList.add('ml-16');
    } else {
        mainContent.classList.remove('ml-16');
        mainContent.classList.add('ml-60');
    }
}

// ==================== Utilities ====================

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatLocation(contact) {
    const parts = [contact.city, contact.state, contact.country].filter(Boolean);
    return parts.length > 0 ? escapeHtml(parts.join(', ')) : '<span class="text-gray-400">—</span>';
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatWorkflowStage(stage) {
    if (!stage || stage === 'new') {
        return '<span class="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">New</span>';
    }

    const stageConfig = {
        'connect_sent': { label: 'Connect Sent', color: 'blue' },
        'connected': { label: 'Connected', color: 'green' },
        'liked': { label: 'Liked Posts', color: 'purple' },
        'commented': { label: 'Commented', color: 'indigo' },
        'messaged': { label: 'Messaged', color: 'yellow' },
        'replied': { label: 'Replied', color: 'teal' },
        'qualified': { label: 'Qualified', color: 'emerald' },
        'disqualified': { label: 'Disqualified', color: 'red' }
    };

    const config = stageConfig[stage] || { label: stage, color: 'gray' };
    return `<span class="inline-block bg-${config.color}-100 text-${config.color}-800 text-xs px-2 py-1 rounded-full">${config.label}</span>`;
}

function showLoading(message = 'Loading...') {
    // TODO: Implement loading overlay
    console.log(message);
}

function showError(message) {
    alert(message);
}

function updateStats() {
    // Update any stats displays
    console.log(`Loaded ${contacts.length} contacts`);
}

function downloadCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}

function convertToCSV(data) {
    if (data.length === 0) return '';

    const headers = ['Name', 'Email', 'Title', 'Company', 'Phone', 'LinkedIn', 'Location'];
    const rows = data.map(c => [
        c.name,
        c.email,
        c.title,
        c.company || c.company_name,
        c.phone,
        c.linkedin_url,
        formatLocation(c).replace(/<[^>]*>/g, '')
    ]);

    return [headers, ...rows].map(row => row.map(cell => `"${cell || ''}"`).join(',')).join('\n');
}

// ==================== Create Contact Modal ====================

function showCreateModal() {
    document.getElementById('create-contact-modal').classList.remove('hidden');
}

function closeCreateModal() {
    const modal = document.getElementById('create-contact-modal');
    const form = document.getElementById('create-contact-form');

    modal.classList.add('hidden');
    form.reset();

    // Reset modal title, button text, and editing state
    delete form.dataset.editingId;
    document.querySelector('#create-contact-modal h2').textContent = 'Create New Contact';
    document.getElementById('submit-contact-btn').textContent = 'Create Contact';
}

document.getElementById('create-contact-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const form = e.target;
    const editingId = form.dataset.editingId;
    const isEditing = !!editingId;

    console.log('Form submission - editingId:', editingId, 'isEditing:', isEditing);

    const tags = document.getElementById('contact-tags').value
        .split(',')
        .map(t => t.trim())
        .filter(t => t);

    const contactData = {
        name: document.getElementById('contact-name').value,
        email: document.getElementById('contact-email').value || null,
        phone: document.getElementById('contact-phone').value || null,
        title: document.getElementById('contact-title').value || null,
        company_name: document.getElementById('contact-company').value || null,
        linkedin_url: document.getElementById('contact-linkedin').value || null,
        city: document.getElementById('contact-city').value || null,
        country: document.getElementById('contact-country').value || null,
        tags: tags,
        source: isEditing ? undefined : 'manual',
        workflow_stage: isEditing ? undefined : 'new',
        next_action: isEditing ? undefined : 'Send connection request'
    };

    try {
        const url = isEditing
            ? `${API_BASE}/api/contacts/${editingId}`
            : `${API_BASE}/api/contacts/create`;
        const method = isEditing ? 'PUT' : 'POST';

        console.log('Sending request:', method, url, contactData);

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contactData)
        });

        if (response.ok) {
            loadContacts();
            closeCreateModal(); // This already resets everything
            alert(isEditing ? 'Contact updated successfully!' : 'Contact created successfully!');
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail || 'Failed to save contact'}`);
        }
    } catch (error) {
        console.error('Error creating contact:', error);
        alert('Failed to create contact. Please try again.');
    }
});

// ==================== CSV Import ====================

function showImportModal() {
    document.getElementById('import-modal').classList.remove('hidden');
    // Reset modal state
    document.getElementById('csv-file-input').value = '';
    document.getElementById('import-preview').classList.add('hidden');
    document.getElementById('import-results').classList.add('hidden');
    document.getElementById('import-errors').classList.add('hidden');
}

function closeImportModal() {
    document.getElementById('import-modal').classList.add('hidden');
}

async function importCSV() {
    const fileInput = document.getElementById('csv-file-input');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a CSV file');
        return;
    }

    if (!file.name.endsWith('.csv')) {
        alert('Please select a valid CSV file');
        return;
    }

    const importBtn = document.getElementById('import-btn');
    const originalText = importBtn.innerHTML;
    importBtn.disabled = true;
    importBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Importing...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/contacts/import-csv`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // Show success message
            document.getElementById('import-results').classList.remove('hidden');
            document.getElementById('results-text').innerHTML = `
                <p><strong>✅ Import Complete!</strong></p>
                <p class="mt-2">• ${result.imported} contacts imported</p>
                <p>• ${result.skipped} duplicates skipped</p>
                ${result.errors > 0 ? `<p>• ${result.errors} errors encountered</p>` : ''}
            `;

            // Show errors if any
            if (result.errors > 0 && result.error_details && result.error_details.length > 0) {
                document.getElementById('import-errors').classList.remove('hidden');
                document.getElementById('errors-text').innerHTML = result.error_details.map(err =>
                    `<p>• ${err}</p>`
                ).join('');
            }

            // Reload contacts
            await loadContacts();

            // Auto-close after 3 seconds if no errors
            if (result.errors === 0) {
                setTimeout(() => {
                    closeImportModal();
                }, 3000);
            }
        } else {
            alert(`Import failed: ${result.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error importing CSV:', error);
        alert('Failed to import CSV. Please check the file format and try again.');
    } finally {
        importBtn.disabled = false;
        importBtn.innerHTML = originalText;
    }
}

// ==================== View Switching ====================

function showView(view) {
    if (view === 'contacts') {
        window.location.href = '/crm';
    } else if (view === 'companies') {
        window.location.href = '/crm/companies';
    } else if (view === 'campaigns') {
        window.location.href = '/crm/campaigns';
    }
}



// ==================== AI Pitch Generator ====================

async function generatePitch(contactId) {
    try {
        // Convert to string for comparison since IDs might be strings
        const contact = contacts.find(c => String(c.id) === String(contactId));
        if (!contact) {
            console.error('Contact not found. ID:', contactId, 'Type:', typeof contactId);
            console.log('Available contacts:', contacts.slice(0, 3).map(c => ({ id: c.id, type: typeof c.id })));
            alert('Contact not found');
            return;
        }

        // Show loading modal
        showPitchModal(contact, null, true);

        // Call API to generate pitch - convert to integer
        const response = await fetch('/api/ai/generate-pitch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contact_id: parseInt(contactId, 10),  // Ensure it's an integer
                pitch_type: 'connection_request'
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Show generated pitch in modal with search context
            showPitchModal(contact, data.pitch, false, data.search_context);
        } else {
            alert(`Error generating pitch: ${data.detail || 'Unknown error'}`);
            closePitchModal();
        }

    } catch (error) {
        console.error('Error generating pitch:', error);
        alert(`Error: ${error.message}`);
        closePitchModal();
    }
}

function showPitchModal(contact, pitch, loading, searchContext) {
    // Create modal HTML
    const modalHTML = `
        <div id="pitch-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onclick="if(event.target.id==='pitch-modal') closePitchModal()">
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4" onclick="event.stopPropagation()">
                <!-- Header -->
                <div class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-t-lg">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <i class="fas fa-magic text-2xl"></i>
                            <div>
                                <h3 class="text-xl font-bold">AI Sales Pitch Generator</h3>
                                <p class="text-sm text-purple-100">Personalized for ${escapeHtml(contact.name)}</p>
                            </div>
                        </div>
                        <button onclick="closePitchModal()" class="text-white hover:text-gray-200">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                </div>

                <!-- Body -->
                <div class="p-6">
                    ${loading ? `
                        <div class="text-center py-12">
                            <i class="fas fa-spinner fa-spin text-4xl text-purple-600 mb-4"></i>
                            <p class="text-gray-600">AI is crafting a personalized pitch...</p>
                            <p class="text-sm text-gray-500 mt-2">Analyzing ${escapeHtml(contact.title)} at ${escapeHtml(contact.company || contact.company_name)}</p>
                        </div>
                    ` : `
                        <!-- Contact Info -->
                        <div class="bg-gray-50 rounded-lg p-4 mb-4">
                            <div class="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span class="text-gray-500">Name:</span>
                                    <span class="font-medium ml-2">${escapeHtml(contact.name)}</span>
                                </div>
                                <div>
                                    <span class="text-gray-500">Title:</span>
                                    <span class="font-medium ml-2">${escapeHtml(contact.title || 'N/A')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-500">Company:</span>
                                    <span class="font-medium ml-2">${escapeHtml(contact.company || contact.company_name || 'N/A')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-500">Length:</span>
                                    <span class="font-medium ml-2">${pitch ? pitch.length : 0} characters</span>
                                </div>
                            </div>
                        </div>

                        <!-- Generated Pitch -->
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Generated Sales Pitch
                            </label>
                            <textarea 
                                id="generated-pitch-text"
                                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                                rows="8"
                                readonly
                            >${pitch || ''}</textarea>
                        </div>

                        <!-- Actions -->
                        <div class="flex items-center justify-between">
                            <div class="flex space-x-2">
                                <button 
                                    onclick="copyPitchToClipboard()"
                                    class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                                >
                                    <i class="fas fa-copy mr-2"></i>Copy to Clipboard
                                </button>
                                <button 
                                    onclick="regeneratePitch(${contact.id})"
                                    class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                                >
                                    <i class="fas fa-sync mr-2"></i>Regenerate
                                </button>
                            </div>
                            <button 
                                onclick="closePitchModal()"
                                class="px-4 py-2 text-gray-600 hover:text-gray-800"
                            >
                                Close
                            </button>
                        </div>

                        <!-- Tips -->
                        <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                            <p class="text-sm text-blue-800">
                                <i class="fas fa-lightbulb mr-2"></i>
                                <strong>Pro Tip:</strong> Personalize this further by mentioning a recent post or achievement you saw on their LinkedIn profile.
                            </p>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existing = document.getElementById('pitch-modal');
    if (existing) existing.remove();

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closePitchModal() {
    const modal = document.getElementById('pitch-modal');
    if (modal) modal.remove();
}

function copyPitchToClipboard() {
    const textarea = document.getElementById('generated-pitch-text');
    if (textarea) {
        textarea.select();
        document.execCommand('copy');
        
        // Show feedback
        const btn = event.target.closest('button');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check mr-2"></i>Copied!';
        btn.classList.add('bg-green-600');
        btn.classList.remove('bg-purple-600');
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('bg-green-600');
            btn.classList.add('bg-purple-600');
        }, 2000);
    }
}

async function regeneratePitch(contactId) {
    // Just call generatePitch again
    await generatePitch(contactId);
}


// ==================== Clear Database ====================

async function clearDatabase() {
    const confirmed = confirm(
        '⚠️ WARNING: This will delete ALL contacts and companies from the database!\n\n' +
        'This action cannot be undone.\n\n' +
        'Are you sure you want to continue?'
    );
    
    if (!confirmed) return;
    
    // Double confirmation
    const doubleConfirm = confirm(
        'Are you ABSOLUTELY sure?\n\n' +
        'Type YES in the next prompt to confirm.'
    );
    
    if (!doubleConfirm) return;
    
    const finalConfirm = prompt('Type YES to confirm deletion:');
    
    if (finalConfirm !== 'YES') {
        alert('Cancelled. Database was not cleared.');
        return;
    }
    
    try {
        const response = await fetch('/api/database/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✅ Database cleared!\n\nDeleted:\n- ${data.contacts_deleted} contacts\n- ${data.companies_deleted} companies`);
            await loadContacts();
        } else {
            alert(`❌ Error: ${data.detail || 'Failed to clear database'}`);
        }
    } catch (error) {
        console.error('Error clearing database:', error);
        alert(`❌ Error: ${error.message}`);
    }
}
