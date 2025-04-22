import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
import threading
import json
from tabulate import tabulate
from jinja2 import Template
import os

class WebScraperGUI:
    def __init__(self):
        # Настройка темы и цветов
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создание главного окна
        self.root = ctk.CTk()
        self.root.title("Web Scraper")
        self.root.geometry("900x700")
        
        # Создаем и размещаем элементы интерфейса
        self.create_widgets()
        
        # HTML шаблон для экспорта
        self.html_template = """
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Scraper Results</h1>
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
"""

    def create_widgets(self):
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
        
        # URL ввод
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", padx=10, pady=(0, 20))
        
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
        
        # Выбор элементов для извлечения
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", padx=10, pady=(0, 20))
        
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
        self.extract_links.pack(anchor="w", padx=10, pady=2)
        self.extract_links.select()
        
        self.extract_text = ctk.CTkCheckBox(
            options_frame,
            text="Текст",
            font=ctk.CTkFont(size=13)
        )
        self.extract_text.pack(anchor="w", padx=10, pady=2)
        self.extract_text.select()
        
        self.extract_headers = ctk.CTkCheckBox(
            options_frame,
            text="Заголовки",
            font=ctk.CTkFont(size=13)
        )
        self.extract_headers.pack(anchor="w", padx=10, pady=2)
        self.extract_headers.select()
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        self.scrape_button = ctk.CTkButton(
            buttons_frame,
            text="Начать извлечение",
            command=self.start_scraping,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.scrape_button.pack(side="left", padx=5)
        
        self.save_button = ctk.CTkButton(
            buttons_frame,
            text="Сохранить результаты",
            command=self.save_results,
            height=40,
            state="disabled",
            font=ctk.CTkFont(size=14)
        )
        self.save_button.pack(side="left", padx=5)
        
        # Переключатель темы
        self.theme_switch = ctk.CTkSwitch(
            buttons_frame,
            text="Темная тема",
            command=self.toggle_theme,
            font=ctk.CTkFont(size=13)
        )
        self.theme_switch.pack(side="right", padx=10)
        self.theme_switch.select()
        
        # Добавляем фрейм для экспорта
        export_frame = ctk.CTkFrame(buttons_frame)
        export_frame.pack(side="left", padx=5)

        # Выпадающий список форматов
        self.export_format = ctk.StringVar(value="Excel (.xlsx)")
        self.format_menu = ctk.CTkOptionMenu(
            export_frame,
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

        # Кнопка экспорта
        self.export_button = ctk.CTkButton(
            export_frame,
            text="Экспортировать",
            command=self.export_results,
            height=40,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.export_button.pack(side="left", padx=5)
        
        # Результаты
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=10)
        
        results_label = ctk.CTkLabel(
            results_frame,
            text="Результаты:",
            font=ctk.CTkFont(size=14)
        )
        results_label.pack(anchor="w", padx=10, pady=5)
        
        self.results_text = ctk.CTkTextbox(
            results_frame,
            wrap="word",
            font=ctk.CTkFont(size=13)
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Прогресс
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=13)
        )
        self.progress_label.pack(pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)
        
        self.results_data = None

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)

    def start_scraping(self):
        url = self.url_entry.get().strip()
        if not url:
            self.show_error("Пожалуйста, введите URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.progress_label.configure(text="Извлечение данных...")
        self.progress_bar.start()
        self.scrape_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.results_text.delete("0.0", "end")
        
        thread = threading.Thread(target=self.scrape_url, args=(url,))
        thread.daemon = True
        thread.start()

    def scrape_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            if self.extract_links.get():
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        if not href.startswith(('http://', 'https://')):
                            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                            href = base_url + href if href.startswith('/') else base_url + '/' + href
                        results.append({
                            'type': 'Ссылка',
                            'text': link.text.strip(),
                            'url': href
                        })
            
            if self.extract_headers.get():
                for tag in ['h1', 'h2', 'h3']:
                    headers = soup.find_all(tag)
                    for header in headers:
                        results.append({
                            'type': f'Заголовок ({tag})',
                            'text': header.text.strip(),
                            'url': ''
                        })
            
            if self.extract_text.get():
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.text.strip()
                    if text:
                        results.append({
                            'type': 'Текст',
                            'text': text,
                            'url': ''
                        })
            
            self.results_data = pd.DataFrame(results)
            self.root.after(0, self.update_results)
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))

    def update_results(self):
        if self.results_data is not None and not self.results_data.empty:
            for _, row in self.results_data.iterrows():
                self.results_text.insert("end", f"Тип: {row['type']}\n")
                self.results_text.insert("end", f"Текст: {row['text']}\n")
                if row['url']:
                    self.results_text.insert("end", f"URL: {row['url']}\n")
                self.results_text.insert("end", "─" * 50 + "\n")
            
            self.progress_label.configure(text="Извлечение завершено")
            self.save_button.configure(state="normal")
            self.export_button.configure(state="normal")
        else:
            self.progress_label.configure(text="Данные не найдены")
            self.save_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
        
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.scrape_button.configure(state="normal")

    def show_error(self, error_message):
        self.progress_label.configure(text="Ошибка")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.scrape_button.configure(state="normal")
        
        dialog = ctk.CTkInputDialog(
            text=f"Произошла ошибка при извлечении данных:\n{error_message}",
            title="Ошибка",
            button_text="OK"
        )
        dialog.get_input()

    def save_results(self):
        if self.results_data is None or self.results_data.empty:
            self.show_error("Нет данных для сохранения")
            return
            
        file_types = [
            ('Excel файлы', '*.xlsx'),
            ('CSV файлы', '*.csv'),
            ('Все файлы', '*.*')
        ]
        
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=file_types
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.results_data.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    self.results_data.to_excel(file_path, index=False)
                    
                dialog = ctk.CTkInputDialog(
                    text="Файл успешно сохранен",
                    title="Успех",
                    button_text="OK"
                )
                dialog.get_input()
            except Exception as e:
                self.show_error(f"Ошибка при сохранении файла:\n{str(e)}")

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

        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(f"{selected_format} files", f"*{extension}"), ("All files", "*.*")]
        )

        if file_path:
            try:
                export_func(file_path)
                dialog = ctk.CTkInputDialog(
                    text=f"Файл успешно экспортирован в формате {selected_format}",
                    title="Успех",
                    button_text="OK"
                )
                dialog.get_input()
            except Exception as e:
                self.show_error(f"Ошибка при экспорте файла:\n{str(e)}")

    def export_excel(self, file_path):
        self.results_data.to_excel(file_path, index=False)

    def export_csv(self, file_path):
        self.results_data.to_csv(file_path, index=False, encoding='utf-8-sig')

    def export_json(self, file_path):
        results = self.results_data.to_dict(orient='records')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def export_html(self, file_path):
        template = Template(self.html_template)
        html_content = template.render(items=self.results_data.to_dict(orient='records'))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def export_markdown(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Web Scraper Results\n\n")
            for _, row in self.results_data.iterrows():
                f.write(f"## {row['type']}\n\n")
                f.write(f"{row['text']}\n\n")
                if row['url']:
                    f.write(f"[Ссылка]({row['url']})\n\n")
                f.write("---\n\n")

    def export_text(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(tabulate(
                self.results_data,
                headers='keys',
                tablefmt='grid',
                showindex=False
            ))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = WebScraperGUI()
    app.run() 