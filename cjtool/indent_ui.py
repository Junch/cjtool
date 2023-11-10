import re
import sys
from pathlib import Path
from common import print_warning
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QMenu, QWidget, QMessageBox, QHBoxLayout, QTextEdit, QSplitter
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
        self.count = 1

    def increaseCount(self):
        self.count += 1
        txt = self.functionName()
        self.setText(f'{txt} * {self.count}')

    def functionName(self):
        arr = self.text().split('*')
        return arr[0].rstrip()


class FunctionView(QTreeView):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)
        self.bStyleSheetNone = False

    def _rightClickMenu(self, pos):
        try:
            self.contextMenu = QMenu()

            indexes = self.selectedIndexes()
            if len(indexes) > 0:
                self.actionCopy = self.contextMenu.addAction('复制')
                self.actionCopy.triggered.connect(self._copy)
                self.contextMenu.addSeparator()

            self.actionStyleSheet = self.contextMenu.addAction('样式切换')
            self.actionStyleSheet.triggered.connect(self._styleSheetChange)

            self.actionExpand = self.contextMenu.addAction('全部展开')
            self.actionExpand.triggered.connect(self.expandAll)

            arr = ['一级展开', '二级展开', '三级展开', '四级展开']
            self.actionExpandAction = [None]*4
            def foo(i): return lambda: self._expandLevel(i+1)
            for i, mi in enumerate(arr):
                self.actionExpandAction[i] = self.contextMenu.addAction(mi)
                self.actionExpandAction[i].triggered.connect(foo(i))

            self.actionLoopMatch = self.contextMenu.addAction('循环识别')
            self.actionLoopMatch.triggered.connect(self._loopMatch)

            self.contextMenu.exec_(self.mapToGlobal(pos))
        except Exception as e:
            print(e)

    def _copy(self):
        index = self.selectedIndexes()[0]
        item = index.model().itemFromIndex(index)
        clipboard = QApplication.clipboard()
        clipboard.setText(item.text())

    def _styleSheetChange(self):
        if self.bStyleSheetNone:
            self.setStyleSheet(
                "QTreeView::branch: {border-image: url(:/vline.png);}")
        else:
            self.setStyleSheet(
                "QTreeView::branch {border-image: url(none.png);}")

        self.bStyleSheetNone = not self.bStyleSheetNone

    def _expandLevel(self, nLevel: int):
        model = self.model()
        rootNode = model.invisibleRootItem()
        queue = []
        queue.append((rootNode, 0))
        while (queue):
            elem, level = queue.pop(0)
            if (level < nLevel):
                self.setExpanded(elem.index(), True)
                for row in range(elem.rowCount()):
                    child = elem.child(row, 0)
                    queue.append((child, level + 1))
            elif (level == nLevel):
                self.setExpanded(elem.index(), False)

    def _loopMatch(self):
        model = self.model()
        rootNode = model.invisibleRootItem()
        queue = []
        queue.append(rootNode)
        nCount = 0
        while (queue):
            elem = queue.pop(0)
            nCount += 1
            preChild = None
            row = 0
            while row < elem.rowCount():
                child = elem.child(row, 0)
                if row > 0 and preChild.functionName() == child.text():
                    elem.removeRow(row)
                    preChild.increaseCount()
                else:
                    row += 1
                    preChild = child
                    queue.append(child)

        # QMessageBox.about(self, '提示', f'节点数 {nCount}')


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('流程图')
        self.resize(1200, 900)

        self._createMenuBar()

        mainWnd = QWidget(self)
        self.setCentralWidget(mainWnd)
        layout = QHBoxLayout(self)
        mainWnd.setLayout(layout)

        splitter = QSplitter(Qt.Horizontal)

        # Left is QTreeView
        treeView = FunctionView(self)
        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()
        self._fillContent(rootNode)
        treeView.setModel(treeModel)
        treeView.expandAll()

        # Right is QTextEdit
        txt  = QTextEdit(self)

        splitter.addWidget(treeView)
        splitter.addWidget(txt)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        layout.addWidget(splitter)
  

    def _fillContent(self, rootNode):
        filepath = ''
        if (len(sys.argv) == 2):
            filepath = adjust_file_path(sys.argv[1])

        if filepath:
            self._parse_file(rootNode, filepath)
        else:
            self._parse_file(rootNode, "E:/github/breakpoints/board.log")

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
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
