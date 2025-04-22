# Подробное объяснение кода Web Scraper

## Импорты и их назначение

```python
import customtkinter as ctk          # Библиотека для создания GUI
import requests                      # Для HTTP-запросов
from bs4 import BeautifulSoup       # Для парсинга HTML
import pandas as pd                  # Для работы с данными в табличном формате
from urllib.parse import urlparse    # Для обработки URL
import threading                     # Для многопоточности
import json                         # Для работы с JSON
from tabulate import tabulate       # Для создания текстовых таблиц
from jinja2 import Template         # Для шаблонов HTML
import os                          # Для работы с файловой системой
```

## Структура программы

### 1. Основной класс WebScraperGUI
Класс инкапсулирует всю логику приложения и содержит следующие компоненты:
- Графический интерфейс
- Логика извлечения данных
- Управление экспортом
- Обработка ошибок

### 2. Инициализация (`__init__`)
```python
def __init__(self):
    # Настройка темы и цветов
    ctk.set_appearance_mode("dark")  # Установка темной темы по умолчанию
    ctk.set_default_color_theme("blue")  # Установка цветовой схемы
    
    # Создание главного окна
    self.root = ctk.CTk()
    self.root.title("Web Scraper")
    self.root.geometry("900x700")  # Размер окна
```
Этот метод:
- Инициализирует основное окно приложения
- Устанавливает тему оформления
- Задает базовые параметры окна

### 3. Создание интерфейса (`create_widgets`)
```python
def create_widgets(self):
    # Главный контейнер
    main_frame = ctk.CTkFrame(self.root)
    
    # URL-ввод
    url_frame = ctk.CTkFrame(main_frame)
    self.url_entry = ctk.CTkEntry(
        url_frame,
        placeholder_text="Введите URL сайта...",
        height=35,
        font=ctk.CTkFont(size=14)
    )
    
    # Чекбоксы для выбора данных
    self.extract_links = ctk.CTkCheckBox(...)
    self.extract_text = ctk.CTkCheckBox(...)
    self.extract_headers = ctk.CTkCheckBox(...)
```
Особенности компонентов:
- Все элементы организованы в фреймы для лучшей структуры
- Использованы современные виджеты CustomTkinter
- Настроены шрифты и отступы для лучшей читаемости

### 4. Процесс извлечения данных
#### 4.1 Запуск извлечения (`start_scraping`)
```python
def start_scraping(self):
    url = self.url_entry.get().strip()
    if not url:
        self.show_error("Пожалуйста, введите URL")
        return
        
    # Автоматическое добавление протокола
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Обновление интерфейса
    self.progress_label.configure(text="Извлечение данных...")
    self.progress_bar.start()
    
    # Запуск в отдельном потоке
    thread = threading.Thread(target=self.scrape_url, args=(url,))
    thread.daemon = True
    thread.start()
```
Важные аспекты:
- Валидация URL
- Автоматическое добавление протокола
- Обновление состояния интерфейса
- Многопоточное выполнение

#### 4.2 Извлечение данных (`scrape_url`)
```python
def scrape_url(self, url):
    try:
        # Загрузка страницы
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # Извлечение ссылок
        if self.extract_links.get():
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if href:
                    # Обработка относительных URL
                    if not href.startswith(('http://', 'https://')):
                        base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                        href = base_url + href if href.startswith('/') else base_url + '/' + href
                    results.append({
                        'type': 'Ссылка',
                        'text': link.text.strip(),
                        'url': href
                    })
        
        # Извлечение заголовков
        if self.extract_headers.get():
            for tag in ['h1', 'h2', 'h3']:
                for header in soup.find_all(tag):
                    results.append({
                        'type': f'Заголовок ({tag})',
                        'text': header.text.strip(),
                        'url': ''
                    })
        
        # Извлечение текста
        if self.extract_text.get():
            for p in soup.find_all('p'):
                if text := p.text.strip():
                    results.append({
                        'type': 'Текст',
                        'text': text,
                        'url': ''
                    })
                    
        # Сохранение результатов
        self.results_data = pd.DataFrame(results)
        
    except Exception as e:
        self.root.after(0, lambda: self.show_error(str(e)))
```
Ключевые моменты:
- Использование BeautifulSoup для парсинга
- Обработка относительных URL
- Фильтрация пустых данных
- Структурированное хранение в DataFrame

