// SnapQuote Dashboard JavaScript
let processingChart = null;

// API Base URL
const API_BASE = window.location.origin;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    
    // Set up auto-refresh every 30 seconds
    setInterval(refreshDashboard, 30000);
});

async function initializeDashboard() {
    try {
        await refreshDashboard();
        initializeChart();
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

async function refreshDashboard() {
    await Promise.all([
        refreshStats(),
        refreshEmails(),
        refreshActivity(),
        updateLastRefresh()
    ]);
}

async function refreshStats() {
    try {
        const response = await fetch(`${API_BASE}/api/emails/stats`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalEmails').textContent = data.stats.total_emails;
            document.getElementById('validQuotations').textContent = data.stats.valid_quotations;
            document.getElementById('irrelevantEmails').textContent = data.stats.irrelevant_emails;
            
            // Update chart data
            updateChart(data.stats);
        }
        
        // Get reprocess queue count
        const reprocessResponse = await fetch(`${API_BASE}/api/reprocess/queue`);
        const reprocessData = await reprocessResponse.json();
        
        if (reprocessData.success) {
            document.getElementById('reprocessQueue').textContent = reprocessData.count;
        }
        
    } catch (error) {
        console.error('Failed to refresh stats:', error);
    }
}

async function refreshEmails() {
    try {
        const response = await fetch(`${API_BASE}/api/emails`);
        const data = await response.json();
        
        if (data.success) {
            updateEmailTable(data.data);
        }
    } catch (error) {
        console.error('Failed to refresh emails:', error);
    }
}

async function refreshActivity() {
    try {
        const response = await fetch(`${API_BASE}/api/monitoring/status`);
        const data = await response.json();
        
        if (data.success) {
            updateRecentActivity(data.monitoring);
        }
    } catch (error) {
        console.error('Failed to refresh activity:', error);
    }
}

function updateEmailTable(emails) {
    const tableBody = document.getElementById('emailTableBody');
    
    if (!emails || emails.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No emails found
                </td>
            </tr>
        `;
        return;
    }
    
    const rows = emails.slice(0, 10).map(email => {
        const status = getStatusBadge(email.extraction_status);
        const receivedDate = formatDate(email.received_at);
        const subject = truncateText(email.subject || 'No Subject', 50);
        const sender = truncateText(email.sender || 'Unknown', 30);
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${subject}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${sender}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${status}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${receivedDate}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex space-x-2">
                        ${email.extraction_status === 'VALID' ? 
                            `<button onclick="generateQuotation('${email.gmail_id}')" 
                                class="text-indigo-600 hover:text-indigo-900">
                                <i class="fas fa-download"></i> Excel
                            </button>` : 
                            ''
                        }
                        <button onclick="markForReprocess('${email.gmail_id}')" 
                            class="text-blue-600 hover:text-blue-900">
                            <i class="fas fa-redo"></i> Reprocess
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    tableBody.innerHTML = rows;
}

function getStatusBadge(status) {
    switch (status) {
        case 'VALID':
            return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <i class="fas fa-check-circle mr-1"></i> Valid
                    </span>`;
        case 'IRRELEVANT':
            return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        <i class="fas fa-times-circle mr-1"></i> Irrelevant
                    </span>`;
        case 'NOT_VALID':
            return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <i class="fas fa-exclamation-circle mr-1"></i> Invalid
                    </span>`;
        default:
            return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        <i class="fas fa-question-circle mr-1"></i> Unknown
                    </span>`;
    }
}

function updateRecentActivity(monitoring) {
    const activityDiv = document.getElementById('recentActivity');
    
    const activities = [
        {
            icon: 'fas fa-sync-alt',
            color: 'text-blue-600',
            text: `Last check: ${formatTime(monitoring.last_check)}`,
            time: 'Now'
        },
        {
            icon: 'fas fa-server',
            color: 'text-green-600',
            text: `System status: ${monitoring.system_status}`,
            time: '1m ago'
        },
        {
            icon: 'fas fa-chart-line',
            color: 'text-indigo-600',
            text: `Emails processed today: ${monitoring.emails_processed_today}`,
            time: '5m ago'
        }
    ];
    
    activityDiv.innerHTML = activities.map(activity => `
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <i class="${activity.icon} ${activity.color} mr-3"></i>
                <span class="text-sm text-gray-900">${activity.text}</span>
            </div>
            <span class="text-xs text-gray-500">${activity.time}</span>
        </div>
    `).join('');
}

function initializeChart() {
    const ctx = document.getElementById('processingChart').getContext('2d');
    
    processingChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Valid Quotations', 'Irrelevant Emails', 'Invalid Emails'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#10b981', // Green
                    '#6b7280', // Gray
                    '#ef4444'  // Red
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function updateChart(stats) {
    if (processingChart) {
        processingChart.data.datasets[0].data = [
            stats.valid_quotations,
            stats.irrelevant_emails,
            stats.total_emails - stats.valid_quotations - stats.irrelevant_emails
        ];
        processingChart.update();
    }
}

async function generateQuotation(gmailId) {
    try {
        showNotification('Generating Excel quotation...', 'info');
        
        const response = await fetch(`${API_BASE}/api/quotation/generate/${gmailId}`);
        
        if (response.ok) {
            // Trigger download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `quotation_${gmailId}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            showNotification('Excel quotation downloaded successfully!', 'success');
        } else {
            const errorData = await response.json();
            showNotification(`Failed to generate quotation: ${errorData.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to generate quotation:', error);
        showNotification('Failed to generate quotation', 'error');
    }
}

async function markForReprocess(gmailId) {
    try {
        const response = await fetch(`${API_BASE}/api/reprocess/add/${gmailId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Email marked for reprocessing', 'success');
            await refreshStats(); // Refresh to update reprocess queue count
        } else {
            showNotification(`Failed to mark for reprocess: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to mark for reprocess:', error);
        showNotification('Failed to mark for reprocess', 'error');
    }
}

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-100 text-green-800 border-green-200',
        error: 'bg-red-100 text-red-800 border-red-200',
        info: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-2 rounded-md border ${colors[type]} z-50 transition-opacity duration-300`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}

function showError(message) {
    showNotification(message, 'error');
}

function updateLastRefresh() {
    document.getElementById('lastUpdate').textContent = `Last updated: ${formatTime(new Date())}`;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function formatTime(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}