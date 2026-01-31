// ============ Global Variables ============
let socket;
let editor;
let currentFile = null;
let currentLanguage = 'python';
let roomUsers = [];
let username = localStorage.getItem('username') || 'Anonymous';
let userColor = '#' + Math.floor(Math.random() * 16777215).toString(16);
let settings = {
    theme: 'monokai',
    font_size: 14,
    tab_size: 4,
    auto_save: true
};
let aiApiKey = localStorage.getItem('aiApiKey') || '';
let isCodeChanging = false;
let saveTimeout = null;
let remoteCursors = {};
let aiProvider = localStorage.getItem('aiProvider') || 'gemini';
let aiModel = localStorage.getItem('aiModel') || 'gemini-pro';

// ============ Initialization ============
document.addEventListener('DOMContentLoaded', function () {
    initializeEditor();
    initializeSocket();
    loadSettings();
    loadFiles();
    setupEventListeners();
    setupSidebarTabs();
    setupOutputTabs();
    loadAISettings();

    // Set initial username display
    document.getElementById('username-display').textContent = username;
});

// ============ Editor Setup ============
function initializeEditor() {
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/python");
    editor.setFontSize(14);
    editor.setOptions({
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: true,
        showPrintMargin: false,
        highlightActiveLine: true,
        displayIndentGuides: true,
        fontFamily: "'JetBrains Mono', monospace"
    });

    editor.session.on('change', function (delta) {
        if (!isCodeChanging && currentFile) {
            const content = editor.getValue();
            socket.emit('code_change', {
                room: ROOM_ID,
                file: currentFile,
                content: content,
                auto_save: settings.auto_save
            });

            updateFileStatus('Modified');

            if (settings.auto_save) {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(function () {
                    saveCurrentFile();
                }, 2000);
            }
        }
    });

    editor.selection.on('changeCursor', function () {
        const cursor = editor.getCursorPosition();
        socket.emit('cursor_move', {
            room: ROOM_ID,
            cursor: cursor
        });
    });
}

// ============ Socket.IO Setup ============
function initializeSocket() {
    socket = io();

    socket.on('connect', function () {
        console.log('Connected to server');
        socket.emit('join', {
            room: ROOM_ID,
            username: username,
            color: userColor
        });
    });

    socket.on('user_joined', function (data) {
        console.log('User joined:', data.username);
        // Use a Set to ensure unique users if needed, or trust server
        roomUsers = data.users;
        updateUsersList();
        addChatMessage('System', data.username + ' joined the room', 'system');
    });

    socket.on('user_left', function (data) {
        console.log('User left:', data.username);
        roomUsers = data.users;
        updateUsersList();
        addChatMessage('System', data.username + ' left the room', 'system');

        if (remoteCursors[data.sid]) {
            // Remove remote cursor marker if implemented
            delete remoteCursors[data.sid];
        }
    });

    socket.on('update_code', function (data) {
        if (data.file === currentFile) {
            isCodeChanging = true;
            const cursor = editor.getCursorPosition();
            editor.setValue(data.content, -1);
            editor.moveCursorToPosition(cursor);
            isCodeChanging = false;
            updateFileStatus('Synced');
        }
    });

    socket.on('chat_message', function (data) {
        addChatMessage(data.username, data.message, 'user');
    });

    socket.on('terminal_output', function (data) {
        addTerminalOutput(data.command, data.output);
    });

    socket.on('disconnect', function () {
        console.log('Disconnected from server');
        updateFileStatus('Disconnected');
        addChatMessage('System', 'Disconnected from server', 'error');
    });
}

