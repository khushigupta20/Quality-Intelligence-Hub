// ═══════════════════════════════════════════════════════════════════════
// Quality Intelligence Hub — Unified Client-Side JavaScript
// ═══════════════════════════════════════════════════════════════════════

// ── Module-level State ────────────────────────────────────────────────
// RCA state
let rcaCurrentFile     = null;
let rcaCurrentFilepath = null;
let rcaSessionId       = null;
let rcaAnalysisResults = null;
let rcaPdfFilename     = null;
let rcaChartSeverity   = null;
let rcaChartStatus     = null;
let rcaChartModule     = null;

// Requirements state: { [taskId]: { fieldValues: {fieldId: string}, reply: '', error: '' } }
const reqState   = {};
// Requirements session history: [{ id, taskId, label, input, reply, timestamp }]
const reqHistory = [];

// Elapsed timer
let elapsedInterval = null;
let elapsedSeconds  = 0;


// ═══════════════════════════════════════════════════════════════════════
// INITIALISATION
// ═══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  wireNavigation();
  initRCADropZone();
  initRCAFileInput();
  showSection('home');
  loadSettings();
});


// ═══════════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════════

// Section ID mapping: nav data-section → full section element id
// e.g. 'req-translate' → 'section-req-translate'
// Note: sidebar nav for edge-cases uses 'req-edge-cases'
//       but the section id uses 'req-edge-cases' — however the
//       HTML textarea IDs use 'edge_cases' (underscore) for task_type
const SECTION_MAP = {
  'home':             'section-home',
  'rca':              'section-rca',
  'req-translate':    'section-req-translate',
  'req-analyze':      'section-req-analyze',
  'req-edge-cases':   'section-req-edge-cases',
  'req-review-tests': 'section-req-review-tests',
  'req-validate':     'section-req-validate',
  'settings':         'section-settings',
};

function wireNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
      // Let the logout button handle its own click via onclick
      if (item.classList.contains('nav-logout-btn')) return;
      e.preventDefault();
      const sec = item.getAttribute('data-section');
      if (sec) showSection(sec);
    });
  });
}

async function signOut() {
  try {
    await fetch('/logout', { method: 'POST' });
  } catch (_) { /* ignore network errors — redirect anyway */ }
  window.location.href = '/login';
}

function showSection(sectionKey) {
  // Hide all sections
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

  // Show target section
  const targetId = SECTION_MAP[sectionKey] || ('section-' + sectionKey);
  const target = document.getElementById(targetId);
  if (target) target.classList.add('active');

  // Update sidebar active state
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-section') === sectionKey);
  });
}


// ═══════════════════════════════════════════════════════════════════════
// DEFECT RCA — FILE HANDLING
// ═══════════════════════════════════════════════════════════════════════

function initRCADropZone() {
  const zone = document.getElementById('rca-drop-zone');
  if (!zone) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
    zone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); });
  });

  ['dragenter', 'dragover'].forEach(ev => {
    zone.addEventListener(ev, () => zone.classList.add('drag-over'));
  });
  ['dragleave', 'drop'].forEach(ev => {
    zone.addEventListener(ev, () => zone.classList.remove('drag-over'));
  });

  zone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleRCAFile(files[0]);
  });

  zone.addEventListener('click', e => {
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
    document.getElementById('rca-file-input').click();
  });
}

function initRCAFileInput() {
  const input = document.getElementById('rca-file-input');
  if (input) {
    input.addEventListener('change', e => {
      if (e.target.files.length > 0) handleRCAFile(e.target.files[0]);
    });
  }
}

function handleRCAFile(file) {
  const allowed = ['.csv', '.xlsx', '.xls'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showRCAError('Invalid file type. Please upload a CSV or Excel (.xlsx, .xls) file.');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showRCAError('File too large. Maximum size is 16 MB.');
    return;
  }
  rcaCurrentFile = file;
  displayRCAFileInfo(file);
}

function displayRCAFileInfo(file) {
  document.getElementById('rca-file-name').textContent = file.name;
  document.getElementById('rca-file-size').textContent = formatFileSize(file.size);
  document.getElementById('rca-file-info').style.display = 'flex';
  document.getElementById('rca-analyze-btn').style.display = 'block';
}

function clearRCAFile() {
  rcaCurrentFile = null;
  document.getElementById('rca-file-info').style.display = 'none';
  document.getElementById('rca-analyze-btn').style.display = 'none';
  document.getElementById('rca-file-input').value = '';
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}


// ═══════════════════════════════════════════════════════════════════════
// DEFECT RCA — ANALYSIS WORKFLOW
// ═══════════════════════════════════════════════════════════════════════

