const socket = io();
const urlParams = new URLSearchParams(window.location.search);
const username = urlParams.get('username') || 'Anonymous';
const roomId = window.location.pathname.split('/').pop();

let editor;
let currentFile = null;
let roomData = { files: {}, users: {}, activeFile: null };
let isOutputPanelCollapsed = false;

function initializeEditor() {
    editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
        lineNumbers: true,
        theme: 'material-darker',
        mode: 'python',
        indentUnit: 4,
        lineWrapping: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        extraKeys: {
            'Ctrl-S': function(cm) {
                saveCurrentFile();
            },
            'Ctrl-/': function(cm) {
                toggleComment(cm);
            }
        }
    });
    
    editor.on('change', debounce(() => {
        if (currentFile) {
            const code = editor.getValue();
            socket.emit('code_change', {
                room_id: roomId,
                file_name: currentFile,
                code: code
            });
        }
    }, 300));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getLanguageFromExtension(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const langMap = {
        'py': 'python',
        'js': 'javascript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'go': 'go',
        'rs': 'rust'
    };
    return langMap[ext] || 'python';
}

function setEditorMode(language) {
    const modeMap = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'text/x-java',
        'c': 'text/x-csrc',
        'cpp': 'text/x-c++src',
        'go': 'go',
        'rust': 'rust'
    };
    editor.setOption('mode', modeMap[language] || 'python');
}

function updateStatus(message) {
    document.getElementById('status-bar').textContent = message;
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function updateFileList() {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    
    Object.keys(roomData.files).forEach(filename => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="file-name">${filename}</span>
            <span class="file-language">${roomData.files[filename].language}</span>
        `;
        li.className = filename === currentFile ? 'active' : '';
        li.onclick = () => switchFile(filename);
        li.oncontextmenu = (e) => showContextMenu(e, filename);
        fileList.appendChild(li);
    });
}

function updateUserList() {
    const userList = document.getElementById('user-list');
    userList.innerHTML = '';
    
    Object.values(roomData.users).forEach((user, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <i class="fas fa-user"></i>
            <span>${user}</span>
            <span class="user-status ${user === username ? 'you' : 'online'}">
                ${user === username ? '(You)' : ''}
            </span>
        `;
        userList.appendChild(li);
    });
}

function switchFile(filename) {
    if (roomData.files[filename]) {
        currentFile = filename;
        const file = roomData.files[filename];
        editor.setValue(file.content);
        setEditorMode(file.language);
        document.getElementById('language-select').value = file.language;
        updateFileList();
        updateStatus(`Editing ${filename}`);
        showToast(`Switched to ${filename}`, 'success');
    }
}

function showContextMenu(e, filename) {
    e.preventDefault();
    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    
    menu.innerHTML = `
        <div onclick="renameFile('${filename}')"><i class="fas fa-edit"></i> Rename</div>
        <div onclick="duplicateFile('${filename}')"><i class="fas fa-copy"></i> Duplicate</div>
        <div onclick="deleteFile('${filename}')"><i class="fas fa-trash"></i> Delete</div>
    `;
    
    document.body.appendChild(menu);
    
    setTimeout(() => {
        document.addEventListener('click', () => {
            if (menu.parentNode) menu.parentNode.removeChild(menu);
        }, { once: true });
    }, 0);
}

function renameFile(filename) {
    const newName = prompt('Enter new filename:', filename);
    if (newName && newName !== filename) {
        socket.emit('rename_file', {
            room_id: roomId,
            old_name: filename,
            new_name: newName
        });
    }
}

function duplicateFile(filename) {
    socket.emit('duplicate_file', {
        room_id: roomId,
        file_name: filename
    });
}

function deleteFile(filename) {
    if (confirm(`Delete ${filename}?`)) {
        socket.emit('delete_file', {
            room_id: roomId,
            file_name: filename
        });
    }
}

function saveCurrentFile() {
    if (currentFile) {
        showToast('File saved automatically', 'success');
    }
}

function toggleComment(cm) {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line);
    const language = roomData.files[currentFile]?.language || 'python';
    
    let commentChar = '# ';
    if (['javascript', 'java', 'c', 'cpp', 'go', 'rust'].includes(language)) {
        commentChar = '// ';
    }
    
    if (line.trim().startsWith(commentChar.trim())) {
        cm.replaceRange('', {line: cursor.line, ch: 0}, {line: cursor.line, ch: commentChar.length});
    } else {
        cm.replaceRange(commentChar, {line: cursor.line, ch: 0});
    }
}