// ============ Event Listeners ============
function setupEventListeners() {
    document.getElementById('copy-room-id').addEventListener('click', function () {
        navigator.clipboard.writeText(ROOM_ID);
        const icon = this.querySelector('i');
        icon.className = 'fas fa-check';
        setTimeout(() => icon.className = 'fas fa-copy', 1500);
    });

    document.getElementById('leave-room').addEventListener('click', function () {
        if (confirm('Are you sure you want to leave this room?')) {
            socket.emit('leave', { room: ROOM_ID, username: username });
            window.location.href = '/';
        }
    });

    document.getElementById('new-file-btn').addEventListener('click', showNewFileModal);
    document.getElementById('refresh-files-btn').addEventListener('click', loadFiles);
    document.getElementById('save-file-btn').addEventListener('click', saveCurrentFile);
    document.getElementById('run-code-btn').addEventListener('click', runCode);
    document.getElementById('analyze-code-btn').addEventListener('click', analyzeCode);

    document.getElementById('ai-assist-btn').addEventListener('click', toggleAIPanel);
    document.getElementById('close-ai-panel').addEventListener('click', toggleAIPanel);

    document.getElementById('close-file-btn').addEventListener('click', closeCurrentFile);
    document.getElementById('settings-btn').addEventListener('click', showSettingsModal);
    document.getElementById('close-settings').addEventListener('click', hideSettingsModal);
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);

    document.getElementById('close-new-file').addEventListener('click', hideNewFileModal);
    document.getElementById('new-file-form').addEventListener('submit', function (e) {
        e.preventDefault();
        createNewFile();
    });

    document.getElementById('create-dir-btn').addEventListener('click', function () {
        const dirname = prompt('Enter folder name:');
        if (dirname) {
            fetch('/api/create_dir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id: ROOM_ID, dirname: dirname })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) loadFiles();
                });
        }
    });

    // Chat / Terminal inputs
    document.getElementById('chat-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendChatMessage();
    });
    document.getElementById('send-chat').addEventListener('click', sendChatMessage);

    document.getElementById('terminal-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') executeTerminalCommand();
    });
    document.getElementById('terminal-send').addEventListener('click', executeTerminalCommand);

    document.getElementById('send-ai-btn').addEventListener('click', sendAIMessage);
    document.getElementById('clear-output-btn').addEventListener('click', function () {
        document.getElementById('output-text').textContent = '';
    });

    // Settings listeners
    document.getElementById('ai-provider').addEventListener('change', function () {
        aiProvider = this.value;
        localStorage.setItem('aiProvider', this.value);
        // Reset model logic if needed
    });
    document.getElementById('ai-api-key').addEventListener('change', function () {
        aiApiKey = this.value;
        localStorage.setItem('aiApiKey', this.value);
    });
}

// ============ UI Helpers ============
function updateUsersList() {
    const usersList = document.getElementById('users-list');
    usersList.innerHTML = '';

    roomUsers.forEach(user => {
        const avatar = document.createElement('div');
        avatar.className = 'user-avatar';
        avatar.title = user;
        avatar.textContent = user.substring(0, 2).toUpperCase();

        // Deterministic color
        const color = '#' + stringToColor(user);
        avatar.style.background = color;
        // Check constrast
        avatar.style.color = getContrastColor(color);

        usersList.appendChild(avatar);
    });
}

function stringToColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    let color = '';
    for (let i = 0; i < 3; i++) {
        let value = (hash >> (i * 8)) & 0xFF;
        color += ('00' + value.toString(16)).substr(-2);
    }
    return color;
}

function getContrastColor(hexcolor) {
    hexcolor = hexcolor.replace('#', '');
    var r = parseInt(hexcolor.substr(0, 2), 16);
    var g = parseInt(hexcolor.substr(2, 2), 16);
    var b = parseInt(hexcolor.substr(4, 2), 16);
    var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
    return (yiq >= 128) ? 'black' : 'white';
}

function updateFileStatus(status) {
    const el = document.getElementById('file-status');
    if (!el) return;
    el.textContent = status;

    if (status === 'Saved' || status === 'Synced') {
        el.style.color = 'var(--success)';
    } else if (status === 'Modified') {
        el.style.color = 'var(--accent)';
    } else {
        el.style.color = 'var(--text-muted)';
    }
}

function toggleAIPanel() {
    const panel = document.getElementById('ai-panel');
    const isVisible = panel.getAttribute('data-visible') === 'true';
    if (isVisible) {
        panel.removeAttribute('data-visible');
    } else {
        panel.setAttribute('data-visible', 'true');
    }
}

function showNewFileModal() { document.getElementById('new-file-modal').classList.add('visible'); }
function hideNewFileModal() { document.getElementById('new-file-modal').classList.remove('visible'); }
function showSettingsModal() { document.getElementById('settings-modal').classList.add('visible'); }
function hideSettingsModal() { document.getElementById('settings-modal').classList.remove('visible'); }

function setupSidebarTabs() {
    setupTabs('#sidebar-tabs button', '#sidebar-content > div', 'data-tab', 'data-panel');
}

function setupOutputTabs() {
    setupTabs('#output-tabs button', '#output-content > div', 'data-output-tab', 'data-output-panel');
}

