"""
Модуль для подсветки синтаксиса markdown
Содержит класс MarkdownHighlighter для подсветки элементов markdown
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


class MarkdownHighlighter(QSyntaxHighlighter):
    """Синтаксический подсветчик с поддержкой светлой и темной тем"""

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setup_formats()

    def setup_formats(self):
        # Цвета для светлой темы
        if not self.dark_mode:
            header_color = QColor(106, 124, 192)
            bold_color = QColor(220, 50, 47)
            italic_color = QColor(255, 140, 0)
            code_bg = QColor(245, 245, 245)
            code_fg = QColor(0, 0, 0)
            link_color = QColor(30, 144, 255)
            blockquote_color = QColor(100, 100, 100)
            list_color = QColor(0, 100, 0)
            inline_code_bg = QColor(240, 240, 240)
            inline_code_fg = QColor(200, 0, 0)
        else:
            header_color = QColor(100, 180, 255)
            bold_color = QColor(255, 100, 100)
            italic_color = QColor(255, 180, 80)
            code_bg = QColor(40, 40, 40)
            code_fg = QColor(220, 220, 220)
            link_color = QColor(100, 180, 255)
            blockquote_color = QColor(180, 180, 180)
            list_color = QColor(100, 200, 100)
            inline_code_bg = QColor(60, 60, 60)
            inline_code_fg = QColor(255, 150, 150)

        self.formats = {}

        header_format = QTextCharFormat()
        header_format.setFontWeight(QFont.Bold)
        header_format.setForeground(header_color)
        self.formats["header"] = header_format

        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(bold_color)
        self.formats["bold"] = bold_format

        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(italic_color)
        self.formats["italic"] = italic_format

        code_format = QTextCharFormat()
        code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        code_format.setBackground(code_bg)
        code_format.setForeground(code_fg)
        self.formats["code"] = code_format

        inline_code_format = QTextCharFormat()
        inline_code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        inline_code_format.setBackground(inline_code_bg)
        inline_code_format.setForeground(inline_code_fg)
        self.formats["inline_code"] = inline_code_format

        link_format = QTextCharFormat()
        link_format.setForeground(link_color)
        link_format.setFontUnderline(True)
        self.formats["link"] = link_format

        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(blockquote_color)
        blockquote_format.setFontItalic(True)
        self.formats["blockquote"] = blockquote_format

        list_format = QTextCharFormat()
        list_format.setForeground(list_color)
        self.formats["list"] = list_format

    def highlightBlock(self, text):
        header1 = self.format_header(text, r'^#{1,6} .+', "header")
        self.format_text(text, r'\*{2}[^*]+\*{2}|_{2}[^_]+_{2}', "bold", 2)
        self.format_text(text, r'\*[^*]+\*|_[^_]+_', "italic", 1)
        self.format_text(text, r'`[^`]+`', "inline_code", 1)

        if text.startswith('    ') or text.startswith('\t'):
            self.setFormat(0, len(text), self.formats["code"])

        if text.startswith('> '):
            self.setFormat(0, len(text), self.formats["blockquote"])

        self.format_text(text, r'\[.*?\]\(.*?\)', "link", 0)

        if text.startswith(('* ', '- ', '+ ')) or (len(text) > 2 and text[1:3] == '. ' and text[0].isdigit()):
            self.setFormat(0, len(text), self.formats["list"])

    def format_header(self, text, pattern, format_key):
        import re
        for match in re.finditer(pattern, text):
            header_level = 0
            for char in match.group():
                if char == '#':
                    header_level += 1
                else:
                    break
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