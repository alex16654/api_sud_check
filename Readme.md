# Руководство по использованию API оценки качества изображений

## Содержание
1. [Обзор](#1-обзор)
2. [Подключение к API](#2-подключение-к-api)
3. [Доступные эндпоинты](#3-доступные-эндпоинты)
4. [Использование клиентской библиотеки](#4-использование-клиентской-библиотеки)
5. [Примеры запросов на разных языках](#5-примеры-запросов-на-разных-языках)
   - [5.1. Python](#51-python-с-библиотекой-requests)
   - [5.2. JavaScript](#52-javascript-с-fetch-api)
   - [5.3. PHP](#53-php)
6. [Обработка ошибок](#6-обработка-ошибок)
7. [Оптимизация производительности](#7-оптимизация-производительности)
8. [Часто задаваемые вопросы](#8-часто-задаваемые-вопросы)
9. [Установка](#9-Установка-и-развертывание-API)

## 1. Обзор

API оценки качества изображений предоставляет сервис для анализа и оценки качества изображений с использованием алгоритма на основе BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator). API возвращает числовую оценку, где более низкие значения обычно указывают на более низкое качество изображения.

### Основные возможности:
- Оценка качества изображений через загрузку файла
- Оценка качества изображений по пути к файлу на сервере
- Настройка параметров обработки (например, уменьшение размера для ускорения)
- Проверка состояния API

## 2. Подключение к API

### Базовый URL
```
http://<server-address>:8000
```

Замените `<server-address>` на IP-адрес или доменное имя сервера, на котором развернут API.

### Проверка доступности
Перед началом использования API рекомендуется проверить его доступность:

```bash
curl http://<server-address>:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "timestamp": 1710615123.456789,
  "active_requests": 0,
  "queue_size": 0,
  "max_workers": 4,
  "max_concurrent_requests": 6
}
```

## 3. Доступные эндпоинты

### 3.1. Получение информации об API

**Запрос:**
```
GET /
```

**Ответ:**
```json
{
  "message": "Image Quality Assessment API",
  "version": "1.0.0",
  "endpoints": {
    "/score-from-file": "Upload an image file to get quality score",
    "/score-from-path": "Provide a path to an image file to get quality score",
    "/health": "Health check endpoint"
  },
  "status": "available"
}
```

### 3.2. Оценка качества по загруженному файлу

**Запрос:**
```
POST /score-from-file
```

**Параметры:**
- `file`: Файл изображения (multipart/form-data)
- `downscale` (опционально): Коэффициент уменьшения изображения (от 0.1 до 1.0, по умолчанию 1.0)

**Пример с curl:**
```bash
curl -X POST http://<server-address>:8000/score-from-file \
  -F "file=@/path/to/your/image.jpg" \
  -F "downscale=1.0"
```

**Ответ:**
```json
{
  "filename": "image.jpg",
  "score": 42.56
}
```

### 3.3. Оценка качества по пути к файлу

**Запрос:**
```
POST /score-from-path
```

**Параметры:**
- `image_path`: Путь к файлу изображения на сервере (form-data)
- `downscale` (опционально): Коэффициент уменьшения изображения (от 0.1 до 1.0, по умолчанию 1.0)

**Пример с curl:**
```bash
curl -X POST http://<server-address>:8000/score-from-path \
  -d "image_path=/data/images/sample.jpg" \
  -d "downscale=1.0"
```

**Ответ:**
```json
{
  "filename": "sample.jpg",
  "score": 38.72
}
```

### 3.4. Проверка состояния API

**Запрос:**
```
GET /health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": 1710615123.456789,
  "active_requests": 1,
  "queue_size": 0,
  "max_workers": 4,
  "max_concurrent_requests": 6
}
```

## 4. Использование клиентской библиотеки

Для удобства взаимодействия с API предоставляется Python-клиент `image_quality_client.py`. Клиент поддерживает все функции API и добавляет дополнительные возможности, такие как повторные попытки, обработка ошибок и пакетная обработка.

### 4.1. Установка зависимостей

```bash
pip install requests tqdm
```

### 4.2. Использование клиента как библиотеки

```python
from image_quality_client import ImageQualityClient

# Создание клиента
client = ImageQualityClient(
    base_url="http://<server-address>:8000",
    timeout=30,
    max_retries=3
)

# Проверка состояния API
health = client.health_check()
print(f"API Status: {health['status']}")

# Оценка качества по пути к файлу
result = client.score_from_path("/path/to/image.jpg", downscale=1.0)
print(f"Score for {result['filename']}: {result['score']}")

# Оценка качества по загруженному файлу
result = client.score_from_file("/path/to/image.jpg", downscale=1.0)
print(f"Score for {result['filename']}: {result['score']}")

# Обработка всех изображений в директории
results = client.process_directory(
    "/path/to/images",
    use_upload=True,  # True для загрузки файлов, False для использования путей
    max_workers=5,
    downscale=1.0
)

# Вывод статистики
scores = [r['score'] for r in results if 'score' in r]
if scores:
    print(f"Average score: {sum(scores) / len(scores):.2f}")
    print(f"Min score: {min(scores):.2f}")
    print(f"Max score: {max(scores):.2f}")
```

### 4.3. Использование клиента из командной строки

```bash
# Оценка качества одного изображения по пути
python image_quality_client.py --url http://<server-address>:8000 --path /path/to/image.jpg

# Оценка качества одного изображения через загрузку
python image_quality_client.py --url http://<server-address>:8000 --file /path/to/image.jpg

# Обработка всех изображений в директории и сохранение результатов в CSV
python image_quality_client.py --url http://<server-address>:8000 --dir /path/to/images --output results.csv --upload --workers 5
```

## 5. Примеры запросов на разных языках

### 5.1. Python (с библиотекой requests)

```python
import requests
import os

# Оценка качества по загруженному файлу
def score_image_file(api_url, image_path, downscale=1.0):
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        data = {'downscale': str(downscale)}
        
        response = requests.post(
            f"{api_url}/score-from-file",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API error: {response.json().get('error', 'Unknown error')}")

# Пример использования
try:
    result = score_image_file("http://<server-address>:8000", "/path/to/image.jpg", 0.5)
    print(f"Score: {result['score']}")
except Exception as e:
    print(f"Error: {str(e)}")
```

### 5.2. JavaScript (с fetch API)

```javascript
// Оценка качества по загруженному файлу
async function scoreImageFile(apiUrl, imageFile, downscale = 1.0) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('downscale', downscale);
  
  try {
    const response = await fetch(`${apiUrl}/score-from-file`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`API error: ${errorData.error || 'Unknown error'}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error scoring image:', error);
    throw error;
  }
}

// Пример использования в браузере
const fileInput = document.getElementById('imageFile');
const scoreButton = document.getElementById('scoreButton');
const resultDiv = document.getElementById('result');

scoreButton.addEventListener('click', async () => {
  if (fileInput.files.length === 0) {
    resultDiv.textContent = 'Please select a file';
    return;
  }
  
  try {
    resultDiv.textContent = 'Processing...';
    const result = await scoreImageFile('http://<server-address>:8000', fileInput.files[0], 0.5);
    resultDiv.textContent = `Score: ${result.score}`;
  } catch (error) {
    resultDiv.textContent = `Error: ${error.message}`;
  }
});
```

### 5.3. PHP

```php
<?php
    
    /**
     * Проверка состояния API
     */
    public function healthCheck() {
        return $this->makeRequest('GET', '/health');
    }
    
    /**
     * Оценка качества изображения по загруженному файлу
     */
    public function scoreFromFile($filePath, $downscale = 1.0) {
        if (!file_exists($filePath)) {
            throw new Exception("File not found: $filePath");
        }
        
        $cFile = new CURLFile($filePath, mime_content_type($filePath), basename($filePath));
        $data = [
            'file' => $cFile,
            'downscale' => $downscale
        ];
        
        return $this->makeRequest('POST', '/score-from-file', $data, true);
    }
```

## 6. Обработка ошибок

API может возвращать следующие коды ошибок:

| Код | Описание | Рекомендуемое действие |
|-----|----------|------------------------|
| 400 | Bad Request | Проверьте параметры запроса |
| 404 | Not Found | Проверьте URL и путь к файлу |
| 413 | Payload Too Large | Уменьшите размер файла или используйте параметр downscale |
| 500 | Internal Server Error | Сообщите администратору API |
| 503 | Service Unavailable | Повторите запрос позже с экспоненциальной задержкой |

### Пример обработки ошибок с повторными попытками:

```python
import time
import random
import requests

def request_with_retry(url, method="GET", data=None, files=None, max_retries=3, backoff_factor=1.5):
    """Make a request with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = requests.get(url)
            else:  # POST
                response = requests.post(url, data=data, files=files)
            
            # Check for server overload (503)
            if response.status_code == 503:
                retry_after = int(response.headers.get('Retry-After', 1))
                wait_time = retry_after + random.uniform(0, 0.5)
                print(f"Server overloaded. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            
            # Return successful response
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            # Calculate backoff time
            wait_time = (backoff_factor ** attempt) + random.uniform(0, 0.5)
            
            if attempt < max_retries - 1:
                print(f"Request failed: {str(e)}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"Request failed after {max_retries} attempts: {str(e)}")
                raise
```

## 7. Оптимизация производительности

### 7.1. Параметр downscale

Параметр `downscale` позволяет уменьшить размер изображения перед обработкой, что значительно ускоряет процесс и снижает нагрузку на сервер:

- `downscale=1.0` - изображение обрабатывается в оригинальном размере
- `downscale=0.5` - изображение уменьшается до 50% от оригинального размера
- `downscale=0.25` - изображение уменьшается до 25% от оригинального размера

Рекомендации по выбору значения:
- Для высокоточной оценки: `downscale=1.0`
- Для быстрой оценки: `downscale=0.5`
- Для обработки большого количества изображений: `downscale=0.25`

### 7.2. Параллельная обработка

При обработке множества изображений используйте параллельную обработку:

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def score_image(image_path, api_url, downscale=1.0):
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        data = {'downscale': str(downscale)}
        response = requests.post(f"{api_url}/score-from-file", files=files, data=data)
        return response.json() if response.status_code == 200 else None

def process_images_in_parallel(image_paths, api_url, max_workers=5, downscale=1.0):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(score_image, path, api_url, downscale): path for path in image_paths}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    return results
```

### 7.3. Выбор эндпоинта

- Используйте `/score-from-path`, если изображения уже находятся на сервере
- Используйте `/score-from-file`, если изображения нужно загрузить с клиента

### 7.4. Мониторинг нагрузки

Регулярно проверяйте эндпоинт `/health` для мониторинга нагрузки на API и соответствующей настройки параметров:

```python
def adjust_parameters_based_on_load(api_url):
    response = requests.get(f"{api_url}/health")
    health = response.json()
    
    # Если API под нагрузкой, уменьшаем размер изображений и количество параллельных запросов
    if health['queue_size'] > 0:
        downscale = 0.25  # Сильное уменьшение
        max_workers = 2   # Меньше параллельных запросов
    else:
        downscale = 0.5   # Умеренное уменьшение
        max_workers = 5   # Больше параллельных запросов
    
    return downscale, max_workers
```

## 8. Часто задаваемые вопросы

### 8.1. Что означает оценка качества?

Оценка качества представляет собой числовое значение, основанное на алгоритме BRISQUE. Более низкие значения обычно указывают на более низкое качество изображения. Однако интерпретация значений может зависеть от конкретного набора изображений и их характеристик.

### 8.2. Какие форматы изображений поддерживаются?

API поддерживает стандартные форматы изображений:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

### 8.3. Есть ли ограничения на размер файла?

Да, максимальный размер файла по умолчанию составляет 20 МБ. Для больших изображений рекомендуется использовать параметр `downscale` для уменьшения размера перед обработкой.

### 8.4. Что делать, если API возвращает ошибку 503?

Ошибка 503 означает, что сервер временно перегружен. Рекомендуется:
1. Подождать некоторое время (обычно несколько секунд)
2. Повторить запрос с экспоненциальной задержкой
3. Уменьшить параметр `downscale` для ускорения обработки
4. Сократить количество параллельных запросов

### 8.5. Как обрабатывать большие наборы изображений?

Для обработки больших наборов изображений рекомендуется:
1. Использовать клиентскую библиотеку `image_quality_client.py`
2. Настроить параметр `downscale` для ускорения обработки
3. Оптимизировать количество параллельных запросов
4. Использовать метод `process_directory` для автоматической обработки

```bash
python image_quality_client.py --url http://<server-address>:8000 --dir /path/to/images --output results.csv --workers 5 --downscale 0.25
```

### 8.6. Как интегрировать API в существующую систему?

API предоставляет стандартные REST-эндпоинты, которые можно легко интегрировать в любую систему, поддерживающую HTTP-запросы. Примеры интеграции на разных языках программирования приведены в разделе 5.

## 9. Установка и развертывание API

### 9.1. Клонирование репозитория с GitHub

Для начала необходимо клонировать репозиторий с GitHub:

```shellscript
# Клонирование репозитория
git clone https://github.com/alex16654/api_sud_check.git

# Переход в директорию проекта
cd api_sud_check
```

### 9.2. Установка зависимостей

API требует Python 3.8 или выше. Установите необходимые зависимости:

```shellscript
# Создание виртуального окружения (рекомендуется)
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 9.3. Настройка конфигурации

Создайте файл `.env` в корневой директории проекта:

```shellscript
# Создание файла .env
touch .env  # для Linux/Mac
# или
type nul > .env  # для Windows
```

Отредактируйте файл `.env` и добавьте следующие параметры:

```plaintext
# Порт для запуска API
PORT=8000

# Максимальное количество рабочих процессов
MAX_WORKERS=4

# Максимальное количество одновременных запросов
MAX_CONCURRENT_REQUESTS=6

# Директория для временных файлов
TEMP_DIR=/tmp/image_quality_api

# Максимальный размер загружаемого файла (в байтах)
MAX_CONTENT_LENGTH=20971520  # 20 МБ
```

### 9.4. Запуск API в режиме разработки

Для локального тестирования запустите API в режиме разработки:

```shellscript
python app.py
```

API будет доступен по адресу `http://localhost:8000`.

### 9.5. Развертывание на сервере

#### 9.5.1. Использование Docker

Для удобства развертывания можно использовать Docker:

```shellscript
# Сборка Docker-образа
docker build -t image-quality-api .

# Запуск контейнера
docker run -d -p 8000:8000 --name image-quality-api image-quality-api
```

#### 9.5.2. Использование systemd (для Linux)

Создайте файл службы systemd:

```shellscript
sudo nano /etc/systemd/system/image-quality-api.service
```

Добавьте следующее содержимое:

```plaintext
[Unit]
Description=Image Quality API Service
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/api_sud_check
ExecStart=/path/to/api_sud_check/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=image-quality-api

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите службу:

```shellscript
sudo systemctl daemon-reload
sudo systemctl enable image-quality-api
sudo systemctl start image-quality-api
```

#### 9.5.3. Использование Gunicorn и Nginx (рекомендуется для продакшн)

Установите Gunicorn:

```shellscript
pip install gunicorn
```

Создайте файл конфигурации Gunicorn:

```shellscript
nano gunicorn_config.py
```

Добавьте следующее содержимое:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
```

Запустите API с помощью Gunicorn:

```shellscript
gunicorn -c gunicorn_config.py app:app
```

Настройте Nginx для проксирования запросов:

```shellscript
sudo nano /etc/nginx/sites-available/image-quality-api
```

Добавьте следующее содержимое:

```plaintext
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        client_max_body_size 20M;
    }
}
```

Активируйте конфигурацию Nginx:

```shellscript
sudo ln -s /etc/nginx/sites-available/image-quality-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9.6. Проверка работоспособности

После развертывания проверьте работоспособность API:

```shellscript
curl http://<server-address>:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "healthy",
  "timestamp": 1710615123.456789,
  "active_requests": 0,
  "queue_size": 0,
  "max_workers": 4,
  "max_concurrent_requests": 6
}
```

### 9.7. Обновление API

Для обновления API до последней версии:

```shellscript
# Переход в директорию проекта
cd /path/to/api_sud_check

# Получение последних изменений
git pull

# Обновление зависимостей
pip install -r requirements.txt

# Перезапуск службы (если используется systemd)
sudo systemctl restart image-quality-api

# Или перезапуск Docker-контейнера (если используется Docker)
docker restart image-quality-api
```

---

Для получения дополнительной информации или технической поддержки обратитесь к администратору API.