# Руководство по развертыванию проекта

## 1. Клонирование репозитория

```bash
git clone <repository-url>
cd test-generator-mvp
```

## 2. Настройка окружения

Создайте файл **.env** в корне проекта:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

#pgsql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=test_mvp_db
DB_USER=test_mvp_user
DB_PASSWORD=test_mvp_password

#mongo
MONGO_URI=mongodb://admin:admin@localhost:27017/test_generator?authSource=admin
MONGO_DBNAME=test_generator

```

## 3. Запуск базы данных

```bash
# Запуск PostgreSQL в Docker
docker-compose up -d

# Проверка статуса базы
docker-compose logs postgres
```

## 4. Настройка Python окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация окружения
# Для Linux/Mac:
source venv/bin/activate
# Для Windows:
# .\venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

## 5. Применение миграций базы данных

```bash
python migrations/migrate.py
```

## 6. Создание индексов MongoDB

``` bash
python init_mongo_indexes.py
```

## 7. Запуск сервера

```bash
python run.py
```

Сервер будет доступен по адресу: [http://localhost:5000](http://localhost:5000)

## 8. Проверка работоспособности

### Тестирование эндпоинтов

* **Статус сервера:** [http://localhost:5000/health](http://localhost:5000/health)
* **Проверка PostgreSQL:** [http://localhost:5000/test-db](http://localhost:5000/test-db)
* **Проверка MongoDB:** [http://localhost:5000/test-mongo](http://localhost:5000/test-mongo)

**Ожидаемый ответ:**

```json
{
    "status": "OK",
    "message": "Server is running",
    "database": "OK"
}
```
