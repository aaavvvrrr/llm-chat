let currentChatId = null;
let attachedFileContent = null;
let attachedFileName = null;

document.addEventListener('DOMContentLoaded', () => {
    // --- ЭЛЕМЕНТЫ ---
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const modelSelect = document.getElementById('model-select');
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const undoBtn = document.getElementById('undo-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Элементы файлов
    const attachBtn = document.getElementById('attach-btn');
    const hiddenFileInput = document.getElementById('hidden-file-input');
    const filePreview = document.getElementById('file-preview-container');
    const fileNameSpan = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file-btn');

    // --- НАСТРОЙКИ MARKDOWN ---
    marked.setOptions({
        breaks: true, // Перенос строки по Enter
        gfm: true     // GitHub стандарты
    });

    // --- HELPER: Рендер формул (KaTeX) ---
    function renderMath(element) {
        if (!window.renderMathInElement) return; // Защита если библиотека не загрузилась
        renderMathInElement(element, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '\\[', right: '\\]', display: true},
                {left: '\\(', right: '\\)', display: false},
                {left: '(', right: ')', display: false} // Поддержка простых скобок как формул (аккуратно!)
            ],
            throwOnError: false
        });
    }

    // --- HELPER: Модальное окно ---
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

    // --- HELPER: Форматирование имени модели ---
    function formatModelName(modelId) {
        if (!modelId) return '';
        return modelId.replace(':free', '')
                      .replace('meta-llama/', 'Llama ')
                      .replace('google/', 'Google ')
                      .replace('microsoft/', 'MS ')
                      .replace('mistralai/', 'Mistral ');
    }

    // --- РАБОТА С ФАЙЛАМИ ---
    attachBtn.onclick = () => hiddenFileInput.click();

    hiddenFileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 50000) {
            alert("File is too large for free models (max ~50KB).");
            hiddenFileInput.value = '';
            return;
        }
        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target.result;
            if (content.includes('\0')) {
                alert("Binary files are not supported. Text only.");
                return;
            }
            attachedFileContent = content;
            attachedFileName = file.name;
            fileNameSpan.innerText = file.name;
            filePreview.classList.remove('hidden');
        };
        reader.onerror = () => alert("Error reading file");
        reader.readAsText(file);
    };

    removeFileBtn.onclick = () => {
        attachedFileContent = null;
        attachedFileName = null;
        hiddenFileInput.value = '';
        filePreview.classList.add('hidden');
    };

    // --- UI ЛОГИКА (Chat List & Models) ---

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
        }
    }

    async function loadChatList() {
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
    }

    async function createNewChat() {
        const res = await fetch('/api/chats/new', { method: 'POST' });
        const data = await res.json();
        currentChatId = data.id;
        await loadChatList();
        loadChat(currentChatId);
    }

    async function loadChat(chatId) {
        currentChatId = chatId;
        loadChatList();
        const res = await fetch(`/api/chats/${chatId}`);
        const messages = await res.json();
        chatBox.innerHTML = '';
        if (messages.length === 0) {
            chatBox.innerHTML = `<div class="empty-state"><h2>AI Assistant</h2><p>Start typing...</p></div>`;
        } else {
            messages.forEach(msg => appendMessage(msg.role, msg.content, msg.model));
        }
        scrollToBottom();
    }

    // --- ОТОБРАЖЕНИЕ СООБЩЕНИЯ (Append Message) ---
    
