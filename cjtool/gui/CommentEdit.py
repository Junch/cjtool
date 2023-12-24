from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFont, QFontMetrics


class CommentEdit(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        font = QFont('Inconsolata')
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(12)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        width = QFontMetrics(font).averageCharWidth()
        self.setTabStopDistance(4 * width)
