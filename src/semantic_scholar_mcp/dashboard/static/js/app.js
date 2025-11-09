// Dashboard Application JavaScript

// Global state
let autoScroll = true;
let logIndex = 0;
let refreshInterval = null;
let fieldChart = null;
let timelineChart = null;

// Theme management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// API calls
async function fetchLogs() {
    try {
        const response = await fetch('/api/logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_idx: logIndex })
        });
        const data = await response.json();

        if (data.messages && data.messages.length > 0) {
            appendLogs(data.messages);
            logIndex = data.max_idx + 1;
        }
    } catch (error) {
        console.error('Failed to fetch logs:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        updateStats(data.summary, data.tool_stats);
    } catch (error) {
        console.error('Failed to fetch stats:', error);
    }
}

async function fetchAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        updateAnalytics(data);
    } catch (error) {
        console.error('Failed to fetch analytics:', error);
    }
}

async function fetchPerformance() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();
        updatePerformance(data);
    } catch (error) {
        console.error('Failed to fetch performance:', error);
    }
}

async function clearStats() {
    try {
        await fetch('/api/stats/clear', { method: 'POST' });
        location.reload();
    } catch (error) {
        console.error('Failed to clear stats:', error);
    }
}

// UI updates
function appendLogs(messages) {
    const logViewer = document.getElementById('log-viewer');

    // Remove placeholder if present
    const placeholder = logViewer.querySelector('.log-placeholder');
    if (placeholder) {
        placeholder.remove();
    }

    messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'log-message';

        // Detect log level
        if (msg.includes('ERROR')) {
            div.classList.add('error');
        } else if (msg.includes('WARNING')) {
            div.classList.add('warning');
        } else if (msg.includes('INFO')) {
            div.classList.add('info');
        } else {
            div.classList.add('debug');
        }

        div.textContent = msg;
        logViewer.appendChild(div);
    });

    // Auto-scroll to bottom
    if (autoScroll) {
        logViewer.scrollTop = logViewer.scrollHeight;
    }
}

function updateStats(summary, toolStats) {
    // Update header
    const uptime = Math.floor(summary.uptime_seconds);
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = uptime % 60;
    document.getElementById('uptime').textContent =
        `Uptime: ${hours}h ${minutes}m ${seconds}s`;
    document.getElementById('total-calls').textContent =
        `Calls: ${summary.total_tool_calls}`;

    // Update stat cards
    document.getElementById('stat-total-calls').textContent =
        summary.total_tool_calls;
    document.getElementById('stat-total-errors').textContent =
        summary.total_errors;
    document.getElementById('stat-cache-rate').textContent =
        `${summary.cache_hit_rate.toFixed(1)}%`;
    document.getElementById('stat-pdf-count').textContent =
        summary.pdf_conversions;

    // Update tool stats
    updateToolStats(toolStats);
}

function updateToolStats(toolStats) {
    const container = document.getElementById('tool-stats-container');

    if (Object.keys(toolStats).length === 0) {
        container.innerHTML =
            '<div class="stats-placeholder">No tool statistics available yet</div>';
        return;
    }

    container.innerHTML = '';

    // Sort tools by call count
    const sortedTools = Object.entries(toolStats)
        .sort((a, b) => b[1].calls - a[1].calls);

    sortedTools.forEach(([toolName, stats]) => {
        const div = document.createElement('div');
        div.className = 'tool-stat-item';

        div.innerHTML = `
            <div class="tool-stat-header">${toolName}</div>
            <div class="tool-stat-details">
                <div class="tool-stat-metric">
                    <span>Calls:</span>
                    <span>${stats.calls}</span>
                </div>
                <div class="tool-stat-metric">
                    <span>Errors:</span>
                    <span>${stats.errors}</span>
                </div>
                <div class="tool-stat-metric">
                    <span>Success Rate:</span>
                    <span>${stats.success_rate.toFixed(1)}%</span>
                </div>
                <div class="tool-stat-metric">
                    <span>Avg Time:</span>
                    <span>${(stats.avg_time * 1000).toFixed(0)}ms</span>
                </div>
            </div>
        `;

        container.appendChild(div);
    });
}

