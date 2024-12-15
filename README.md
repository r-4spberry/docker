
# Инструментарий создания и анализа математических записей. Команда "Котики", 2024

---

## Структура проекта
```plaintext
.
├── client/           # Фронтенд-приложение на основе Vite
│   ├── Dockerfile
│   └── ...
├── server/           # Бэкенд-сервер на Flask
│   ├── Dockerfile
│   └── ...
└── docker-compose.yml
```

---

## Предварительные требования
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Запуск проекта

1. Клонируйте репозиторий:
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. Запустите сервисы с помощью Docker Compose:
   ```bash
   docker compose up --build
   ```

3. Доступ к приложению:
   - **Фронтенд (Vite)**: `http://localhost:8080`
   - **Бэкенд (Flask API)**: `http://localhost:5000`

---

## Устранение неполадок
- Убедитесь, что Docker и Docker Compose установлены и работают.
- Проверьте, что порты `8080` и `5000` не заняты другими процессами.

---

## Лицензия
Лицензия MIT
