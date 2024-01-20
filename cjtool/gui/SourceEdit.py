from PyQt5.QtGui import QFont, QFontMetrics, QColor
from .Document import StandardItem, Document
from PyQt5.Qsci import QsciScintilla, QsciLexerCPP
from PyQt5.QtCore import pyqtSignal

class SourceEdit(QsciScintilla):
    sourceChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(SourceEdit, self).__init__(parent)

        # Set the default font
        font = QFont()
        font.setFamily('Inconsolata')  # Courier
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setUtf8(True)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        # Set CPP lexer
        # Set style for Python comments (style number 1) to a fixed-width
        # courier.
        #
        lexer = QsciLexerCPP()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)

        # Indentation
        #
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setTabIndents(True)
        self.setAutoIndent(True)

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        # not too small
        self.setMinimumSize(600, 450)
        self.textChanged.connect(self.onTextChanged)
        self.isItemChanged = False

    def setDocument(self, doc: Document):
        self.document: Document = doc
        self.document.curItemChanged.connect(self.onCurItemChanged)
        self.sourceChanged.connect(doc.onSourceChanged)

    def onCurItemChanged(self, item: StandardItem) -> None:
        self.isItemChanged = True
        content = self.document.get_source(item.functionData)
        self.setText(content)
        self.isItemChanged = False

    def onTextChanged(self) -> None:
        if self.isItemChanged:
            return

        self.sourceChanged.emit(self.text())
