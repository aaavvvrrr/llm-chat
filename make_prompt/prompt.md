# Промпт с кодовой базой

**Сгенерировано:** make_prompt

**Источник:** `/home/avr/work/llm-chat`

**Файлов найдено:** 5

## Оглавление

- [README.md](#READMEmd)
- [app.py](#apppy)
- [static/script.js](#static/scriptjs)
- [static/style.css](#static/stylecss)
- [templates/index.html](#templates/indexhtml)

---

<a id='READMEmd'></a>

* README.md

```markdown
# 🚀 Flask AI Chat Service

Современный, легковесный и производительный чат-интерфейс для работы с LLM моделями через OpenRouter API. Проект сфокусирован на использовании **бесплатных моделей** (Free Tier), сохранении контекста и удобстве разработчика.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Особенности

*   **🤖 Поддержка OpenRouter:** Автоматический парсинг и фильтрация бесплатных моделей (Llama 3, Mistral, Gemini, etc.).
*   **💾 История чатов (SQLite):** Создание множества диалогов, автоматическое сохранение переписки. История сохраняется даже после перезагрузки контейнера.
*   **📎 Работа с файлами:** Возможность прикрепить код или текстовый файл для анализа (Client-side processing).
*   **🎨 Современный UI:**
    *   Темная тема (Dark Mode) в стиле IDE.
    *   Подсветка синтаксиса кода (Highlight.js).
    *   Рендеринг Markdown (Marked.js).
    *   Адаптивность (Mobile/Desktop).
*   **⚡ Функционал:**
    *   Возможность отмены последнего шага (Undo).
    *   Индикатор печати (Typing indicator).
    *   Запоминание последней выбранной модели.
*   **🐳 Docker Support:** Полная контейнеризация для быстрого развертывания.

---

## 🛠 Технологический стек

*   **Backend:** Python, Flask, SQLite, Requests.
*   **Frontend:** Vanilla JS, CSS3 (Flexbox/Grid), HTML5.
*   **Libraries:** Highlight.js, Marked.js, FontAwesome.
*   **DevOps:** Docker, Docker Compose.

---

## 🚀 Установка и запуск

### Предварительные требования
1.  Получите API Key на [OpenRouter.ai](https://openrouter.ai/).
2.  Установленный Python 3.x или Docker.

### Способ 1: Запуск через Docker (Рекомендуется)

Самый простой способ. Не требует установки зависимостей Python локально.

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/aaavvvrrr/flask-ai-chat.git
    cd flask-ai-chat
    ```

2.  **Создайте файл `.env`:**
    ```bash
    # Linux/Mac
    cp .env.example .env
    # Или создайте вручную
    ```
    Вставьте ваш ключ:
    ```env
    OPENROUTER_API_KEY=sk-or-v1-ваш-ключ...
    FLASK_SECRET_KEY=придумайте_случайную_строку
    ```

3.  **Запустите проект:**
    ```bash
    docker-compose up --build
    ```

4.  Откройте браузер по адресу: `http://localhost:5000`

---

### Способ 2: Локальный запуск (Python)

1.  **Создайте виртуальное окружение:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Mac/Linux
    venv\Scripts\activate     # Windows
    ```

2.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Настройте `.env`** (см. пункт выше).

4.  **Запустите сервер:**
    ```bash
    python app.py
    ```

---

## 📂 Структура проекта

```text
├── flask_ai_chat/
│   ├── static/             # Статические файлы
│   │   ├── style.css       # Стили (Dark Theme)
│   │   └── script.js       # Логика фронтенда (Fetch, UI)
│   ├── templates/
│   │   └── index.html      # Основной HTML шаблон
│   ├── app.py              # Flask сервер и логика БД
│   ├── requirements.txt    # Зависимости Python
│   ├── Dockerfile          # Инструкция сборки образа
│   ├── docker-compose.yml  # Оркестрация контейнеров
│   └── .env                # Переменные окружения (Секреты)
```


---

## 💡 Использование

1.  **Выбор модели:** При загрузке страницы приложение само подтянет список доступных бесплатных моделей. Выберите нужную из выпадающего списка.
2.  **Чат:** Пишите сообщения, используйте Markdown. Код будет автоматически подсвечен.
3.  **Файлы:** Нажмите на иконку 📎 (скрепка), чтобы загрузить текстовый файл или код. Он будет добавлен к контексту вашего вопроса.
4.  **Управление:**
    *   `New Chat` — создать чистый диалог.
    *   `Undo` (стрелка назад) — удалить последний вопрос и ответ.
    *   `Delete` (мусорка) — удалить текущий чат навсегда.

---

## 👤 Автор

**Architected & Coded by Gemini 3.0 Pro**
*(Prompted by a aaavvvrrr)*

Проект создан с целью демонстрации возможностей современных LLM в генерации чистого, рабочего и поддерживаемого кода.

---

## 📄 Лицензия

MIT License. Используйте свободно.
```


```

---

<a id='apppy'></a>

* app.py

```python
import os
import json
import sqlite3
import requests
from flask import Response, stream_with_context 
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev_key")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Заголовки для OpenRouter
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Flask Chat Service",
    "Content-Type": "application/json"
}

# --- DATABASE HELPER ---
# Убедись, что папка data существует (для продакшн варианта)
if not os.path.exists('data'):
    os.makedirs('data')

DB_NAME = "data/chat.db" 

def init_db():
    """Создает таблицы и обновляет схему при необходимости."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Таблица чатов
        c.execute('''CREATE TABLE IF NOT EXISTS chats 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Таблица сообщений
        c.execute('''CREATE TABLE IF NOT EXISTS messages 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      chat_id INTEGER, 
                      role TEXT, 
                      content TEXT, 
                      model TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE)''')
        
        # --- МИГРАЦИЯ ---
        # Пытаемся добавить колонку model, если база была создана ранее без неё
        try:
            c.execute("ALTER TABLE messages ADD COLUMN model TEXT")
        except sqlite3.OperationalError:
            pass # Колонка уже существует, игнорируем ошибку
            
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Позволяет обращаться к полям по имени
    return conn

# Инициализируем БД при старте
init_db()

# --- API ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def list_models():
    """Получает список моделей и фильтрует только бесплатные."""
    try:
        response = requests.get(f"{OPENROUTER_URL}/models", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            # Фильтруем модели, содержащие ':free' в ID или имеющие нулевую стоимость
            free_models = [
                model for model in data 
                if ":free" in model["id"] or 
                (float(model.get("pricing", {}).get("prompt", -1)) == 0 and 
                 float(model.get("pricing", {}).get("completion", -1)) == 0)
            ]
            # Сортируем по алфавиту
            free_models.sort(key=lambda x: x["name"])
            return jsonify(free_models)
    except Exception as e:
        print(f"Error fetching models: {e}")
    
    # Fallback список, если API не ответил
    return jsonify([
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Google: Gemini 2.0 Flash (Free)"},
        {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Meta: Llama 3.2 3B (Free)"},
        {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Microsoft: Phi-3 Medium (Free)"},
    ])

# --- CHAT MANAGEMENT ---

@app.route('/api/chats', methods=['GET'])
def get_chats():
    conn = get_db_connection()
    chats = conn.execute('SELECT * FROM chats ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in chats])

@app.route('/api/chats/new', methods=['POST'])
def create_chat():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chats (title) VALUES (?)', ("New Chat",))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": chat_id, "title": "New Chat"})

@app.route('/api/chats/<int:chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    conn = get_db_connection()
    # Выбираем колонку model тоже
    messages = conn.execute('SELECT role, content, model FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in messages])

@app.route('/api/chats/<int:chat_id>/delete', methods=['DELETE'])
def delete_chat(chat_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route('/api/chats/<int:chat_id>/message', methods=['POST'])
def send_message(chat_id):
    data = request.json
    user_msg = data.get('message')
    model_id = data.get('model')
    
    if not user_msg or not model_id:
        return jsonify({"error": "Required fields missing"}), 400

    conn = get_db_connection()
    
    # 1. Сохраняем сообщение юзера
    conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', 
                 (chat_id, 'user', user_msg))
    
    # Обновляем заголовок чата, если он новый
    msg_count = conn.execute('SELECT count(*) FROM messages WHERE chat_id = ?', (chat_id,)).fetchone()[0]
    if msg_count <= 1:
        new_title = user_msg[:30] + "..." if len(user_msg) > 30 else user_msg
        conn.execute('UPDATE chats SET title = ? WHERE id = ?', (new_title, chat_id))
    
    conn.commit()

    # 2. Получаем контекст
    history_rows = conn.execute('SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    history = [{"role": row["role"], "content": row["content"]} for row in history_rows]
    conn.close() # Закрываем соединение перед стримом

    payload = {
        "model": model_id,
        "messages": history,
        "stream": True  # ВАЖНО: Включаем стриминг в API OpenRouter
    }

    def generate():
        full_response = []
        try:
            # Делаем запрос с stream=True
            with requests.post(
                f"{OPENROUTER_URL}/chat/completions",
                headers=HEADERS,
                data=json.dumps(payload),
                timeout=60,
                stream=True # Важно для requests
            ) as r:
                if r.status_code != 200:
                    yield json.dumps({"error": f"Error: {r.text}"})
                    return

                # Читаем поток построчно
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        # OpenRouter шлет "data: {...}"
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:] # Убираем "data: "
                            if json_str.strip() == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(json_str)
                                content = chunk_json['choices'][0]['delta'].get('content', '')
                                if content:
                                    full_response.append(content)
                                    # Отправляем кусочек фронтенду
                                    yield json.dumps({"chunk": content}) + "\n"
                            except Exception:
                                pass
        except Exception as e:
            yield json.dumps({"error": str(e)})

        # 3. После завершения стрима сохраняем ПОЛНЫЙ ответ в БД
        final_text = "".join(full_response)
        if final_text:
            # Открываем новое соединение, так как старое закрыто, а мы внутри генератора
            # В Flask это допустимо, но нужно быть аккуратным с потоками. 
            # SQLite в Python по умолчанию запрещает шаринг соединения между потоками, поэтому создаем новое.
            with sqlite3.connect(DB_NAME) as db:
                db.execute('INSERT INTO messages (chat_id, role, content, model) VALUES (?, ?, ?, ?)', 
                             (chat_id, 'assistant', final_text, model_id))
                db.commit()

    return Response(stream_with_context(generate()), content_type='application/x-ndjson')


@app.route('/api/chats/<int:chat_id>/undo', methods=['POST'])
def undo_last(chat_id):
    """Удаляет последние 2 сообщения (assistant + user)"""
    conn = get_db_connection()
    last_ids = conn.execute('SELECT id FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 2', (chat_id,)).fetchall()
    
    if last_ids:
        for row in last_ids:
            conn.execute('DELETE FROM messages WHERE id = ?', (row['id'],))
        conn.commit()
        
    # Возвращаем обновленную историю (включая model)
    messages = conn.execute('SELECT role, content, model FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in messages])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, host='0.0.0.0')
```

---

<a id='static/scriptjs'></a>

* static/script.js

```javascript
let currentChatId = null;
let attachedFileContent = null;
let attachedFileName = null;

// --- HELPER: Экранирование HTML (защита от <тегов>) ---
    function escapeHtml(text) {
        if (!text) return text;
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

// --- HELPER: Автокоррекция LaTeX ---
    // Превращает ( \frac{1}{2} ) в \( \frac{1}{2} \), чтобы KaTeX это увидел.
    // Игнорирует обычный текст в скобках (текст).
    function preprocessLaTeX(text) {
        if (!text) return text;
        // Регулярка ищет (...) внутри которых есть хотя бы один обратный слеш "\"
        return text.replace(/\(([^)]*\\+[^)]*)\)/g, '\\($1\\)');
    }    

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
        if (!window.renderMathInElement) return; 
        renderMathInElement(element, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '\\[', right: '\\]', display: true},
                {left: '\\(', right: '\\)', display: false},
                // ❌ УДАЛИ ИЛИ ЗАКОММЕНТИРУЙ СТРОКУ НИЖЕ:
                // {left: '(', right: ')', display: false} 
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
            if (role === 'assistant') {
                contentHtml = marked.parse(preprocessLaTeX(text));
            } else {
                // Сначала экранируем скобки < >, потом меняем переносы строк
                contentHtml = escapeHtml(text).replace(/\n/g, '<br>');
            }
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
```

---

<a id='static/stylecss'></a>

* static/style.css

```css
:root {
    --bg-color: #343541;
    --sidebar-bg: #202123;
    --main-bg: #343541;
    --input-bg: #40414f;
    --border-color: #4d4d4f;
    --text-primary: #ececec;
    --text-secondary: #c5c5d2;
    --accent: #10a37f;
    --accent-hover: #1a7f64;
    --modal-bg: #2d2d2d;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', sans-serif;
    background-color: var(--main-bg);
    color: var(--text-primary);
    height: 100vh;
    overflow: hidden;
}

.layout {
    display: flex;
    height: 100%;
}

/* --- Sidebar --- */
.sidebar {
    width: 260px;
    background-color: var(--sidebar-bg);
    display: flex;
    flex-direction: column;
    padding: 10px;
    border-right: 1px solid #333;
    transition: transform 0.3s ease;
}

.new-chat-btn {
    width: 100%;
    padding: 10px;
    background: transparent;
    border: 1px solid #565869;
    border-radius: 5px;
    color: white;
    text-align: left;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9rem;
}

.new-chat-btn:hover { background: rgba(255,255,255,0.1); }

.history-list {
    margin-top: 20px;
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.history-item {
    padding: 10px;
    border-radius: 5px;
    cursor: pointer;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.9rem;
    transition: background 0.2s;
}

.history-item:hover { background: #2a2b32; }
.history-item.active { background: #343541; color: white; }

/* --- Main Content --- */
.main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
}

.chat-header {
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--main-bg);
    border-bottom: 1px solid rgba(0,0,0,0.1);
}

/* --- Обновленный селектор моделей --- */

/* Контейнер (обертка) */
.model-selector-wrapper {
    display: flex;
    align-items: center;
    gap: 10px;
    background-color: var(--sidebar-bg);
    padding: 5px 15px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    max-width: 60%; 
}

.model-selector-wrapper i {
    color: var(--text-secondary);
}

/* Сам выпадающий список */
select#model-select {
    background-color: var(--sidebar-bg);
    color: var(--text-primary);
    border: none;
    outline: none;
    font-size: 0.95rem;
    width: 100%;
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
}

/* Стили для выпадающих пунктов */
select#model-select option {
    background-color: #202123;
    color: #ececec;
    padding: 10px;
}

select#model-select:focus {
    box-shadow: none;
}

/* Chat Area */
.chat-box {
    flex: 1;
    overflow-y: auto;
    padding: 20px 10%;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.empty-state {
    text-align: center;
    margin-top: 30vh;
    color: #666;
}

/* Сообщения */
.message {
    display: flex;
    gap: 15px;
    padding: 20px;
    border-radius: 8px;
    align-items: flex-start; /* Аватар сверху */
}

.message.assistant { background: #444654; }
.message.user { background: transparent; }

.message .avatar {
    width: 30px;
    height: 30px;
    flex-shrink: 0;
    background: var(--accent);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
}
.message.user .avatar { background: #555; }

/* Обертка для контента и меты */
.message-body {
    flex: 1;
    overflow-x: hidden;
}

/* Стиль подписи модели */
/* Контейнер для мета-информации (Имя модели + Кнопки) */
/* Контейнер для мета-информации (Имя модели + Кнопки) */
.message-header {
    display: flex;
    align-items: center;
    justify-content: space-between; /* <--- ГЛАВНОЕ ИЗМЕНЕНИЕ: разносит элементы по краям */
    margin-bottom: 5px;
    width: 100%; /* Гарантирует, что заголовок занимает всю ширину */
}

/* Имя модели */
.message-meta {
    font-size: 0.75rem;
    color: var(--accent);
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Кнопка копирования Markdown */
.md-copy-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.8rem;
    padding: 2px 5px;
    border-radius: 4px;
    opacity: 0; /* Скрыта по умолчанию */
    transition: opacity 0.2s, color 0.2s;
}

/* Показываем кнопку только когда наводим мышь на сообщение */
.message:hover .md-copy-btn {
    opacity: 1;
}

.md-copy-btn:hover {
    color: white;
    background: rgba(255,255,255,0.1);
}

.message.assistant .message-meta {
    color: var(--accent);
}

.content {
    line-height: 1.6;
    width: 100%;
}

/* Обновляем контейнер кода */
.content pre { 
    margin: 15px 0; 
    border-radius: 8px; 
    overflow: hidden; 
    background: #282c34; 
    position: relative; /* ВАЖНО: чтобы кнопка позиционировалась относительно этого блока */
}

/* Стиль кнопки копирования */
.copy-btn {
    position: absolute;
    top: 6px;
    right: 6px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 4px;
    color: #c5c5d2;
    cursor: pointer;
    padding: 5px 8px;
    font-size: 0.8rem;
    transition: all 0.2s;
    display: flex; /* По умолчанию скрываем или показываем, тут оставим видимым */
    align-items: center;
    justify-content: center;
}

.copy-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
}

/* Анимация нажатия (опционально) */
.copy-btn.copied {
    color: #10a37f; /* Зеленый цвет успеха */
    background: rgba(16, 163, 127, 0.1);
}

/* Стили для самого кода */
.content pre code {
    display: block;
    padding: 15px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    overflow-x: auto; /* Горизонтальный скролл */
    color: #abb2bf;   /* Базовый цвет текста */
    background: transparent; /* Фон берем от pre */
}

/* Класс hljs добавляется скриптом, но если его нет - стили выше сработают */
.content pre code.hljs {
    background: transparent; /* Гарантируем прозрачность, чтобы не было двойного фона */
    padding: 15px;
}

/* Input Area */
.chat-input-area {
    padding: 30px 10%;
    background-image: linear-gradient(180deg, rgba(53,53,65,0), #353541 50%);
    position: relative;
}

.input-wrapper {
    background: var(--input-bg);
    border: 1px solid rgba(0,0,0,0.3);
    border-radius: 12px;
    padding: 10px 15px;
    display: flex;
    align-items: flex-end;
    gap: 10px;
    box-shadow: 0 0 15px rgba(0,0,0,0.1);
}

textarea {
    flex: 1;
    background: transparent;
    border: none;
    color: white;
    resize: none;
    max-height: 200px;
    font-family: inherit;
    font-size: 1rem;
    outline: none;
    padding: 5px;
}

.send-btn, .secondary-btn, .icon-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 8px;
    border-radius: 5px;
    transition: 0.2s;
}

.send-btn { background: var(--accent); color: white; border-radius: 8px; }
.send-btn:hover { background: var(--accent-hover); }
.secondary-btn:hover, .icon-btn:hover { background: rgba(255,255,255,0.1); color: white; }

/* --- Modal --- */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(5px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}
.modal-overlay.hidden { display: none; }

.modal-content {
    background: var(--modal-bg);
    padding: 25px;
    border-radius: 10px;
    width: 350px;
    border: 1px solid #444;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    text-align: center;
}

.modal-actions {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 10px;
}

.btn-confirm, .btn-cancel {
    padding: 8px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-weight: 600;
}
.btn-confirm { background: #ef4444; color: white; }
.btn-cancel { background: #555; color: white; }

/* Typing Indicator */
.typing-indicator {
    padding: 20px 10%;
    display: flex;
    gap: 5px;
    min-height: 20px;
}

.typing-indicator.hidden {
    display: none !important;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    background: #888;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}

/* --- File Preview --- */
.file-preview {
    position: absolute;
    top: -50px;
    left: 10%;
    z-index: 5;
}

.file-preview.hidden {
    display: none;
}

.file-chip {
    background: #40414f;
    border: 1px solid #565869;
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-primary);
    font-size: 0.9rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    animation: slideUp 0.2s ease-out;
}

.file-chip i.fa-file-code {
    color: var(--accent);
}

#remove-file-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    margin-left: 5px;
}

#remove-file-btn:hover {
    color: #ef4444;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
```

---

<a id='templates/indexhtml'></a>

* templates/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pro AI Chat</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
</head>
<body>

    <div class="layout">
        <!-- Сайдбар -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <button id="new-chat-btn" class="new-chat-btn">
                    <i class="fa-solid fa-plus"></i> New Chat
                </button>
            </div>
            <div class="history-list" id="history-list">
                <!-- Сюда загружаются чаты -->
            </div>
        </aside>

        <!-- Основная зона -->
        <div class="main-content">
            <header class="chat-header">
                <div class="model-selector-wrapper">
                    <i class="fa-solid fa-microchip"></i>
                    <select id="model-select" title="Choose Model">
                        <option value="" disabled selected>Loading models...</option>
                    </select>
                </div>

                <div class="controls">
                    <button id="delete-chat-btn" class="icon-btn" title="Delete current chat">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </header>

            <main id="chat-box" class="chat-box">
                <div class="empty-state">
                    <h2>AI Assistant</h2>
                    <p>Create a new chat or select one from history.</p>
                </div>
            </main>

            <div id="typing-indicator" class="typing-indicator hidden">
                <span></span><span></span><span></span>
            </div>

                <footer class="chat-input-area">
                    <!-- Контейнер для превью файла -->
                    <div id="file-preview-container" class="file-preview hidden">
                        <div class="file-chip">
                            <i class="fa-solid fa-file-code"></i>
                            <span id="file-name">code.py</span>
                            <button id="remove-file-btn"><i class="fa-solid fa-xmark"></i></button>
                        </div>
                    </div>

                    <div class="input-wrapper">
                        <!-- Скрытый инпут -->
                        <input type="file" id="hidden-file-input" style="display: none;">

                        <button id="undo-btn" class="secondary-btn" title="Undo last turn">
                            <i class="fa-solid fa-rotate-left"></i>
                        </button>

                        <!-- Кнопка скрепки -->
                        <button id="attach-btn" class="secondary-btn" title="Attach file (text/code)">
                            <i class="fa-solid fa-paperclip"></i>
                        </button>

                        <textarea id="user-input" rows="1" placeholder="Type a message..."></textarea>

                        <button id="send-btn" class="send-btn">
                            <i class="fa-solid fa-arrow-up"></i>
                        </button>
                    </div>
                </footer>
        </div>
    </div>

    <!-- Модальное окно -->
    <div id="confirm-modal" class="modal-overlay hidden">
        <div class="modal-content">
            <h3 id="modal-title">Confirm Action</h3>
            <p id="modal-text">Are you sure?</p>
            <div class="modal-actions">
                <button id="modal-cancel" class="btn-cancel">Cancel</button>
                <button id="modal-confirm" class="btn-confirm">Confirm</button>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.0.0/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>

```

---

