import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import threading
import json
from tabulate import tabulate
from jinja2 import Template
import os
import re
from datetime import datetime
import logging
from typing import Dict, List, Optional

class WebScraperGUI:
    def __init__(self):
        # Настройка логирования
        self.setup_logging()
        
        # Загрузка настроек
        self.settings = self.load_settings()
        
        # Настройка темы и цветов
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
        
        # Создание главного окна
        self.root = ctk.CTk()
        self.root.title("Web Scraper")
        self.root.geometry("1000x800")
        
        # Инициализация переменных
        self.results_data = None
        self.current_url = None
        self.is_scraping = False
        
        # Создаем и размещаем элементы интерфейса
        self.create_widgets()
        
        # Загрузка последнего URL
        if last_url := self.settings.get("last_url"):
            self.url_entry.insert(0, last_url)

    def setup_logging(self):
        """Настройка системы логирования"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        logging.basicConfig(
            filename=f'logs/scraper_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_settings(self) -> Dict:
        """Загрузка настроек из файла"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки настроек: {e}")
        return {}

    def save_settings(self):
        """Сохранение настроек в файл"""
        settings = {
            "theme": ctk.get_appearance_mode().lower(),
            "last_url": self.url_entry.get(),
            "depth": self.depth_var.get(),
            "filters": {
                "min_text_length": self.min_length_var.get(),
                "exclude_patterns": self.exclude_patterns_var.get()
            },
            "extract_options": {
                "links": self.extract_links.get(),
                "text": self.extract_text.get(),
                "headers": self.extract_headers.get()
            }
        }
        
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек: {e}")

    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Главный контейнер
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Web Scraper", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # URL и настройки
        self.create_url_frame(main_frame)
        self.create_options_frame(main_frame)
        self.create_filters_frame(main_frame)
        self.create_buttons_frame(main_frame)
        self.create_results_frame(main_frame)
        self.create_status_frame(main_frame)

    def create_url_frame(self, parent):
        """Создание фрейма для URL"""
        url_frame = ctk.CTkFrame(parent)
        url_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        url_label = ctk.CTkLabel(
            url_frame,
            text="URL:",
            font=ctk.CTkFont(size=14)
        )
        url_label.pack(side="left", padx=(10, 5))
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Введите URL сайта...",
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Глубина поиска
        depth_label = ctk.CTkLabel(
            url_frame,
            text="Глубина:",
            font=ctk.CTkFont(size=14)
        )
        depth_label.pack(side="left", padx=(10, 5))
        
        self.depth_var = ctk.StringVar(value="1")
        depth_menu = ctk.CTkOptionMenu(
            url_frame,
            values=["1", "2", "3", "4", "5"],
            variable=self.depth_var,
            width=60
        )
        depth_menu.pack(side="left", padx=5)

    def create_options_frame(self, parent):
        """Создание фрейма с опциями извлечения"""
        options_frame = ctk.CTkFrame(parent)
        options_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="Опции извлечения:",
            font=ctk.CTkFont(size=14)
        )
        options_label.pack(anchor="w", padx=10, pady=5)
        
        self.extract_links = ctk.CTkCheckBox(
            options_frame,
            text="Ссылки",
            font=ctk.CTkFont(size=13)
        )
        self.extract_links.pack(side="left", padx=10)
        self.extract_links.select()
        
        self.extract_text = ctk.CTkCheckBox(
            options_frame,
            text="Текст",
            font=ctk.CTkFont(size=13)
        )
        self.extract_text.pack(side="left", padx=10)
        self.extract_text.select()
        
        self.extract_headers = ctk.CTkCheckBox(
            options_frame,
            text="Заголовки",
            font=ctk.CTkFont(size=13)
        )
        self.extract_headers.pack(side="left", padx=10)
        self.extract_headers.select()

    def create_filters_frame(self, parent):
        """Создание фрейма с фильтрами"""
        filters_frame = ctk.CTkFrame(parent)
        filters_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        filters_label = ctk.CTkLabel(
            filters_frame,
            text="Фильтры:",
            font=ctk.CTkFont(size=14)
        )
        filters_label.pack(anchor="w", padx=10, pady=5)
        
        # Минимальная длина текста
        length_frame = ctk.CTkFrame(filters_frame)
        length_frame.pack(fill="x", padx=10, pady=2)
        
        length_label = ctk.CTkLabel(
            length_frame,
            text="Мин. длина текста:",
            font=ctk.CTkFont(size=13)
        )
        length_label.pack(side="left")
        
        self.min_length_var = ctk.StringVar(value="10")
        length_entry = ctk.CTkEntry(
            length_frame,
            textvariable=self.min_length_var,
            width=60
        )
        length_entry.pack(side="left", padx=5)
        
        # Исключающие паттерны
        patterns_frame = ctk.CTkFrame(filters_frame)
        patterns_frame.pack(fill="x", padx=10, pady=2)
        
        patterns_label = ctk.CTkLabel(
            patterns_frame,
            text="Исключить (regex):",
            font=ctk.CTkFont(size=13)
        )
        patterns_label.pack(side="left")
        
        self.exclude_patterns_var = ctk.StringVar()
        patterns_entry = ctk.CTkEntry(
            patterns_frame,
            textvariable=self.exclude_patterns_var,
            placeholder_text="Например: реклама|контакты"
        )
        patterns_entry.pack(side="left", padx=5, fill="x", expand=True)

    def create_buttons_frame(self, parent):
        """Создание фрейма с кнопками"""
        buttons_frame = ctk.CTkFrame(parent)
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.scrape_button = ctk.CTkButton(
            buttons_frame,
            text="Начать извлечение",
            command=self.start_scraping,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.scrape_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(
            buttons_frame,
            text="Экспортировать",
            command=self.export_results,
            height=40,
            state="disabled",
            font=ctk.CTkFont(size=14)
        )
        self.export_button.pack(side="left", padx=5)
        
        # Формат экспорта
        self.export_format = ctk.StringVar(value="Excel (.xlsx)")
        self.format_menu = ctk.CTkOptionMenu(
            buttons_frame,
            values=[
                "Excel (.xlsx)",
                "CSV (.csv)",
                "JSON (.json)",
                "HTML (.html)",
                "Markdown (.md)",
                "Text (.txt)"
            ],
            variable=self.export_format,
            font=ctk.CTkFont(size=13)
        )
        self.format_menu.pack(side="left", padx=5)
        
        # Переключатель темы
        self.theme_switch = ctk.CTkSwitch(
            buttons_frame,
            text="Темная тема",
            command=self.toggle_theme,
            font=ctk.CTkFont(size=13)
        )
        self.theme_switch.pack(side="right", padx=10)
        if self.settings.get("theme") == "dark":
            self.theme_switch.select()

    def create_results_frame(self, parent):
        """Создание фрейма с результатами"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Статистика
        stats_frame = ctk.CTkFrame(results_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Статистика: нет данных",
            font=ctk.CTkFont(size=13)
        )
        self.stats_label.pack(pady=5)
        
        # Результаты
        self.results_text = ctk.CTkTextbox(
            results_frame,
            wrap="word",
            font=ctk.CTkFont(size=13)
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_status_frame(self, parent):
        """Создание фрейма статуса"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=10)
        
        self.progress_label = ctk.CTkLabel(
            status_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=13)
        )
        self.progress_label.pack(side="left", pady=5, padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, pady=5, padx=10)
        self.progress_bar.set(0)

    def toggle_theme(self):
        """Переключение темы оформления"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.save_settings()

    def start_scraping(self):
        """Запуск процесса извлечения данных"""
        if self.is_scraping:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            self.show_error("Пожалуйста, введите URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.current_url = url
        self.is_scraping = True
        self.results_data = pd.DataFrame()
        self.results_text.delete("0.0", "end")
        self.progress_label.configure(text="Извлечение данных...")
        self.progress_bar.start()
        self.scrape_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        
        thread = threading.Thread(target=self.scrape_url, args=(url, int(self.depth_var.get())))
        thread.daemon = True
        thread.start()

    def scrape_url(self, url: str, depth: int, visited: Optional[set] = None):
        """Рекурсивное извлечение данных с указанной глубиной"""
        if visited is None:
            visited = set()
            
        if url in visited or depth < 1:
            return
            
        visited.add(url)
        
        try:
            self.logger.info(f"Обработка URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            # Извлечение данных
            if self.extract_links.get():
                results.extend(self.extract_links_data(soup, url))
            
            if self.extract_headers.get():
                results.extend(self.extract_headers_data(soup))
            
            if self.extract_text.get():
                results.extend(self.extract_text_data(soup))
            
            # Применение фильтров
            results = self.apply_filters(results)
            
            # Добавление результатов
            if results:
                new_data = pd.DataFrame(results)
                self.results_data = pd.concat([self.results_data, new_data], ignore_index=True)
                self.root.after(0, self.update_results)
            
            # Рекурсивный обход ссылок
            if depth > 1:
                links = soup.find_all('a')
                for link in links:
                    if href := link.get('href'):
                        next_url = urljoin(url, href)
                        if next_url.startswith(('http://', 'https://')) and next_url not in visited:
                            self.scrape_url(next_url, depth - 1, visited)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке {url}: {e}")
            self.root.after(0, lambda: self.show_error(f"Ошибка при обработке {url}: {str(e)}"))
        
        if url == self.current_url:  # Завершение основного процесса
            self.is_scraping = False
            self.root.after(0, self.finalize_scraping)

    def extract_links_data(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Извлечение ссылок"""
        results = []
        for link in soup.find_all('a'):
            if href := link.get('href'):
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                results.append({
                    'type': 'Ссылка',
                    'text': link.text.strip(),
                    'url': href
                })
        return results

    def extract_headers_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение заголовков"""
        results = []
        for tag in ['h1', 'h2', 'h3']:
            for header in soup.find_all(tag):
                results.append({
                    'type': f'Заголовок ({tag})',
                    'text': header.text.strip(),
                    'url': ''
                })
        return results

    def extract_text_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение текста"""
        results = []
        for p in soup.find_all('p'):
            if text := p.text.strip():
                results.append({
                    'type': 'Текст',
                    'text': text,
                    'url': ''
                })
        return results

    def apply_filters(self, results: List[Dict]) -> List[Dict]:
        """Применение фильтров к результатам"""
        filtered_results = []
        
        try:
            min_length = int(self.min_length_var.get())
        except ValueError:
            min_length = 0
            
        exclude_pattern = self.exclude_patterns_var.get().strip()
        
        for item in results:
            text = item['text']
            
            # Проверка длины
            if len(text) < min_length:
                continue
                
            # Проверка паттерна
            if exclude_pattern and re.search(exclude_pattern, text, re.IGNORECASE):
                continue
                
            filtered_results.append(item)
            
        return filtered_results

    def update_results(self):
        """Обновление отображения результатов"""
        if self.results_data is not None and not self.results_data.empty:
            self.results_text.delete("0.0", "end")
            
            # Обновление статистики
            stats = (
                f"Найдено: {len(self.results_data)} элементов "
                f"(Ссылок: {len(self.results_data[self.results_data['type'] == 'Ссылка'])}, "
                f"Заголовков: {len(self.results_data[self.results_data['type'].str.startswith('Заголовок')])}, "
                f"Текста: {len(self.results_data[self.results_data['type'] == 'Текст'])})"
            )
            self.stats_label.configure(text=stats)
            
            # Вывод результатов
            for _, row in self.results_data.iterrows():
                self.results_text.insert("end", f"Тип: {row['type']}\n")
                self.results_text.insert("end", f"Текст: {row['text']}\n")
                if row['url']:
                    self.results_text.insert("end", f"URL: {row['url']}\n")
                self.results_text.insert("end", "─" * 50 + "\n")

    def finalize_scraping(self):
        """Завершение процесса извлечения"""
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.scrape_button.configure(state="normal")
        self.export_button.configure(state="normal")
        self.progress_label.configure(text="Извлечение завершено")
        self.save_settings()

    def show_error(self, error_message: str):
        """Отображение ошибки"""
        self.logger.error(error_message)
        self.progress_label.configure(text="Ошибка")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.scrape_button.configure(state="normal")
        self.is_scraping = False
        
        dialog = ctk.CTkInputDialog(
            text=f"Произошла ошибка:\n{error_message}",
            title="Ошибка",
            button_text="OK"
        )
        dialog.get_input()

    def export_results(self):
        """Экспорт результатов"""
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
        
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(f"{selected_format} files", f"*{extension}"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                export_func(file_path)
                self.logger.info(f"Данные экспортированы в {file_path}")
                dialog = ctk.CTkInputDialog(
                    text=f"Файл успешно экспортирован в формате {selected_format}",
                    title="Успех",
                    button_text="OK"
                )
                dialog.get_input()
            except Exception as e:
                self.show_error(f"Ошибка при экспорте файла:\n{str(e)}")

    def export_excel(self, file_path: str):
        """Экспорт в Excel"""
        self.results_data.to_excel(file_path, index=False)

    def export_csv(self, file_path: str):
        """Экспорт в CSV"""
        self.results_data.to_csv(file_path, index=False, encoding='utf-8-sig')

    def export_json(self, file_path: str):
        """Экспорт в JSON"""
        results = self.results_data.to_dict(orient='records')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def export_html(self, file_path: str):
        """Экспорт в HTML"""
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Web Scraper Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .item {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .type {
            color: #666;
            font-size: 0.9em;
        }
        .text {
            margin: 10px 0;
        }
        .url {
            color: #0066cc;
            word-break: break-all;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .stats {
            background-color: #f8f9fa;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Scraper Results</h1>
        <div class="stats">
            <p>Всего элементов: {{ total_items }}</p>
            <p>Ссылок: {{ links_count }}</p>
            <p>Заголовков: {{ headers_count }}</p>
            <p>Текстовых блоков: {{ text_count }}</p>
        </div>
        {% for item in items %}
        <div class="item">
            <div class="type">{{ item.type }}</div>
            <div class="text">{{ item.text }}</div>
            {% if item.url %}
            <a href="{{ item.url }}" class="url">{{ item.url }}</a>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """)
        
        stats = {
            'total_items': len(self.results_data),
            'links_count': len(self.results_data[self.results_data['type'] == 'Ссылка']),
            'headers_count': len(self.results_data[self.results_data['type'].str.startswith('Заголовок')]),
            'text_count': len(self.results_data[self.results_data['type'] == 'Текст'])
        }
        
        html_content = template.render(
            items=self.results_data.to_dict(orient='records'),
            **stats
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def export_markdown(self, file_path: str):
        """Экспорт в Markdown"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Web Scraper Results\n\n")
            
            # Статистика
            f.write("## Статистика\n\n")
            f.write(f"- Всего элементов: {len(self.results_data)}\n")
            f.write(f"- Ссылок: {len(self.results_data[self.results_data['type'] == 'Ссылка'])}\n")
            f.write(f"- Заголовков: {len(self.results_data[self.results_data['type'].str.startswith('Заголовок')])}\n")
            f.write(f"- Текстовых блоков: {len(self.results_data[self.results_data['type'] == 'Текст'])}\n\n")
            
            # Данные
            for _, row in self.results_data.iterrows():
                f.write(f"## {row['type']}\n\n")
                f.write(f"{row['text']}\n\n")
                if row['url']:
                    f.write(f"[Ссылка]({row['url']})\n\n")
                f.write("---\n\n")

    def export_text(self, file_path: str):
        """Экспорт в текстовый формат"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # Статистика
            f.write("=== Web Scraper Results ===\n\n")
            f.write(f"Всего элементов: {len(self.results_data)}\n")
            f.write(f"Ссылок: {len(self.results_data[self.results_data['type'] == 'Ссылка'])}\n")
            f.write(f"Заголовков: {len(self.results_data[self.results_data['type'].str.startswith('Заголовок')])}\n")
            f.write(f"Текстовых блоков: {len(self.results_data[self.results_data['type'] == 'Текст'])}\n\n")
            f.write("=" * 50 + "\n\n")
            
            # Данные
            f.write(tabulate(
                self.results_data,
                headers='keys',
                tablefmt='grid',
                showindex=False
            ))

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()
        self.save_settings()  # Сохранение настроек при закрытии

if __name__ == "__main__":
    app = WebScraperGUI()
    app.run() 