function addChatMessage(username, message, isAI = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isAI ? 'ai-message' : ''}`;
    
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    if (isAI) {
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="username ai-username"><i class="fas fa-robot"></i> ${username}</span>
                <span class="timestamp">${time}</span>
            </div>
            <div class="message-content ai-content">
                <pre>${message}</pre>
                <button class="copy-message-btn" onclick="copyToClipboard('${message.replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="username ${username === 'You' ? 'you' : ''}">${username}</span>
                <span class="timestamp">${time}</span>
            </div>
            <div class="message-content">${message}</div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById('chat-message');
    const message = input.value.trim();
    if (message) {
        if (message.startsWith('/ai ')) {
            const prompt = message.substring(4).trim();
            if (prompt) {
                socket.emit('chat_message', {
                    room_id: roomId,
                    message: message
                });
                addChatMessage('You', `/ai ${prompt}`);
                showToast('AI is thinking...', 'info');
            }
        } else {
            socket.emit('chat_message', {
                room_id: roomId,
                message: message
            });
            addChatMessage('You', message);
        }
        input.value = '';
    }
}

function showAIModal(title, content, type = 'response') {
    const modal = document.getElementById('ai-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = title;
    
    if (type === 'code') {
        modalBody.innerHTML = `
            <div class="code-container">
                <pre><code>${content}</code></pre>
            </div>
        `;
    } else {
        modalBody.innerHTML = `<div class="response-container"><pre>${content}</pre></div>`;
    }
    
    modal.style.display = 'block';
    
    document.getElementById('copy-ai-response-btn').onclick = () => {
        copyToClipboard(content);
    };
}

function closeAIModal() {
    document.getElementById('ai-modal').style.display = 'none';
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function toggleOutputPanel() {
    const outputPanel = document.getElementById('output-panel');
    const toggleBtn = document.getElementById('toggle-output-btn');
    const icon = toggleBtn.querySelector('i');
    
    if (isOutputPanelCollapsed) {
        outputPanel.style.height = '200px';
        icon.className = 'fas fa-chevron-down';
        isOutputPanelCollapsed = false;
    } else {
        outputPanel.style.height = '40px';
        icon.className = 'fas fa-chevron-up';
        isOutputPanelCollapsed = true;
    }
}

function clearOutput() {
    document.getElementById('output').innerHTML = '';
    showToast('Output cleared', 'info');
}

function clearChat() {
    document.getElementById('chat-messages').innerHTML = '';
    showToast('Chat cleared', 'info');
}

socket.on('connect', () => {
    socket.emit('join_room', {
        room_id: roomId,
        username: username
    });
    updateStatus('Connected');
    showToast('Connected to room', 'success');
});

socket.on('room_state', (data) => {
    roomData = data;
    currentFile = data.activeFile;
    updateFileList();
    updateUserList();
    if (currentFile && roomData.files[currentFile]) {
        switchFile(currentFile);
    }
});

socket.on('code_update', (data) => {
    if (data.file_name === currentFile) {
        const cursor = editor.getCursor();
        editor.setValue(data.code);
        editor.setCursor(cursor);
    }
    if (roomData.files[data.file_name]) {
        roomData.files[data.file_name].content = data.code;
    }
});

socket.on('code_output', (data) => {
    const outputDiv = document.getElementById('output');
    outputDiv.innerHTML = `<pre>${data.output}</pre>`;
    updateStatus('Code executed');
    showToast('Code executed successfully', 'success');
});

socket.on('new_chat_message', (data) => {
    const isAI = data.username === 'Gemini AI';
    addChatMessage(data.username, data.message, isAI);
});

socket.on('code_suggestion', (data) => {
    showAIModal('Code Suggestion', data.suggestion);
    updateStatus('AI suggestion received');
});

socket.on('ai_response', (data) => {
    const titles = {
        'code_review': 'Code Review',
        'explanation': 'Code Explanation',
        'code_generation': 'Generated Code',
        'error': 'Error'
    };
    
    showAIModal(titles[data.type] || 'AI Response', data.content, data.type === 'code_generation' ? 'code' : 'response');
    updateStatus('AI response received');
});

socket.on('user_joined', (message) => {
    updateStatus(message);
    showToast(message, 'info');
});

socket.on('user_left', (message) => {
    updateStatus(message);
    showToast(message, 'info');
});

socket.on('error_message', (data) => {
    showToast(data.message, 'error');
});

document.addEventListener('DOMContentLoaded', () => {
    initializeEditor();
    
    // File management
    document.getElementById('create-file-btn').onclick = () => {
        const filename = document.getElementById('new-filename').value.trim();
        if (filename) {
            socket.emit('create_file', {
                room_id: roomId,
                file_name: filename
            });
            document.getElementById('new-filename').value = '';
        }
    };
    
    // Code execution
    document.getElementById('run-button').onclick = () => {
        if (currentFile) {
            updateStatus('Running code...');
            socket.emit('execute_code', {
                room_id: roomId,
                file_name: currentFile
            });
        } else {
            showToast('Please select a file to run', 'error');
        }
    };
    
    // AI Features
    document.getElementById('ai-suggestion-btn').onclick = () => {
        if (currentFile) {
            const file = roomData.files[currentFile];
            socket.emit('get_code_suggestion', {
                language: file.language,
                code: editor.getValue()
            });
            updateStatus('Getting AI suggestion...');
        }
    };
    
    document.getElementById('ai-review-btn').onclick = () => {
        if (currentFile) {
            const file = roomData.files[currentFile];
            socket.emit('ai_code_review', {
                language: file.language,
                code: editor.getValue()
            });
            updateStatus('Getting AI review...');
        }
    };
    
    document.getElementById('ai-explain-btn').onclick = () => {
        if (currentFile) {
            const file = roomData.files[currentFile];
            socket.emit('ai_explain_code', {
                language: file.language,
                code: editor.getValue()
            });
            updateStatus('Getting AI explanation...');
        }
    };
    
    
    // Utility functions
    document.getElementById('format-code-btn').onclick = () => {
        if (currentFile) {
            const code = editor.getValue();
            const formatted = formatCode(code, roomData.files[currentFile].language);
            editor.setValue(formatted);
            updateStatus('Code formatted');
            showToast('Code formatted', 'success');
        }
    };
    
    document.getElementById('download-button').onclick = () => {
        if (currentFile) {
            const code = editor.getValue();
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFile;
            a.click();
            URL.revokeObjectURL(url);
            showToast('File downloaded', 'success');
        }
    };
    
    // Output panel controls
    document.getElementById('copy-output-btn').onclick = () => {
        const output = document.getElementById('output').textContent;
        copyToClipboard(output);
    };
    
    document.getElementById('clear-output-btn').onclick = clearOutput;
    document.getElementById('toggle-output-btn').onclick = toggleOutputPanel;
    
    // Chat controls
    document.getElementById('send-chat-btn').onclick = sendChatMessage;
    document.getElementById('clear-chat-btn').onclick = clearChat;
    
    // Modal controls
    document.getElementById('close-modal-btn').onclick = closeAIModal;
    
    // Keyboard shortcuts
    document.getElementById('chat-message').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
    
    document.getElementById('new-filename').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('create-file-btn').click();
        }
    });
    
    // Close modal when clicking outside
    document.getElementById('ai-modal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('ai-modal')) {
            closeAIModal();
        }
    });
    
    // Language selector change
    document.getElementById('language-select').addEventListener('change', (e) => {
        if (currentFile) {
            const newLanguage = e.target.value;
            setEditorMode(newLanguage);
            roomData.files[currentFile].language = newLanguage;
        }
    });
});

function formatCode(code, language) {
    const lines = code.split('\n');
    let formatted = [];
    let indentLevel = 0;
    
    for (let line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
            formatted.push('');
            continue;
        }
        
        if (language === 'python') {
            if (trimmed.endsWith(':')) {
                formatted.push('    '.repeat(indentLevel) + trimmed);
                indentLevel++;
            } else if (trimmed.startsWith('except') || trimmed.startsWith('elif') || trimmed.startsWith('else') || trimmed.startsWith('finally')) {
                formatted.push('    '.repeat(indentLevel - 1) + trimmed);
            } else {
                formatted.push('    '.repeat(indentLevel) + trimmed);
            }
        } else {
            if (trimmed.includes('}')) indentLevel = Math.max(0, indentLevel - 1);
            formatted.push('    '.repeat(indentLevel) + trimmed);
            if (trimmed.includes('{')) indentLevel++;
        }
    }
    
    return formatted.join('\n');
}

window.renameFile = renameFile;
window.duplicateFile = duplicateFile;
window.deleteFile = deleteFile;
window.copyToClipboard = copyToClipboard;
