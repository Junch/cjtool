from PyQt5.QtGui import QFont, QFontMetrics, QColor, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import QPlainTextEdit
from gui.CallStackView import StandardItem
import linecache
from pygments import highlight
from pygments.lexers import *
from pygments.formatter import Formatter
from pygments.styles import get_style_by_name

# https://github.com/agoose77/hive2/blob/235a2f01dfd922f56d850062f2219bd444d24e7e/hive_editor/qt/code_editor.py
# https://ralsina.me/static/highlighter.py


def hex_to_qcolor(c):
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return QColor(r, g, b)


class CodeFormatter(Formatter):

    def __init__(self, style='', font=None):
        Formatter.__init__(self, style=style)

        self._character_formats = []
        self._token_styles = {}

        for token, style in self.style:
            text_char_format = QTextCharFormat()

            if font is not None:
                text_char_format.setFont(font)
            if style['color']:
                text_char_format.setForeground(hex_to_qcolor(style['color']))
            if style['bgcolor']:
                text_char_format.setBackground(hex_to_qcolor(style['bgcolor']))
            if style['bold']:
                text_char_format.setFontWeight(QFont.Bold)
            if style['italic']:
                text_char_format.setFontItalic(True)
            if style['underline']:
                text_char_format.setFontUnderline(True)

            self._token_styles[token] = text_char_format

        self._default_format = QTextCharFormat()

        if font is not None:
            self._default_format.setFont(font)

    def get_format(self, index):
        try:
            return self._character_formats[index]

        except IndexError:
            return self._default_format

    def format(self, tokens, outfile):
        self._character_formats.clear()

        for token, value in tokens:
            self._character_formats.extend(
                (self._token_styles[token],) * len(value))


class CodeHighlighter(QSyntaxHighlighter):

    def __init__(self, parent, lexer, formatter):
        QSyntaxHighlighter.__init__(self, parent)
        self._formatter = formatter
        self._lexer = lexer

    def highlightBlock(self, text):
        current_block = self.currentBlock()
        position = current_block.position()

        text = self.document().toPlainText() + '\n'
        highlight(text, self._lexer, self._formatter)

        for i in range(len(text)):
            text_format = self._formatter.get_format(position + i)
            self.setFormat(i, 1, text_format)


class SourceEdit(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        font = QFont('Inconsolata', 9)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        width = QFontMetrics(font).averageCharWidth()
        self.setTabStopDistance(4 * width)

        # 设置pygments的内建style
        style_name = 'nord-darker' # github-dark', 'solarized-dark'
        self.formatter = CodeFormatter(style=style_name, font=font)
        style = get_style_by_name(style_name)
        bgcolor = style.background_color
        self.setStyleSheet(f"background-color: {bgcolor};")

    def selectionChanged(self, selected, deselected) -> None:
        " Slot is called when the selection has been changed "
        selectedIndex = selected.indexes()[0]
        item: StandardItem = selectedIndex.model().itemFromIndex(selectedIndex)
        if not item.functionData:
            return

        # 确定函数名所在的行
        functionName = item.functionData.funtionName.split('!')[1]  # 去掉!前的模块名称
        filefullpath = item.functionData.fileName
        for i in range(item.functionData.startLineNumber, 0, -1):
            line = linecache.getline(filefullpath, i)
            if functionName in line:
                break

        line_numbers = range(i, item.functionData.endLineNumber + 1)

        lines = []
        for i in line_numbers:
            line = linecache.getline(filefullpath, i)
            lines.append(line)

        self.setPlainText(''.join(lines))

        # Highlighting
        lexer = get_lexer_by_name('cpp')
        self._highlighter = CodeHighlighter(
            self.document(), lexer, self.formatter)