function updateAnalytics(data) {
    // Update top queries
    const queriesList = document.getElementById('top-queries-list');
    queriesList.innerHTML = '';

    if (data.top_queries.length === 0) {
        queriesList.innerHTML = '<li class="placeholder">No queries yet</li>';
    } else {
        data.top_queries.forEach(([query, count]) => {
            const li = document.createElement('li');
            li.innerHTML = `<span>${query}</span><span>${count}</span>`;
            queriesList.appendChild(li);
        });
    }

    // Update top papers
    const papersList = document.getElementById('top-papers-list');
    papersList.innerHTML = '';

    if (data.top_papers.length === 0) {
        papersList.innerHTML = '<li class="placeholder">No papers yet</li>';
    } else {
        data.top_papers.forEach(([paperId, count]) => {
            const li = document.createElement('li');
            // Truncate long paper IDs
            const displayId = paperId.length > 20 ?
                paperId.substring(0, 20) + '...' : paperId;
            li.innerHTML = `<span>${displayId}</span><span>${count}</span>`;
            li.title = paperId; // Full ID on hover
            papersList.appendChild(li);
        });
    }

    // Update field distribution chart
    updateFieldChart(data.field_distribution);
}

function updateFieldChart(fieldDistribution) {
    const ctx = document.getElementById('field-chart').getContext('2d');

    // Prepare data
    const labels = Object.keys(fieldDistribution);
    const values = Object.values(fieldDistribution);

    if (labels.length === 0) {
        return;
    }

    // Destroy existing chart
    if (fieldChart) {
        fieldChart.destroy();
    }

    // Create new chart
    fieldChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#2563eb', '#10b981', '#f59e0b', '#ef4444',
                    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function updatePerformance(data) {
    document.getElementById('perf-cache-rate').textContent =
        `${data.cache_hit_rate.toFixed(1)}%`;
    document.getElementById('perf-pdf-cache-rate').textContent =
        `${data.pdf_cache_hit_rate.toFixed(1)}%`;

    updateTimelineChart(data.timeline);
}

function updateTimelineChart(timeline) {
    const ctx = document.getElementById('timeline-chart').getContext('2d');

    if (timeline.length === 0) {
        return;
    }

    // Prepare data - group by minute
    const minuteData = {};
    timeline.forEach(call => {
        const minute = Math.floor(call.timestamp / 60) * 60;
        if (!minuteData[minute]) {
            minuteData[minute] = { count: 0, totalTime: 0 };
        }
        minuteData[minute].count += 1;
        minuteData[minute].totalTime += call.duration;
    });

    const labels = Object.keys(minuteData).map(ts => {
        const date = new Date(parseInt(ts) * 1000);
        return date.toLocaleTimeString();
    });

    const counts = Object.values(minuteData).map(d => d.count);

    // Destroy existing chart
    if (timelineChart) {
        timelineChart.destroy();
    }

    // Create new chart
    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'API Calls per Minute',
                data: counts,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();

    // Theme toggle button
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Load logs button
    document.getElementById('load-logs').addEventListener('click', fetchLogs);

    // Auto-scroll toggle
    document.getElementById('auto-scroll-toggle').addEventListener('click', () => {
        autoScroll = !autoScroll;
        document.getElementById('auto-scroll-toggle').textContent =
            `Auto-scroll: ${autoScroll ? 'ON' : 'OFF'}`;
    });

    // Initial data fetch
    fetchStats();
    fetchAnalytics();
    fetchPerformance();

    // Set up auto-refresh (every 5 seconds)
    refreshInterval = setInterval(() => {
        fetchStats();
        fetchAnalytics();
        fetchPerformance();
    }, 5000);
});