async function startRCAAnalysis() {
  if (!rcaCurrentFile) { showRCAError('No file selected.'); return; }

  document.getElementById('rca-upload-card').style.display  = 'none';
  document.getElementById('rca-progress-card').style.display = 'block';
  document.getElementById('rca-error-card').style.display   = 'none';

  try {
    // Step 1 — Upload
    updateRCAProgress(25, 'Uploading file…', 'upload');
    const uploadData = await rcaUploadFile(rcaCurrentFile);
    rcaSessionId       = uploadData.session_id;
    rcaCurrentFilepath = uploadData.filepath;

    // Step 2 — Analyze
    updateRCAProgress(50, 'Analyzing defects…', 'analyze');
    await sleep(400);
    const analyzeData = await rcaAnalyze(rcaSessionId, rcaCurrentFilepath);
    rcaAnalysisResults = analyzeData.results;

    // Step 3 — Generate PDF
    updateRCAProgress(75, 'Generating PDF report…', 'report');
    await sleep(400);
    const pdfData = await rcaGeneratePdf(rcaSessionId, rcaCurrentFilepath);
    rcaPdfFilename = pdfData.pdf_report;

    // Step 4 — Complete
    updateRCAProgress(100, 'Analysis complete!', 'complete');
    await sleep(900);

    displayRCAResults();

  } catch (err) {
    showRCAError(err.message || 'An error occurred during analysis.');
  }
}

async function rcaUploadFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Upload failed.');
  return data;
}

async function rcaAnalyze(sessionId, filepath) {
  const res = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, filepath }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Analysis failed.');
  return data;
}

async function rcaGeneratePdf(sessionId, filepath) {
  const res = await fetch('/generate-pdf-report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, filepath }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'PDF generation failed.');
  return data;
}

function updateRCAProgress(pct, text, activeStep) {
  document.getElementById('rca-progress-fill').style.width = pct + '%';
  document.getElementById('rca-progress-text').textContent = text;

  const steps = ['upload', 'analyze', 'report', 'complete'];
  const idx = steps.indexOf(activeStep);
  steps.forEach((s, i) => {
    const el = document.getElementById('rca-step-' + s);
    if (!el) return;
    el.classList.remove('active', 'completed');
    if (i < idx) el.classList.add('completed');
    else if (i === idx) el.classList.add('active');
  });
}


// ═══════════════════════════════════════════════════════════════════════
// DEFECT RCA — DISPLAY RESULTS
// ═══════════════════════════════════════════════════════════════════════

function displayRCAResults() {
  document.getElementById('rca-progress-card').style.display = 'none';
  document.getElementById('rca-results-card').style.display  = 'block';

  const r = rcaAnalysisResults;

  // Stat cards
  document.getElementById('rca-total-defects').textContent = r.total_defects || 0;
  document.getElementById('rca-high-severity').textContent  = r.summary?.high_severity || 0;
  document.getElementById('rca-open-defects').textContent   = r.summary?.open || 0;
  document.getElementById('rca-needed').textContent         = r.rca_candidates?.length || 0;

  // Destroy existing charts before recreating (avoid "canvas already in use" error)
  if (rcaChartSeverity) { rcaChartSeverity.destroy(); rcaChartSeverity = null; }
  if (rcaChartStatus)   { rcaChartStatus.destroy();   rcaChartStatus   = null; }
  if (rcaChartModule)   { rcaChartModule.destroy();   rcaChartModule   = null; }

  createSeverityChart();
  createStatusChart();
  createModuleChart();

  displayRCACandidates();
  displayPreventiveMeasures();

  // Show overview tab by default
  switchRCATab('overview');
}

function createSeverityChart() {
  const ctx  = document.getElementById('rca-severity-chart');
  if (!ctx) return;
  const data = rcaAnalysisResults.severity_distribution || {};
  rcaChartSeverity = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: 'Defects',
        data: Object.values(data),
        backgroundColor: ['rgba(218,30,40,0.8)', 'rgba(217,119,6,0.8)', 'rgba(251,191,36,0.8)', 'rgba(25,128,56,0.8)', 'rgba(15,98,254,0.8)'],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });
}

function createStatusChart() {
  const ctx  = document.getElementById('rca-status-chart');
  if (!ctx) return;
  const data = rcaAnalysisResults.status_distribution || {};
  rcaChartStatus = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(data),
      datasets: [{
        data: Object.values(data),
        backgroundColor: ['rgba(25,128,56,0.8)', 'rgba(217,119,6,0.8)', 'rgba(218,30,40,0.8)'],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
    },
  });
}

