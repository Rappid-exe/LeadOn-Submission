// Companies Page JavaScript
const API_BASE = 'http://localhost:8000';

let companies = [];

// Helper function to get color for relationship stage
function getStageColor(stage) {
    const colors = {
        'prospect': 'bg-gray-100 text-gray-800',
        'contacted': 'bg-blue-100 text-blue-800',
        'qualified': 'bg-green-100 text-green-800',
        'customer': 'bg-purple-100 text-purple-800',
        'partner': 'bg-yellow-100 text-yellow-800',
        'lost': 'bg-red-100 text-red-800'
    };
    return colors[stage.toLowerCase()] || 'bg-gray-100 text-gray-800';
}

document.addEventListener('DOMContentLoaded', () => {
    loadCompanies();
});

async function loadCompanies() {
    try {
        const response = await fetch(`${API_BASE}/api/companies`);
        const data = await response.json();

        companies = data.companies || [];

        document.getElementById('loading').classList.add('hidden');

        if (companies.length === 0) {
            document.getElementById('empty-state').classList.remove('hidden');
        } else {
            renderCompaniesTable();
        }
    } catch (error) {
        console.error('Error loading companies:', error);
        document.getElementById('loading').innerHTML = '<p class="text-red-500">Error loading companies</p>';
    }
}