// --- ОБНОВЛЕННАЯ ФУНКЦИЯ appendMessage ---
    function appendMessage(role, text, modelId = null, isStreaming = false) {
        document.querySelector('.empty-state')?.remove();
        
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        // 1. СОХРАНЯЕМ СЫРОЙ MARKDOWN В АТРИБУТ (Важно!)
        // Если это стриминг, текст пока неполный, обновим его в sendMessage
        div.setAttribute('data-raw', text);
        
        const avatar = `<div class="avatar"><i class="fa-solid ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>`;
        
        let contentHtml = text;
        if (!isStreaming) {
            contentHtml = role === 'assistant' ? marked.parse(text) : text.replace(/\n/g, '<br>');
        }
        
        // 2. ГЕНЕРИРУЕМ ЗАГОЛОВОК С КНОПКОЙ
        let headerHtml = '';
        if (role === 'assistant') {
            const cleanName = modelId ? formatModelName(modelId) : 'AI';
            
            // Кнопка копирования MD
            const copyMdBtn = `
                <button class="md-copy-btn" title="Copy raw Markdown" onclick="copyMarkdown(this)">
                    <i class="fa-regular fa-file-lines"></i> MD
                </button>
            `;

            headerHtml = `
                <div class="message-header">
                    <span class="message-meta">${cleanName}</span>
                    ${!isStreaming ? copyMdBtn : ''} <!-- Показываем кнопку только когда готово -->
                </div>
            `;
        }

        div.innerHTML = `
            ${avatar}
            <div class="message-body">
                ${headerHtml}
                <div class="content">${contentHtml}</div>
            </div>
        `;

        if (!isStreaming && role === 'assistant') {
            applySyntaxHighlightingAndCopy(div);
            renderMath(div.querySelector('.content'));
        }

        chatBox.appendChild(div);
        scrollToBottom();
        return div; 
    }
    
    // --- НОВАЯ ГЛОБАЛЬНАЯ ФУНКЦИЯ ДЛЯ КОПИРОВАНИЯ ---
    // Мы делаем её глобальной (window.), чтобы работал onclick в HTML строке выше
    window.copyMarkdown = function(btn) {
        // Ищем родительский message div
        const messageDiv = btn.closest('.message');
        const rawText = messageDiv.getAttribute('data-raw');
        
        if (rawText) {
            navigator.clipboard.writeText(rawText).then(() => {
                const originalIcon = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
                setTimeout(() => {
                    btn.innerHTML = originalIcon;
                }, 2000);
            });
        }
    };

    function applySyntaxHighlightingAndCopy(parentElement) {
        parentElement.querySelectorAll('pre').forEach((pre) => {
            // 1. Подсветка
            const codeBlock = pre.querySelector('code');
            if (codeBlock) hljs.highlightElement(codeBlock);

            // 2. Кнопка копирования
            if (!pre.querySelector('.copy-btn')) { // Защита от дублей
                const btn = document.createElement('button');
                btn.className = 'copy-btn';
                btn.innerHTML = '<i class="fa-regular fa-copy"></i>';
                btn.title = 'Copy code';
                
                btn.addEventListener('click', () => {
                    const textToCopy = codeBlock ? codeBlock.innerText : pre.innerText;
                    navigator.clipboard.writeText(textToCopy);
                    btn.innerHTML = '<i class="fa-solid fa-check"></i>';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.innerHTML = '<i class="fa-regular fa-copy"></i>';
                        btn.classList.remove('copied');
                    }, 2000);
                });
                pre.appendChild(btn);
            }
        });
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- ОТПРАВКА СООБЩЕНИЯ (STREAMING) ---

    async function sendMessage() {
        if (!currentChatId) await createNewChat(); 
        
        let text = userInput.value.trim();
        const model = modelSelect.value;

        if (!text && !attachedFileContent) return;
        if (!model) { alert("Select model"); return; }

        // Добавляем файл в текст
        if (attachedFileContent) {
            const filePrompt = `\n\n--- BEGIN FILE: ${attachedFileName} ---\n${attachedFileContent}\n--- END FILE ---\n\n`;
            text = text + filePrompt;
        }

        // Сброс UI
        userInput.value = '';
        userInput.style.height = 'auto';
        removeFileBtn.click();
        
        // 1. Показываем сообщение пользователя
        const userDisplay = attachedFileName 
            ? `${text.split('--- BEGIN FILE')[0].trim()} \n\n*[Attached file: ${attachedFileName}]*` 
            : text;
        appendMessage('user', userDisplay);
        
        // 2. Создаем "контейнер" для ответа ассистента (пустой)
        const assistantMsgDiv = appendMessage('assistant', '', model, true);
        const contentDiv = assistantMsgDiv.querySelector('.content');
        
        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        let fullText = ""; // Сюда копим ответ

        try {
            const response = await fetch(`/api/chats/${currentChatId}/message`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text, model: model })
            });

            // Читаем Stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // Сервер шлет NDJSON. Разбиваем по строкам.
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const json = JSON.parse(line);
                        if (json.chunk) {
                            fullText += json.chunk;
                            // Пока стримим - просто текст (чтобы не ломать HTML разметку на лету)
                            contentDiv.innerText = fullText;
                            scrollToBottom();
                        }
                        if (json.error) {
                            fullText += `\n[Error: ${json.error}]`;
                            contentDiv.innerText = fullText;
                        }
                    } catch (e) {
                        console.error("JSON parse error", e);
                    }
                }
            }

            typingIndicator.classList.add('hidden');

            // 3. Финализация: когда стрим кончился
            
            // ВАЖНО: Сохраняем полный сырой текст в атрибут
            assistantMsgDiv.setAttribute('data-raw', fullText);

            // Перерисовываем заголовок, чтобы появилась кнопка MD (так как при стриме её не было)
            const headerDiv = assistantMsgDiv.querySelector('.message-body');
            // Вставляем заголовок заново (немного хардкода для скорости, но работает надежно)
            const cleanName = formatModelName(model);
            const newHeader = `
                <div class="message-header">
                    <span class="message-meta">${cleanName}</span>
                    <button class="md-copy-btn" title="Copy raw Markdown" onclick="copyMarkdown(this)">
                        <i class="fa-regular fa-file-lines"></i> MD
                    </button>
                </div>
                <div class="content"></div>
            `;
            
            // Аккуратно меняем HTML, сохраняя структуру
            headerDiv.innerHTML = newHeader;
            const newContentDiv = headerDiv.querySelector('.content');
            
            // Рендерим контент
            newContentDiv.innerHTML = marked.parse(fullText);
            
            applySyntaxHighlightingAndCopy(assistantMsgDiv);
            renderMath(newContentDiv);
            
            loadChatList();

        } catch (e) {
            typingIndicator.classList.add('hidden');
            contentDiv.innerHTML += `<br><span style="color:red">Network Error: ${e.message}</span>`;
        }
    }

    // --- КНОПКИ УПРАВЛЕНИЯ ---

    undoBtn.onclick = async () => {
        if (!currentChatId) return;
        const confirm = await showModal('Undo', 'Remove last interaction?');
        if (confirm) {
            const res = await fetch(`/api/chats/${currentChatId}/undo`, { method: 'POST' });
            const messages = await res.json();
            chatBox.innerHTML = '';
            if (messages.length === 0) {
                chatBox.innerHTML = `<div class="empty-state"><h2>AI Assistant</h2><p>Start typing...</p></div>`;
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
            if (historyList.children.length > 0) historyList.children[0].click();
            else createNewChat();
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

    // --- ИНИЦИАЛИЗАЦИЯ ---
    loadModels();
    loadChatList().then(() => {
        const firstChat = document.querySelector('.history-item');
        if (firstChat) firstChat.click();
        else createNewChat();
    });
});