"""
Основной модуль редактора markdown
Содержит класс MarkdownEditor - главное окно приложения
"""

import sys
import os
import re
import chardet
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel,
                             QVBoxLayout, QSplitter, QTextEdit, QFileDialog,
                             QMenu, QAction, QMessageBox, QShortcut, QFrame, QPlainTextEdit)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, Qt, QSettings, QSize, QRect
from PyQt5.QtGui import (QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
                         QTextCursor, QKeySequence, QPalette, QPainter, QTextFormat)
from PyQt5.QtWebChannel import QWebChannel

# Импортируем наши модули
from widgets import TextEditWithLineNumbers
from highlighter import MarkdownHighlighter


class MarkdownEditor(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        # self.apply_theme()
        self.settings = QSettings("Markdown", "Editor")
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.current_encoding = self.settings.value("encoding", "utf-8", type=str)

        self.setWindowTitle("Markdown Editor")
        self.setGeometry(100, 100, 1200, 800)

        self.current_file = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.editor = TextEditWithLineNumbers()
        self.editor.setFont(QFont("Consolas", 11))  # Моноширинный шрифт как в блокноте
        self.editor.setTabStopDistance(40)
        editor_layout.addWidget(self.editor)

        # Highlighter отключен - текст отображается как в обычном блокноте
        # self.highlighter = MarkdownHighlighter(self.editor.document(), self.dark_mode)

        self.splitter.addWidget(editor_container)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QWebEngineView()
        preview_layout.addWidget(self.preview)

        self.splitter.addWidget(preview_container)

        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.render_preview)
        self.editor.textChanged.connect(self.start_update_timer)

        self.create_menu()

        self.statusBar().showMessage("Ready")

        self.setup_shortcuts()

        self.apply_theme()

        # Синхронизация прокрутки
        self.sync_scroll_enabled = True
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_editor_to_preview)

        self.render_preview()

    def create_menu(self):
        file_menu = self.menuBar().addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        view_menu = self.menuBar().addMenu("View")

        toggle_preview_action = QAction("Toggle Preview", self)
        toggle_preview_action.setShortcut("F11")
        toggle_preview_action.setCheckable(True)
        toggle_preview_action.setChecked(True)
        toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_preview_action)

        self.toggle_dark_mode_action = QAction("Dark Mode", self)
        self.toggle_dark_mode_action.setCheckable(True)
        self.toggle_dark_mode_action.setChecked(self.dark_mode)
        self.toggle_dark_mode_action.setShortcut("Ctrl+D")
        self.toggle_dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.toggle_dark_mode_action)

        encoding_menu = self.menuBar().addMenu("Encoding")

        encodings = [
            ("UTF-8", "utf-8"),
            ("Windows-1251 (Cyrillic)", "cp1251"),
            ("KOI8-R", "koi8-r"),
            ("UTF-16", "utf-16"),
            ("ISO-8859-5", "iso8859_5"),
            ("MacCyrillic", "mac_cyrillic")
        ]

        self.encoding_actions = {}
        for name, encoding in encodings:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(encoding == self.current_encoding)
            action.triggered.connect(lambda checked, enc=encoding: self.set_encoding(enc))
            encoding_menu.addAction(action)
            self.encoding_actions[encoding] = action

        help_menu = self.menuBar().addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.statusBar().addPermanentWidget(QLabel("Encoding: "))
        self.encoding_label = QLabel(self.current_encoding)
        self.statusBar().addPermanentWidget(self.encoding_label)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self, self.editor.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.editor.redo)
        QShortcut(QKeySequence("Ctrl+X"), self, self.editor.cut)
        QShortcut(QKeySequence("Ctrl+C"), self, self.editor.copy)
        QShortcut(QKeySequence("Ctrl+V"), self, self.editor.paste)
        QShortcut(QKeySequence("Ctrl+A"), self, self.editor.selectAll)

    def start_update_timer(self):
        self.update_timer.start(300)

    def render_preview(self):
        md_text = self.editor.toPlainText()
        html = self.markdown_to_html(md_text)

        # Устанавливаем базовый URL для загрузки локальных изображений
        if self.current_file:
            base_url = QUrl.fromLocalFile(os.path.dirname(os.path.abspath(self.current_file)) + os.sep)
        else:
            base_url = QUrl.fromLocalFile(os.getcwd() + os.sep)

        self.preview.setHtml(html, base_url)
        # Синхронизируем прокрутку после рендеринга
        QTimer.singleShot(100, self.sync_editor_to_preview)

    def sync_editor_to_preview(self):
        """Синхронизация прокрутки редактора с preview"""
        if not self.sync_scroll_enabled:
            return

        # Получаем позицию прокрутки редактора
        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() == 0:
            scroll_percent = 0
        else:
            scroll_percent = scrollbar.value() / scrollbar.maximum()

        # Прокручиваем preview на тот же процент
        js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent});"
        self.preview.page().runJavaScript(js_code)

    def sync_preview_to_editor(self, scroll_percent):
        """Синхронизация прокрутки preview с редактором"""
        if not self.sync_scroll_enabled:
            return

        scrollbar = self.editor.verticalScrollBar()
        new_value = int(scrollbar.maximum() * scroll_percent)

        # Временно отключаем синхронизацию, чтобы избежать рекурсии
        self.sync_scroll_enabled = False
        scrollbar.setValue(new_value)
        self.sync_scroll_enabled = True

    def find_matching_brace(self, text, start_pos):
        """Находит соответствующую закрывающую скобку с учетом вложенности"""
        count = 1
        pos = start_pos + 1
        while pos < len(text) and count > 0:
            if text[pos] == '{':
                count += 1
            elif text[pos] == '}':
                count -= 1
            pos += 1
        return pos if count == 0 else -1

    def extract_latex_commands(self, text):
        """Извлекает LaTeX команды с правильной обработкой вложенных скобок"""
        result = []
        i = 0
        while i < len(text):
            if text[i:i + 1] == '\\' and i + 1 < len(text) and text[i + 1].isalpha():
                # Нашли LaTeX команду
                cmd_start = i
                i += 1
                # Читаем имя команды
                while i < len(text) and text[i].isalpha():
                    i += 1

                # Проверяем, есть ли аргументы
                args_end = i
                while i < len(text) and text[i] in ' \t':
                    i += 1

                # Собираем все аргументы команды
                while i < len(text) and text[i] in '{[':
                    if text[i] == '{':
                        end = self.find_matching_brace(text, i)
                        if end > 0:
                            args_end = end
                            i = end
                        else:
                            break
                    elif text[i] == '[':
                        # Опциональный аргумент
                        end = text.find(']', i)
                        if end > 0:
                            args_end = end + 1
                            i = end + 1
                        else:
                            break
                    # Пропускаем пробелы между аргументами
                    while i < len(text) and text[i] in ' \t':
                        i += 1

                result.append((cmd_start, args_end, text[cmd_start:args_end]))
            else:
                i += 1
        return result

    def markdown_to_html(self, md_text):
        """Конвертация Markdown в HTML с поддержкой LaTeX"""
        # Защищаем LaTeX формулы от обработки Markdown
        latex_blocks = []

        # Сохраняем display math с \[ ... \]
        def save_bracket_display_math(match):
            latex_blocks.append(('display', match.group(1)))
            return f'LATEX_DISPLAY_{len(latex_blocks) - 1}_PLACEHOLDER'

        md_text = re.sub(r'\\\[(.*?)\\\]', save_bracket_display_math, md_text, flags=re.DOTALL)

        # Сохраняем display math ($$...$$)
        def save_display_math(match):
            latex_blocks.append(('display', match.group(1)))
            return f'LATEX_DISPLAY_{len(latex_blocks) - 1}_PLACEHOLDER'

        md_text = re.sub(r'\$\$(.*?)\$\$', save_display_math, md_text, flags=re.DOTALL)

        # Сохраняем inline math с \( ... \)
        def save_paren_inline_math(match):
            latex_blocks.append(('inline', match.group(1)))
            return f'LATEX_INLINE_{len(latex_blocks) - 1}_PLACEHOLDER'

        md_text = re.sub(r'\\\((.*?)\\\)', save_paren_inline_math, md_text, flags=re.DOTALL)

        # Сохраняем inline math ($...$)
        def save_inline_math(match):
            latex_blocks.append(('inline', match.group(1)))
            return f'LATEX_INLINE_{len(latex_blocks) - 1}_PLACEHOLDER'

        md_text = re.sub(r'\$([^\$\n]+?)\$', save_inline_math, md_text)

        # Сохраняем одиночные LaTeX команды с правильной обработкой вложенных скобок
        latex_commands = self.extract_latex_commands(md_text)

        # Заменяем команды в обратном порядке, чтобы не сбить индексы
        for start, end, cmd_text in reversed(latex_commands):
            latex_blocks.append(('inline', cmd_text))
            placeholder = f'LATEX_INLINE_{len(latex_blocks) - 1}_PLACEHOLDER'
            md_text = md_text[:start] + placeholder + md_text[end:]

        # Конвертируем Markdown в HTML
        html = markdown.markdown(md_text,
                                 extensions=[
                                     'fenced_code',
                                     'codehilite',
                                     'tables',
                                     'nl2br',
                                     'sane_lists'
                                 ],
                                 extension_configs={
                                     'codehilite': {
                                         'css_class': 'highlight',
                                         'guess_lang': True,  # Автоматическое определение языка
                                         'linenums': False,  # Без номеров строк в коде
                                         'use_pygments': True  # Использовать Pygments для подсветки
                                     }
                                 })

        # Восстанавливаем LaTeX формулы
        for i, (math_type, content) in enumerate(latex_blocks):
            if math_type == 'display':
                placeholder = f'LATEX_DISPLAY_{i}_PLACEHOLDER'
                html = html.replace(placeholder, f'$$${content}$$$')
            else:
                placeholder = f'LATEX_INLINE_{i}_PLACEHOLDER'
                html = html.replace(placeholder, f'${content}$')

        # Создаем HTML с правильной конфигурацией MathJax
        dark_styles = ""
        if self.dark_mode:
            dark_styles = """
            body {
                background-color: #2b2b2b !important;
                color: #e0e0e0 !important;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #64b4ff !important;
                border-bottom: 1px solid #444 !important;
            }
            code {
                background-color: #1a1a1a !important;
                color: #ff9ea8 !important;
            }
            pre {
                background-color: #1a1a1a !important;
                margin: 0 !important;
                padding: 10px !important;
            }
            pre code {
                background-color: #1a1a1a !important;
                color: #e0e0e0 !important;
            }
            blockquote {
                border-left: 4px solid #64b4ff !important;
                background-color: #333333 !important;
            }
            .highlight {
                background-color: #1a1a1a !important;
                margin: 0 !important;
                padding: 10px !important;
            }
            table, th, td {
                border-color: #555 !important;
            }
            th {
                background-color: #333 !important;
            }

            /* Подсветка синтаксиса для темной темы */
            .highlight .hll { background-color: #404040 !important }
            .highlight .c { color: #6a9955 !important; font-style: italic } /* Комментарии */
            .highlight .err { color: #f44747 !important } /* Ошибки */
            .highlight .k { color: #569cd6 !important; font-weight: bold } /* Ключевые слова */
            .highlight .o { color: #d4d4d4 !important } /* Операторы */
            .highlight .ch { color: #6a9955 !important; font-style: italic } /* Комментарии */
            .highlight .cm { color: #6a9955 !important; font-style: italic } /* Многострочные комментарии */
            .highlight .cp { color: #9b9b9b !important } /* Препроцессор */
            .highlight .cpf { color: #6a9955 !important; font-style: italic } /* Комментарии препроцессора */
            .highlight .c1 { color: #6a9955 !important; font-style: italic } /* Однострочные комментарии */
            .highlight .cs { color: #6a9955 !important; font-style: italic } /* Специальные комментарии */
            .highlight .gd { color: #f44747 !important } /* Удаленное */
            .highlight .ge { font-style: italic !important } /* Курсив */
            .highlight .gr { color: #f44747 !important } /* Ошибки */
            .highlight .gh { color: #569cd6 !important; font-weight: bold } /* Заголовки */
            .highlight .gi { color: #4ec9b0 !important } /* Добавленное */
            .highlight .go { color: #808080 !important } /* Вывод */
            .highlight .gp { color: #569cd6 !important; font-weight: bold } /* Приглашение */
            .highlight .gs { font-weight: bold !important } /* Жирный */
            .highlight .gu { color: #c586c0 !important; font-weight: bold } /* Подзаголовки */
            .highlight .gt { color: #569cd6 !important } /* Трассировка */
            .highlight .kc { color: #569cd6 !important; font-weight: bold } /* Константы */
            .highlight .kd { color: #569cd6 !important; font-weight: bold } /* Объявления */
            .highlight .kn { color: #c586c0 !important; font-weight: bold } /* Namespace */
            .highlight .kp { color: #569cd6 !important } /* Псевдо */
            .highlight .kr { color: #569cd6 !important; font-weight: bold } /* Зарезервированные */
            .highlight .kt { color: #4ec9b0 !important } /* Типы */
            .highlight .m { color: #b5cea8 !important } /* Числа */
            .highlight .s { color: #ce9178 !important } /* Строки */
            .highlight .na { color: #9cdcfe !important } /* Атрибуты */
            .highlight .nb { color: #dcdcaa !important } /* Встроенные */
            .highlight .nc { color: #4ec9b0 !important; font-weight: bold } /* Классы */
            .highlight .no { color: #4fc1ff !important } /* Константы */
            .highlight .nd { color: #dcdcaa !important } /* Декораторы */
            .highlight .ni { color: #4fc1ff !important } /* Сущности */
            .highlight .ne { color: #f44747 !important; font-weight: bold } /* Исключения */
            .highlight .nf { color: #dcdcaa !important; font-weight: bold } /* Функции */
            .highlight .nl { color: #4fc1ff !important } /* Метки */
            .highlight .nn { color: #4ec9b0 !important } /* Пространства имен */
            .highlight .nt { color: #569cd6 !important } /* Теги */
            .highlight .nv { color: #9cdcfe !important } /* Переменные */
            .highlight .ow { color: #569cd6 !important; font-weight: bold } /* Операторы-слова */
            .highlight .w { color: #d4d4d4 !important } /* Пробелы */
            .highlight .mb { color: #b5cea8 !important } /* Числа */
            .highlight .mf { color: #b5cea8 !important } /* Float */
            .highlight .mh { color: #b5cea8 !important } /* Hex */
            .highlight .mi { color: #b5cea8 !important } /* Integer */
            .highlight .mo { color: #b5cea8 !important } /* Octal */
            .highlight .sa { color: #ce9178 !important } /* Строки */
            .highlight .sb { color: #ce9178 !important } /* Строки */
            .highlight .sc { color: #ce9178 !important } /* Символы */
            .highlight .dl { color: #ce9178 !important } /* Разделители строк */
            .highlight .sd { color: #6a9955 !important; font-style: italic } /* Docstring */
            .highlight .s2 { color: #ce9178 !important } /* Двойные кавычки */
            .highlight .se { color: #d7ba7d !important } /* Escape */
            .highlight .sh { color: #ce9178 !important } /* Shell */
            .highlight .si { color: #ce9178 !important } /* Интерполяция */
            .highlight .sx { color: #ce9178 !important } /* Другие строки */
            .highlight .sr { color: #d16969 !important } /* Regex */
            .highlight .s1 { color: #ce9178 !important } /* Одинарные кавычки */
            .highlight .ss { color: #ce9178 !important } /* Символы */
            .highlight .bp { color: #dcdcaa !important } /* Встроенные псевдо */
            .highlight .fm { color: #dcdcaa !important; font-weight: bold } /* Магические функции */
            .highlight .vc { color: #9cdcfe !important } /* Переменные класса */
            .highlight .vg { color: #9cdcfe !important } /* Глобальные переменные */
            .highlight .vi { color: #9cdcfe !important } /* Переменные экземпляра */
            .highlight .vm { color: #9cdcfe !important } /* Переменные магические */
            .highlight .il { color: #b5cea8 !important } /* Integer long */
            """

        template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Markdown Preview</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", 
                        "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }}
        {dark_styles}
        h1, h2, h3, h4, h5, h6 {{
            color: #1e6bb8;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
            margin-top: 24px;
        }}
        h1 {{ font-size: 2em; }}
        h2 {{ font-size: 1.75em; }}
        h3 {{ font-size: 1.5em; }}
        h4 {{ font-size: 1.25em; }}
        h5 {{ font-size: 1.1em; }}
        h6 {{ font-size: 1em; }}
        p {{ margin: 16px 0; }}
        a {{ color: #1e6bb8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        blockquote {{
            border-left: 4px solid #1e6bb8;
            padding: 10px 15px;
            background-color: #f8f9fa;
            margin: 20px 0;
        }}
        code {{
            background-color: #f0f0f0;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: Consolas, "Courier New", monospace;
            color: #d73a49;
        }}
        pre {{
            background-color: #f0f0f0;
            border-radius: 4px;
            padding: 10px;
            overflow: auto;
            margin: 0;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        table, th, td {{ border: 1px solid #ddd; }}
        th, td {{
            padding: 10px;
            text-align: left;
        }}
        th {{ background-color: #f5f5f5; }}
        ul, ol {{
            padding-left: 25px;
            margin: 16px 0;
        }}
        li {{ margin-bottom: 8px; }}
        img {{ 
            max-width: 100%; 
            height: auto;
            display: block;
            margin: 10px 0;
        }}
        .highlight {{
            background-color: #f0f0f0;
            border-radius: 4px;
            padding: 10px;
            overflow: auto;
            margin: 0;
        }}

        /* Подсветка синтаксиса для светлой темы */
        .highlight .hll {{ background-color: #ffffcc }}
        .highlight .c {{ color: #008000; font-style: italic }} /* Комментарии */
        .highlight .err {{ border: 1px solid #FF0000 }} /* Ошибки */
        .highlight .k {{ color: #0000ff; font-weight: bold }} /* Ключевые слова */
        .highlight .o {{ color: #666666 }} /* Операторы */
        .highlight .ch {{ color: #008000; font-style: italic }} /* Комментарии */
        .highlight .cm {{ color: #008000; font-style: italic }} /* Многострочные комментарии */
        .highlight .cp {{ color: #0000ff }} /* Препроцессор */
        .highlight .cpf {{ color: #008000; font-style: italic }} /* Комментарии препроцессора */
        .highlight .c1 {{ color: #008000; font-style: italic }} /* Однострочные комментарии */
        .highlight .cs {{ color: #008000; font-style: italic }} /* Специальные комментарии */
        .highlight .gd {{ color: #A00000 }} /* Удаленное */
        .highlight .ge {{ font-style: italic }} /* Курсив */
        .highlight .gr {{ color: #FF0000 }} /* Ошибки */
        .highlight .gh {{ color: #000080; font-weight: bold }} /* Заголовки */
        .highlight .gi {{ color: #00A000 }} /* Добавленное */
        .highlight .go {{ color: #888888 }} /* Вывод */
        .highlight .gp {{ color: #000080; font-weight: bold }} /* Приглашение */
        .highlight .gs {{ font-weight: bold }} /* Жирный */
        .highlight .gu {{ color: #800080; font-weight: bold }} /* Подзаголовки */
        .highlight .gt {{ color: #0044DD }} /* Трассировка */
        .highlight .kc {{ color: #0000ff; font-weight: bold }} /* Константы */
        .highlight .kd {{ color: #0000ff; font-weight: bold }} /* Объявления */
        .highlight .kn {{ color: #0000ff; font-weight: bold }} /* Namespace */
        .highlight .kp {{ color: #0000ff }} /* Псевдо */
        .highlight .kr {{ color: #0000ff; font-weight: bold }} /* Зарезервированные */
        .highlight .kt {{ color: #2b91af }} /* Типы */
        .highlight .m {{ color: #009999 }} /* Числа */
        .highlight .s {{ color: #a31515 }} /* Строки */
        .highlight .na {{ color: #ff0000 }} /* Атрибуты */
        .highlight .nb {{ color: #0000ff }} /* Встроенные */
        .highlight .nc {{ color: #2b91af; font-weight: bold }} /* Классы */
        .highlight .no {{ color: #880000 }} /* Константы */
        .highlight .nd {{ color: #808080 }} /* Декораторы */
        .highlight .ni {{ color: #880000 }} /* Сущности */
        .highlight .ne {{ color: #CC0000; font-weight: bold }} /* Исключения */
        .highlight .nf {{ color: #000000; font-weight: bold }} /* Функции */
        .highlight .nl {{ color: #880000 }} /* Метки */
        .highlight .nn {{ color: #0000ff }} /* Пространства имен */
        .highlight .nt {{ color: #800000 }} /* Теги */
        .highlight .nv {{ color: #000000 }} /* Переменные */
        .highlight .ow {{ color: #0000ff; font-weight: bold }} /* Операторы-слова */
        .highlight .w {{ color: #bbbbbb }} /* Пробелы */
        .highlight .mb {{ color: #009999 }} /* Числа */
        .highlight .mf {{ color: #009999 }} /* Float */
        .highlight .mh {{ color: #009999 }} /* Hex */
        .highlight .mi {{ color: #009999 }} /* Integer */
        .highlight .mo {{ color: #009999 }} /* Octal */
        .highlight .sa {{ color: #a31515 }} /* Строки */
        .highlight .sb {{ color: #a31515 }} /* Строки */
        .highlight .sc {{ color: #a31515 }} /* Символы */
        .highlight .dl {{ color: #a31515 }} /* Разделители строк */
        .highlight .sd {{ color: #a31515; font-style: italic }} /* Docstring */
        .highlight .s2 {{ color: #a31515 }} /* Двойные кавычки */
        .highlight .se {{ color: #a31515 }} /* Escape */
        .highlight .sh {{ color: #a31515 }} /* Shell */
        .highlight .si {{ color: #a31515 }} /* Интерполяция */
        .highlight .sx {{ color: #a31515 }} /* Другие строки */
        .highlight .sr {{ color: #a31515 }} /* Regex */
        .highlight .s1 {{ color: #a31515 }} /* Одинарные кавычки */
        .highlight .ss {{ color: #a31515 }} /* Символы */
        .highlight .bp {{ color: #0000ff }} /* Встроенные псевдо */
        .highlight .fm {{ color: #000000; font-weight: bold }} /* Магические функции */
        .highlight .vc {{ color: #000000 }} /* Переменные класса */
        .highlight .vg {{ color: #000000 }} /* Глобальные переменные */
        .highlight .vi {{ color: #000000 }} /* Переменные экземпляра */
        .highlight .vm {{ color: #000000 }} /* Переменные магические */
        .highlight .il {{ color: #009999 }} /* Integer long */
    </style>
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$$', '$$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true,
                packages: {{'[+]': ['ams', 'newcommand', 'configmacros', 'action', 'bbox', 'boldsymbol', 'braket', 'cancel', 'color', 'enclose', 'extpfeil', 'html', 'mhchem', 'unicode', 'verb']}},
                tags: 'ams',
                macros: {{
                    implies: '\\\\Rightarrow',
                    iff: '\\\\Leftrightarrow'
                }}
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            }},
            startup: {{
                pageReady: () => {{
                    return MathJax.startup.defaultPageReady().then(() => {{
                        console.log('MathJax loaded and ready');
                    }});
                }}
            }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
    <script>
        // Синхронизация прокрутки preview с редактором
        let scrollTimeout;
        window.addEventListener('scroll', function() {{
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {{
                const scrollPercent = window.scrollY / (document.body.scrollHeight - window.innerHeight);
                // Отправляем процент прокрутки обратно в Qt (если нужно)
                console.log('Preview scroll:', scrollPercent);
            }}, 100);
        }});
    </script>
</head>
<body>
    {html}
</body>
</html>"""

        return template

    def apply_theme(self):

        if self.dark_mode:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(45, 45, 45))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(30, 30, 30))
            palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
            palette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, QColor(255, 100, 100))
            palette.setColor(QPalette.Highlight, QColor(142, 45, 197))
            palette.setColor(QPalette.HighlightedText, Qt.white)

            # Цвета для меню
            palette.setColor(QPalette.Light, QColor(60, 60, 60))
            palette.setColor(QPalette.Midlight, QColor(50, 50, 50))
            palette.setColor(QPalette.Dark, QColor(35, 35, 35))
            palette.setColor(QPalette.Mid, QColor(40, 40, 40))
            palette.setColor(QPalette.Shadow, QColor(20, 20, 20))

            self.app.setPalette(palette)

            # Дополнительные стили для меню
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-bottom: 1px solid #555555;
                }
                QMenuBar::item {
                    background-color: transparent;
                    color: #ffffff;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QMenuBar::item:pressed {
                    background-color: #4d4d4d;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QMenu::item {
                    background-color: transparent;
                    color: #ffffff;
                    padding: 5px 25px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #555555;
                    margin: 5px 0px;
                }
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
            """)

            self.editor.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #2b2b2b;
                    color: #e0e0e0;
                    border: 1px solid #555555;
                    font-family: Consolas, "Courier New", monospace;
                }
            """)

        else:
            self.app.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, QColor(50, 50, 50))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            self.app.setPalette(palette)

            # Стили для светлой темы
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMenuBar::item {
                    background-color: transparent;
                    color: #000000;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QMenu::item {
                    background-color: transparent;
                    color: #000000;
                    padding: 5px 25px 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #cccccc;
                    margin: 5px 0px;
                }
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
            """)

            self.editor.setStyleSheet("""
                QPlainTextEdit {
                    font-family: Consolas, "Courier New", monospace;
                }
            """)

    def toggle_dark_mode(self, checked):
        self.dark_mode = checked
        self.settings.setValue("dark_mode", checked)
        self.apply_theme()
        self.editor.highlight_current_line()  # Обновляем подсветку текущей строки
        self.editor.line_number_area.update()  # Обновляем номера строк
        self.render_preview()
        self.statusBar().showMessage("Dark Mode ON" if checked else "Dark Mode OFF", 2000)

    def create_message_box(self, icon, title, text, buttons=QMessageBox.Ok):
        """Создает QMessageBox с правильной темой"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(buttons)

        # Применяем текущую палитру приложения к диалогу
        msg_box.setPalette(self.app.palette())

        # Применяем стили в зависимости от темы
        if self.dark_mode:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #5d5d5d;
                }
            """)

        return msg_box

    def new_file(self):
        if self.editor.document().isModified():
            msg_box = self.create_message_box(
                QMessageBox.Question,
                "Save Changes",
                "Do you want to save changes to the current document?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            reply = msg_box.exec_()

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("Markdown Editor - New Document")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown File", "",
                                              "Markdown Files (*.md *.markdown *.mkd);;All Files (*)")

        if path:
            try:
                with open(path, 'rb') as f:
                    raw = f.read()

                detected = chardet.detect(raw)
                auto_encoding = detected['encoding'] or 'utf-8'

                supported_encodings = [enc for enc in self.encoding_actions.keys()]
                if auto_encoding.lower() not in [e.lower() for e in supported_encodings]:
                    auto_encoding = 'utf-8'

                for enc, action in self.encoding_actions.items():
                    action.setChecked(enc.lower() == auto_encoding.lower())

                text = raw.decode(auto_encoding, errors='replace')

                self.editor.setPlainText(text)
                self.current_file = path
                self.current_encoding = auto_encoding
                self.encoding_label.setText(auto_encoding)
                self.setWindowTitle(f"Markdown Editor - {path}")
                self.statusBar().showMessage(f"Opened {path} [{auto_encoding}]", 5000)
            except Exception as e:
                msg_box = self.create_message_box(
                    QMessageBox.Critical,
                    "Error",
                    f"Failed to open file: {str(e)}"
                )
                msg_box.exec_()

    def set_encoding(self, encoding):
        if not self.current_file:
            return

        self.current_encoding = encoding
        self.settings.setValue("encoding", encoding)

        for enc, action in self.encoding_actions.items():
            action.setChecked(enc == encoding)

        try:
            with open(self.current_file, 'rb') as f:
                raw = f.read()
            text = raw.decode(encoding, errors='replace')

            cursor = self.editor.textCursor()
            scroll_pos = self.editor.verticalScrollBar().value()

            self.editor.setPlainText(text)

            self.editor.setTextCursor(cursor)
            self.editor.verticalScrollBar().setValue(scroll_pos)

            self.encoding_label.setText(encoding)
            self.statusBar().showMessage(f"Reloaded with {encoding} encoding", 3000)
        except Exception as e:
            msg_box = self.create_message_box(
                QMessageBox.Warning,
                "Encoding Error",
                f"Failed to decode with {encoding}:\n{str(e)}"
            )
            msg_box.exec_()

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'wb') as f:
                    text = self.editor.toPlainText()
                    f.write(text.encode(self.current_encoding, errors='replace'))

                self.editor.document().setModified(False)
                self.statusBar().showMessage(f"Saved {self.current_file} [{self.current_encoding}]", 3000)
            except Exception as e:
                msg_box = self.create_message_box(
                    QMessageBox.Critical,
                    "Error",
                    f"Failed to save file: {str(e)}"
                )
                msg_box.exec_()
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown File", "",
                                              "Markdown Files (*.md);;All Files (*)")

        if path:
            if not path.endswith('.md'):
                path += '.md'

            self.current_file = path
            self.save_file()
            self.setWindowTitle(f"Markdown Editor - {path}")

    def toggle_preview(self, checked):
        if checked:
            self.splitter.widget(1).show()
        else:
            self.splitter.widget(1).hide()

    def show_about(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About Markdown Editor")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(
            "<h3>Markdown Editor</h3>"
            "<p>A Markdown editor and viewer with syntax highlighting and LaTeX support.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Real-time preview</li>"
            "<li>Markdown syntax highlighting</li>"
            "<li>LaTeX formula rendering:</li>"
            "(inline: $...$ and display: $$...$$)"
            "<li>Support for various encodings</li>"
            "<li>Customizable interface</li>"
            "</ul>"
            "<p>Version 0.1.0</p>"
            "<p>Developer - alexsevas</p>"
            "<p>mailto - a1exsevas@yandex.ru</p>"
        )

        # Применяем текущую палитру приложения к диалогу
        msg_box.setPalette(self.app.palette())

        # Применяем стили в зависимости от темы
        if self.dark_mode:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #5d5d5d;
                }
            """)

        msg_box.exec_()

    def closeEvent(self, event):
        if self.editor.document().isModified():
            msg_box = self.create_message_box(
                QMessageBox.Question,
                "Save Changes",
                "Do you want to save changes to the current document?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            reply = msg_box.exec_()

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()