function createModuleChart() {
  const ctx  = document.getElementById('rca-module-chart');
  if (!ctx) return;
  const data = rcaAnalysisResults.module_distribution || {};

  if (Object.keys(data).length === 0) {
    ctx.parentElement.innerHTML = '<p style="text-align:center;color:#8d8d8d;padding:2rem 0;">No module/area data available in the uploaded file.</p>';
    return;
  }

  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const labels = sorted.map(([m]) => m);
  const values = sorted.map(([, v]) => v);
  const colors = [
    'rgba(218,30,40,0.8)', 'rgba(217,119,6,0.8)', 'rgba(251,191,36,0.8)',
    'rgba(25,128,56,0.8)', 'rgba(15,98,254,0.8)',  'rgba(124,92,216,0.8)',
    'rgba(236,72,153,0.8)','rgba(20,184,166,0.8)', 'rgba(251,146,60,0.8)',
    'rgba(168,85,247,0.8)',
  ];
  const type = sorted.length <= 5 ? 'pie' : 'bar';
  rcaChartModule = new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [{
        label: 'Defects',
        data: values,
        backgroundColor: type === 'pie' ? colors : 'rgba(15,98,254,0.8)',
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: type === 'pie' ? false : true,
      indexAxis: type === 'bar' ? 'y' : undefined,
      plugins: {
        legend: { display: type === 'pie', position: 'bottom' },
        title:  { display: true, text: `Top ${sorted.length} Affected Modules / Areas` },
      },
      scales: type === 'bar' ? { x: { beginAtZero: true, ticks: { stepSize: 1 } } } : undefined,
    },
  });
}

function displayRCACandidates() {
  const list       = document.getElementById('rca-candidates-list');
  const countEl    = document.getElementById('rca-count');
  const candidates = rcaAnalysisResults.rca_candidates || [];
  const grouped    = rcaAnalysisResults.grouped_count || 0;
  const standalone = rcaAnalysisResults.standalone_count || 0;

  if (countEl) {
    countEl.textContent = grouped > 0 && standalone > 0
      ? `${candidates.length} (${grouped} grouped + ${standalone} standalone)`
      : `${candidates.length}`;
  }

  if (candidates.length === 0) {
    list.innerHTML = '<p style="text-align:center;color:#8d8d8d;padding:1rem 0;">✅ No high-severity defects require RCA at this time.</p>';
    return;
  }

  // Show "AI Enhanced" badge if LLM was used
  const aiEnhanced = rcaAnalysisResults.ai_enhanced || false;
  const aiBadge    = aiEnhanced
    ? '<span class="ai-enhanced-badge">✦ AI Enhanced</span>'
    : '';

  list.innerHTML = candidates.map(c => `
    <div class="candidate-item">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.4rem;">
        <div>
          <div class="candidate-id">${esc(c.id)} ${aiBadge}</div>
          ${c.module ? `<div style="font-size:0.75rem;color:#8d8d8d;margin-top:2px;">📁 ${esc(c.module)}</div>` : ''}
        </div>
        <span class="candidate-severity ${getSeverityClass(c.severity)}">${esc(c.severity)}</span>
      </div>
      <div class="candidate-summary">${esc(c.summary)}</div>
      ${c.suggested_root_cause ? `
        <div class="suggested-root-cause">
          <strong>💡 Suggested Root Cause:</strong> ${esc(c.suggested_root_cause)}
        </div>` : ''}
      ${c.group_size > 1 ? `
        <div style="margin-top:0.6rem;padding:0.5rem 0.75rem;background:#fff8e1;border-left:3px solid #fdd13a;border-radius:4px;font-size:0.8rem;">
          <strong>🔗 Pattern:</strong> ${esc(getPatternName(c.group_key))} — ${c.group_size} similar defects
          ${c.similar_defects?.length ? `<div style="margin-top:0.3rem;color:#684e08;"><strong>Similar:</strong> ${c.similar_defects.slice(0,5).map(esc).join(', ')}${c.similar_defects.length > 5 ? ` +${c.similar_defects.length - 5} more` : ''}</div>` : ''}
        </div>` : `
        <div style="margin-top:0.6rem;padding:0.4rem 0.75rem;background:#f4f4f4;border-radius:4px;font-size:0.8rem;color:#8d8d8d;">
          ℹ️ Standalone defect — no similar patterns detected
        </div>`}
    </div>
  `).join('');
}

