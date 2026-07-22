// ALM RCA Web Application - Client-side JavaScript

let currentFile = null;
let currentFilepath = null;
let sessionId = null;
let analysisResults = null;
let reportFilenames = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeDropZone();
    initializeFileInput();
});

// Drop Zone Functionality
function initializeDropZone() {
    const dropZone = document.getElementById('drop-zone');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        }, false);
    });
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    // Only trigger file input on drop zone click, not on button click
    dropZone.addEventListener('click', (e) => {
        // Don't trigger if clicking the browse button
        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
            return;
        }
        document.getElementById('file-input').click();
    });
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File Input Functionality
function initializeFileInput() {
    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

function handleFile(file) {
    // Validate file type
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    const allowedExtensions = ['.csv', '.xls', '.xlsx'];
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showError('Invalid file type. Please upload a CSV or Excel file.');
        return;
    }
    
    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        showError('File too large. Maximum size is 16MB.');
        return;
    }
    
    currentFile = file;
    displayFileInfo(file);
}

function displayFileInfo(file) {
    const fileInfoBox = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    fileInfoBox.style.display = 'flex';
    analyzeBtn.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function clearFile() {
    currentFile = null;
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('analyze-btn').style.display = 'none';
    document.getElementById('file-input').value = '';
}

// Analysis Workflow
async function startAnalysis() {
    if (!currentFile) {
        showError('No file selected');
        return;
    }
    
    // Hide upload section, show progress
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('progress-section').style.display = 'block';
    
    try {
        // Step 1: Upload file
        updateProgress(25, 'Uploading file...', 'upload');
        const uploadResult = await uploadFile(currentFile);
        sessionId = uploadResult.session_id;
        currentFilepath = uploadResult.filepath;
        
        // Step 2: Analyze data
        updateProgress(50, 'Analyzing defects...', 'analyze');
        await sleep(500);
        const analysisResult = await analyzeData(sessionId, uploadResult.filepath);
        analysisResults = analysisResult.results;
        
        // Step 3: Generate reports
        updateProgress(75, 'Generating reports...', 'report');
        await sleep(500);
        const reportResult = await generateReports(sessionId, uploadResult.filepath);
        reportFilenames = {
            summary: reportResult.summary_report,
            json: reportResult.json_export,
            html: null   // generated on demand via /generate-html-report
        };
        
        // Step 4: Complete
        updateProgress(100, 'Analysis complete!', 'complete');
        await sleep(1000);
        
        // Show results
        displayResults();
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message || 'An error occurred during analysis');
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
    }
    
    return await response.json();
}

async function analyzeData(sessionId, filepath) {
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId, filepath: filepath })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Analysis failed');
    }
    
    return await response.json();
}

async function generateReports(sessionId, filepath) {
    const response = await fetch('/generate-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId, filepath: filepath })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Report generation failed');
    }
    
    return await response.json();
}

function updateProgress(percentage, text, step) {
    document.getElementById('progress-fill').style.width = percentage + '%';
    document.getElementById('progress-text').textContent = text;
    
    // Update step indicators
    const steps = ['upload', 'analyze', 'report', 'complete'];
    const currentIndex = steps.indexOf(step);
    
    steps.forEach((s, index) => {
        const stepElement = document.getElementById(`step-${s}`);
        if (index < currentIndex) {
            stepElement.classList.add('completed');
            stepElement.classList.remove('active');
        } else if (index === currentIndex) {
            stepElement.classList.add('active');
            stepElement.classList.remove('completed');
        } else {
            stepElement.classList.remove('active', 'completed');
        }
    });
}

// Display Results
function displayResults() {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    
    // Update summary statistics
    document.getElementById('total-defects').textContent = analysisResults.total_defects || 0;
    document.getElementById('high-severity').textContent = analysisResults.summary?.high_severity || 0;
    document.getElementById('open-defects').textContent = analysisResults.summary?.open || 0;
    document.getElementById('rca-needed').textContent = analysisResults.rca_candidates?.length || 0;
    
    // Create charts
    createSeverityChart();
    createStatusChart();
    createModuleChart();
    
    // Display RCA candidates
    displayRCACandidates();
    
    // Display preventive measures
    displayPreventiveMeasures();
}

