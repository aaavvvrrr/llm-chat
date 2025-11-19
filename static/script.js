let currentChatId = null;
let attachedFileContent = null;
let attachedFileName = null;

document.addEventListener('DOMContentLoaded', () => {
    // Элементы UI
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const modelSelect = document.getElementById('model-select');
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const undoBtn = document.getElementById('undo-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Элементы загрузки файла
    const attachBtn = document.getElementById('attach-btn');
    const hiddenFileInput = document.getElementById('hidden-file-input');
    const filePreview = document.getElementById('file-preview-container');
    const fileNameSpan = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file-btn');

    // Настройка Markdown
    marked.setOptions({
        highlight: (code, lang) => {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });

    // --- МОДАЛЬНОЕ ОКНО ---
    function showModal(title, text) {
        return new Promise((resolve) => {
            const modal = document.getElementById('confirm-modal');
            document.getElementById('modal-title').innerText = title;
            document.getElementById('modal-text').innerText = text;
            modal.classList.remove('hidden');

            const confirmBtn = document.getElementById('modal-confirm');
            const cancelBtn = document.getElementById('modal-cancel');

            const cleanup = () => {
                modal.classList.add('hidden');
                confirmBtn.onclick = null;
                cancelBtn.onclick = null;
            };

            confirmBtn.onclick = () => { cleanup(); resolve(true); };
            cancelBtn.onclick = () => { cleanup(); resolve(false); };
        });
    }

    // --- РАБОТА С ФАЙЛАМИ ---

    attachBtn.onclick = () => {
        hiddenFileInput.click();
    };

    hiddenFileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 50000) {
            alert("File is too large for free models context (max ~50KB).");
            hiddenFileInput.value = '';
            return;
        }

        const reader = new FileReader();
        
        reader.onload = (event) => {
            const content = event.target.result;
            if (content.includes('\0')) {
                alert("Binary files (images/pdf/exe) are not supported yet. Text/Code only.");
                return;
            }
            
            attachedFileContent = content;
            attachedFileName = file.name;
            
            fileNameSpan.innerText = file.name;
            filePreview.classList.remove('hidden');
        };

        reader.onerror = () => {
            alert("Error reading file");
        };

        reader.readAsText(file);
    };

    removeFileBtn.onclick = () => {
        attachedFileContent = null;
        attachedFileName = null;
        hiddenFileInput.value = '';
        filePreview.classList.add('hidden');
    };

    // --- ОСНОВНЫЕ ФУНКЦИИ ---

    async function loadModels() {
        try {
            const res = await fetch('/api/models');
            const models = await res.json();
            modelSelect.innerHTML = '';
            
            if(models.length === 0) {
                modelSelect.add(new Option('No free models found', ''));
                return;
            }

            models.forEach(m => {
                const name = m.name.replace(' (Free)', '');
                modelSelect.add(new Option(name, m.id));
            });

            const savedModel = localStorage.getItem('selected_model');
            if (savedModel && [...modelSelect.options].some(opt => opt.value === savedModel)) {
                modelSelect.value = savedModel;
            }

        } catch (e) {
            console.error("Error loading models:", e);
            modelSelect.innerHTML = '<option>Error loading models</option>';
        }
    }

    async function loadChatList() {
        try {
            const res = await fetch('/api/chats');
            const chats = await res.json();
            historyList.innerHTML = '';
            
            chats.forEach(chat => {
                const div = document.createElement('div');
                div.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
                div.innerText = chat.title || 'New Chat';
                div.onclick = () => loadChat(chat.id);
                historyList.appendChild(div);
            });
        } catch (e) {
            console.error("Error loading history:", e);
        }
    }

    async function createNewChat() {
        const res = await fetch('/api/chats/new', { method: 'POST' });
        const data = await res.json();
        currentChatId = data.id;
        await loadChatList();
        loadChat(currentChatId);
    }

    // Форматирование имени модели для UI
    function formatModelName(modelId) {
        if (!modelId) return '';
        // Очистка имени от лишних тегов
        let name = modelId.replace(':free', '')
                          .replace('meta-llama/', 'Llama ')
                          .replace('google/', 'Google ')
                          .replace('microsoft/', 'MS ')
                          .replace('mistralai/', 'Mistral ');
        return name;
    }

    async function loadChat(chatId) {
        currentChatId = chatId;
        loadChatList();
        
        const res = await fetch(`/api/chats/${chatId}`);
        const messages = await res.json();
        
        chatBox.innerHTML = '';
        if (messages.length === 0) {
            chatBox.innerHTML = `
            <div class="empty-state">
                <h2>AI Assistant</h2>
                <p>Start typing to begin conversation.</p>
            </div>`;
        } else {
            messages.forEach(msg => appendMessage(msg.role, msg.content, msg.model));
        }
        scrollToBottom();
    }

    function appendMessage(role, text, modelId = null) {
        document.querySelector('.empty-state')?.remove();
        
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        const avatar = `<div class="avatar"><i class="fa-solid ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>`;
        const contentHtml = role === 'assistant' ? marked.parse(text) : text.replace(/\n/g, '<br>');
        
        // Создаем блок с именем модели
        let metaHtml = '';
        if (role === 'assistant' && modelId) {
            const cleanName = formatModelName(modelId);
            metaHtml = `<div class="message-meta">${cleanName}</div>`;
        }

        div.innerHTML = `
            ${avatar}
            <div class="message-body">
                ${metaHtml}
                <div class="content">${contentHtml}</div>
            </div>
        `;

        chatBox.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- ДЕЙСТВИЯ ---

    async function sendMessage() {
        if (!currentChatId) await createNewChat(); 
        
        let text = userInput.value.trim();
        const model = modelSelect.value;

        if (!text && !attachedFileContent) return;
        if (!model) {
            alert("Please select a model first.");
            return;
        }

        if (attachedFileContent) {
            const filePrompt = `\n\n--- BEGIN FILE: ${attachedFileName} ---\n${attachedFileContent}\n--- END FILE ---\n\n`;
            text = text + filePrompt;
        }

        userInput.value = '';
        userInput.style.height = 'auto';
        removeFileBtn.click();
        
        if (attachedFileName) {
            appendMessage('user', `${text.split('--- BEGIN FILE')[0].trim()} \n\n*[Attached file: ${attachedFileName}]*`);
        } else {
            appendMessage('user', text);
        }
        
        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        try {
            const res = await fetch(`/api/chats/${currentChatId}/message`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text, model: model })
            });
            
            const data = await res.json();
            typingIndicator.classList.add('hidden');
            
            if (res.ok) {
                // Используем модель из ответа сервера, или текущую выбранную
                appendMessage('assistant', data.response, data.model || model);
                loadChatList(); 
            } else {
                appendMessage('assistant', `Error: ${data.error}`);
            }
        } catch (e) {
            typingIndicator.classList.add('hidden');
            appendMessage('assistant', `Network error: ${e}`);
        }
    }

    undoBtn.onclick = async () => {
        if (!currentChatId) return;
        const confirm = await showModal('Undo', 'Remove last question and answer?');
        if (confirm) {
            const res = await fetch(`/api/chats/${currentChatId}/undo`, { method: 'POST' });
            const messages = await res.json();
            
            chatBox.innerHTML = '';
            if (messages.length === 0) {
                chatBox.innerHTML = `
                <div class="empty-state">
                    <h2>AI Assistant</h2>
                    <p>Start typing to begin conversation.</p>
                </div>`;
            } else {
                messages.forEach(msg => appendMessage(msg.role, msg.content, msg.model));
            }
        }
    };

    deleteChatBtn.onclick = async () => {
        if (!currentChatId) return;
        const confirm = await showModal('Delete Chat', 'This cannot be undone.');
        if (confirm) {
            await fetch(`/api/chats/${currentChatId}/delete`, { method: 'DELETE' });
            currentChatId = null;
            chatBox.innerHTML = '';
            await loadChatList();
            if (historyList.children.length > 0) {
                historyList.children[0].click();
            } else {
                createNewChat();
            }
        }
    };

    newChatBtn.onclick = createNewChat;

    modelSelect.addEventListener('change', function() {
        localStorage.setItem('selected_model', this.value);
    });

    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.onclick = sendMessage;

    // Инициализация
    loadModels();
    loadChatList().then(() => {
        const firstChat = document.querySelector('.history-item');
        if (firstChat) firstChat.click();
        else createNewChat();
    });
});