function displayPreventiveMeasures() {
  const container = document.getElementById('rca-preventive-list');
  const measures  = rcaAnalysisResults.preventive_measures || [];

  if (!measures.length) {
    container.innerHTML = '<p style="color:#8d8d8d;padding:1rem 0;">No grouped defect patterns detected. Focus on individual RCA for each defect.</p>';
    return;
  }

  container.innerHTML = measures.map(m => `
    <div class="measure-category">
      <div class="measure-header">
        <span class="measure-icon">${m.icon || '📋'}</span>
        <h4>${esc(m.category)}</h4>
        ${m.affected_count ? `<span class="measure-badge">${m.affected_count} defects</span>` : ''}
      </div>
      ${m.modules?.length ? `<div class="measure-modules"><strong>Affected Modules:</strong> ${m.modules.map(esc).join(', ')}</div>` : ''}
      ${m.five_whys ? `
        <div class="five-whys-section">
          <h5>🔍 5-Whys Root Cause Analysis</h5>
          <div style="padding-left:1rem;border-left:3px solid #0f62fe;">
            ${[1,2,3,4,5].map(n => `
              <div style="margin-bottom:0.5rem;">
                <strong>${n}. ${esc(m.five_whys['why'+n])}</strong><br>
                <span style="color:#525252;">→ ${esc(m.five_whys['answer'+n])}</span>
              </div>`).join('')}
            <div style="margin-top:0.75rem;padding:0.6rem 0.85rem;background:#fef3c7;border-radius:4px;">
              <strong style="color:#92400e;">🎯 ROOT CAUSE:</strong><br>
              <span style="color:#78350f;">${esc(m.five_whys.root_cause)}</span>
            </div>
          </div>
        </div>` : ''}
      ${m.immediate_actions?.length ? `
        <div style="margin:0.75rem 0;">
          <h5 style="font-size:0.875rem;margin-bottom:0.4rem;">⚡ Immediate Actions</h5>
          <ul class="measure-list">${m.immediate_actions.map(a => `<li>${esc(a)}</li>`).join('')}</ul>
        </div>` : ''}
      ${m.long_term_prevention?.length ? `
        <div style="margin:0.75rem 0;">
          <h5 style="font-size:0.875rem;margin-bottom:0.4rem;">📋 Long-term Prevention</h5>
          <ul class="measure-list">${m.long_term_prevention.map(a => `<li>${esc(a)}</li>`).join('')}</ul>
        </div>` : ''}
      ${!m.immediate_actions && !m.long_term_prevention && m.measures?.length ? `
        <ul class="measure-list">${m.measures.map(a => `<li>${esc(a)}</li>`).join('')}</ul>` : ''}
    </div>
  `).join('');
}

function getSeverityClass(sev) {
  const s = (sev || '').toLowerCase();
  if (s.includes('kritisk') || s.includes('critical') || s.includes('high') || /1\s*-/.test(s) || s.startsWith('1')) return 'severity-high';
  if (s.includes('medium') || /2\s*-/.test(s) || /3\s*-/.test(s)) return 'severity-medium';
  return 'severity-low';
}

function getPatternName(groupKey) {
  if (!groupKey) return 'Similar Issues';
  const parts   = groupKey.split('_');
  const keyword = parts[parts.length - 1];
  const module  = parts.slice(0, -1).join(' ');
  const map = {
    login:'Login Issues', password:'Password Problems', authentication:'Auth Failures',
    timeout:'Timeout Issues', connection:'Connection Problems', error:'Error Handling',
    crash:'System Crashes', performance:'Performance Issues', slow:'Slow Response',
    loading:'Loading Problems', display:'Display Issues', button:'Button Functionality',
    link:'Link Problems', navigation:'Navigation Issues', search:'Search Functionality',
    filter:'Filter Problems', save:'Save Functionality', delete:'Delete Operations',
    update:'Update Issues', create:'Create Operations', validation:'Validation Errors',
    format:'Format Issues', data:'Data Problems', database:'Database Issues',
    api:'API Problems', integration:'Integration Issues', email:'Email Functionality',
    notification:'Notification Problems',
  };
  const name = map[keyword.toLowerCase()] || (keyword.charAt(0).toUpperCase() + keyword.slice(1));
  return module && module !== 'General' ? `${module} — ${name}` : name;
}

