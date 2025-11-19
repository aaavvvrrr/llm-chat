import os
import json
import sqlite3
import requests
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
    model_id = data.get('model') # ID модели
    
    if not user_msg or not model_id:
        return jsonify({"error": "Message and model are required"}), 400

    conn = get_db_connection()
    
    # 1. Сохраняем сообщение пользователя
    conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', 
                 (chat_id, 'user', user_msg))
    
    # Обновляем название чата, если это первое сообщение
    msg_count = conn.execute('SELECT count(*) FROM messages WHERE chat_id = ?', (chat_id,)).fetchone()[0]
    if msg_count <= 1:
        new_title = user_msg[:30] + "..." if len(user_msg) > 30 else user_msg
        conn.execute('UPDATE chats SET title = ? WHERE id = ?', (new_title, chat_id))
    
    conn.commit()

    # 2. Собираем контекст для API
    history_rows = conn.execute('SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,)).fetchall()
    # Для API нам нужны только role и content
    history = [{"role": row["role"], "content": row["content"]} for row in history_rows]

    payload = {
        "model": model_id,
        "messages": history
    }

    try:
        response = requests.post(
            f"{OPENROUTER_URL}/chat/completions",
            headers=HEADERS,
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code == 200:
            ai_content = response.json()['choices'][0]['message']['content']
            
            # Сохраняем ответ ИИ ВМЕСТЕ С ИМЕНЕМ МОДЕЛИ
            conn.execute('INSERT INTO messages (chat_id, role, content, model) VALUES (?, ?, ?, ?)', 
                         (chat_id, 'assistant', ai_content, model_id))
            conn.commit()
            conn.close()
            
            # Возвращаем имя модели фронтенду
            return jsonify({"response": ai_content, "model": model_id})
        else:
            conn.close()
            return jsonify({"error": f"Provider Error: {response.text}"}), response.status_code

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

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