function setupTabs(tabSelector, panelSelector, tabAttr, panelAttr) {
    const tabs = document.querySelectorAll(tabSelector);
    const panels = document.querySelectorAll(panelSelector);

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute(tabAttr);

            tabs.forEach(t => t.removeAttribute('data-active'));
            tab.setAttribute('data-active', 'true');

            panels.forEach(panel => {
                if (panel.getAttribute(panelAttr) === target) {
                    panel.setAttribute('data-active', 'true');
                } else {
                    panel.removeAttribute('data-active');
                }
            });
        });
    });
}

// ============ File Management ============
function loadFiles() {
    fetch('/api/files/' + ROOM_ID)
        .then(res => res.json())
        .then(files => displayFiles(files))
        .catch(err => console.error(err));
}

function displayFiles(files) {
    const list = document.getElementById('files-list');
    list.innerHTML = '';

    if (files.length === 0) {
        list.innerHTML = '<div style="padding:15px; text-align:center; opacity:0.5; font-size:0.8rem;">No files</div>';
        return;
    }

    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        // Icon matching
        let iconClass = 'fas fa-file';
        if (file.type === 'python') iconClass = 'fab fa-python';
        else if (file.type === 'javascript') iconClass = 'fab fa-js';
        else if (file.type === 'html') iconClass = 'fab fa-html5';
        else if (file.type === 'css') iconClass = 'fab fa-css3-alt';
        else if (file.type === 'java') iconClass = 'fab fa-java';

        item.innerHTML = `<i class="${iconClass} file-icon"></i> <span class="file-name">${file.name}</span> <button class="delete-btn"><i class="fas fa-times"></i></button>`;

        item.addEventListener('click', () => {
            document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            openFile(file.path);
        });

        item.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteFile(file.path);
        });

        list.appendChild(item);
    });
}

function openFile(filename) {
    fetch('/api/files/' + ROOM_ID + '/' + filename)
        .then(res => res.json())
        .then(data => {
            currentFile = filename;
            isCodeChanging = true;
            editor.setValue(data.content, -1);
            isCodeChanging = false;

            currentLanguage = detectLanguage(filename);
            setEditorMode(currentLanguage);

            document.getElementById('current-file').textContent = filename;
            updateFileStatus('Loaded');
        });
}

function saveCurrentFile() {
    if (!currentFile) return;
    const content = editor.getValue();

    fetch('/api/save_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: ROOM_ID, filename: currentFile, content: content })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) updateFileStatus('Saved');
            else updateFileStatus('Error');
        });
}

function createNewFile() {
    const filename = document.getElementById('new-file-name').value.trim();
    const language = document.getElementById('file-language').value;

    if (!filename) return;

    fetch('/api/create_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: ROOM_ID, filename: filename, language: language })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadFiles();
                hideNewFileModal();
            } else {
                alert('Failed to create file');
            }
        });
}

function deleteFile(filename) {
    if (!confirm('Delete ' + filename + '?')) return;

    fetch('/api/delete_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: ROOM_ID, filename: filename })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadFiles();
                if (currentFile === filename) closeCurrentFile();
            }
        });
}

function closeCurrentFile() {
    currentFile = null;
    editor.setValue('', -1);
    document.getElementById('current-file').textContent = 'No file';
    document.getElementById('file-status').textContent = '';
}

// ============ Code Execution ============
function runCode() {
    if (!currentFile) return alert('No file open');

    document.querySelector('[data-output-tab="output"]').click();
    document.getElementById('output-text').textContent = 'Running...';

    const input = document.getElementById('code-input').value;

    fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            language: currentLanguage,
            code: editor.getValue(),
            input: input,
            room_id: ROOM_ID,
            filename: currentFile
        })
    })
        .then(res => res.json())
        .then(data => {
            document.getElementById('output-text').textContent = data.output;
        });
}

// ============ Chat & AI ============
function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    socket.emit('chat_message', { room: ROOM_ID, message: msg });
    input.value = '';
}

