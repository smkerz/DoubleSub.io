// DoubleSub.io - Frontend JavaScript

// Etat de l'application
const state = {
    currentMode: 'srt',
    currentLang: 'en',
    files: {
        srt1: null,
        srt2: null
    },
    batchMode: false,
    batchPairs: [] // [{srt1: File, srt2: File}, ...]
};

// Config
const MAX_SRT_SIZE = 2 * 1024 * 1024; // 2 MB max pour les fichiers SRT
const MAX_HISTORY = 20; // Max items in history
const HISTORY_KEY = 'doublesub_history';

// Translations for dynamic content
const translations = {
    en: {
        errorInvalidFormat: 'Unsupported subtitle format. Use: SRT, ASS, SSA',
        errorFileTooLarge: 'File too large. Maximum size: 2 MB',
        processing: 'Processing...',
        mergeSuccess: '{count} subtitles merged successfully!',
        errorMerge: 'Error during merge',
        errorSignup: 'Error during signup',
        errorConnection: 'Connection error',
        historyEmpty: 'No merge history yet',
        historyTitle: 'Recent merges',
        batchProcessing: 'Processing {current}/{total}...',
        batchSuccess: '{count} files merged successfully!',
        clearHistory: 'Clear history'
    },
    fr: {
        errorInvalidFormat: 'Format de sous-titre non supporte. Utilisez: SRT, ASS, SSA',
        errorFileTooLarge: 'Fichier trop volumineux. Taille maximum: 2 MB',
        processing: 'Traitement en cours...',
        mergeSuccess: '{count} sous-titres fusionnes avec succes!',
        errorMerge: 'Erreur lors de la fusion',
        errorSignup: 'Erreur lors de l\'inscription',
        errorConnection: 'Erreur de connexion',
        historyEmpty: 'Aucun historique de fusion',
        historyTitle: 'Fusions recentes',
        batchProcessing: 'Traitement {current}/{total}...',
        batchSuccess: '{count} fichiers fusionnes avec succes!',
        clearHistory: 'Effacer l\'historique'
    }
};

// Get translated string
function t(key) {
    return translations[state.currentLang][key] || translations['en'][key] || key;
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    initLanguageSwitcher();
    initFileUploads();
    initMergeButton();
    initNotifyForm();
    initHistory();
    initBatchMode();
});

// Language Switcher
function initLanguageSwitcher() {
    // Load saved language or default to English
    const savedLang = localStorage.getItem('doublesub_lang') || 'en';
    setLanguage(savedLang);

    // Attach click handlers to language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lang = btn.dataset.lang;
            setLanguage(lang);
            localStorage.setItem('doublesub_lang', lang);
        });
    });
}

function setLanguage(lang) {
    state.currentLang = lang;

    // Update active button
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    // Update all translatable elements
    document.querySelectorAll('[data-en][data-fr]').forEach(el => {
        const text = el.getAttribute(`data-${lang}`);
        if (text) {
            el.textContent = text;
        }
    });

    // Update HTML lang attribute
    document.documentElement.lang = lang;

    // Update page title
    if (lang === 'fr') {
        document.title = 'DoubleSub.io - Fusion de Sous-titres Bilingues';
    } else {
        document.title = 'DoubleSub.io - Bilingual Subtitle Merger';
    }
}

// Gestion des uploads
function initFileUploads() {
    // SRT uploads
    setupDropZone('srt1DropZone', 'srt1File', 'srt1');
    setupDropZone('srt2DropZone', 'srt2File', 'srt2');
}

function setupDropZone(zoneId, inputId, fileType) {
    const dropZone = document.getElementById(zoneId);
    const fileInput = document.getElementById(inputId);

    if (!dropZone || !fileInput) return;

    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());

    // File selected
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file, fileType);
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file) handleFile(file, fileType);
    });
}

function handleFile(file, fileType) {
    console.log(`File uploaded: ${file.name} (${fileType})`);

    // Validate file extension
    const validExtensions = ['srt', 'ass', 'ssa'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
        showError(t('errorInvalidFormat'));
        return;
    }

    // Validate file size (max 2 MB)
    if (file.size > MAX_SRT_SIZE) {
        showError(t('errorFileTooLarge'));
        return;
    }

    // Store file
    state.files[fileType] = file;

    // Update UI
    showFileInfo(file, fileType);
    updateActionButton();
}

function showFileInfo(file, fileType) {
    const info = document.getElementById(`${fileType}Info`);
    const dropZone = document.getElementById(`${fileType}DropZone`);

    if (!info) return;

    const fileName = info.querySelector('.file-name');

    fileName.textContent = file.name;

    dropZone.classList.add('hidden');
    info.classList.remove('hidden');
}