function createSeverityChart() {
    const ctx = document.getElementById('severity-chart').getContext('2d');
    const data = analysisResults.severity_distribution || {};
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Defects',
                data: Object.values(data),
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(16, 185, 129, 0.8)'
                ],
                borderColor: [
                    'rgb(239, 68, 68)',
                    'rgb(245, 158, 11)',
                    'rgb(251, 191, 36)',
                    'rgb(16, 185, 129)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createStatusChart() {
    const ctx = document.getElementById('status-chart').getContext('2d');
    const data = analysisResults.status_distribution || {};
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createModuleChart() {
    const ctx = document.getElementById('module-chart').getContext('2d');
    const data = analysisResults.module_distribution || {};
    
    // Check if we have module data
    if (Object.keys(data).length === 0) {
        // No module data - show message
        const chartContainer = document.getElementById('module-chart').parentElement;
        chartContainer.innerHTML = `
            <h3>Defects by Module/Area</h3>
            <div style="text-align: center; padding: 2rem; color: #6b7280;">
                <p>📊 No module/area data available in the uploaded file.</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">
                    To see this chart, include a "Module", "Component", or "Area" column in your defect file.
                </p>
            </div>
        `;
        return;
    }
    
    // Get top 10 modules
    const sortedModules = Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    const labels = sortedModules.map(([module]) => module);
    const values = sortedModules.map(([, count]) => count);
    
    // Generate colors for pie chart
    const colors = [
        'rgba(239, 68, 68, 0.8)',   // red
        'rgba(245, 158, 11, 0.8)',  // orange
        'rgba(251, 191, 36, 0.8)',  // yellow
        'rgba(16, 185, 129, 0.8)',  // green
        'rgba(59, 130, 246, 0.8)',  // blue
        'rgba(139, 92, 246, 0.8)',  // purple
        'rgba(236, 72, 153, 0.8)',  // pink
        'rgba(20, 184, 166, 0.8)',  // teal
        'rgba(251, 146, 60, 0.8)',  // amber
        'rgba(168, 85, 247, 0.8)'   // violet
    ];
    
    // Use pie chart if 5 or fewer modules, otherwise horizontal bar
    const chartType = sortedModules.length <= 5 ? 'pie' : 'bar';
    
    new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: 'Defects',
                data: values,
                backgroundColor: chartType === 'pie' ? colors : 'rgba(59, 130, 246, 0.8)',
                borderColor: chartType === 'pie' ? colors.map(c => c.replace('0.8', '1')) : 'rgb(59, 130, 246)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: chartType === 'pie' ? false : true,
            indexAxis: chartType === 'bar' ? 'y' : undefined,
            plugins: {
                legend: {
                    display: chartType === 'pie',
                    position: 'bottom',
                    align: 'center',
                    labels: {
                        padding: 15,
                        boxWidth: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                title: {
                    display: true,
                    text: `Top ${sortedModules.length} Affected Modules/Areas`,
                    padding: {
                        top: 5,
                        bottom: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed.y || context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} defects (${percentage}%)`;
                        }
                    }
                }
            },
            layout: chartType === 'pie' ? {
                padding: {
                    left: 20,
                    right: 20,
                    top: 10,
                    bottom: 5
                }
            } : undefined,
            scales: chartType === 'bar' ? {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            } : undefined
        }
    });
}

function displayRCACandidates() {
    const candidatesList = document.getElementById('candidates-list');
    const candidates = analysisResults.rca_candidates || [];
    const rcaCount = document.getElementById('rca-count');
    const totalRcaDefects = analysisResults.total_rca_defects || candidates.length;
    const groupedCount = analysisResults.grouped_count || 0;
    const standaloneCount = analysisResults.standalone_count || 0;
    
    if (rcaCount) {
        if (groupedCount > 0 && standaloneCount > 0) {
            rcaCount.textContent = `${candidates.length} defects (${groupedCount} grouped + ${standaloneCount} standalone)`;
        } else {
            rcaCount.textContent = `${candidates.length} defects`;
        }
    }
    
    if (candidates.length === 0) {
        candidatesList.innerHTML = '<p style="text-align: center; color: #6b7280;">✅ No high-severity defects require RCA at this time.</p>';
        return;
    }
    
    candidatesList.innerHTML = candidates.map(candidate => `
        <div class="candidate-item">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div>
                    <div class="candidate-id">${candidate.id}</div>
                    ${candidate.module ? `<div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">📁 ${candidate.module}</div>` : ''}
                </div>
                <span class="candidate-severity ${getSeverityClass(candidate.severity)}">${candidate.severity}</span>
            </div>
            <div class="candidate-summary">${candidate.summary}</div>
            ${candidate.group_size > 1 ? `
                <div style="margin-top: 0.75rem; padding: 0.5rem; background: #fef3c7; border-left: 3px solid #f59e0b; border-radius: 4px; font-size: 0.875rem;">
                    <strong>🔗 Pattern Detected:</strong> ${getPatternName(candidate.group_key)} - Group of ${candidate.group_size} similar defects
                    ${candidate.similar_defects && candidate.similar_defects.length > 0 ? `
                        <div style="margin-top: 0.5rem; color: #92400e;">
                            <strong>Similar defects:</strong> ${candidate.similar_defects.slice(0, 5).join(', ')}${candidate.similar_defects.length > 5 ? ` +${candidate.similar_defects.length - 5} more` : ''}
                        </div>
                    ` : ''}
                </div>
            ` : `
                <div style="margin-top: 0.75rem; padding: 0.5rem; background: #f3f4f6; border-radius: 4px; font-size: 0.875rem; color: #6b7280;">
                    ℹ️ Standalone defect - no similar patterns detected
                </div>
            `}
        </div>
    `).join('');
}

function displayPreventiveMeasures() {
    try {
        const measuresList = document.getElementById('preventive-measures-list');
        
        if (!measuresList) {
            console.error('preventive-measures-list element not found!');
            return;
        }
        
        const measures = analysisResults.preventive_measures || [];
        
        if (!measures || measures.length === 0) {
            measuresList.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #6b7280;">
                    <p style="font-size: 1.1rem; margin-bottom: 1rem;">ℹ️ No grouped defect patterns detected</p>
                    <p>Preventive measures are generated when similar defects are found. Since all defects are standalone, focus on individual RCA for each defect.</p>
                </div>
            `;
            return;
        }
        
        const html = measures.map(measure => `
        <div class="measure-category">
            <div class="measure-header">
                <span class="measure-icon">${measure.icon || '📋'}</span>
                <h4>${measure.category}</h4>
                ${measure.affected_count ? `<span class="measure-badge">${measure.affected_count} defects</span>` : ''}
            </div>
            
            ${measure.modules && measure.modules.length > 0 ? `
                <div class="measure-modules">
                    <strong>Affected Modules:</strong> ${measure.modules.join(', ')}
                </div>
            ` : ''}
            
            ${measure.five_whys ? `
                <div class="five-whys-section" style="background: #f9fafb; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: #1f2937; margin-bottom: 0.75rem; font-size: 1rem;">🔍 5 WHYs Root Cause Analysis</h5>
                    <div style="padding-left: 1rem; border-left: 3px solid #3b82f6;">
                        <div style="margin-bottom: 0.5rem;">
                            <strong>1. ${measure.five_whys.why1}</strong><br>
                            <span style="color: #6b7280;">→ ${measure.five_whys.answer1}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong>2. ${measure.five_whys.why2}</strong><br>
                            <span style="color: #6b7280;">→ ${measure.five_whys.answer2}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong>3. ${measure.five_whys.why3}</strong><br>
                            <span style="color: #6b7280;">→ ${measure.five_whys.answer3}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong>4. ${measure.five_whys.why4}</strong><br>
                            <span style="color: #6b7280;">→ ${measure.five_whys.answer4}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong>5. ${measure.five_whys.why5}</strong><br>
                            <span style="color: #6b7280;">→ ${measure.five_whys.root_cause}</span>
                        </div>
                        <div style="margin-top: 1rem; padding: 0.75rem; background: #fef3c7; border-radius: 6px;">
                            <strong style="color: #92400e;">🎯 ROOT CAUSE:</strong><br>
                            <span style="color: #78350f;">${measure.five_whys.root_cause}</span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            ${measure.immediate_actions ? `
                <div style="margin: 1rem 0;">
                    <h5 style="color: #1f2937; margin-bottom: 0.5rem; font-size: 0.95rem;">⚡ Immediate Actions</h5>
                    <ul class="measure-list" style="margin-bottom: 0;">
                        ${measure.immediate_actions.map(m => `<li>${m}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${measure.long_term_prevention ? `
                <div style="margin: 1rem 0;">
                    <h5 style="color: #1f2937; margin-bottom: 0.5rem; font-size: 0.95rem;">📋 Long-term Prevention</h5>
                    <ul class="measure-list" style="margin-bottom: 0;">
                        ${measure.long_term_prevention.map(m => `<li>${m}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${!measure.immediate_actions && !measure.long_term_prevention && measure.measures ? `
                <ul class="measure-list">
                    ${measure.measures.map(m => `<li>${m}</li>`).join('')}
                </ul>
            ` : ''}
        </div>
    `).join('');
        
        measuresList.innerHTML = html;
        
    } catch (error) {
        console.error('Error in displayPreventiveMeasures:', error);
        const measuresList = document.getElementById('preventive-measures-list');
        if (measuresList) {
            measuresList.innerHTML = `<div style="color: red; padding: 2rem;">Error displaying measures: ${error.message}</div>`;
        }
    }
}

function getPatternName(groupKey) {
    if (!groupKey) return 'Similar Issues';
    
    // Extract the pattern from group_key (format: "Module_keyword")
    const parts = groupKey.split('_');
    if (parts.length < 2) return 'Similar Issues';
    
    const keyword = parts[parts.length - 1];
    const module = parts.slice(0, -1).join(' ');
    
    // Capitalize and format the keyword
    const patternNames = {
        'login': 'Login Issues',
        'password': 'Password Problems',
        'authentication': 'Authentication Failures',
        'timeout': 'Timeout Issues',
        'connection': 'Connection Problems',
        'error': 'Error Handling',
        'crash': 'System Crashes',
        'performance': 'Performance Issues',
        'slow': 'Slow Response',
        'loading': 'Loading Problems',
        'display': 'Display Issues',
        'button': 'Button Functionality',
        'link': 'Link Problems',
        'navigation': 'Navigation Issues',
        'search': 'Search Functionality',
        'filter': 'Filter Problems',
        'save': 'Save Functionality',
        'delete': 'Delete Operations',
        'update': 'Update Issues',
        'create': 'Create Operations',
        'validation': 'Validation Errors',
        'format': 'Format Issues',
        'data': 'Data Problems',
        'database': 'Database Issues',
        'api': 'API Problems',
        'integration': 'Integration Issues',
        'email': 'Email Functionality',
        'notification': 'Notification Problems'
    };
    
    const patternName = patternNames[keyword.toLowerCase()] || keyword.charAt(0).toUpperCase() + keyword.slice(1);
    
    if (module && module !== 'General') {
        return `${module} - ${patternName}`;
    }
    return patternName;
}

function getSeverityClass(severity) {
    const severityLower = severity.toLowerCase();
    if (severityLower.includes('high') || severityLower.includes('critical') || severityLower.includes('kritisk') || severityLower.includes('1 -') || severityLower.includes('1-')) {
        return 'severity-high';
    } else if (severityLower.includes('medium') || severityLower.includes('2 -') || severityLower.includes('2-') || severityLower.includes('3 -') || severityLower.includes('3-')) {
        return 'severity-medium';
    }
    return 'severity-low';
}

// Download Reports
async function downloadReport(type) {
    if (!reportFilenames) {
        alert('Report filenames not available. Please run analysis again.');
        return;
    }

    if (type === 'html') {
        // Generate PDF report on demand if not already done
        if (!reportFilenames.html) {
            try {
                const resp = await fetch('/generate-pdf-report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId, filepath: currentFilepath })
                });
                if (!resp.ok) {
                    const err = await resp.json();
                    alert('Failed to generate PDF report: ' + (err.error || 'Unknown error'));
                    return;
                }
                const data = await resp.json();
                reportFilenames.html = data.pdf_report;
            } catch (e) {
                alert('Error generating PDF report: ' + e.message);
                return;
            }
        }
        window.location.href = `/download/${reportFilenames.html}`;
        return;
    }

    let filename;
    if (type === 'summary') {
        filename = reportFilenames.summary;
    } else if (type === 'json') {
        filename = reportFilenames.json;
    }

    if (filename) {
        window.location.href = `/download/${filename}`;
    } else {
        alert('Report file not found.');
    }
}

// Error Handling
function showError(message) {
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

// Reset App
function resetApp() {
    currentFile = null;
    currentFilepath = null;
    sessionId = null;
    analysisResults = null;
    reportFilenames = null;
    
    document.getElementById('upload-section').style.display = 'block';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    
    clearFile();
}

// Utility Functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Made with Bob

// Tab Switching for Results
function switchResultTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    if (tabName === 'overview') {
        document.getElementById('overview-tab').classList.add('active');
        document.querySelector('.tab:nth-child(1)').classList.add('active');
    } else if (tabName === 'rca-candidates') {
        document.getElementById('rca-candidates-tab').classList.add('active');
        document.querySelector('.tab:nth-child(2)').classList.add('active');
    } else if (tabName === 'preventive-measures') {
        document.getElementById('preventive-measures-tab').classList.add('active');
        document.querySelector('.tab:nth-child(2)').classList.add('active');
    } else if (tabName === 'preventive-measures') {
        document.getElementById('preventive-measures-tab').classList.add('active');
        document.querySelector('.tab:nth-child(3)').classList.add('active');
    }
}