function switchRCATab(tabName) {
  document.querySelectorAll('#rca-results-card .tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('#rca-results-card .tab').forEach(el => el.classList.remove('active'));
  const panel = document.getElementById('rca-tab-' + tabName);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('#rca-results-card .tab').forEach(btn => {
    if (btn.getAttribute('onclick')?.includes(tabName)) btn.classList.add('active');
  });
}

function rcaDownloadPdf() {
  if (!rcaPdfFilename) { alert('PDF report not yet generated. Please run analysis first.'); return; }
  window.location.href = '/download/' + rcaPdfFilename;
}

function showRCAError(msg) {
  document.getElementById('rca-upload-card').style.display   = 'block';
  document.getElementById('rca-progress-card').style.display = 'none';
  document.getElementById('rca-results-card').style.display  = 'none';
  document.getElementById('rca-error-card').style.display    = 'block';
  document.getElementById('rca-error-message').textContent   = msg;
}

function resetRCA() {
  rcaCurrentFile     = null;
  rcaCurrentFilepath = null;
  rcaSessionId       = null;
  rcaAnalysisResults = null;
  rcaPdfFilename     = null;

  document.getElementById('rca-upload-card').style.display   = 'block';
  document.getElementById('rca-progress-card').style.display = 'none';
  document.getElementById('rca-results-card').style.display  = 'none';
  document.getElementById('rca-error-card').style.display    = 'none';
  clearRCAFile();
}


// ═══════════════════════════════════════════════════════════════════════
// REQUIREMENTS ANALYZER
// ═══════════════════════════════════════════════════════════════════════

// Task configuration (mirrors ICA_BOB/src/tasks.js + backend TASK_PROMPTS)
const TASKS = [
  {
    id: 'translate',
    label: 'Translate Requirements',
    fields: [{ id: 'requirements', label: 'Requirements (any language)' }],
  },
  {
    id: 'analyze',
    label: 'Analyze Requirements',
    fields: [{ id: 'requirements', label: 'Software Requirements' }],
  },
  {
    id: 'edge_cases',
    label: 'Identify Edge Cases',
    // HTML section id uses 'req-edge-cases'; task_type uses 'edge_cases'
    fields: [{ id: 'requirements', label: 'Requirements / Feature Description' }],
  },
  {
    id: 'review_tests',
    label: 'Review Test Scenarios',
    fields: [
      { id: 'requirements', label: 'Requirements' },
      { id: 'test_cases',   label: 'Test Scenarios / Test Cases' },
    ],
  },
  {
    id: 'validate',
    label: 'Validate Consistency',
    fields: [
      { id: 'requirements', label: 'Requirements' },
      { id: 'test_cases',   label: 'Test Cases' },
    ],
  },
];

// Initialise reqState for all tasks
TASKS.forEach(task => {
  reqState[task.id] = { fieldValues: {}, reply: '', error: '' };
  task.fields.forEach(f => { reqState[task.id].fieldValues[f.id] = ''; });
});

// Called from textarea oninput (inline HTML handlers)
function onReqFieldInput(taskId, fieldId, value) {
  if (!reqState[taskId]) return;
  reqState[taskId].fieldValues[fieldId] = value;

  // Build the HTML id - note edge_cases uses underscore in field ids
  const clearBtn = document.getElementById(`req-${taskId}-${fieldId}-clear`);
  if (clearBtn) clearBtn.style.display = value.trim() ? 'block' : 'none';

  // Enable/disable submit button
  updateReqSubmitButton(taskId);
}

function updateReqSubmitButton(taskId) {
  const task   = TASKS.find(t => t.id === taskId);
  if (!task) return;
  const btn    = document.getElementById(`req-${taskId}-submit`);
  if (!btn) return;
  const allFilled = task.fields.every(f => (reqState[taskId].fieldValues[f.id] || '').trim());
  btn.disabled = !allFilled;
}

function clearReqField(taskId, fieldId) {
  if (!reqState[taskId]) return;
  reqState[taskId].fieldValues[fieldId] = '';
  const ta = document.getElementById(`req-${taskId}-${fieldId}`);
  if (ta) ta.value = '';
  const clearBtn = document.getElementById(`req-${taskId}-${fieldId}-clear`);
  if (clearBtn) clearBtn.style.display = 'none';
  updateReqSubmitButton(taskId);
}

// Called from file input onchange (inline HTML handlers)
function handleReqFileUpload(taskId, fieldId, inputEl) {
  const file = inputEl.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = evt => {
    const existing = reqState[taskId]?.fieldValues[fieldId] || '';
    const newVal   = existing ? existing + '\n\n' + evt.target.result : evt.target.result;
    reqState[taskId].fieldValues[fieldId] = newVal;
    const ta = document.getElementById(`req-${taskId}-${fieldId}`);
    if (ta) ta.value = newVal;
    const clearBtn = document.getElementById(`req-${taskId}-${fieldId}-clear`);
    if (clearBtn) clearBtn.style.display = 'block';
    updateReqSubmitButton(taskId);
  };
  reader.readAsText(file);
  inputEl.value = ''; // allow re-upload of same file
}

async function submitRequirement(taskId) {
  const task = TASKS.find(t => t.id === taskId);
  if (!task) return;

  // Build combined prompt
  const combined = task.fields
    .map(f => {
      const val = (reqState[taskId].fieldValues[f.id] || '').trim();
      return val ? `### ${f.label}\n${val}` : null;
    })
    .filter(Boolean)
    .join('\n\n');

  if (!combined) return;

  // UI: show loading
  reqState[taskId].reply  = '';
  reqState[taskId].error  = '';
  hideReqResponse(taskId);
  showReqLoading(taskId, true);
  startElapsedTimer(taskId);

  // Disable submit button while loading
  const btn = document.getElementById(`req-${taskId}-submit`);
  if (btn) btn.disabled = true;

  try {
    const res  = await fetch('/api/requirements', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ task_type: taskId, user_input: combined }),
    });
    const data = await res.json();

    if (!res.ok) {
      reqState[taskId].error = data.error || 'Agent returned an error.';
      showReqError(taskId, reqState[taskId].error);
    } else {
      reqState[taskId].reply = data.reply;
      showReqResponse(taskId, data.reply);
      addToReqHistory(taskId, task.label, combined, data.reply);
    }
  } catch (err) {
    const msg = 'Could not reach the backend. Is the server running on port 5000?';
    reqState[taskId].error = msg;
    showReqError(taskId, msg);
  } finally {
    stopElapsedTimer();
    showReqLoading(taskId, false);
    updateReqSubmitButton(taskId);
  }
}

function showReqLoading(taskId, show) {
  const el = document.getElementById(`req-${taskId}-loading`);
  if (el) el.style.display = show ? 'flex' : 'none';
}

