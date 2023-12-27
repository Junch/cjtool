from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMenu, QTreeView
from PyQt5.Qt import QStandardItem
from debuger import FunctionData
from pathlib import Path


class StandardItem(QStandardItem):
    def __init__(self, txt=''):
        super().__init__()
        self.setEditable(False)
        self.setText(txt)
        self.count = 1
        self.offset = 0
        self.id = 0
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
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection)
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

    def _save(self, work_dir: str) -> None:
        src_dir = Path(work_dir).joinpath('code')
        if not src_dir.exists():
            Path(src_dir).mkdir()

        comment_dir = Path(work_dir).joinpath('comment')
        if not comment_dir.exists():
            Path(comment_dir).mkdir()

        lines = []
        model = self.model()
        rootNode = model.invisibleRootItem()
        stack = []
        stack.append((rootNode, -1))
        while stack:
            elem = stack[-1][0]
            depth = stack[-1][1]
            stack.pop()
            if hasattr(elem, 'functionData'):
                lines.append(
                    '\t'*depth + f"{elem.id} {elem.functionData.funtionName}\n")
                self._save_elem(elem, work_dir)

            for row in range(elem.rowCount() - 1, -1, -1):
                child = elem.child(row, 0)
                stack.append((child, depth + 1))

        with open(Path(work_dir).joinpath('tree.txt').absolute(), 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _save_elem(self, elem: StandardItem, work_dir: str) -> None:
        src_filename = Path(work_dir).joinpath(
            'code').joinpath(f"{elem.offset}.cpp")
        if not src_filename.exists():
            with open(src_filename.absolute(), 'w', encoding='utf-8') as f:
                content = elem.functionData.content()
                f.write(content)

        comment = elem.functionData.comment if hasattr(
            elem.functionData, 'comment') else ''
        cmt_filename = Path(work_dir).joinpath(
            'comment').joinpath(f"{elem.offset}.txt")
        if comment:
            with open(cmt_filename.absolute(), 'w', encoding='utf-8') as f:
                f.write(comment)
        else:
            if cmt_filename.exists():
                cmt_filename.unlink()

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

    def getSameItems(self, item: StandardItem) -> list[StandardItem]:
        arr = []
        if not item.functionData:
            return arr

        model = self.model()
        root = model.invisibleRootItem()
        for node in self.iterItems(root):
            if node.functionData == item.functionData:
                arr.append(node)

        return arr

    def getCurrentFunctionData(self) -> FunctionData:
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            return None

        index = self.selectedIndexes()[0]
        item: StandardItem = index.model().itemFromIndex(index)
        return item.functionData
