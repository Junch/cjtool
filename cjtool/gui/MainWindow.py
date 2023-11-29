from common import BreakPointHit, BreakPointPairError, FunctionData
from gui.CallStackView import CallStackView, StandardItem
from gui.SourceEdit import SourceEdit
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget, QStatusBar, QFileDialog, QAction, QMessageBox
from PyQt5.QtGui import QStandardItemModel
from pathlib import Path
import json
import sys


def keystoint(x):
    return {int(k): v for k, v in x.items()}


def adjust_file_path(filename: str) -> str:
    if Path(filename).is_file():
        return filename

    newpath = Path.cwd().joinpath(filename)
    if Path(newpath).is_file():
        return newpath

    return None


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
        treeView = CallStackView()
        treeModel = QStandardItemModel()
        treeView.setModel(treeModel)

        # Right is QTextEdit
        sourceEdit = SourceEdit()

        splitter.addWidget(treeView)
        splitter.addWidget(sourceEdit)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        layout.addWidget(splitter)

        treeView.selectionModel().selectionChanged.connect(sourceEdit.selectionChanged)
        treeView.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.treeView = treeView

    def _fillContent(self, rootNode) -> None:
        filepath = ''
        if (len(sys.argv) == 2):
            filepath = adjust_file_path(sys.argv[1])

        if filepath:
            self._parse_file(rootNode, filepath)

    def _createMenuBar(self) -> None:
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("&File")
        importAct = QAction('&Import', self)
        importAct.triggered.connect(self._import_file)
        fileMenu.addAction(importAct)

        helpMenu = menuBar.addMenu("&Help")
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        statusBar.showMessage("...")

    def _import_file(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Json file (*.json)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        if dialog.exec():
            filenames = dialog.selectedFiles()
            if filenames:
                self.treeView.clear()
                rootNode = self.treeView.model().invisibleRootItem()
                self._parse_file(rootNode, filenames[0])
                self.treeView.expandAll()

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

    def selectionChanged(self, selected, deselected) -> None:
        if not selected.indexes():
            return

        selectedIndex = selected.indexes()[0]
        item: StandardItem = selectedIndex.model().itemFromIndex(selectedIndex)
        if not item.functionData:
            return

        # 确定函数名所在的行
        filefullpath = item.functionData.fileName
        self.statusBar().showMessage(
            f"{filefullpath}({item.functionData.startLineNumber})")