function hideReqResponse(taskId) {
  const wrap  = document.getElementById(`req-${taskId}-response-wrap`);
  const error = document.getElementById(`req-${taskId}-error`);
  if (wrap)  wrap.style.display  = 'none';
  if (error) error.style.display = 'none';
}

function showReqResponse(taskId, reply) {
  const box  = document.getElementById(`req-${taskId}-response`);
  const wrap = document.getElementById(`req-${taskId}-response-wrap`);
  const err  = document.getElementById(`req-${taskId}-error`);
  if (box)  box.textContent   = reply;
  if (wrap) wrap.style.display = 'block';
  if (err)  err.style.display  = 'none';
}

function showReqError(taskId, msg) {
  const el   = document.getElementById(`req-${taskId}-error`);
  const wrap = document.getElementById(`req-${taskId}-response-wrap`);
  if (el)   { el.textContent = msg; el.style.display = 'block'; }
  if (wrap) wrap.style.display = 'none';
}

function copyReqResponse(taskId) {
  const reply = reqState[taskId]?.reply;
  if (!reply) return;
  navigator.clipboard.writeText(reply).then(() => {
    // Find the copy button for this task and show feedback
    const btns = document.querySelectorAll(`#section-req-${taskId.replace('_','-')} .copy-btn, #req-${taskId}-response-wrap .copy-btn`);
    btns.forEach(btn => {
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    });
  }).catch(() => {});
}

// Elapsed timer
function startElapsedTimer(taskId) {
  elapsedSeconds = 0;
  stopElapsedTimer();
  const elapsedEl = document.getElementById(`req-${taskId}-elapsed`);
  elapsedInterval = setInterval(() => {
    elapsedSeconds++;
    if (elapsedEl && elapsedSeconds >= 5) {
      elapsedEl.textContent = `(${elapsedSeconds}s — complex tasks can take up to 120s)`;
    }
  }, 1000);
}

function stopElapsedTimer() {
  if (elapsedInterval) { clearInterval(elapsedInterval); elapsedInterval = null; }
  elapsedSeconds = 0;
}

// History
function addToReqHistory(taskId, label, input, reply) {
  reqHistory.push({
    id:        Date.now(),
    taskId,
    label,
    input,
    reply,
    timestamp: new Date().toLocaleTimeString(),
  });
  renderReqHistory(taskId);
}

function renderReqHistory(taskId) {
  // Use the section id mapping for edge_cases
  const sectionSuffix = taskId === 'edge_cases' ? 'edge-cases'
    : taskId === 'review_tests' ? 'review-tests' : taskId;

  const container = document.getElementById(`req-${taskId}-history`);
  if (!container) return;

  const items = reqHistory.filter(h => h.taskId === taskId).reverse();
  if (!items.length) { container.innerHTML = ''; return; }

  container.innerHTML = `
    <div class="history-section">
      <h3>Session History (${items.length})</h3>
      ${items.map(item => `
        <div class="history-item">
          <div class="history-meta">
            <span class="history-badge">${esc(item.label)}</span>
            <span class="history-time">${esc(item.timestamp)}</span>
          </div>
          <div class="history-input"><strong>Input:</strong> ${esc(item.input.slice(0, 120))}${item.input.length > 120 ? '…' : ''}</div>
          <div class="history-response">${esc(item.reply)}</div>
        </div>`).join('')}
    </div>`;
}


// ═══════════════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════════════

async function loadSettings() {
  try {
    const res  = await fetch('/api/settings');
    const data = await res.json();
    if (!res.ok) return;
    // Also refresh user list whenever settings section is loaded
    loadUsers();

    // ICA fields
    const endpointEl = document.getElementById('settings-endpoint');
    if (endpointEl) endpointEl.value = data.ica_endpoint || '';

    const keyStatusEl = document.getElementById('settings-key-status');
    if (keyStatusEl) {
      if (data.ica_api_key_set) {
        keyStatusEl.textContent = '✓ API key is configured';
        keyStatusEl.className   = 'key-status-configured';
      } else {
        keyStatusEl.textContent = 'Not configured';
        keyStatusEl.className   = 'key-status-not-set';
      }
    }

    // watsonx.ai fields
    const wxModelEl = document.getElementById('settings-wx-model');
    if (wxModelEl) wxModelEl.value = data.watsonx_model_id || '';

    const wxKeyStatusEl = document.getElementById('settings-wx-key-status');
    if (wxKeyStatusEl) {
      if (data.watsonx_api_key_set) {
        wxKeyStatusEl.textContent = '✓ watsonx API key is configured';
        wxKeyStatusEl.className   = 'key-status-configured';
      } else {
        wxKeyStatusEl.textContent = 'Not configured — rule-based RCA will be used';
        wxKeyStatusEl.className   = 'key-status-not-set';
      }
    }

    const wxProjectStatusEl = document.getElementById('settings-wx-project-status');
    if (wxProjectStatusEl) {
      if (data.watsonx_project_id_set) {
        wxProjectStatusEl.textContent = '✓ watsonx Project ID is configured — AI RCA enabled';
        wxProjectStatusEl.className   = 'key-status-configured';
      } else {
        wxProjectStatusEl.textContent = 'Not configured — rule-based RCA will be used';
        wxProjectStatusEl.className   = 'key-status-not-set';
      }
    }
  } catch (_) { /* server might not be ready — ignore */ }
}

