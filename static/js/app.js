// DoubleSub.io - Frontend JavaScript

// Etat de l'application
const state = {
    currentMode: 'srt',
    currentLang: 'en',
    files: {
        srt1: null,
        srt2: null
    }
};

// Translations for dynamic content
const translations = {
    en: {
        errorInvalidFormat: 'Unsupported subtitle format. Use: SRT, ASS, SSA',
        processing: 'Processing...',
        mergeSuccess: '{count} subtitles merged successfully!',
        errorMerge: 'Error during merge',
        errorSignup: 'Error during signup',
        errorConnection: 'Connection error'
    },
    fr: {
        errorInvalidFormat: 'Format de sous-titre non supporte. Utilisez: SRT, ASS, SSA',
        processing: 'Traitement en cours...',
        mergeSuccess: '{count} sous-titres fusionnes avec succes!',
        errorMerge: 'Erreur lors de la fusion',
        errorSignup: 'Erreur lors de l\'inscription',
        errorConnection: 'Erreur de connexion'
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

    // Validate file
    const validExtensions = ['srt', 'ass', 'ssa'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
        showError(t('errorInvalidFormat'));
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

    showProgress(t('processing'));

    const formData = new FormData();
    formData.append('mode', mergeMode);
    formData.append('tolerance', tolerance);
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
            showSuccess(data.message, data.output_file, data.cue_count);
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

function showSuccess(message, outputFile, cueCount) {
    const resultSection = document.getElementById('resultSection');
    const successMsg = t('mergeSuccess').replace('{count}', cueCount);
    resultSection.querySelector('.result-message').textContent = successMsg;

    const downloadBtn = document.getElementById('downloadBtn');
    downloadBtn.onclick = () => {
        window.location.href = `/download/${outputFile}`;
    };

    resultSection.classList.remove('hidden');
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
