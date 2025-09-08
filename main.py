# conda activate allpy311

# pip install PyQt5 PyQtWebEngine markdown chardet

# + Проблема с RU кодировкой
# + инфо сообщения в консоли.


# Подавление предупреждений о deprecated sipPyTypeDict
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")


import sys
import chardet
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel,
                             QVBoxLayout, QSplitter, QTextEdit, QFileDialog,
                             QMenu, QAction, QMessageBox, QShortcut, QFrame)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, Qt, QSettings  # Исправлено: QSettings здесь
from PyQt5.QtGui import (QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
                         QTextCursor, QKeySequence, QPalette)
from PyQt5.QtWebChannel import QWebChannel


class MarkdownHighlighter(QSyntaxHighlighter):
    """Синтаксический подсветчик с поддержкой светлой и темной тем"""

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setup_formats()

    def setup_formats(self):
        # Цвета для светлой темы
        if not self.dark_mode:
            header_color = QColor(106, 124, 192)  # Синий для заголовков
            bold_color = QColor(220, 50, 47)  # Красный для жирного
            italic_color = QColor(255, 140, 0)  # Оранжевый для курсива
            code_bg = QColor(245, 245, 245)  # Светлый фон для кода
            code_fg = QColor(0, 0, 0)
            link_color = QColor(30, 144, 255)  # Синий для ссылок
            blockquote_color = QColor(100, 100, 100)
            list_color = QColor(0, 100, 0)
            inline_code_bg = QColor(240, 240, 240)
            inline_code_fg = QColor(200, 0, 0)
        # Цвета для темной темы
        else:
            header_color = QColor(100, 180, 255)  # Светло-синий
            bold_color = QColor(255, 100, 100)  # Светло-красный
            italic_color = QColor(255, 180, 80)  # Светло-оранжевый
            code_bg = QColor(40, 40, 40)  # Темный фон для кода
            code_fg = QColor(220, 220, 220)
            link_color = QColor(100, 180, 255)  # Светло-синий для ссылок
            blockquote_color = QColor(180, 180, 180)
            list_color = QColor(100, 200, 100)
            inline_code_bg = QColor(60, 60, 60)
            inline_code_fg = QColor(255, 150, 150)

        # Создаем форматы
        self.formats = {}

        # Заголовки
        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Bold)
        header_format.setForeground(header_color)
        self.formats["header"] = header_format

        # Жирный текст
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(bold_color)
        self.formats["bold"] = bold_format

        # Курсив
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(italic_color)
        self.formats["italic"] = italic_format

        # Блоки кода
        code_format = QTextCharFormat()
        code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        code_format.setBackground(code_bg)
        code_format.setForeground(code_fg)
        self.formats["code"] = code_format

        # Встроенный код
        inline_code_format = QTextCharFormat()
        inline_code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        inline_code_format.setBackground(inline_code_bg)
        inline_code_format.setForeground(inline_code_fg)
        self.formats["inline_code"] = inline_code_format

        # Ссылки
        link_format = QTextCharFormat()
        link_format.setForeground(link_color)
        link_format.setFontUnderline(True)
        self.formats["link"] = link_format

        # Цитаты
        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(blockquote_color)
        blockquote_format.setFontItalic(True)
        self.formats["blockquote"] = blockquote_format

        # Списки
        list_format = QTextCharFormat()
        list_format.setForeground(list_color)
        self.formats["list"] = list_format

    def highlightBlock(self, text):
        # Заголовки - # Header
        header1 = self.format_header(text, r'^#{1,6} .+', "header")

        # Жирный - **bold** или __bold__
        self.format_text(text, r'\*{2}[^*]+\*{2}|_{2}[^_]+_{2}', "bold", 2)

        # Курсив - *italic* или _italic_
        self.format_text(text, r'\*[^*]+\*|_[^_]+_', "italic", 1)

        # Встроенный код - `code`
        self.format_text(text, r'`[^`]+`', "inline_code", 1)

        # Блоки кода - с отступом 4 пробела или табуляция
        if text.startswith('    ') or text.startswith('\t'):
            self.setFormat(0, len(text), self.formats["code"])

        # Цитаты - > quote
        if text.startswith('> '):
            self.setFormat(0, len(text), self.formats["blockquote"])

        # Ссылки - [text](url)
        self.format_text(text, r'\[.*?\]\(.*?\)', "link", 0)

        # Списки - * item или - item или 1. item
        if text.startswith(('* ', '- ', '+ ')) or (len(text) > 2 and text[1:3] == '. ' and text[0].isdigit()):
            self.setFormat(0, len(text), self.formats["list"])

    def format_header(self, text, pattern, format_key):
        import re
        for match in re.finditer(pattern, text):
            # Определяем уровень заголовка по количеству #
            header_level = 0
            for char in match.group():
                if char == '#':
                    header_level += 1
                else:
                    break

            # Применяем формат ко всему заголовку
            start = match.start()
            length = match.end() - match.start()
            self.setFormat(start, length, self.formats[format_key])
            return True
        return False

    def format_text(self, text, pattern, format_key, offset=0):
        import re
        for match in re.finditer(pattern, text):
            start = match.start() + offset
            length = match.end() - match.start() - 2 * offset
            self.setFormat(start, length, self.formats[format_key])


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загрузка настроек
        self.settings = QSettings("Markdown", "Editor")
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.current_encoding = self.settings.value("encoding", "utf-8", type=str)

        self.setWindowTitle("Markdown Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Текущий файл
        self.current_file = None

        # Создание центрального виджета и макета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Создание сплиттера для редактора и превью
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Панель редактора
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Segoe UI", 10))
        self.editor.setTabStopDistance(40)  # 4 пробела для табуляции
        editor_layout.addWidget(self.editor)

        # Применение подсветки синтаксиса
        self.highlighter = MarkdownHighlighter(self.editor.document(), self.dark_mode)

        self.splitter.addWidget(editor_container)

        # Панель превью
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QWebEngineView()
        preview_layout.addWidget(self.preview)

        self.splitter.addWidget(preview_container)

        # Начальное соотношение сплиттера (50% на каждую панель)
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        # Таймер для обновления превью
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.render_preview)
        self.editor.textChanged.connect(self.start_update_timer)

        # Создание меню
        self.create_menu()

        # Настройка статусбара
        self.statusBar().showMessage("Ready")

        # Создание сочетаний клавиш
        self.setup_shortcuts()

        # Применение текущей темы
        self.apply_theme()

        # Инициализация превью
        self.render_preview()

    def create_menu(self):
        # Меню Файл
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

        # Меню Редактирование
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

        # Меню Вид
        view_menu = self.menuBar().addMenu("View")

        toggle_preview_action = QAction("Toggle Preview", self)
        toggle_preview_action.setShortcut("F11")
        toggle_preview_action.setCheckable(True)
        toggle_preview_action.setChecked(True)
        toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_preview_action)

        # Переключение темной темы
        self.toggle_dark_mode_action = QAction("Dark Mode", self)
        self.toggle_dark_mode_action.setCheckable(True)
        self.toggle_dark_mode_action.setChecked(self.dark_mode)
        self.toggle_dark_mode_action.setShortcut("Ctrl+D")
        self.toggle_dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.toggle_dark_mode_action)

        # Меню Кодировка
        encoding_menu = self.menuBar().addMenu("Encoding")

        # Список популярных кодировок для кириллицы
        encodings = [
            ("UTF-8", "utf-8"),
            ("Windows-1251 (Cyrillic)", "cp1251"),
            ("KOI8-R", "koi8-r"),
            ("UTF-16", "utf-16"),
            ("ISO-8859-5", "iso8859_5"),
            ("MacCyrillic", "mac_cyrillic")
        ]

        # Создаем действия для каждой кодировки
        self.encoding_actions = {}
        for name, encoding in encodings:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(encoding == self.current_encoding)
            action.triggered.connect(lambda checked, enc=encoding: self.set_encoding(enc))
            encoding_menu.addAction(action)
            self.encoding_actions[encoding] = action

        # Меню Помощь
        help_menu = self.menuBar().addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Добавляем статусную метку для кодировки
        self.statusBar().addPermanentWidget(QLabel("Encoding: "))
        self.encoding_label = QLabel(self.current_encoding)
        self.statusBar().addPermanentWidget(self.encoding_label)

    def setup_shortcuts(self):
        # Дополнительные сочетания клавиш
        QShortcut(QKeySequence("Ctrl+Z"), self, self.editor.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.editor.redo)
        QShortcut(QKeySequence("Ctrl+X"), self, self.editor.cut)
        QShortcut(QKeySequence("Ctrl+C"), self, self.editor.copy)
        QShortcut(QKeySequence("Ctrl+V"), self, self.editor.paste)
        QShortcut(QKeySequence("Ctrl+A"), self, self.editor.selectAll)

    def start_update_timer(self):
        """Запуск таймера для обновления превью"""
        self.update_timer.start(300)  # 300ms для оптимизации

    def render_preview(self):
        """Конвертация Markdown в HTML и отображение в превью"""
        md_text = self.editor.toPlainText()

        # Конвертация Markdown в HTML
        html = self.markdown_to_html(md_text)

        # Установка HTML в превью
        self.preview.setHtml(html, QUrl(""))

    def markdown_to_html(self, md_text):
        """Конвертация Markdown в HTML с поддержкой синтаксической подсветки"""
        # Используем расширение codehilite для подсветки синтаксиса
        html = markdown.markdown(md_text,
                                 extensions=[
                                     'fenced_code',
                                     'codehilite',  # Расширение для подсветки синтаксиса
                                     'tables',
                                     'nl2br',
                                     'sane_lists'
                                 ],
                                 extension_configs={
                                     'codehilite': {
                                         'css_class': 'highlight',
                                         'guess_lang': False,
                                     }
                                 })
        # HTML шаблон с экранированными фигурными скобками
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Markdown Preview</title>
            <style>
                /* Стили для светлой темы */
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", 
                                "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 0 20px;
                }}
                {0} /* Стили для темной темы будут здесь */
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
                p {{
                    margin: 16px 0;
                }}
                a {{
                    color: #1e6bb8;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                blockquote {{
                    border-left: 4px solid #1e6bb8;
                    padding: 10px 15px;
                    background-color: #f8f9fa;
                    margin: 20px 0;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: Consolas, "Courier New", monospace;
                    color: #d73a49;
                }}
                pre {{
                    background-color: #f5f5f5;
                    border-radius: 4px;
                    padding: 15px;
                    overflow: auto;
                    margin: 20px 0;
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
                table, th, td {{
                    border: 1px solid #ddd;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                }}
                th {{
                    background-color: #f5f5f5;
                }}
                ul, ol {{
                    padding-left: 25px;
                    margin: 16px 0;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                img {{
                    max-width: 100%;
                }}
                /* Стили для подсветки синтаксиса*/
                .highlight {{
                    background-color: #f5f5f5;
                    border-radius: 4px;
                    padding: 15px;
                    overflow: auto;
                    margin: 20px 0;
                }}
                .highlight .c {{ color: #999988; font-style: italic }} /* Комментарии */
                .highlight .err {{ color: #a61717; background-color: #e3d2d2 }} /* Ошибки */
                .highlight .k {{ color: #000080; font-weight: bold }} /* Ключевые слова */
                .highlight .o {{ color: #000000; font-weight: bold }} /* Операторы */
                .highlight .cm {{ color: #999988; font-style: italic }} /* Многострочные комментарии */
                .highlight .cp {{ color: #999999; font-weight: bold }} /* Директивы препроцессора */
                .highlight .c1 {{ color: #999988; font-style: italic }} /* Однострочные комментарии */
                .highlight .cs {{ color: #999999; font-weight: bold; font-style: italic }} /* Секции комментариев */
                .highlight .gd {{ color: #000000; background-color: #ffdddd }} /* Удаленные строки */
                .highlight .ge {{ color: #000000; font-style: italic }} /* Курсив */
                .highlight .gr {{ color: #aa0000 }} /* Ошибки */
                .highlight .gh {{ color: #999999 }} /* Заголовки */
                .highlight .gi {{ color: #000000; background-color: #ddffdd }} /* Добавленные строки */
                .highlight .go {{ color: #888888 }} /* Вывод */
                .highlight .gp {{ color: #555555 }} /* Приглашение */
                .highlight .gs {{ font-weight: bold }} /* Жирный */
                .highlight .gu {{ color: #aaaaaa; font-weight: bold }} /* Заголовки разделов */
                .highlight .gt {{ color: #aa0000 }} /* Типы */
                .highlight .kc {{ color: #000080; font-weight: bold }} /* Ключевые слова (константы) */
                .highlight .kd {{ color: #000080; font-weight: bold }} /* Ключевые слова (объявления) */
                .highlight .kn {{ color: #000080; font-weight: bold }} /* Ключевые слова (namespace) */
                .highlight .kp {{ color: #000080 }} /* Ключевые слова (пакеты) */
                .highlight .kr {{ color: #000080; font-weight: bold }} /* Ключевые слова (резервированные) */
                .highlight .kt {{ color: #445588; font-weight: bold }} /* Типы */
                .highlight .m {{ color: #009999 }} /* Числа */
                .highlight .s {{ color: #d14 }} /* Строки */
                .highlight .na {{ color: #008080 }} /* Атрибуты */
                .highlight .nb {{ color: #0086B3 }} /* Встроенные */
                .highlight .nc {{ color: #445588; font-weight: bold }} /* Классы */
                .highlight .no {{ color: #008080 }} /* Константы */
                .highlight .ni {{ color: #800080 }} /* Идентификаторы */
                .highlight .ne {{ color: #990000; font-weight: bold }} /* Исключения */
                .highlight .nf {{ color: #990000; font-weight: bold }} /* Функции */
                .highlight .nl {{ color: #990000; font-weight: bold }} /* Имена */
                .highlight .nn {{ color: #555555 }} /* Пространства имен */
                .highlight .nt {{ color: #000080 }} /* Теги */
                .highlight .nv {{ color: #008080 }} /* Переменные */
                .highlight .ow {{ color: #000000; font-weight: bold }} /* Операторы (слова) */
                .highlight .w {{ color: #bbbbbb }} /* Пробелы */
                .highlight .mf {{ color: #009999 }} /* Числа с плавающей точкой */
                .highlight .mh {{ color: #009999 }} /* Шестнадцатеричные числа */
                .highlight .mi {{ color: #009999 }} /* Целые числа */
                .highlight .mo {{ color: #009999 }} /* Восьмеричные числа */
                .highlight .sb {{ color: #d14 }} /* Строки (обратные кавычки) */
                .highlight .sc {{ color: #d14 }} /* Строки (символы) */
                .highlight .sd {{ color: #d14 }} /* Строки (документация) */
                .highlight .s2 {{ color: #d14 }} /* Строки (двойные кавычки) */
                .highlight .se {{ color: #d14 }} /* Строки (спец. символы) */
                .highlight .sh {{ color: #d14 }} /* Строки (оболочка) */
                .highlight .si {{ color: #d14 }} /* Строки (интерполяция) */
                .highlight .sx {{ color: #d14 }} /* Строки (произвольный синтаксис) */
                .highlight .sr {{ color: #009926 }} /* Регулярные выражения */
                .highlight .s1 {{ color: #d14 }} /* Строки (одинарные кавычки) */
                .highlight .ss {{ color: #990073 }} /* Строки (символы) */
                .highlight .bp {{ color: #999999 }} /* Встроенные переменные */
                .highlight .vc {{ color: #008080 }} /* Переменные (класс) */
                .highlight .vg {{ color: #008080 }} /* Переменные (глобальные) */
                .highlight .vi {{ color: #008080 }} /* Переменные (экземпляр) */
                .highlight .il {{ color: #009999 }} /* Целые литералы */
                /* MathJax styling */
                .MathJax {{
                    font-size: 110% !important;
                }}
                /* Custom styling for LaTeX formulas */
                .katex {{
                    font-size: 1.1em;
                }}
            </style>
        </head>
        <body>
            {1}
            <!-- MathJax для LaTeX -->
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    MathJax = {{
                        tex: {{
                            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                            processEscapes: true,
                            processEnvironments: true
                        }},
                        options: {{
                            ignoreHtmlClass: '.*|',
                            processHtmlClass: 'arithmatex'
                        }}
                    }};
                }});
            </script>
        </body>
        </html>
        """
        # Добавляем стили для темной темы если нужно
        dark_styles = ""
        if self.dark_mode:
            dark_styles = """
            body {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #64b4ff;
                border-bottom: 1px solid #444;
            }
            code {
                background-color: #333333;
                color: #ff9ea8;
            }
            pre {
                background-color: #252525;
            }
            blockquote {
                border-left: 4px solid #64b4ff;
                background-color: #333333;
            }
            .highlight {
                background-color: #252525;
            }
            """
        # Форматируем шаблон с правильным экранированием
        return template.format(dark_styles, html).replace("{{", "{").replace("}}", "}")

    def apply_theme(self):
        """Применение текущей темы ко всему приложению"""
        if self.dark_mode:
            # Темная тема
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
            palette.setColor(QPalette.HighlightedText, Qt.black)

            # Применяем палитру
            app.setPalette(palette)

            # Стиль для редактора
            self.editor.setStyleSheet("""
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #e0e0e0;
                    border: 1px solid #555555;
                }
            """)

            # Обновляем подсветку синтаксиса для темной темы
            self.highlighter = MarkdownHighlighter(self.editor.document(), dark_mode=True)

        else:
            # Светлая тема (по умолчанию)
            app.setStyle("Fusion")
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

            app.setPalette(palette)
            self.editor.setStyleSheet("")
            self.highlighter = MarkdownHighlighter(self.editor.document(), dark_mode=False)

    def toggle_dark_mode(self, checked):
        """Переключение между светлой и темной темой"""
        self.dark_mode = checked
        self.settings.setValue("dark_mode", checked)
        self.apply_theme()
        self.render_preview()  # Обновляем превью с новыми стилями
        self.statusBar().showMessage("Dark Mode ON" if checked else "Dark Mode OFF", 2000)

    def new_file(self):
        """Создание нового файла"""
        if self.editor.document().isModified():
            reply = QMessageBox.question(self, "Save Changes",
                                         "Do you want to save changes to the current document?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("Markdown Editor - New Document")

    def open_file(self):
        """Открытие markdown-файла с поддержкой ручного выбора кодировки"""
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown File", "",
                                              "Markdown Files (*.md *.markdown *.mkd);;All Files (*)")

        if path:
            try:
                # Пытаемся определить кодировку автоматически
                with open(path, 'rb') as f:
                    raw = f.read()

                detected = chardet.detect(raw)
                auto_encoding = detected['encoding'] or 'utf-8'

                # Проверяем, поддерживается ли кодировка
                supported_encodings = [enc for enc in self.encoding_actions.keys()]
                if auto_encoding.lower() not in [e.lower() for e in supported_encodings]:
                    auto_encoding = 'utf-8'

                # Устанавливаем соответствующую отметку в меню
                for enc, action in self.encoding_actions.items():
                    action.setChecked(enc.lower() == auto_encoding.lower())

                # Читаем с определенной кодировки
                text = raw.decode(auto_encoding, errors='replace')

                self.editor.setPlainText(text)
                self.current_file = path
                self.current_encoding = auto_encoding
                self.encoding_label.setText(auto_encoding)
                self.setWindowTitle(f"Markdown Editor - {path}")
                self.statusBar().showMessage(f"Opened {path} [{auto_encoding}]", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def set_encoding(self, encoding):
        """Установка кодировки и перезагрузка файла"""
        if not self.current_file:
            return

        # Обновляем статус и запоминаем выбранную кодировку
        self.current_encoding = encoding
        self.settings.setValue("encoding", encoding)

        # Переключаем отметку в меню
        for enc, action in self.encoding_actions.items():
            action.setChecked(enc == encoding)

        # Перечитываем файл с новой кодировкой
        try:
            with open(self.current_file, 'rb') as f:
                raw = f.read()
            text = raw.decode(encoding, errors='replace')

            # Сохраняем положение курсора
            cursor = self.editor.textCursor()
            scroll_pos = self.editor.verticalScrollBar().value()

            self.editor.setPlainText(text)

            # Восстанавливаем положение
            self.editor.setTextCursor(cursor)
            self.editor.verticalScrollBar().setValue(scroll_pos)

            self.encoding_label.setText(encoding)
            self.statusBar().showMessage(f"Reloaded with {encoding} encoding", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Encoding Error",
                                f"Failed to decode with {encoding}:\n{str(e)}")

    def save_file(self):
        """Сохранение текущего файла в выбранной кодировке"""
        if self.current_file:
            try:
                # Сохраняем в текущей кодировке
                with open(self.current_file, 'wb') as f:
                    text = self.editor.toPlainText()
                    f.write(text.encode(self.current_encoding, errors='replace'))

                self.editor.document().setModified(False)
                self.statusBar().showMessage(f"Saved {self.current_file} [{self.current_encoding}]", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
        else:
            self.save_file_as()

    def save_file_as(self):
        """Сохранение текущего файла с новым именем"""
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown File", "",
                                              "Markdown Files (*.md);;All Files (*)")

        if path:
            if not path.endswith('.md'):
                path += '.md'

            self.current_file = path
            self.save_file()
            self.setWindowTitle(f"Markdown Editor - {path}")

    def toggle_preview(self, checked):
        """Переключение видимости панели превью"""
        if checked:
            self.splitter.widget(1).show()
        else:
            self.splitter.widget(1).hide()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Markdown Editor",
                          "<h3>Markdown Editor</h3>"
                          "<p>A Markdown editor and viewer with syntax highlighting and LaTeX support.</p>"
                          "<p>Features:</p>"
                          "<ul>"
                          "<li>Real-time preview</li>"
                          "<li>Markdown syntax highlighting</li>"
                          "<li>LaTeX formula rendering</li>"
                          "<li>Support for various encodings</li>"
                          "<li>Customizable interface</li>"
                          "</ul>"
                          "<p>Version 0.0.3</p>"
                          "<p>Developer - alexsevas</p>"
                          "<p>mailto - a1exsevas@yandex.ru</p>")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.editor.document().isModified():
            reply = QMessageBox.question(self, "Save Changes",
                                         "Do you want to save changes to the current document?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Создаем и показываем редактор
    editor = MarkdownEditor()
    editor.show()

    sys.exit(app.exec_())