async function saveSettings() {
  const endpoint    = (document.getElementById('settings-endpoint')?.value       || '').trim();
  const apiKey      = (document.getElementById('settings-api-key')?.value        || '').trim();
  const wxApiKey    = (document.getElementById('settings-wx-api-key')?.value     || '').trim();
  const wxProjectId = (document.getElementById('settings-wx-project-id')?.value  || '').trim();
  const wxModel     = (document.getElementById('settings-wx-model')?.value       || '').trim();
  const statusEl    = document.getElementById('settings-status');

  try {
    const res  = await fetch('/api/settings', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        ica_endpoint:       endpoint,
        ica_api_key:        apiKey,
        watsonx_api_key:    wxApiKey,
        watsonx_project_id: wxProjectId,
        watsonx_model_id:   wxModel,
      }),
    });
    const data = await res.json();

    if (statusEl) {
      statusEl.style.display = 'block';
      if (res.ok) {
        statusEl.className   = 'settings-status-success';
        statusEl.textContent = '✓ Settings saved successfully.';
        // Clear key fields so they don't show plaintext after save
        const keyEl       = document.getElementById('settings-api-key');
        const wxKeyEl     = document.getElementById('settings-wx-api-key');
        const wxProjectEl = document.getElementById('settings-wx-project-id');
        if (keyEl)       keyEl.value       = '';
        if (wxKeyEl)     wxKeyEl.value     = '';
        if (wxProjectEl) wxProjectEl.value = '';
      } else {
        statusEl.className   = 'settings-status-error';
        statusEl.textContent = '✗ ' + (data.error || 'Failed to save settings.');
      }
      setTimeout(() => { if (statusEl) statusEl.style.display = 'none'; }, 4000);
    }

    // Refresh status indicators
    await loadSettings();

  } catch (err) {
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.className     = 'settings-status-error';
      statusEl.textContent   = '✗ Could not reach the server.';
    }
  }
}

function toggleApiKeyVisibility() {
  const input  = document.getElementById('settings-api-key');
  const toggle = document.getElementById('settings-key-toggle');
  if (!input || !toggle) return;
  if (input.type === 'password') {
    input.type         = 'text';
    toggle.textContent = 'Hide';
  } else {
    input.type         = 'password';
    toggle.textContent = 'Show';
  }
}

function toggleWatsonxKeyVisibility() {
  const input  = document.getElementById('settings-wx-api-key');
  const toggle = document.getElementById('settings-wx-key-toggle');
  if (!input || !toggle) return;
  if (input.type === 'password') {
    input.type         = 'text';
    toggle.textContent = 'Hide';
  } else {
    input.type         = 'password';
    toggle.textContent = 'Show';
  }
}

function toggleWatsonxProjectVisibility() {
  const input  = document.getElementById('settings-wx-project-id');
  const toggle = document.getElementById('settings-wx-project-toggle');
  if (!input || !toggle) return;
  if (input.type === 'password') {
    input.type         = 'text';
    toggle.textContent = 'Hide';
  } else {
    input.type         = 'password';
    toggle.textContent = 'Show';
  }
}


// ═══════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// HTML-escape helper (prevents XSS from defect data)
function esc(str) {
  return String(str)
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#39;');
}


// ═══════════════════════════════════════════════════════════════════════
// USER MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════

// Detect current user role from sidebar badge (set by Jinja2 on page load)
function _isAdmin() {
  return document.querySelector('.sidebar-user-role') !== null;
}

async function loadUsers() {
  const container = document.getElementById('users-list');
  if (!container) return;

  // Show/hide admin-only section based on role
  const adminSection = document.getElementById('admin-user-section');
  if (adminSection) adminSection.style.display = _isAdmin() ? 'block' : 'none';

  try {
    const res  = await fetch('/api/users');
    if (!res.ok) { container.innerHTML = '<p style="color:var(--cds-gray-50);font-size:0.875rem;">Could not load users.</p>'; return; }
    const data = await res.json();
    const users = data.users || [];

    if (!users.length) {
      container.innerHTML = '<p style="color:var(--cds-gray-50);font-size:0.875rem;">No users found.</p>';
      return;
    }

    // Render users table — admin gets Remove button, all get Reset Password inline
    container.innerHTML = `
      <table class="users-table">
        <thead><tr><th>Username</th><th>Role</th><th>Actions</th></tr></thead>
        <tbody>
          ${users.map(u => `
            <tr>
              <td>${esc(u.username)}</td>
              <td><span class="user-role-badge ${u.role === 'admin' ? 'role-admin' : 'role-user'}">${esc(u.role)}</span></td>
              <td class="user-actions-cell">
                ${_isAdmin() ? `
                  <button class="btn btn-sm btn-secondary"
                    onclick="deleteUser('${esc(u.username)}')"
                    title="Remove user">✕ Remove</button>` : ''}
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;

    // Populate the admin "reset any user" dropdown
    const dropdown = document.getElementById('reset-target-username');
    if (dropdown) {
      dropdown.innerHTML = '<option value="">— Select a user —</option>' +
        users.map(u => `<option value="${esc(u.username)}">${esc(u.username)} (${esc(u.role)})</option>`).join('');
    }

  } catch (_) {
    container.innerHTML = '<p style="color:var(--cds-gray-50);font-size:0.875rem;">Could not load users.</p>';
  }
}

