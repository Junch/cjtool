import re
import sys
from pathlib import Path
from common import print_warning
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QMenu, QWidget
from PyQt5.Qt import QStandardItemModel, QStandardItem
from PyQt5.QtCore import *


class PairError(Exception):

    def __init__(self, lineNum: int, line: str):
        self.lineNum = lineNum
        self.line = line


class Item(object):

    def __init__(self, enterFlag: bool, moduleName: str, funcName: str):
        self.enterFlag = enterFlag
        self.moduleName = moduleName
        self.funcName = funcName

    def pairWith(self, item) -> bool:
        return self.moduleName == item.moduleName and \
            self.funcName == item.funcName and \
            self.enterFlag != item.enterFlag


def parse(line: str) -> Item:
    pattern = r'^.{23} \[\w.+\] (>>|<<)(\w*)!(\S+)'
    m = re.match(pattern, line)
    if m:
        enterFlag = m.group(1) == ">>"
        moduleName = m.group(2)
        funcName = m.group(3)
        item = Item(enterFlag, moduleName, funcName)
        return item


def adjust_file_path(filename: str) -> str:
    if Path(filename).is_file():
        return filename

    newpath = Path.cwd().joinpath(filename)
    if Path(newpath).is_file():
        return newpath

    return None


class StandardItem(QStandardItem):
    def __init__(self, txt=''):
        super().__init__()
        self.setEditable(False)
        self.setText(txt)


class FunctionView(QTreeView):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setStyleSheet(
            "QTreeView::branch {  border-image: url(none.png); }")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)
        self.bStyleSheetNone = True

    def _rightClickMenu(self, pos):
        try:
            self.contextMenu = QMenu()
            self.actionExpand = self.contextMenu.addAction('全部展开')
            self.actionExpand.triggered.connect(self.expandAll)
            self.actionStyleSheet = self.contextMenu.addAction('样式切换')
            self.actionStyleSheet.triggered.connect(self._styleSheetChange)
            self.contextMenu.exec_(self.mapToGlobal(pos))  # 随指针的位置显示菜单
        except Exception as e:
            print(e)

    def _styleSheetChange(self):
        if self.bStyleSheetNone:
            self.setStyleSheet(
                "QTreeView::branch: {border-image: url(:/vline.png);}")
        else:
            self.setStyleSheet(
                "QTreeView::branch {  border-image: url(none.png); }")

        self.bStyleSheetNone = not self.bStyleSheetNone


class AppDemo(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('流程图')
        self.resize(500, 700)

        self._createMenuBar()

        treeView = FunctionView(self)

        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()
        self._fillContent(rootNode)

        treeView.setModel(treeModel)
        treeView.expandAll()
        self.setCentralWidget(treeView)

    def _fillContent(self, rootNode):
        filepath = ''
        if (len(sys.argv) == 2):
            filepath = adjust_file_path(sys.argv[1])

        if filepath:
            self._parse_file(rootNode, filepath)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

    def _parse_file(self, rootNode, filefullpath: str):
        stack = []
        nDepth = 0
        curRootNode = rootNode
        with open(filefullpath, 'r', encoding='utf-8') as f:
            for num, line in enumerate(f, 1):
                curItem = parse(line.rstrip())
                if not curItem:
                    continue

                paired = False
                if stack:
                    topItem = stack[-1][0]
                    if curItem.pairWith(topItem):
                        if curItem.enterFlag:
                            raise PairError(num, line)
                        paired = True

                if paired:
                    curRootNode = stack[-1][1]
                    stack.pop()
                    nDepth = nDepth - 1
                else:
                    if not curItem.enterFlag:
                        raise PairError(num, line)
                    stack.append((curItem, curRootNode))
                    nDepth = nDepth + 1
                    node = StandardItem(curItem.funcName)
                    curRootNode.appendRow(node)
                    curRootNode = node


def main():
    app = QApplication(sys.argv)
    demo = AppDemo()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