### 5. Экспорт данных
#### 5.1 Общий механизм экспорта
```python
def export_results(self):
    if self.results_data is None or self.results_data.empty:
        self.show_error("Нет данных для экспорта")
        return

    format_mapping = {
        "Excel (.xlsx)": (".xlsx", self.export_excel),
        "CSV (.csv)": (".csv", self.export_csv),
        "JSON (.json)": (".json", self.export_json),
        "HTML (.html)": (".html", self.export_html),
        "Markdown (.md)": (".md", self.export_markdown),
        "Text (.txt)": (".txt", self.export_text)
    }

    selected_format = self.export_format.get()
    extension, export_func = format_mapping[selected_format]
```

#### 5.2 HTML экспорт
```python
def export_html(self, file_path):
    template = Template(self.html_template)
    html_content = template.render(
        items=self.results_data.to_dict(orient='records')
    )
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
```
HTML шаблон включает:
- Адаптивный дизайн
- CSS стили
- Форматирование данных

#### 5.3 Markdown экспорт
```python
def export_markdown(self, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("# Web Scraper Results\n\n")
        for _, row in self.results_data.iterrows():
            f.write(f"## {row['type']}\n\n")
            f.write(f"{row['text']}\n\n")
            if row['url']:
                f.write(f"[Ссылка]({row['url']})\n\n")
            f.write("---\n\n")
```

### 6. Обработка ошибок
```python
def show_error(self, error_message):
    self.progress_label.configure(text="Ошибка")
    self.progress_bar.stop()
    self.progress_bar.set(0)
    self.scrape_button.configure(state="normal")
    
    dialog = ctk.CTkInputDialog(
        text=f"Произошла ошибка:\n{error_message}",
        title="Ошибка",
        button_text="OK"
    )
```
Обрабатываются следующие типы ошибок:
- Сетевые ошибки при загрузке страницы
- Ошибки парсинга HTML
- Ошибки при сохранении файлов
- Некорректный URL

### 7. Дополнительные функции

#### 7.1 Переключение темы
```python
def toggle_theme(self):
    current_mode = ctk.get_appearance_mode()
    new_mode = "light" if current_mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)
```

#### 7.2 Управление состоянием интерфейса
- Блокировка кнопок во время извлечения
- Обновление прогресс-бара
- Изменение состояния кнопок экспорта

### 8. Запуск приложения
```python
if __name__ == "__main__":
    app = WebScraperGUI()  # Создание экземпляра
    app.run()              # Запуск главного цикла
```

# Техническая документация Web Scraper

## Архитектура приложения

Приложение построено на основе класса `WebScraperGUI`, который реализует весь функционал веб-скрапера. Архитектура разделена на несколько логических блоков:

### 1. Инициализация и настройка
```python
def __init__(self):
    self.setup_logging()
    self.settings = self.load_settings()
    # ...
```
- Настройка системы логирования
- Загрузка пользовательских настроек
- Инициализация GUI компонентов

### 2. Управление интерфейсом

#### 2.1 Создание виджетов
```python
def create_widgets(self):
    # Основные фреймы
    self.create_url_frame()
    self.create_options_frame()
    self.create_filters_frame()
    self.create_buttons_frame()
    self.create_results_frame()
    self.create_status_frame()
```
- Модульная структура интерфейса
- Каждый фрейм отвечает за свой функционал
- Использование современных виджетов CustomTkinter

#### 2.2 Управление состоянием
- Отслеживание состояния извлечения данных через `self.is_scraping`
- Блокировка/разблокировка кнопок
- Обновление прогресс-бара и статуса

