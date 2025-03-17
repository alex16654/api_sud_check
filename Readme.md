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
   - [5.4. Java](#54-java)
6. [Обработка ошибок](#6-обработка-ошибок)
7. [Оптимизация производительности](#7-оптимизация-производительности)
8. [Часто задаваемые вопросы](#8-часто-задаваемые-вопросы)

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
  -F "downscale=0.5"
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
  -d "downscale=0.5"
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
result = client.score_from_path("/path/to/image.jpg", downscale=0.5)
print(f"Score for {result['filename']}: {result['score']}")

# Оценка качества по загруженному файлу
result = client.score_from_file("/path/to/image.jpg", downscale=0.5)
print(f"Score for {result['filename']}: {result['score']}")

# Обработка всех изображений в директории
results = client.process_directory(
    "/path/to/images",
    use_upload=True,  # True для загрузки файлов, False для использования путей
    max_workers=5,
    downscale=0.5
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
 * Клиент для API оценки качества изображений
 */
class ImageQualityClient {
    private $apiUrl;
    private $timeout;
    private $maxRetries;
    private $backoffFactor;
    
    /**
     * Конструктор класса
     * 
     * @param string $apiUrl Базовый URL API
     * @param int $timeout Таймаут запроса в секундах
     * @param int $maxRetries Максимальное количество повторных попыток
     * @param float $backoffFactor Фактор экспоненциальной задержки
     */
    public function __construct($apiUrl, $timeout = 30, $maxRetries = 3, $backoffFactor = 1.5) {
        $this->apiUrl = rtrim($apiUrl, '/');
        $this->timeout = $timeout;
        $this->maxRetries = $maxRetries;
        $this->backoffFactor = $backoffFactor;
    }
    
    /**
     * Проверка состояния API
     * 
     * @return array Информация о состоянии API
     * @throws Exception В случае ошибки
     */
    public function healthCheck() {
        return $this->makeRequest('GET', '/health');
    }
    
    /**
     * Оценка качества изображения по пути к файлу
     * 
     * @param string $imagePath Путь к файлу изображения на сервере
     * @param float $downscale Коэффициент уменьшения изображения
     * @return array Результат оценки качества
     * @throws Exception В случае ошибки
     */
    public function scoreFromPath($imagePath, $downscale = 1.0) {
        $data = [
            'image_path' => $imagePath,
            'downscale' => $downscale
        ];
        
        return $this->makeRequest('POST', '/score-from-path', $data);
    }
    
    /**
     * Оценка качества изображения по загруженному файлу
     * 
     * @param string $filePath Путь к файлу изображения на клиенте
     * @param float $downscale Коэффициент уменьшения изображения
     * @return array Результат оценки качества
     * @throws Exception В случае ошибки
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
    
    /**
     * Обработка всех изображений в директории
     * 
     * @param string $directory Путь к директории с изображениями
     * @param bool $useUpload Использовать загрузку файлов (true) или пути (false)
     * @param float $downscale Коэффициент уменьшения изображения
     * @param array $extensions Поддерживаемые расширения файлов
     * @return array Результаты оценки качества
     * @throws Exception В случае ошибки
     */
    public function processDirectory($directory, $useUpload = false, $downscale = 0.5, $extensions = ['jpg', 'jpeg', 'png']) {
        if (!is_dir($directory)) {
            throw new Exception("Directory not found: $directory");
        }
        
        $results = [];
        $errors = [];
        
        // Получаем список файлов изображений
        $files = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($directory, RecursiveDirectoryIterator::SKIP_DOTS)
        );
        
        $imageFiles = [];
        foreach ($files as $file) {
            $extension = strtolower(pathinfo($file->getPathname(), PATHINFO_EXTENSION));
            if (in_array($extension, $extensions)) {
                $imageFiles[] = $file->getPathname();
            }
        }
        
        if (empty($imageFiles)) {
            echo "No image files found in $directory\n";
            return [];
        }
        
        echo "Processing " . count($imageFiles) . " images...\n";
        
        // Обрабатываем каждый файл
        foreach ($imageFiles as $index => $file) {
            echo "Processing file " . ($index + 1) . "/" . count($imageFiles) . ": " . basename($file) . "\n";
            
            try {
                if ($useUpload) {
                    $result = $this->scoreFromFile($file, $downscale);
                } else {
                    $result = $this->scoreFromPath($file, $downscale);
                }
                $results[] = $result;
                echo "  Score: " . $result['score'] . "\n";
            } catch (Exception $e) {
                $errors[] = [
                    'filename' => basename($file),
                    'error' => $e->getMessage()
                ];
                echo "  Error: " . $e->getMessage() . "\n";
            }
        }
        
        // Выводим статистику
        if (!empty($results)) {
            $scores = array_column($results, 'score');
            $avgScore = array_sum($scores) / count($scores);
            $minScore = min($scores);
            $maxScore = max($scores);
            
            echo "\nProcessed " . count($results) . " images successfully\n";
            echo "  Average score: " . round($avgScore, 2) . "\n";
            echo "  Min score: " . round($minScore, 2) . "\n";
            echo "  Max score: " . round($maxScore, 2) . "\n";
        }
        
        if (!empty($errors)) {
            echo "\nEncountered " . count($errors) . " errors\n";
        }
        
        return array_merge($results, $errors);
    }
    
    /**
     * Сохранение результатов в CSV файл
     * 
     * @param array $results Результаты оценки качества
     * @param string $outputFile Путь к выходному CSV файлу
     */
    public function saveResultsToCsv($results, $outputFile) {
        if (empty($results)) {
            echo "No results to save\n";
            return;
        }
        
        // Определяем все возможные ключи
        $keys = [];
        foreach ($results as $result) {
            $keys = array_merge($keys, array_keys($result));
        }
        $keys = array_unique($keys);
        sort($keys);
        
        // Создаем CSV файл
        $fp = fopen($outputFile, 'w');
        fputcsv($fp, $keys);
        
        foreach ($results as $result) {
            $row = [];
            foreach ($keys as $key) {
                $row[] = isset($result[$key]) ? $result[$key] : '';
            }
            fputcsv($fp, $row);
        }
        
        fclose($fp);
        echo "Results saved to $outputFile\n";
    }
    
    /**
     * Выполнение HTTP запроса с повторными попытками
     * 
     * @param string $method HTTP метод (GET, POST)
     * @param string $endpoint Эндпоинт API
     * @param array $data Данные для отправки
     * @param bool $isMultipart Использовать multipart/form-data
     * @return array Ответ API в виде массива
     * @throws Exception В случае ошибки
     */
    private function makeRequest($method, $endpoint, $data = [], $isMultipart = false) {
        $url = $this->apiUrl . $endpoint;
        $lastException = null;
        
        for ($attempt = 0; $attempt < $this->maxRetries; $attempt++) {
            try {
                $ch = curl_init();
                
                if ($method === 'GET') {
                    if (!empty($data)) {
                        $url .= '?' . http_build_query($data);
                    }
                    curl_setopt($ch, CURLOPT_URL, $url);
                } else { // POST
                    curl_setopt($ch, CURLOPT_URL, $url);
                    curl_setopt($ch, CURLOPT_POST, true);
                    
                    if ($isMultipart) {
                        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
                    } else {
                        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
                    }
                }
                
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
                curl_setopt($ch, CURLOPT_HEADER, true);
                
                $response = curl_exec($ch);
                
                if ($response === false) {
                    throw new Exception("CURL error: " . curl_error($ch));
                }
                
                $headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
                $header = substr($response, 0, $headerSize);
                $body = substr($response, $headerSize);
                
                $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                curl_close($ch);
                
                // Проверяем на перегрузку сервера (503)
                if ($statusCode === 503) {
                    // Ищем заголовок Retry-After
                    preg_match('/Retry-After: (\d+)/i', $header, $matches);
                    $retryAfter = isset($matches[1]) ? (int)$matches[1] : 1;
                    
                    $waitTime = $retryAfter + (mt_rand(0, 100) / 100); // Добавляем случайную задержку
                    echo "Server overloaded. Retrying in {$waitTime}s...\n";
                    sleep(ceil($waitTime));
                    continue;
                }
                
                // Декодируем JSON ответ
                $result = json_decode($body, true);
                
                if ($statusCode >= 200 && $statusCode < 300) {
                    return $result;
                } else {
                    $errorMsg = isset($result['error']) ? $result['error'] : 'Unknown error';
                    throw new Exception("API error ($statusCode): $errorMsg");
                }
                
            } catch (Exception $e) {
                $lastException = $e;
                
                // Рассчитываем время задержки с экспоненциальным ростом
                $waitTime = pow($this->backoffFactor, $attempt) + (mt_rand(0, 100) / 100);
                
                if ($attempt < $this->maxRetries - 1) {
                    echo "Request failed: " . $e->getMessage() . ". Retrying in {$waitTime}s...\n";
                    sleep(ceil($waitTime));
                }
            }
        }
        
        throw new Exception("Failed after {$this->maxRetries} attempts: " . $lastException->getMessage());
    }
}

/**
 * Пример использования клиента
 */
function exampleUsage() {
    try {
        // Создаем клиент
        $client = new ImageQualityClient('http://<server-address>:8000');
        
        // Проверяем состояние API
        $health = $client->healthCheck();
        echo "API Status: " . $health['status'] . "\n";
        
        // Оцениваем качество одного изображения
        $result = $client->scoreFromFile('/path/to/image.jpg', 0.5);
        echo "Score for " . $result['filename'] . ": " . $result['score'] . "\n";
        
        // Обрабатываем директорию с изображениями
        $results = $client->processDirectory('/path/to/images', true, 0.5);
        
        // Сохраняем результаты в CSV
        $client->saveResultsToCsv($results, 'results.csv');
        
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }
}

// Запуск примера использования
// exampleUsage();

/**
 * Обработка аргументов командной строки
 */
function processCommandLineArgs() {
    global $argv;
    
    if (count($argv) < 3) {
        echo "Usage: php image_quality_client.php [options]\n";
        echo "Options:\n";
        echo "  --url URL         API base URL (required)\n";
        echo "  --file PATH       Path to image file to upload\n";
        echo "  --path PATH       Path to image file on server\n";
        echo "  --dir PATH        Directory containing images to process\n";
        echo "  --output FILE     Output CSV file for directory results\n";
        echo "  --upload          Upload files when processing directory\n";
        echo "  --downscale VAL   Downscale factor (0.1-1.0, default: 0.5)\n";
        exit(1);
    }
    
    $options = [
        'url' => null,
        'file' => null,
        'path' => null,
        'dir' => null,
        'output' => null,
        'upload' => false,
        'downscale' => 0.5
    ];
    
    for ($i = 1; $i < count($argv); $i++) {
        if ($argv[$i] === '--url' && isset($argv[$i+1])) {
            $options['url'] = $argv[++$i];
        } elseif ($argv[$i] === '--file' && isset($argv[$i+1])) {
            $options['file'] = $argv[++$i];
        } elseif ($argv[$i] === '--path' && isset($argv[$i+1])) {
            $options['path'] = $argv[++$i];
        } elseif ($argv[$i] === '--dir' && isset($argv[$i+1])) {
            $options['dir'] = $argv[++$i];
        } elseif ($argv[$i] === '--output' && isset($argv[$i+1])) {
            $options['output'] = $argv[++$i];
        } elseif ($argv[$i] === '--upload') {
            $options['upload'] = true;
        } elseif ($argv[$i] === '--downscale' && isset($argv[$i+1])) {
            $options['downscale'] = (float)$argv[++$i];
        }
    }
    
    if (!$options['url']) {
        echo "Error: --url is required\n";
        exit(1);
    }
    
    try {
        $client = new ImageQualityClient($options['url']);
        
        // Проверяем состояние API
        $health = $client->healthCheck();
        echo "API Status: " . $health['status'] . "\n";
        
        if ($options['file']) {
            // Оцениваем качество по загруженному файлу
            $result = $client->scoreFromFile($options['file'], $options['downscale']);
            echo "\nResults for " . $result['filename'] . ":\n";
            echo "  Score: " . $result['score'] . "\n";
        } elseif ($options['path']) {
            // Оцениваем качество по пути к файлу
            $result = $client->scoreFromPath($options['path'], $options['downscale']);
            echo "\nResults for " . $result['filename'] . ":\n";
            echo "  Score: " . $result['score'] . "\n";
        } elseif ($options['dir']) {
            // Обрабатываем директорию
            $results = $client->processDirectory(
                $options['dir'],
                $options['upload'],
                $options['downscale']
            );
            
            // Сохраняем результаты в CSV, если указан выходной файл
            if ($options['output']) {
                $client->saveResultsToCsv($results, $options['output']);
            }
        }
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
        exit(1);
    }
}

// Запуск обработки аргументов командной строки
// processCommandLineArgs();
?>
```

### Пример использования PHP клиента:

```php
<?php
require_once 'image_quality_client.php';

// Создаем клиент
$client = new ImageQualityClient('http://<server-address>:8000');

try {
    // Проверяем состояние API
    $health = $client->healthCheck();
    echo "API Status: " . $health['status'] . "\n";
    
    // Оцениваем качество одного изображения
    $result = $client->scoreFromFile('/path/to/image.jpg', 0.5);
    echo "Score for " . $result['filename'] . ": " . $result['score'] . "\n";
    
    // Обрабатываем директорию с изображениями
    $results = $client->processDirectory('/path/to/images', true, 0.5);
    
    // Сохраняем результаты в CSV
    $client->saveResultsToCsv($results, 'results.csv');
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

### Использование PHP клиента из командной строки:

```bash
php image_quality_client.php --url http://<server-address>:8000 --file /path/to/image.jpg --downscale 0.5
php image_quality_client.php --url http://<server-address>:8000 --dir /path/to/images --output results.csv --upload
```

### 5.4. Java

```java
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.util.Map;

import org.json.JSONObject;

public class ImageQualityClient {
    private final String apiUrl;
    private final HttpClient httpClient;
    
    public ImageQualityClient(String apiUrl) {
        this.apiUrl = apiUrl;
        this.httpClient = HttpClient.newBuilder().build();
    }
    
    public JSONObject scoreFromFile(File imageFile, double downscale) throws IOException, InterruptedException {
        String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
        
        // Prepare multipart form data
        byte[] fileBytes = Files.readAllBytes(imageFile.toPath());
        String filename = imageFile.getName();
        
        String formData = "--" + boundary + "
" +
                "Content-Disposition: form-data; name="file"; filename="" + filename + ""
" +
                "Content-Type: image/jpeg

";
        
        String endFormData = "
--" + boundary + "
" +
                "Content-Disposition: form-data; name="downscale"

" +
                downscale + "
--" + boundary + "--
";
        
        byte[] formDataBytes = formData.getBytes();
        byte[] endFormDataBytes = endFormData.getBytes();
        
        byte[] requestBody = new byte[formDataBytes.length + fileBytes.length + endFormDataBytes.length];
        System.arraycopy(formDataBytes, 0, requestBody, 0, formDataBytes.length);
        System.arraycopy(fileBytes, 0, requestBody, formDataBytes.length, fileBytes.length);
        System.arraycopy(endFormDataBytes, 0, requestBody, formDataBytes.length + fileBytes.length, endFormDataBytes.length);
        
        // Create request
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl + "/score-from-file"))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(requestBody))
                .build();
        
        // Send request and get response
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() == 200) {
            return new JSONObject(response.body());
        } else {
            JSONObject error = new JSONObject(response.body());
            throw new IOException("API error: " + error.optString("error", "Unknown error"));
        }
    }
    
    // Example usage
    public static void main(String[] args) {
        try {
            ImageQualityClient client = new ImageQualityClient("http://<server-address>:8000");
            JSONObject result = client.scoreFromFile(new File("/path/to/image.jpg"), 0.5);
            System.out.println("Score: " + result.getDouble("score"));
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }
    }
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

def score_image(image_path, api_url, downscale=0.5):
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        data = {'downscale': str(downscale)}
        response = requests.post(f"{api_url}/score-from-file", files=files, data=data)
        return response.json() if response.status_code == 200 else None

def process_images_in_parallel(image_paths, api_url, max_workers=5, downscale=0.5):
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

---

Для получения дополнительной информации или технической поддержки обратитесь к администратору API.