function removeFile(fileType) {
    state.files[fileType] = null;

    const info = document.getElementById(`${fileType}Info`);
    const dropZone = document.getElementById(`${fileType}DropZone`);
    const input = document.getElementById(`${fileType}File`);

    if (info) info.classList.add('hidden');
    if (dropZone) dropZone.classList.remove('hidden');
    if (input) input.value = '';

    updateActionButton();
}

// Bouton de fusion
function initMergeButton() {
    const mergeBtn = document.getElementById('mergeBtn');
    mergeBtn.addEventListener('click', performMerge);
}

function updateActionButton() {
    const actionSection = document.getElementById('actionSection');
    const optionsCard = document.getElementById('optionsCard');
    const mergeBtn = document.getElementById('mergeBtn');

    const canMerge = state.files.srt1 !== null && state.files.srt2 !== null;

    if (canMerge) {
        actionSection.classList.remove('hidden');
        optionsCard.classList.remove('hidden');
        mergeBtn.disabled = false;
    } else {
        actionSection.classList.add('hidden');
        optionsCard.classList.add('hidden');
        mergeBtn.disabled = true;
    }
}

async function performMerge() {
    const mergeMode = document.getElementById('mergeMode').value;
    const tolerance = parseInt(document.getElementById('tolerance').value);
    const offset1 = parseInt(document.getElementById('offset1').value) || 0;
    const offset2 = parseInt(document.getElementById('offset2').value) || 0;

    // Get colors if enabled
    const color1Enabled = document.getElementById('color1Enabled').checked;
    const color2Enabled = document.getElementById('color2Enabled').checked;
    const color1 = color1Enabled ? document.getElementById('color1').value : '';
    const color2 = color2Enabled ? document.getElementById('color2').value : '';

    showProgress(t('processing'));

    const formData = new FormData();
    formData.append('mode', mergeMode);
    formData.append('tolerance', tolerance);
    formData.append('offset1', offset1);
    formData.append('offset2', offset2);
    formData.append('color1', color1);
    formData.append('color2', color2);
    formData.append('srt1', state.files.srt1);
    formData.append('srt2', state.files.srt2);

    try {
        const response = await fetch('/api/merge', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            hideProgress();
            showSuccess(data.message, data.output_file, data.cue_count, data.preview);
        } else {
            throw new Error(data.error || t('errorMerge'));
        }
    } catch (error) {
        console.error('Merge error:', error);
        hideProgress();
        showError(error.message);
    }
}

// Formulaire de notification email
function initNotifyForm() {
    const form = document.getElementById('notifyForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const emailInput = document.getElementById('notifyEmail');
        const email = emailInput.value.trim();

        if (!email) return;

        try {
            const response = await fetch('/api/notify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();

            if (data.success) {
                form.classList.add('hidden');
                document.getElementById('notifySuccess').classList.remove('hidden');
            } else {
                alert(data.error || t('errorSignup'));
            }
        } catch (error) {
            console.error('Notify error:', error);
            alert(t('errorConnection'));
        }
    });
}

// UI Helpers
function showProgress(message) {
    document.getElementById('actionSection').classList.add('hidden');
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('errorSection').classList.add('hidden');

    const progressSection = document.getElementById('progressSection');
    progressSection.querySelector('.progress-text').textContent = message;
    progressSection.classList.remove('hidden');
}

function hideProgress() {
    document.getElementById('progressSection').classList.add('hidden');
}

function showSuccess(message, outputFile, cueCount, preview) {
    const resultSection = document.getElementById('resultSection');
    const successMsg = t('mergeSuccess').replace('{count}', cueCount);
    resultSection.querySelector('.result-message').textContent = successMsg;

    // Display preview
    const previewContent = document.getElementById('previewContent');
    if (preview && preview.length > 0) {
        let previewHtml = '';
        preview.forEach(cue => {
            // Escape HTML but preserve font tags for color display
            const escapedText = cue.text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/&lt;font color="([^"]+)"&gt;/g, '<span style="color:$1">')
                .replace(/&lt;\/font&gt;/g, '</span>');

            previewHtml += `
                <div class="preview-cue">
                    <div class="preview-time">${cue.start} --> ${cue.end}</div>
                    <div class="preview-text">${escapedText.replace(/\n/g, '<br>')}</div>
                </div>
            `;
        });
        previewContent.innerHTML = previewHtml;
        document.getElementById('previewSection').classList.remove('hidden');
    } else {
        document.getElementById('previewSection').classList.add('hidden');
    }

    // Save to history
    saveToHistory({
        file1: state.files.srt1 ? state.files.srt1.name : 'Unknown',
        file2: state.files.srt2 ? state.files.srt2.name : 'Unknown',
        outputFile: outputFile,
        cueCount: cueCount,
        date: new Date().toISOString()
    });

    const downloadBtn = document.getElementById('downloadBtn');
    downloadBtn.onclick = () => {
        window.location.href = `/download/${outputFile}`;
    };

    resultSection.classList.remove('hidden');
    renderHistory();
}