### 3. Система извлечения данных

#### 3.1 Основной процесс
```python
def scrape_url(self, url: str, depth: int, visited: Optional[set] = None):
    # Рекурсивный обход страниц
    # Извлечение данных
    # Применение фильтров
```
- Многопоточное выполнение
- Рекурсивный обход с контролем глубины
- Отслеживание посещенных URL

#### 3.2 Извлечение контента
```python
def extract_links_data(self, soup: BeautifulSoup, base_url: str) -> List[Dict]
def extract_headers_data(self, soup: BeautifulSoup) -> List[Dict]
def extract_text_data(self, soup: BeautifulSoup) -> List[Dict]
```
- Модульная система извлечения разных типов данных
- Автоматическая коррекция относительных URL
- Фильтрация пустых данных

### 4. Система фильтрации

#### 4.1 Применение фильтров
```python
def apply_filters(self, results: List[Dict]) -> List[Dict]:
    # Фильтрация по длине
    # Фильтрация по регулярным выражениям
```
- Настраиваемые фильтры
- Поддержка регулярных выражений
- Валидация входных данных

### 5. Управление данными

#### 5.1 Хранение результатов
```python
self.results_data = pd.DataFrame()
```
- Использование pandas для эффективной работы с данными
- Динамическое обновление результатов
- Поддержка различных форматов экспорта

#### 5.2 Экспорт данных
```python
def export_excel(self, file_path: str)
def export_csv(self, file_path: str)
def export_json(self, file_path: str)
def export_html(self, file_path: str)
def export_markdown(self, file_path: str)
def export_text(self, file_path: str)
```
- Множество форматов экспорта
- Кастомизация каждого формата
- Обработка ошибок при сохранении

### 6. Система настроек

#### 6.1 Сохранение настроек
```python
def save_settings(self):
    settings = {
        "theme": ctk.get_appearance_mode().lower(),
        "last_url": self.url_entry.get(),
        # ...
    }
```
- JSON формат для хранения
- Автоматическое сохранение при закрытии
- Восстановление состояния при запуске

#### 6.2 Логирование
```python
def setup_logging(self):
    logging.basicConfig(
        filename=f'logs/scraper_{datetime.now().strftime("%Y%m%d")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
```
- Ежедневные лог-файлы
- Структурированный формат логов
- Отслеживание всех важных событий

## Потоки выполнения

### 1. Основной поток
- Управление интерфейсом
- Обработка событий
- Обновление UI

### 2. Поток извлечения данных
- Выполнение HTTP запросов
- Парсинг HTML
- Применение фильтров

## Обработка ошибок

### 1. Сетевые ошибки
```python
try:
    response = requests.get(url)
    response.raise_for_status()
except Exception as e:
    self.logger.error(f"Ошибка при обработке {url}: {e}")
```
- Обработка недоступных URL
- Таймауты
- HTTP ошибки

### 2. Ошибки парсинга
- Некорректный HTML
- Отсутствующие элементы
- Кодировка

### 3. Ошибки экспорта
- Права доступа
- Занятые файлы
- Недостаточно места

## Оптимизация

### 1. Производительность
- Многопоточное извлечение данных
- Эффективное использование памяти
- Кэширование посещенных URL

### 2. Пользовательский опыт
- Отзывчивый интерфейс
- Информативные сообщения
- Сохранение настроек

### 3. Надежность
- Проверка входных данных
- Восстановление после ошибок
- Логирование для отладки

## Расширение функционала

Для добавления новых возможностей:

1. Новые типы данных для извлечения:
   - Добавить метод извлечения
   - Обновить интерфейс
   - Добавить в систему экспорта

2. Новые форматы экспорта:
   - Создать метод экспорта
   - Добавить в mapping форматов
   - Обновить UI

3. Новые фильтры:
   - Добавить параметры в интерфейс
   - Обновить метод apply_filters
   - Добавить в настройки
