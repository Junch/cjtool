from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMenu, QTreeView
from PyQt5.Qt import QStandardItem
from common import FunctionData
from pathlib import Path
import zipfile
import tempfile


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


class CallStackView(QTreeView):
    def __init__(self) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bStyleSheetNone = False

    def clear(self):
        self.model().beginResetModel()
        rowCount = self.model().rowCount()
        for i in range(rowCount):
            self.model().removeRow(0)
        self.model().endResetModel()

    def _rightClickMenu(self, pos) -> None:
        try:
            self.contextMenu = QMenu(self)

            indexes = self.selectedIndexes()
            if len(indexes) > 0:
                self.contextMenu.addAction('复制').triggered.connect(self._copy)
                self.contextMenu.addAction(
                    '复制路径').triggered.connect(self._copyPath)
                self.contextMenu.addSeparator()

            self.contextMenu.addAction(
                '样式切换').triggered.connect(self._styleSheetChange)
            self.contextMenu.addAction(
                '全部展开').triggered.connect(self.expandAll)

            arr = ['一级展开', '二级展开', '三级展开', '四级展开']
            def foo(i): return lambda: self.expandToDepth(i)
            for i, mi in enumerate(arr):
                self.contextMenu.addAction(mi).triggered.connect(foo(i))

            self.contextMenu.addAction(
                '循环识别').triggered.connect(self._loopMatch)

            self.contextMenu.exec_(self.mapToGlobal(pos))
        except Exception as e:
            print(e)

    def _copy(self) -> None:
        index = self.selectedIndexes()[0]
        item = index.model().itemFromIndex(index)
        clipboard = QApplication.clipboard()
        clipboard.setText(item.text())

    def _copyPath(self) -> None:
        index = self.selectedIndexes()[0]
        item: StandardItem = index.model().itemFromIndex(index)
        if not item.functionData:
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(item.functionData.fileName)

    def _styleSheetChange(self) -> None:
        if self.bStyleSheetNone:
            self.setStyleSheet(
                "QTreeView::branch: {border-image: url(:/vline.png);}")
        else:
            self.setStyleSheet(
                "QTreeView::branch {border-image: url(none.png);}")

        self.bStyleSheetNone = not self.bStyleSheetNone

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

    def _save(self, codeFolder: str) -> None:
        src_dir = Path(codeFolder).joinpath('code')
        if not src_dir.exists():
            Path(src_dir).mkdir()

        model = self.model()
        rootNode = model.invisibleRootItem()
        stack = []
        stack.append((rootNode, 0))
        while stack:
            elem = stack[-1][0]
            depth = stack[-1][1]
            stack.pop()
            if hasattr(elem, 'functionData'):
                # print('    '*depth + elem.functionData.funtionName)
                self._save_elem(elem, codeFolder)

            for row in range(elem.rowCount() - 1, -1, -1):
                child = elem.child(row, 0)
                stack.append((child, depth + 1))

    def _save_elem(self, elem: StandardItem, codeFolder: str) -> None:
        src_filename = Path(codeFolder).joinpath('code', f"{elem.offset}.cpp")
        if not src_filename.exists():
            with open(src_filename.absolute(), 'w', encoding='utf-8') as f:
                content = elem.functionData.content()
                f.write(content)
