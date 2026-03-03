# 🚀 Flask AI Chat Service

Современный, легковесный и производительный чат-интерфейс для работы с LLM моделями через OpenRouter API. Проект сфокусирован на использовании **бесплатных моделей** (Free Tier), сохранении контекста и удобстве разработчика.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Особенности

*   **🤖 Поддержка OpenRouter:** Автоматический парсинг и фильтрация бесплатных моделей (Llama 3, Mistral, Gemini, etc.).
*   **🏠 Локальные модели:** Поддержка локальных LLM через llama.cpp server (Qwen, Llama, Mistral и др.).
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

### 🏠 Запуск с локальной моделью (llama.cpp)

Для использования локальной модели (например, Qwen3.5-27B):

1.  **Запустите llama-server:**
    ```bash
    ~/github/llama.cpp/build/bin/llama-server \
      -m ./final_models/llm/Qwen3.5-27B-IQ4_XS.gguf \
      -ngl 99 -fa on -c 16384 --port 8010 --host 0.0.0.0
    ```

2.  **Настройте `.env`:**
    ```env
    LOCAL_MODEL_ID=local/qwen3.5-27b
    LOCAL_MODEL_URL=http://localhost:8010
    ```

3.  **Запустите Flask приложение** (через Docker или локально).

4.  В интерфейсе выберите модель **"Local: Qwen3.5-27B (llama.cpp)"**.

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