function showError(message) {
    const errorSection = document.getElementById('errorSection');
    errorSection.querySelector('.error-message').textContent = message;
    errorSection.classList.remove('hidden');
}

function resetUpload() {
    state.files = { srt1: null, srt2: null };

    document.querySelectorAll('.file-info').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.upload-zone').forEach(el => el.classList.remove('hidden'));
    document.querySelectorAll('input[type="file"]').forEach(el => el.value = '');

    document.getElementById('actionSection').classList.add('hidden');
    document.getElementById('optionsCard').classList.add('hidden');
    document.getElementById('progressSection').classList.add('hidden');
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('errorSection').classList.add('hidden');
}

// ==================== HISTORY ====================

function initHistory() {
    renderHistory();
}

function getHistory() {
    try {
        const history = localStorage.getItem(HISTORY_KEY);
        return history ? JSON.parse(history) : [];
    } catch (e) {
        return [];
    }
}

function saveToHistory(item) {
    const history = getHistory();
    history.unshift(item);
    // Keep only MAX_HISTORY items
    if (history.length > MAX_HISTORY) {
        history.pop();
    }
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function clearHistory() {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
}

function renderHistory() {
    const historySection = document.getElementById('historySection');
    const historyList = document.getElementById('historyList');

    if (!historySection || !historyList) return;

    const history = getHistory();

    if (history.length === 0) {
        historySection.classList.add('hidden');
        return;
    }

    historySection.classList.remove('hidden');

    let html = '';
    history.forEach((item, index) => {
        const date = new Date(item.date);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        html += `
            <div class="history-item">
                <div class="history-files">
                    <span class="history-file">${escapeHtml(item.file1)}</span>
                    <span class="history-separator">+</span>
                    <span class="history-file">${escapeHtml(item.file2)}</span>
                </div>
                <div class="history-meta">
                    <span class="history-count">${item.cueCount} subs</span>
                    <span class="history-date">${dateStr}</span>
                    <a href="/download/${item.outputFile}" class="history-download" title="Download">DL</a>
                </div>
            </div>
        `;
    });

    historyList.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== BATCH MODE ====================

function initBatchMode() {
    const batchToggle = document.getElementById('batchModeToggle');
    if (!batchToggle) return;

    batchToggle.addEventListener('change', (e) => {
        state.batchMode = e.target.checked;
        toggleBatchMode(state.batchMode);
    });

    // Init batch file input
    const batchInput = document.getElementById('batchFiles');
    if (batchInput) {
        batchInput.addEventListener('change', handleBatchFiles);
    }
}

function toggleBatchMode(enabled) {
    const singleMode = document.getElementById('srtMode');
    const batchSection = document.getElementById('batchSection');

    if (enabled) {
        singleMode.classList.add('hidden');
        batchSection.classList.remove('hidden');
        document.getElementById('actionSection').classList.add('hidden');
        document.getElementById('optionsCard').classList.add('hidden');
    } else {
        singleMode.classList.remove('hidden');
        batchSection.classList.add('hidden');
        state.batchPairs = [];
        renderBatchList();
        updateActionButton();
    }
}

function handleBatchFiles(e) {
    const files = Array.from(e.target.files);

    // Sort files by name to try to match pairs
    files.sort((a, b) => a.name.localeCompare(b.name));

    // Validate all files
    for (const file of files) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['srt', 'ass', 'ssa'].includes(ext)) {
            showError(t('errorInvalidFormat'));
            return;
        }
        if (file.size > MAX_SRT_SIZE) {
            showError(t('errorFileTooLarge'));
            return;
        }
    }

    // Group into pairs (every 2 files)
    state.batchPairs = [];
    for (let i = 0; i < files.length - 1; i += 2) {
        state.batchPairs.push({
            srt1: files[i],
            srt2: files[i + 1]
        });
    }

    renderBatchList();
    updateBatchButton();
}

