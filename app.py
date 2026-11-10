import os
import json
import sqlite3
import requests
from flask import Response, stream_with_context
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev_key")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# ==================== ЛОКАЛЬНАЯ МОДЕЛЬ (ВСЁ В .env) ====================
LOCAL_MODEL_ID = os.getenv("LOCAL_MODEL_ID", "local/qwen3.5-27b")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "Local: Qwen3.5-27B (llama.cpp)")
LOCAL_MODEL_URL = os.getenv("LOCAL_MODEL_URL", "http://localhost:8010")
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", "0.7"))
LOCAL_MAX_TOKENS = int(os.getenv("LOCAL_MAX_TOKENS", "16384"))

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Flask Chat Service",
    "Content-Type": "application/json"
}

# --- DATABASE ---
if not os.path.exists('data'):
    os.makedirs('data')
DB_NAME = "data/chat.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        # Таблица чатов (system_prompt убираем или оставляем для совместимости)
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
        
        # === НОВАЯ ТАБЛИЦА ДЛЯ ГЛОБАЛЬНЫХ НАСТРОЕК ===
        c.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY,
                      value TEXT)''')
        
        # Миграция: если раньше был system_prompt в chats — можно перенести, но пока игнорируем
        try:
            c.execute("ALTER TABLE messages ADD COLUMN model TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Добавляем дефолтный глобальный промпт (если ещё нет)
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                  ("global_system_prompt", 
                   """ 
Ты — ассистент базы данных орнитологического питомника. Твоя задача — анализировать сообщения сотрудников о пересадке птиц между комнатами (вольерами) и извлекать из них данные в строгом формате JSON.

ПРАВИЛА ИЗВЛЕЧЕНИЯ:
1. В одном сообщении может быть несколько перемещений. Выводи их списком в массиве "transfers".
2. Поля для каждой пересадки:
   - "ring": номер кольца птицы (обычно 4 цифры, например "1503", "1756"). Если нет, пиши null.
   - "gender": пол птицы ("Самец" или "Самка"). Если не указан, пиши null.
   - "morph": морфа ("Тёмный", "Светлый", "Дикий тип"). "Темная" -> "Тёмный". Если не указана, пиши null.
   - "from_room": комната, ОТКУДА забрали (например "1/2л", "517", "402", "стадион"). Если не указано, пиши null.
   - "to_room": комната, КУДА посадили.
3. Обрати внимание на контекст. Если написано "В 1/5п Самец 1756", значит to_room="1/5п", ring="1756", gender="Самец", from_room=null.
4. Отвечай ТОЛЬКО валидным JSON, без markdown разметки, без пояснений.

ПРИМЕР ВХОДА:
"Из 1/2л самка 1503 в 517
Из 3/8п самец 1883 в 604"

ПРИМЕР ВЫХОДА:
{
  "transfers": [
    {
      "ring": "1503",
      "gender": "Самка",
      "morph": null,
      "from_room": "1/2л",
      "to_room": "517"
    },
    {
      "ring": "1883",
      "gender": "Самец",
      "morph": null,
      "from_room": "3/8п",
      "to_room": "604"
    }
  ]
}
"""))
        
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# ====================== MODELS ======================
@app.route('/api/models', methods=['GET'])
def list_models():
    models = []
    models.append({
        "id": LOCAL_MODEL_ID,
        "name": LOCAL_MODEL_NAME,
        "local": True
    })
    # ... (остальной код получения бесплатных моделей OpenRouter без изменений)
    try:
        response = requests.get(f"{OPENROUTER_URL}/models", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            free_models = [
                model for model in data
                if ":free" in model["id"] or
                   (float(model.get("pricing", {}).get("prompt", -1)) == 0 and
                    float(model.get("pricing", {}).get("completion", -1)) == 0)
            ]
            free_models.sort(key=lambda x: x["name"])
            models.extend(free_models)
    except Exception as e:
        print(f"Error fetching OpenRouter models: {e}")

    if len(models) == 1:
        models.extend([
            {"id": "google/gemini-2.0-flash-exp:free", "name": "Google: Gemini 2.0 Flash (Free)"},
            {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Meta: Llama 3.2 3B (Free)"},
            {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Microsoft: Phi-3 Medium (Free)"},
        ])
    return jsonify(models)

# ====================== LOCAL MODEL ======================
def stream_local_model(history):
    payload = {
        "messages": history,
        "stream": True,
        "temperature": LOCAL_TEMPERATURE,
        "max_tokens": LOCAL_MAX_TOKENS
    }
    # ... (остальной код стриминга без изменений)
    try:
        with requests.post(
            f"{LOCAL_MODEL_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=120,
            stream=True
        ) as r:
            if r.status_code != 200:
                yield json.dumps({"error": f"Local model error: {r.text}"})
                return
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:]
                        if json_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(json_str)
                            content = chunk_json['choices'][0]['delta'].get('content', '')
                            if content:
                                yield json.dumps({"chunk": content}) + "\n"
                        except Exception:
                            pass
    except Exception as e:
        yield json.dumps({"error": f"Connection error: {str(e)}"})


# ====================== CHAT ROUTES ======================
@app.route('/api/chats/new', methods=['POST'])
def create_chat():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chats (title, system_prompt) VALUES (?, ?)', ("New Chat", None))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": chat_id, "title": "New Chat"})

# ... (get_chats, get_chat_history, delete_chat, undo_last — без изменений)

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

    system_row = conn.execute("SELECT value FROM settings WHERE key = 'global_system_prompt'").fetchone()
    system_prompt = system_row["value"] if system_row and system_row["value"] else None

    # Получаем историю сообщений
    history_rows = conn.execute('SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    conn.close()

    # Сборка истории
    history = []
    if system_prompt:
        history.append({"role": "system", "content": system_prompt})
    history.extend([{"role": row["role"], "content": row["content"]} for row in history_rows])

    is_local = model_id == LOCAL_MODEL_ID or model_id.startswith("local/")

    def generate():
        full_response = []
        try:
            if is_local:
                for chunk in stream_local_model(history):
                    if chunk:
                        yield chunk
                        try:
                            chunk_data = json.loads(chunk.strip())
                            if "chunk" in chunk_data:
                                full_response.append(chunk_data["chunk"])
                        except Exception:
                            pass
            else:
                # OpenRouter
                payload = {"model": model_id, "messages": history, "stream": True}
                with requests.post(f"{OPENROUTER_URL}/chat/completions", headers=HEADERS, data=json.dumps(payload), timeout=60, stream=True) as r:
                    # ... (тот же стриминг, что был раньше)
                    if r.status_code != 200:
                        yield json.dumps({"error": f"Error: {r.text}"})
                        return
                    for line in r.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                json_str = decoded_line[6:]
                                if json_str.strip() == "[DONE]":
                                    break
                                try:
                                    chunk_json = json.loads(json_str)
                                    content = chunk_json['choices'][0]['delta'].get('content', '')
                                    if content:
                                        full_response.append(content)
                                        yield json.dumps({"chunk": content}) + "\n"
                                except Exception:
                                    pass
        except Exception as e:
            yield json.dumps({"error": str(e)})

        # Сохраняем полный ответ
        final_text = "".join(full_response)
        if final_text:
            with sqlite3.connect(DB_NAME) as db:
                db.execute('INSERT INTO messages (chat_id, role, content, model) VALUES (?, ?, ?, ?)',
                           (chat_id, 'assistant', final_text, model_id))
                db.commit()

    return Response(stream_with_context(generate()), content_type='application/x-ndjson')

# --- API ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')


# --- LOCAL MODEL HELPER ---

def check_local_model_available():
    """Проверяет доступность локального llama-server."""
    try:
        response = requests.get(f"{LOCAL_MODEL_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False



# --- CHAT MANAGEMENT ---

@app.route('/api/chats', methods=['GET'])
def get_chats():
    conn = get_db_connection()
    chats = conn.execute('SELECT * FROM chats ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in chats])

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

@app.route('/api/local-model/status', methods=['GET'])
def local_model_status():
    """Проверяет доступность локальной модели."""
    is_available = check_local_model_available()
    if is_available:
        return jsonify({
            "status": "online",
            "model": LOCAL_MODEL_ID,
            "url": LOCAL_MODEL_URL
        })
    else:
        return jsonify({
            "status": "offline",
            "model": LOCAL_MODEL_ID,
            "url": LOCAL_MODEL_URL,
            "message": "llama-server недоступен. Запустите сервер для использования локальной модели."
        }), 503
    
@app.route('/api/system-prompt', methods=['GET', 'POST'])
def global_system_prompt():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        prompt = data.get('system_prompt')
        if prompt == "":
            prompt = None
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                     ("global_system_prompt", prompt))
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})
    
    row = conn.execute("SELECT value FROM settings WHERE key = 'global_system_prompt'").fetchone()
    conn.close()
    return jsonify({"system_prompt": row["value"] if row else None})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=9001, host='0.0.0.0')