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