function renderBatchList() {
    const list = document.getElementById('batchList');
    if (!list) return;

    if (state.batchPairs.length === 0) {
        list.innerHTML = `<p class="batch-empty" data-en="Select files to create pairs" data-fr="Selectionnez des fichiers pour creer des paires">Select files to create pairs</p>`;
        return;
    }

    let html = '';
    state.batchPairs.forEach((pair, index) => {
        html += `
            <div class="batch-pair">
                <span class="batch-index">#${index + 1}</span>
                <div class="batch-files">
                    <span class="batch-file">${escapeHtml(pair.srt1.name)}</span>
                    <span class="batch-separator">+</span>
                    <span class="batch-file">${escapeHtml(pair.srt2.name)}</span>
                </div>
                <button class="batch-remove" onclick="removeBatchPair(${index})">X</button>
            </div>
        `;
    });

    list.innerHTML = html;
}

function removeBatchPair(index) {
    state.batchPairs.splice(index, 1);
    renderBatchList();
    updateBatchButton();
}

function updateBatchButton() {
    const batchBtn = document.getElementById('batchMergeBtn');
    const batchOptions = document.getElementById('batchOptionsCard');

    if (batchBtn) {
        batchBtn.disabled = state.batchPairs.length === 0;
    }
    if (batchOptions) {
        if (state.batchPairs.length > 0) {
            batchOptions.classList.remove('hidden');
        } else {
            batchOptions.classList.add('hidden');
        }
    }
}

async function performBatchMerge() {
    if (state.batchPairs.length === 0) return;

    const mergeMode = document.getElementById('mergeMode').value;
    const tolerance = parseInt(document.getElementById('tolerance').value);
    const offset1 = parseInt(document.getElementById('offset1').value) || 0;
    const offset2 = parseInt(document.getElementById('offset2').value) || 0;
    const color1Enabled = document.getElementById('color1Enabled').checked;
    const color2Enabled = document.getElementById('color2Enabled').checked;
    const color1 = color1Enabled ? document.getElementById('color1').value : '';
    const color2 = color2Enabled ? document.getElementById('color2').value : '';

    const results = [];
    const total = state.batchPairs.length;

    for (let i = 0; i < total; i++) {
        const pair = state.batchPairs[i];
        showProgress(t('batchProcessing').replace('{current}', i + 1).replace('{total}', total));

        const formData = new FormData();
        formData.append('mode', mergeMode);
        formData.append('tolerance', tolerance);
        formData.append('offset1', offset1);
        formData.append('offset2', offset2);
        formData.append('color1', color1);
        formData.append('color2', color2);
        formData.append('srt1', pair.srt1);
        formData.append('srt2', pair.srt2);

        try {
            const response = await fetch('/api/merge', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                results.push({
                    success: true,
                    file1: pair.srt1.name,
                    file2: pair.srt2.name,
                    outputFile: data.output_file,
                    cueCount: data.cue_count
                });

                // Save each to history
                saveToHistory({
                    file1: pair.srt1.name,
                    file2: pair.srt2.name,
                    outputFile: data.output_file,
                    cueCount: data.cue_count,
                    date: new Date().toISOString()
                });
            } else {
                results.push({
                    success: false,
                    file1: pair.srt1.name,
                    file2: pair.srt2.name,
                    error: data.error
                });
            }
        } catch (error) {
            results.push({
                success: false,
                file1: pair.srt1.name,
                file2: pair.srt2.name,
                error: error.message
            });
        }
    }

    hideProgress();
    showBatchResults(results);
    renderHistory();
}

function showBatchResults(results) {
    const successCount = results.filter(r => r.success).length;
    const resultSection = document.getElementById('batchResultSection');

    if (!resultSection) return;

    let html = `
        <div class="result-card ${successCount === results.length ? 'success' : 'warning'}">
            <div class="result-icon">${successCount === results.length ? 'OK' : '!'}</div>
            <h3>${t('batchSuccess').replace('{count}', successCount + '/' + results.length)}</h3>
            <div class="batch-results-list">
    `;

    results.forEach(r => {
        if (r.success) {
            html += `
                <div class="batch-result-item success">
                    <span>${escapeHtml(r.file1)} + ${escapeHtml(r.file2)}</span>
                    <a href="/download/${r.outputFile}" class="btn-small">DL</a>
                </div>
            `;
        } else {
            html += `
                <div class="batch-result-item error">
                    <span>${escapeHtml(r.file1)} + ${escapeHtml(r.file2)}</span>
                    <span class="error-text">${escapeHtml(r.error)}</span>
                </div>
            `;
        }
    });

    html += `
            </div>
            <button class="btn-secondary" onclick="location.reload()">
                <span data-en="New batch" data-fr="Nouveau lot">New batch</span>
            </button>
        </div>
    `;

    resultSection.innerHTML = html;
    resultSection.classList.remove('hidden');
}
