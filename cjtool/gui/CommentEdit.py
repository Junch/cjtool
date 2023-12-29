from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import pyqtSignal
from debuger import FunctionData
from gui.Document import StandardItem, Document


class CommentEdit(QPlainTextEdit):
    commentChanged = pyqtSignal(str)

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
        self.textChanged.connect(self.textChangedAction)
        self.curDocument = None

    def setDocument(self, doc: Document):
        self.curDocument = doc
        doc.curItemChanged.connect(self.onCurItemChanged)
        self.commentChanged.connect(doc.onCommentChanged)

    def onCurItemChanged(self, item: StandardItem) -> None:
        comment = item.functionData.comment
        self.setPlainText(comment)

    def beforeSave(self, data: FunctionData):
        if self.document().isModified():
            comment = self.toPlainText()
            data.comment = comment
            self.document().setModified(False)

    def textChangedAction(self):
        comment = self.toPlainText()
        self.commentChanged.emit(comment)
