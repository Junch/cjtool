from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFont, QFontMetrics
from gui.CallStackView import StandardItem


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

    def selectionChanged(self, selected, deselected) -> None:
        " Slot is called when the selection has been changed "
        if not selected.indexes():
            self.setPlainText('')
            return

        selectedIndex = selected.indexes()[0]
        item: StandardItem = selectedIndex.model().itemFromIndex(selectedIndex)
        if not item.functionData:
            return
