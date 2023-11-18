import re
import sys
from pathlib import Path
from common import print_warning, BreakPointHit, BreakPointPairError, FunctionData
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QMenu, QWidget, \
    QHBoxLayout, QTextEdit, QSplitter, QAbstractItemView
from PyQt5.Qt import QStandardItemModel, QStandardItem
from PyQt5.QtCore import *
import json


def keystoint(x):
    return {int(k): v for k, v in x.items()}


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
        self.offset = 0
        self.functionData: FunctionData = None

    def increaseCount(self):
        self.count += 1
        txt = self.functionName()
        self.setText(f'{txt} * {self.count}')

    def functionName(self):
        arr = self.text().split('*')
        return arr[0].rstrip()


class SourceEdit(QTextEdit):
    def __init__(self) -> None:
        super().__init__()

    def selectionChanged(self, selected, deselected):
        " Slot is called when the selection has been changed "
        selectedIndex = selected.indexes()[0]
        item: StandardItem = selectedIndex.model().itemFromIndex(selectedIndex)
        self.setText(str(item.functionData))


class FunctionView(QTreeView):
    def __init__(self) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bStyleSheetNone = False

    def _rightClickMenu(self, pos) -> None:
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

    def _copy(self) -> None:
        index = self.selectedIndexes()[0]
        item = index.model().itemFromIndex(index)
        clipboard = QApplication.clipboard()
        clipboard.setText(item.text())

    def _styleSheetChange(self) -> None:
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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('流程图')
        self.resize(1200, 900)

        self._createMenuBar()

        # You can't set a QLayout directly on the QMainWindow. You need to create a QWidget
        # and set it as the central widget on the QMainWindow and assign the QLayout to that.
        mainWnd = QWidget()
        self.setCentralWidget(mainWnd)
        layout = QHBoxLayout()
        mainWnd.setLayout(layout)

        splitter = QSplitter(Qt.Horizontal)

        # Left is QTreeView
        treeView = FunctionView()
        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()
        self._fillContent(rootNode)
        treeView.setModel(treeModel)
        treeView.expandAll()

        # Right is QTextEdit
        txt = SourceEdit()

        splitter.addWidget(treeView)
        splitter.addWidget(txt)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        layout.addWidget(splitter)

        treeView.selectionModel().selectionChanged.connect(txt.selectionChanged)

    def _fillContent(self, rootNode) -> None:
        filepath = ''
        if (len(sys.argv) == 2):
            filepath = adjust_file_path(sys.argv[1])

        if filepath:
            self._parse_file(rootNode, filepath)
        else:
            self._parse_file(rootNode, "E:/github/breakpoints/board.json")

    def _createMenuBar(self) -> None:
        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)

    def _parse_file(self, rootNode, filefullpath: str) -> None:
        stack = []
        nDepth = 0
        curRootNode = rootNode
        with open(filefullpath, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            hits = data['hits']
            functions = keystoint(data['functions'])

            for num, hit in enumerate(hits, 1):
                curItem = BreakPointHit()
                curItem.assign(hit)

                paired = False
                if stack:
                    topItem = stack[-1][0]
                    if curItem.pairWith(topItem):
                        if curItem.isStart:
                            raise BreakPointPairError(num, curItem)
                        paired = True

                if paired:
                    curRootNode = stack[-1][1]
                    stack.pop()
                    nDepth = nDepth - 1
                else:
                    if not curItem.isStart:
                        raise BreakPointPairError(num, hit)
                    stack.append((curItem, curRootNode))
                    nDepth = nDepth + 1
                    node = StandardItem(curItem.funtionName)
                    node.offset = curItem.offset
                    data = FunctionData()
                    data.assign(functions[node.offset])
                    node.functionData = data
                    curRootNode.appendRow(node)
                    curRootNode = node


def main():
    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
