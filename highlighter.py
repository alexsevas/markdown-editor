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
        # Цвета для светлой и темной темы
        # Фиолетовый для заголовков, оранжевый для элементов разметки
        if not self.dark_mode:
            header_text_color = QColor(138, 43, 226)  # Фиолетовый для текста заголовков
            markup_color = QColor(255, 140, 0)  # Оранжевый для символов разметки
            text_color = QColor(0, 0, 0)  # Черный для обычного текста
            code_bg = QColor(245, 245, 245)
            code_fg = QColor(0, 0, 0)
            link_color = QColor(30, 144, 255)
            inline_code_bg = QColor(240, 240, 240)
            inline_code_fg = QColor(200, 0, 0)
        else:
            header_text_color = QColor(186, 85, 211)  # Светло-фиолетовый для текста заголовков
            markup_color = QColor(255, 165, 0)  # Оранжевый для символов разметки
            text_color = QColor(224, 224, 224)  # Светлый для обычного текста
            code_bg = QColor(40, 40, 40)
            code_fg = QColor(220, 220, 220)
            link_color = QColor(100, 180, 255)
            inline_code_bg = QColor(60, 60, 60)
            inline_code_fg = QColor(255, 150, 150)

        self.formats = {}

        # Формат для текста заголовков (фиолетовый)
        header_text_format = QTextCharFormat()
        header_text_format.setFontWeight(QFont.Bold)
        header_text_format.setForeground(header_text_color)
        self.formats["header_text"] = header_text_format

        # Формат для символов разметки (оранжевый)
        markup_format = QTextCharFormat()
        markup_format.setForeground(markup_color)
        self.formats["markup"] = markup_format

        # Формат для жирного текста
        bold_text_format = QTextCharFormat()
        bold_text_format.setFontWeight(QFont.Bold)
        bold_text_format.setForeground(text_color)
        self.formats["bold_text"] = bold_text_format

        # Формат для курсива
        italic_text_format = QTextCharFormat()
        italic_text_format.setFontItalic(True)
        italic_text_format.setForeground(text_color)
        self.formats["italic_text"] = italic_text_format

        # Формат для блоков кода
        code_format = QTextCharFormat()
        code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        code_format.setBackground(code_bg)
        code_format.setForeground(code_fg)
        self.formats["code"] = code_format

        # Формат для inline кода
        inline_code_format = QTextCharFormat()
        inline_code_format.setFontFamilies(["Consolas", "Courier New", "monospace"])
        inline_code_format.setBackground(inline_code_bg)
        inline_code_format.setForeground(inline_code_fg)
        self.formats["inline_code"] = inline_code_format

        # Формат для ссылок
        link_format = QTextCharFormat()
        link_format.setForeground(link_color)
        link_format.setFontUnderline(True)
        self.formats["link"] = link_format

        # Формат для изображений (синий)
        image_format = QTextCharFormat()
        image_format.setForeground(QColor(30, 144, 255) if not self.dark_mode else QColor(100, 180, 255))
        self.formats["image"] = image_format

        # Формат для цитат
        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(text_color)
        blockquote_format.setFontItalic(True)
        self.formats["blockquote"] = blockquote_format

    def highlightBlock(self, text):
        # Заголовки: # оранжевым, текст фиолетовым
        header_match = re.match(r'^(#{1,6})\s+(.+)', text)
        if header_match:
            # Символы # - оранжевым
            self.setFormat(0, len(header_match.group(1)), self.formats["markup"])
            # Пробел после #
            space_start = len(header_match.group(1))
            # Текст заголовка - фиолетовым
            text_start = header_match.start(2)
            text_length = len(header_match.group(2))
            self.setFormat(text_start, text_length, self.formats["header_text"])
            return

        # Жирный текст: ** или __ оранжевым, текст жирным
        for match in re.finditer(r'(\*\*|__)([^*_]+)(\*\*|__)', text):
            # Открывающие символы - оранжевым
            self.setFormat(match.start(1), len(match.group(1)), self.formats["markup"])
            # Текст - жирным
            self.setFormat(match.start(2), len(match.group(2)), self.formats["bold_text"])
            # Закрывающие символы - оранжевым
            self.setFormat(match.start(3), len(match.group(3)), self.formats["markup"])

        # Курсив: * или _ оранжевым, текст курсивом
        for match in re.finditer(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)|(?<!_)_(?!_)([^_]+)_(?!_)', text):
            if match.group(1):  # * ... *
                self.setFormat(match.start(), 1, self.formats["markup"])
                self.setFormat(match.start() + 1, len(match.group(1)), self.formats["italic_text"])
                self.setFormat(match.end() - 1, 1, self.formats["markup"])
            elif match.group(2):  # _ ... _
                self.setFormat(match.start(), 1, self.formats["markup"])
                self.setFormat(match.start() + 1, len(match.group(2)), self.formats["italic_text"])
                self.setFormat(match.end() - 1, 1, self.formats["markup"])

        # Inline код: ` оранжевым, текст с фоном
        for match in re.finditer(r'(`+)([^`]+)(`+)', text):
            # Открывающие ` - оранжевым
            self.setFormat(match.start(1), len(match.group(1)), self.formats["markup"])
            # Текст кода
            self.setFormat(match.start(2), len(match.group(2)), self.formats["inline_code"])
            # Закрывающие ` - оранжевым
            self.setFormat(match.start(3), len(match.group(3)), self.formats["markup"])

        # Блоки кода (4 пробела или tab)
        if text.startswith('    ') or text.startswith('\t'):
            self.setFormat(0, len(text), self.formats["code"])
            return

        # Цитаты: > оранжевым, текст курсивом
        if text.startswith('> '):
            self.setFormat(0, 1, self.formats["markup"])  # >
            self.setFormat(1, len(text) - 1, self.formats["blockquote"])  # текст
            return

        # Списки: *, -, +, 1. оранжевым
        list_match = re.match(r'^(\s*)([\*\-\+]|\d+\.)\s+', text)
        if list_match:
            # Отступ
            indent_len = len(list_match.group(1))
            # Маркер списка - оранжевым
            marker_start = indent_len
            marker_len = len(list_match.group(2))
            self.setFormat(marker_start, marker_len, self.formats["markup"])

        # Изображения Markdown: ![alt](url) - синим
        for match in re.finditer(r'!\[([^\]]*)\]\(([^\)]+)\)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats["image"])

        # HTML img теги: <img ... /> - синим
        for match in re.finditer(r'<img\s+[^>]*/?>', text, re.IGNORECASE):
            self.setFormat(match.start(), match.end() - match.start(), self.formats["image"])

        # Ссылки: [текст](url) - скобки оранжевым
        for match in re.finditer(r'(\[)([^\]]+)(\])(\()([^\)]+)(\))', text):
            self.setFormat(match.start(1), 1, self.formats["markup"])  # [
            self.setFormat(match.start(2), len(match.group(2)), self.formats["link"])  # текст
            self.setFormat(match.start(3), 1, self.formats["markup"])  # ]
            self.setFormat(match.start(4), 1, self.formats["markup"])  # (
            self.setFormat(match.start(5), len(match.group(5)), self.formats["link"])  # url
            self.setFormat(match.start(6), 1, self.formats["markup"])  # )