async function syncContactsForAllCompanies() {
    if (!confirm('This will search Apollo for 1 decision-maker (CEO/Director) at each company. Continue?')) {
        return;
    }

    const loadingMsg = document.createElement('div');
    loadingMsg.id = 'sync-loading';
    loadingMsg.className = 'fixed top-4 right-4 bg-indigo-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    loadingMsg.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Syncing contacts for companies...';
    document.body.appendChild(loadingMsg);

    try {
        const response = await fetch(`${API_BASE}/api/companies/sync-contacts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok) {
            alert(`✅ Success! Added ${result.contacts_added} new contacts from ${result.companies_processed} companies.`);
            loadCompanies(); // Reload to show updated contact counts
        } else {
            alert(`❌ Error: ${result.detail || 'Failed to sync contacts'}`);
        }
    } catch (error) {
        console.error('Error syncing contacts:', error);
        alert('❌ Error syncing contacts. Check console for details.');
    } finally {
        document.getElementById('sync-loading')?.remove();
    }
}

function renderCompaniesTable() {
    const tbody = document.getElementById('companies-table-body');
    
    tbody.innerHTML = companies.map(company => `
        <tr class="table-row">
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <div>
                        <div class="text-sm font-medium text-gray-900">${escapeHtml(company.name)}</div>
                        ${company.linkedin_url ? `
                            <a href="${escapeHtml(company.linkedin_url)}" target="_blank" class="text-xs text-blue-600 hover:underline">
                                <i class="fab fa-linkedin mr-1"></i>LinkedIn
                            </a>
                        ` : ''}
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 text-sm">
                ${company.tags && company.tags.length > 0 ? `
                    <div class="flex flex-wrap gap-1">
                        ${company.tags.slice(0, 3).map(tag => `
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                ${escapeHtml(tag)}
                            </span>
                        `).join('')}
                        ${company.tags.length > 3 ? `
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                +${company.tags.length - 3}
                            </span>
                        ` : ''}
                    </div>
                ` : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-6 py-4 text-sm">
                ${company.relationship_stage ? `
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStageColor(company.relationship_stage)}">
                        ${escapeHtml(company.relationship_stage)}
                    </span>
                ` : '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-6 py-4 text-sm text-gray-700">
                ${escapeHtml(company.employee_count) || '<span class="text-gray-400">—</span>'}
            </td>
            <td class="px-6 py-4 text-sm text-gray-700">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                    ${company.contact_count || 0} contacts
                </span>
            </td>
            <td class="px-6 py-4 text-sm">
                ${company.last_enriched_at ? `
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        <i class="fas fa-check-circle mr-1"></i>Enriched
                    </span>
                ` : `
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                        <i class="fas fa-circle mr-1"></i>Not enriched
                    </span>
                `}
            </td>
            <td class="px-6 py-4 text-sm">
                <button onclick="viewCompanyDetails(${company.id})" class="text-indigo-600 hover:text-indigo-900 mr-2" title="View details">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="enrichCompany(${company.id})" class="text-green-600 hover:text-green-900 mr-2" title="Enrich with AI">
                    <i class="fas fa-magic"></i>
                </button>
                <button onclick="enrichWithApollo(${company.id})" class="text-purple-600 hover:text-purple-900" title="Enrich with Apollo">
                    <i class="fas fa-database"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function filterCompanies() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    
    if (!searchTerm) {
        renderCompaniesTable();
        return;
    }
    
    const filtered = companies.filter(company => {
        return (
            company.name?.toLowerCase().includes(searchTerm) ||
            company.industry?.toLowerCase().includes(searchTerm) ||
            company.website?.toLowerCase().includes(searchTerm)
        );
    });
    
    const originalCompanies = companies;
    companies = filtered;
    renderCompaniesTable();
    companies = originalCompanies;
}

function syncCompanies() {
    loadCompanies();
}

function showCreateCompanyModal() {
    alert('Add Company feature coming soon! Companies are automatically added when you search for contacts.');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== Company Profile Functions ====================

let currentProfile = null;

async function showProfileModal() {
    document.getElementById('profile-modal').classList.remove('hidden');
    document.getElementById('profile-loading').classList.remove('hidden');
    document.getElementById('profile-form').classList.add('hidden');

    // Load existing profile
    try {
        const response = await fetch(`${API_BASE}/api/profile`);
        const data = await response.json();

        currentProfile = data.profile;

        document.getElementById('profile-loading').classList.add('hidden');
        document.getElementById('profile-form').classList.remove('hidden');

        if (currentProfile) {
            // Pre-fill form
            document.getElementById('profile-website').value = currentProfile.website_url || '';
            document.getElementById('profile-company-name').value = currentProfile.company_name || '';
            document.getElementById('profile-tagline').value = currentProfile.tagline || '';
            document.getElementById('profile-description').value = currentProfile.description || '';
            document.getElementById('profile-ai-summary').value = currentProfile.ai_summary || '';
            document.getElementById('profile-details').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        document.getElementById('profile-loading').innerHTML = '<p class="text-red-500">Error loading profile</p>';
    }
}

function closeProfileModal() {
    document.getElementById('profile-modal').classList.add('hidden');
}

async function analyzeWebsite() {
    const websiteUrl = document.getElementById('profile-website').value;

    if (!websiteUrl) {
        alert('Please enter a website URL');
        return;
    }

    const button = event.target;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';

    try {
        const response = await fetch(`${API_BASE}/api/profile/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ website_url: websiteUrl })
        });

        const data = await response.json();

        if (response.ok) {
            // Fill in the form with AI-generated data
            const profile = data.profile;
            document.getElementById('profile-company-name').value = profile.company_name || '';
            document.getElementById('profile-tagline').value = profile.tagline || '';
            document.getElementById('profile-description').value = profile.description || '';
            document.getElementById('profile-ai-summary').value = profile.ai_summary || '';
            document.getElementById('profile-details').classList.remove('hidden');

            alert('✅ Website analyzed successfully!');
        } else {
            alert(`❌ Error: ${data.detail || 'Failed to analyze website'}`);
        }
    } catch (error) {
        console.error('Error analyzing website:', error);
        alert('❌ Error analyzing website. Check console for details.');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-magic mr-2"></i>Analyze Website with AI';
    }
}

async function saveProfile() {
    alert('✅ Profile saved! (Profile is automatically saved when you analyze the website)');
    closeProfileModal();
}

// ==================== Company Enrichment Functions ====================

async function enrichCompany(companyId) {
    if (!confirm('Enrich this company with AI-powered insights?')) {
        return;
    }

    const loadingMsg = document.createElement('div');
    loadingMsg.id = 'enrich-loading';
    loadingMsg.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    loadingMsg.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Enriching company...';
    document.body.appendChild(loadingMsg);

    try {
        const response = await fetch(`${API_BASE}/api/companies/${companyId}/enrich`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
            alert('✅ Company enriched successfully!');
            loadCompanies(); // Reload to show enrichment status
        } else {
            alert(`❌ Error: ${data.detail || 'Failed to enrich company'}`);
        }
    } catch (error) {
        console.error('Error enriching company:', error);
        alert('❌ Error enriching company. Check console for details.');
    } finally {
        document.getElementById('enrich-loading')?.remove();
    }
}

async function enrichAllCompanies() {
    if (!confirm('This will enrich ALL companies with AI-powered insights. This may take a while and use API credits. Continue?')) {
        return;
    }

    const loadingMsg = document.createElement('div');
    loadingMsg.id = 'enrich-all-loading';
    loadingMsg.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    loadingMsg.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Enriching all companies...';
    document.body.appendChild(loadingMsg);

    try {
        const response = await fetch(`${API_BASE}/api/companies/enrich-all`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ Success! Enriched ${data.success} companies (${data.failure} failed)`);
            loadCompanies(); // Reload to show enrichment status
        } else {
            alert(`❌ Error: ${data.detail || 'Failed to enrich companies'}`);
        }
    } catch (error) {
        console.error('Error enriching companies:', error);
        alert('❌ Error enriching companies. Check console for details.');
    } finally {
        document.getElementById('enrich-all-loading')?.remove();
    }
}

async function viewCompanyDetails(companyId) {
    const company = companies.find(c => c.id === companyId);
    if (!company) return;

    document.getElementById('company-details-title').textContent = company.name;

    const content = document.getElementById('company-details-content');
    content.innerHTML = `
        <div class="space-y-4">
            <div>
                <h3 class="text-sm font-medium text-gray-500">Basic Information</h3>
                <div class="mt-2 space-y-2">
                    <p><strong>Industry:</strong> ${escapeHtml(company.industry) || '—'}</p>
                    <p><strong>Website:</strong> ${company.website ? `<a href="${escapeHtml(company.website)}" target="_blank" class="text-blue-600 hover:underline">${escapeHtml(company.website)}</a>` : '—'}</p>
                    <p><strong>Company Size:</strong> ${escapeHtml(company.employee_count) || '—'}</p>
                    <p><strong>Location:</strong> ${escapeHtml(company.location) || '—'}</p>
                    <p><strong>Relationship Stage:</strong> ${company.relationship_stage ? `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStageColor(company.relationship_stage)}">${escapeHtml(company.relationship_stage)}</span>` : '—'}</p>
                    ${company.founded_year ? `<p><strong>Founded:</strong> ${company.founded_year}</p>` : ''}
                    ${company.funding_stage ? `<p><strong>Funding Stage:</strong> ${escapeHtml(company.funding_stage)}</p>` : ''}
                    ${company.total_funding ? `<p><strong>Total Funding:</strong> ${escapeHtml(company.total_funding)}</p>` : ''}
                </div>
            </div>

            ${company.tags && company.tags.length > 0 ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Tags</h3>
                    <div class="mt-2 flex flex-wrap gap-2">
                        ${company.tags.map(tag => `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${escapeHtml(tag)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${company.technologies && company.technologies.length > 0 ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Technologies</h3>
                    <div class="mt-2 flex flex-wrap gap-2">
                        ${company.technologies.map(tech => `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                ${escapeHtml(tech)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${company.industry_analysis ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Industry Analysis</h3>
                    <p class="mt-2 text-gray-700">${escapeHtml(company.industry_analysis)}</p>
                </div>
            ` : ''}

            ${company.pain_points && company.pain_points.length > 0 ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Pain Points</h3>
                    <ul class="mt-2 list-disc list-inside space-y-1">
                        ${(Array.isArray(company.pain_points) ? company.pain_points : JSON.parse(company.pain_points)).map(p => `<li class="text-gray-700">${escapeHtml(p)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${company.value_proposition ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Value Proposition</h3>
                    <p class="mt-2 text-gray-700">${escapeHtml(company.value_proposition)}</p>
                </div>
            ` : ''}

            ${company.enrichment_notes ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500">Enrichment Notes</h3>
                    <p class="mt-2 text-gray-700 whitespace-pre-wrap">${escapeHtml(company.enrichment_notes)}</p>
                </div>
            ` : ''}

            ${!company.last_enriched_at ? `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p class="text-sm text-yellow-800">
                        <i class="fas fa-info-circle mr-2"></i>
                        This company has not been enriched yet. Click the magic wand icon to enrich with AI.
                    </p>
                </div>
            ` : ''}
        </div>
    `;

    document.getElementById('company-details-modal').classList.remove('hidden');
}

function closeCompanyDetailsModal() {
    document.getElementById('company-details-modal').classList.add('hidden');
}

async function enrichWithApollo(companyId) {
    if (!confirm('Enrich this company with Apollo API data? This will fetch company size, funding, technologies, and more.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/companies/${companyId}/enrich-apollo`, {
            method: 'POST'
        });

        if (response.ok) {
            alert('Company enriched successfully with Apollo!');
            loadCompanies(); // Reload to show updated data
        } else {
            const error = await response.json();
            alert(`Failed to enrich company: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error enriching company with Apollo:', error);
        alert('Error enriching company with Apollo');
    }
}

async function enrichAllWithApollo() {
    if (!confirm('Enrich all companies with Apollo API data? This may take a while and use Apollo credits.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/companies/enrich-all-apollo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        if (response.ok) {
            const result = await response.json();
            alert(result.message);
            loadCompanies(); // Reload to show updated data
        } else {
            const error = await response.json();
            alert(`Failed to enrich companies: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error enriching companies with Apollo:', error);
        alert('Error enriching companies with Apollo');
    }
}

