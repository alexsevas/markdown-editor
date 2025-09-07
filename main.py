# conda activate allpy311

# pip install PyQt5 PyQtWebEngine markdown chardet

# + Проблема с RU кодировкой
# - инфо сообщения в консоли:
'''
main.py: DeprecationWarning:
sipPyTypeDict() is deprecated, the extension module should use sipPyTypeDictRef() instead
'''


import sys
import chardet
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QSplitter, QTextEdit, QFileDialog,
                             QMenu, QAction, QMessageBox, QShortcut, QFrame)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import (QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
                         QTextCursor, QKeySequence, QPalette)
from PyQt5.QtWebChannel import QWebChannel

class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown syntax"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Style definitions
        self.formats = {}

        # Headers
        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Bold)
        header_format.setForeground(QColor(106, 124, 192))  # Blue color for headers
        self.formats["header"] = header_format

        # Bold
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(QColor(220, 50, 47))  # Red color for bold
        self.formats["bold"] = bold_format

        # Italic
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor(255, 140, 0))  # Orange color for italic
        self.formats["italic"] = italic_format

        # Code blocks
        code_format = QTextCharFormat()
        code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        code_format.setBackground(QColor(245, 245, 245))
        code_format.setForeground(QColor(0, 0, 0))
        self.formats["code"] = code_format

        # Inline code
        inline_code_format = QTextCharFormat()
        inline_code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        inline_code_format.setBackground(QColor(240, 240, 240))
        inline_code_format.setForeground(QColor(200, 0, 0))
        self.formats["inline_code"] = inline_code_format

        # Links
        link_format = QTextCharFormat()
        link_format.setForeground(QColor(30, 144, 255))
        link_format.setFontUnderline(True)
        self.formats["link"] = link_format

        # Blockquotes
        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(QColor(100, 100, 100))
        blockquote_format.setFontItalic(True)
        self.formats["blockquote"] = blockquote_format

        # Lists
        list_format = QTextCharFormat()
        list_format.setForeground(QColor(0, 100, 0))
        self.formats["list"] = list_format

    def highlightBlock(self, text):
        # Headers - # Header
        header1 = self.format_header(text, r'^#{1,6} .+', "header")

        # Bold - **bold** or __bold__
        self.format_text(text, r'\*{2}[^*]+\*{2}|_{2}[^_]+_{2}', "bold", 2)

        # Italic - *italic* or _italic_
        self.format_text(text, r'\*[^*]+\*|_[^_]+_', "italic", 1)

        # Inline code - `code`
        self.format_text(text, r'`[^`]+`', "inline_code", 1)

        # Code blocks - indented by 4 spaces or tabs
        if text.startswith('    ') or text.startswith('\t'):
            self.setFormat(0, len(text), self.formats["code"])

        # Blockquotes - > quote
        if text.startswith('> '):
            self.setFormat(0, len(text), self.formats["blockquote"])

        # Links - [text](url)
        self.format_text(text, r'\[.*?\]\(.*?\)', "link", 0)

        # Lists - * item or - item or 1. item
        if text.startswith(('* ', '- ', '+ ')) or (len(text) > 2 and text[1:3] == '. ' and text[0].isdigit()):
            self.setFormat(0, len(text), self.formats["list"])

    def format_header(self, text, pattern, format_key):
        import re
        for match in re.finditer(pattern, text):
            # Count # symbols to determine header level
            header_level = 0
            for char in match.group():
                if char == '#':
                    header_level += 1
                else:
                    break

            # Apply format to the entire header
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
        self.setWindowTitle("Markdown Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Current file path
        self.current_file = None

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for editor and preview
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Editor pane
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Segoe UI", 10))
        self.editor.setTabStopDistance(40)  # 4 spaces for tabs
        editor_layout.addWidget(self.editor)

        # Apply syntax highlighting
        self.highlighter = MarkdownHighlighter(self.editor.document())  # Syntax highlighting for Markdown [[7]]

        self.splitter.addWidget(editor_container)

        # Preview pane
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QWebEngineView()
        preview_layout.addWidget(self.preview)

        self.splitter.addWidget(preview_container)

        # Set initial splitter ratio (50% each)
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        # Timer for debouncing preview updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.render_preview)
        self.editor.textChanged.connect(self.start_update_timer)

        # Create menu bar
        self.create_menu()

        # Set up status bar
        self.statusBar().showMessage("Ready")

        # Create shortcuts
        self.setup_shortcuts()

        # Initial preview
        self.render_preview()

    def create_menu(self):
        # File menu
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

        # Edit menu
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

        # View menu
        view_menu = self.menuBar().addMenu("View")

        toggle_preview_action = QAction("Toggle Preview", self)
        toggle_preview_action.setShortcut("F11")
        toggle_preview_action.setCheckable(True)
        toggle_preview_action.setChecked(True)
        toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_preview_action)

        # Help menu
        help_menu = self.menuBar().addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Добавляем меню кодировок
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
            action.triggered.connect(lambda checked, enc=encoding: self.set_encoding(enc))
            encoding_menu.addAction(action)
            self.encoding_actions[encoding] = action

        # По умолчанию выбрана UTF-8
        self.current_encoding = "utf-8"
        self.encoding_actions["utf-8"].setChecked(True)



    def set_encoding(self, encoding):
        """Установить кодировку и перезагрузить файл"""
        if not self.current_file:
            return

        # Обновляем статус и запоминаем выбранную кодировку
        self.current_encoding = encoding

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

            self.statusBar().showMessage(f"Reloaded with {encoding} encoding", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Encoding Error",
                                f"Failed to decode with {encoding}:\n{str(e)}")



    def setup_shortcuts(self):
        # Additional shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self, self.editor.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.editor.redo)
        QShortcut(QKeySequence("Ctrl+X"), self, self.editor.cut)
        QShortcut(QKeySequence("Ctrl+C"), self, self.editor.copy)
        QShortcut(QKeySequence("Ctrl+V"), self, self.editor.paste)
        QShortcut(QKeySequence("Ctrl+A"), self, self.editor.selectAll)

    def start_update_timer(self):
        """Start the timer to debounce preview updates"""
        self.update_timer.start(300)  # 300ms debounce

    def render_preview(self):
        """Render the markdown to HTML and display in the preview pane"""
        md_text = self.editor.toPlainText()

        # Convert markdown to HTML with appropriate extensions
        html = self.markdown_to_html(md_text)

        # Set the HTML to the preview pane
        self.preview.setHtml(html, QUrl(""))

    def markdown_to_html(self, md_text):
        """Convert markdown text to HTML with styling similar"""
        # Convert markdown to HTML
        html = markdown.markdown(md_text,
                                 extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])

        # HTML template с ЭКРАНИРОВАННЫМИ фигурными скобками в CSS/JS
        template = """
        <!DOCTYPE html>
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
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 0 20px;
                }}
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
            {}

            <!-- MathJax for LaTeX rendering -->
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

        return template.format(html)

    def new_file(self):
        """Create a new file"""
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
        """Open a markdown file with manual encoding selection"""
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown File", "",
                                              "Markdown Files (*.md *.markdown *.mkd);;All Files (*)")

        if path:
            try:
                # Пытаемся определить кодировку автоматически
                with open(path, 'rb') as f:
                    raw = f.read()

                detected = chardet.detect(raw)
                self.current_encoding = detected['encoding'] or 'utf-8'

                # Проверяем, поддерживается ли кодировка
                supported_encodings = [enc for enc in self.encoding_actions.keys()]
                if self.current_encoding.lower() not in [e.lower() for e in supported_encodings]:
                    self.current_encoding = 'utf-8'

                # Устанавливаем соответствующую отметку в меню
                for enc, action in self.encoding_actions.items():
                    action.setChecked(enc.lower() == self.current_encoding.lower())

                # Читаем с определенной кодировки
                text = raw.decode(self.current_encoding, errors='replace')

                self.editor.setPlainText(text)
                self.current_file = path
                self.setWindowTitle(f"Markdown Editor - {path}")
                self.statusBar().showMessage(f"Opened {path} [{self.current_encoding}]", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def save_file(self):
        """Save the current file with current encoding"""
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
        """Save the current file with a new name"""
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown File", "",
                                              "Markdown Files (*.md);;All Files (*)")

        if path:
            if not path.endswith('.md'):
                path += '.md'

            self.current_file = path
            self.save_file()
            self.setWindowTitle(f"Markdown Editor - {path}")

    def toggle_preview(self, checked):
        """Toggle the preview pane visibility"""
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
                          "<p>Version 0.0.2</p>"
                          "<p>Developer - alexsevas</p>"
                          "<p>mailto - a1exsevas@yandex.ru</p>")

    def closeEvent(self, event):
        """Handle window close event"""
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

    # Set application style
    app.setStyle("Fusion")

    # Customize palette for better appearance
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

    editor = MarkdownEditor()
    editor.show()

    sys.exit(app.exec_())