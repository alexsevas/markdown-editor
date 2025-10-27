"""
Виджеты для работы с текстом в Markdown редакторе
Содержит компоненты для отображения номеров строк и расширенного текстового редактора
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


class TextEditWithLineNumbers(QPlainTextEdit):
    """Текстовый редактор с номерами строк"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        """Вычисляет ширину области для номеров строк"""
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Обновляет отступ для номеров строк"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Обновляет область номеров строк при прокрутке"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Обрабатывает изменение размера редактора"""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """Отрисовывает номера строк"""
        painter = QPainter(self.line_number_area)

        # Используем тот же шрифт, что и в редакторе
        painter.setFont(self.font())

        # Фон для области номеров строк
        if self.palette().color(QPalette.Base).lightness() > 128:
            # Светлая тема
            painter.fillRect(event.rect(), QColor(240, 240, 240))
            text_color = QColor(100, 100, 100)
        else:
            # Темная тема
            painter.fillRect(event.rect(), QColor(40, 40, 40))
            text_color = QColor(150, 150, 150)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        # Рисуем номера строк
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(text_color)
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight | Qt.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        """Подсвечивает текущую строку"""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            # Цвет подсветки текущей строки
            if self.palette().color(QPalette.Base).lightness() > 128:
                # Светлая тема
                line_color = QColor(255, 255, 200, 100)
            else:
                # Темная тема
                line_color = QColor(60, 60, 60, 100)

            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)


class LineNumberArea(QWidget):
    """Виджет для отображения номеров строк"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)