async function addUser() {
  const username  = (document.getElementById('new-username')?.value  || '').trim().toLowerCase();
  const password  = (document.getElementById('new-password')?.value  || '').trim();
  const role      = (document.getElementById('new-role')?.value      || 'user');
  const statusEl  = document.getElementById('user-mgmt-status');

  if (!username || !password) {
    showUserStatus('Username and password are required.', false);
    return;
  }
  if (password.length < 6) {
    showUserStatus('Password must be at least 6 characters.', false);
    return;
  }

  try {
    const res  = await fetch('/api/users', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ username, password, role }),
    });
    const data = await res.json();
    if (res.ok) {
      showUserStatus(`✓ User '${username}' created successfully.`, true);
      document.getElementById('new-username').value = '';
      document.getElementById('new-password').value = '';
      loadUsers();
    } else {
      showUserStatus('✗ ' + (data.error || 'Failed to create user.'), false);
    }
  } catch (_) {
    showUserStatus('✗ Could not reach the server.', false);
  }
}

async function deleteUser(username) {
  if (!confirm(`Remove user '${username}'? This cannot be undone.`)) return;
  try {
    const res  = await fetch(`/api/users/${encodeURIComponent(username)}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showUserStatus(`✓ User '${username}' removed.`, true);
      loadUsers();
    } else {
      showUserStatus('✗ ' + (data.error || 'Failed to remove user.'), false);
    }
  } catch (_) {
    showUserStatus('✗ Could not reach the server.', false);
  }
}

// ── Password reset helpers ────────────────────────────────────────────

async function _doPasswordReset(username, newPw, confirmPw) {
  if (!newPw) {
    showUserStatus('New password is required.', false); return;
  }
  if (newPw.length < 6) {
    showUserStatus('Password must be at least 6 characters.', false); return;
  }
  if (newPw !== confirmPw) {
    showUserStatus('Passwords do not match.', false); return;
  }
  try {
    const res  = await fetch(`/api/users/${encodeURIComponent(username)}/password`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ new_password: newPw }),
    });
    const data = await res.json();
    if (res.ok) {
      showUserStatus(`✓ Password updated for '${username}'.`, true);
    } else {
      showUserStatus('✗ ' + (data.error || 'Failed to reset password.'), false);
    }
  } catch (_) {
    showUserStatus('✗ Could not reach the server.', false);
  }
}

async function resetOwnPassword() {
  const newPw     = (document.getElementById('self-new-password')?.value     || '').trim();
  const confirmPw = (document.getElementById('self-confirm-password')?.value || '').trim();

  // Get current logged-in username from sidebar
  const usernameEl = document.querySelector('.sidebar-user-name');
  const username   = usernameEl ? usernameEl.textContent.trim() : '';

  if (!username) { showUserStatus('Could not detect current user.', false); return; }

  await _doPasswordReset(username, newPw, confirmPw);

  // Clear fields on success
  if (document.getElementById('self-new-password'))
    document.getElementById('self-new-password').value = '';
  if (document.getElementById('self-confirm-password'))
    document.getElementById('self-confirm-password').value = '';
}

async function resetAnyPassword() {
  const username  = (document.getElementById('reset-target-username')?.value || '').trim();
  const newPw     = (document.getElementById('reset-new-password')?.value    || '').trim();
  const confirmPw = (document.getElementById('reset-confirm-password')?.value || '').trim();

  if (!username) { showUserStatus('Please select a user.', false); return; }

  await _doPasswordReset(username, newPw, confirmPw);

  // Clear fields on success
  if (document.getElementById('reset-new-password'))
    document.getElementById('reset-new-password').value = '';
  if (document.getElementById('reset-confirm-password'))
    document.getElementById('reset-confirm-password').value = '';
}

function showUserStatus(msg, success) {
  const el = document.getElementById('user-mgmt-status');
  if (!el) return;
  el.style.display = 'block';
  el.className     = success ? 'settings-status-success' : 'settings-status-error';
  el.textContent   = msg;
  setTimeout(() => { if (el) el.style.display = 'none'; }, 4000);
}