function addChatMessage(username, message, type) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    div.innerHTML = `<strong>${username} ${type === 'system' ? '' : `<span>${time}</span>`}</strong><p>${message}</p>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function executeTerminalCommand() {
    const input = document.getElementById('terminal-input');
    const cmd = input.value.trim();
    if (!cmd) return;

    socket.emit('terminal_input', { room: ROOM_ID, command: cmd });
    input.value = '';
    // Optimistic UI could go here
}

function addTerminalOutput(command, output) {
    const container = document.getElementById('terminal-output');
    const div = document.createElement('div');
    div.innerHTML = `<div style="color:var(--text-muted);">$ ${command}</div><pre>${output}</pre>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function loadAISettings() {
    if (document.getElementById('ai-provider')) document.getElementById('ai-provider').value = aiProvider;
    if (document.getElementById('ai-api-key')) document.getElementById('ai-api-key').value = aiApiKey;
}

function sendAIMessage() {
    const input = document.getElementById('ai-input');
    const prompt = input.value.trim();
    if (!prompt) return;
    if (!aiApiKey) return alert('Please set API Key');

    const context = document.getElementById('include-code-context').checked && currentFile ? {
        code: editor.getValue(), language: currentLanguage
    } : null;

    addAIMessage('You', prompt);
    input.value = '';
    addAIMessage('AI', 'Thinking...');

    fetch('/api/ai_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt, context: context, api_key: aiApiKey,
            provider: aiProvider, model: aiModel, task: document.getElementById('ai-task').value
        })
    })
        .then(res => res.json())
        .then(data => {
            // remove 'Thinking...'
            const msgs = document.getElementById('ai-messages');
            if (msgs.lastChild && msgs.lastChild.textContent.includes('Thinking...')) msgs.removeChild(msgs.lastChild);

            addAIMessage('AI', data.response);
        });
}

function addAIMessage(sender, text) {
    const container = document.getElementById('ai-messages');
    const div = document.createElement('div');
    div.style.background = sender === 'AI' ? 'rgba(255,255,255,0.05)' : 'rgba(0, 242, 254, 0.1)';
    div.style.padding = '10px';
    div.style.borderRadius = '8px';
    div.innerHTML = `<strong>${sender}:</strong> <span>${text}</span>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function analyzeCode() {
    if (!currentFile) return alert('No file');
    document.querySelector('[data-output-tab="analysis"]').click();

    fetch('/api/analyze_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editor.getValue(), language: currentLanguage })
    })
        .then(res => res.json())
        .then(data => {
            const m = data.analysis;
            document.getElementById('metrics').innerHTML = `
            <h5>Metrics</h5>
            <p>Lines: ${m.total_lines}</p>
            <p>Complexity: ${m.cyclomatic_complexity} (${m.complexity_rating})</p>
        `;
            document.getElementById('suggestions').innerHTML = '<h5>Suggestions</h5>' +
                (data.suggestions.length ? data.suggestions.map(s => `<div>[${s.type}] ${s.message}</div>`).join('') : 'No suggestions');
        });
}

function loadSettings() {
    fetch('/api/settings/' + ROOM_ID)
        .then(res => res.json())
        .then(data => {
            settings = data;
            applySettings();
        });
}

function saveSettings() {
    settings.theme = document.getElementById('theme-select').value;
    settings.font_size = parseInt(document.getElementById('font-size').value);
    settings.tab_size = parseInt(document.getElementById('tab-size').value);
    settings.auto_save = document.getElementById('auto-save').checked;

    fetch('/api/settings/' + ROOM_ID, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    }).then(res => res.json()).then(data => {
        if (data.success) { applySettings(); hideSettingsModal(); }
    });
}

function applySettings() {
    editor.setTheme("ace/theme/" + settings.theme);
    editor.setFontSize(settings.font_size);
    editor.session.setTabSize(settings.tab_size);

    document.getElementById('theme-select').value = settings.theme;
    document.getElementById('font-size').value = settings.font_size;
    document.getElementById('tab-size').value = settings.tab_size;
    document.getElementById('auto-save').checked = settings.auto_save;
}

function detectLanguage(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const map = {
        'py': 'python', 'js': 'javascript', 'java': 'java', 'html': 'html', 'css': 'css', 'cpp': 'cpp', 'rs': 'rust', 'ts': 'typescript', 'go': 'go'
    };
    return map[ext] || 'text';
}

function setEditorMode(lang) {
    const mode = {
        'python': 'python', 'javascript': 'javascript', 'java': 'java', 'html': 'html', 'css': 'css', 'cpp': 'c_cpp', 'rust': 'rust', 'typescript': 'typescript', 'go': 'golang'
    }[lang] || 'text';
    editor.session.setMode("ace/mode/" + mode);
}