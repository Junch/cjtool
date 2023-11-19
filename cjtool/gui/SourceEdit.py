from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QTextEdit
from gui.CallStackView import StandardItem
import linecache

class SourceEdit(QTextEdit):
    def __init__(self) -> None:
        super().__init__()
        font = QFont('Courier', 10)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setLineWrapMode(QTextEdit.NoWrap)
        width = QFontMetrics(font).averageCharWidth()
        self.setTabStopDistance(4 * width)

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

        self.setText(''.join(lines))