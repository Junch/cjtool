from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMenu, QTreeView
from PyQt5.QtGui import QStandardItemModel
from PyQt5.Qt import QIcon
from debuger import FunctionData
from .Document import StandardItem
from pathlib import Path


class CallStackView(QTreeView):
    def __init__(self) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection)
        model = QStandardItemModel()
        self.setModel(model)
        self.bStyleSheetNone = False

        comment_path = str(
            (Path(__file__).parent.parent/'image/comment.png').absolute())
        self.comment_icon = QIcon(comment_path)

    def clear(self):
        self.selectionModel().selectionChanged.disconnect()
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
                self.contextMenu.addAction(
                    '删除').triggered.connect(self._delete)
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
        names = []
        for index in self.selectedIndexes():
            item = index.model().itemFromIndex(index)
            names.append(item.text())

        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(names))

    def _delete(self) -> None:
        while self.selectedIndexes():
            idx = self.selectedIndexes()[0]
            self.model().removeRow(idx.row(), idx.parent())

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

    def iterItems(self, root):
        # https://stackoverflow.com/questions/41949370/collect-all-items-in-qtreeview-recursively
        def recurse(parent):
            for row in range(parent.rowCount()):
                for column in range(parent.columnCount()):
                    child = parent.child(row, column)
                    yield child
                    if child.hasChildren():
                        yield from recurse(child)
        if root is not None:
            yield from recurse(root)

    def getSameItems(self, offset: int) -> list[StandardItem]:
        arr = []

        model = self.model()
        root = model.invisibleRootItem()
        for node in self.iterItems(root):
            if node.offset == offset:
                arr.append(node)

        return arr

    def getCurrentFunctionData(self) -> FunctionData:
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            return None

        index = self.selectedIndexes()[0]
        item: StandardItem = index.model().itemFromIndex(index)
        return item.functionData

    def onCommentChanged(self, comment: str):
        functionData = self.getCurrentFunctionData()
        if not functionData:
            return

        items = self.getSameItems(functionData.offset)
        for item in items:
            icon = self.comment_icon if comment else QIcon()
            item.setIcon(icon)
