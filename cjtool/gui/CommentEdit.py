from PyQt5.QtWidgets import QPlainTextEdit, QStyle
from PyQt5.QtGui import QFont, QFontMetrics, QStandardItem
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
        self.functionData = None

    def selectionChanged(self, selected, deselected) -> None:
        " Slot is called when the selection has been changed "
        if not selected.indexes():
            self.setPlainText('')
            return

        selectedIndex = selected.indexes()[0]
        item: StandardItem = selectedIndex.model().itemFromIndex(selectedIndex)
        if not item.functionData:
            return

        # 如果前面的数据修改了
        if self.functionData:
            if self.document().isModified():
                comment = self.toPlainText()
                self.functionData.comment = comment
                self.document().setModified(False)

        self.functionData = item.functionData
        comment = self.functionData.comment if hasattr(
            self.functionData, 'comment') else ''
        self.setPlainText(comment)
