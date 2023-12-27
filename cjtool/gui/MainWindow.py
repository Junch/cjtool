from debuger import BreakPointHit, FunctionData
from gui.CallStackView import CallStackView, StandardItem
from gui.SourceEdit import SourceEdit
from gui.CommentEdit import CommentEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget, QStyle, \
    QStatusBar, QFileDialog, QAction, QDockWidget
from PyQt5.QtGui import QStandardItemModel, QIcon
from pathlib import Path
import json
import sys
import zipfile
import tempfile
import os


def keystoint(x):
    return {int(k): v for k, v in x.items()}


def adjust_file_path(filename: str) -> str:
    if Path(filename).is_file():
        return filename

    newpath = Path.cwd().joinpath(filename)
    if Path(newpath).is_file():
        return newpath

    return None


def zipDir(dirpath: str, outFullName: str) -> None:
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename),
                      os.path.join(fpath, filename))
    zip.close()


class MainWindow(QMainWindow):
    beforeSave = pyqtSignal(FunctionData)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('CodeBook')
        self.resize(1200, 900)

        self._createMenuBar()

        # You can't set a QLayout directly on the QMainWindow. You need to create a QWidget
        # and set it as the central widget on the QMainWindow and assign the QLayout to that.
        self.tree_view = CallStackView()
        self.tree_view.setModel(QStandardItemModel())
        self.tree_view.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.setCentralWidget(self.tree_view)
        self.setContentsMargins(4, 0, 4, 0)

        source_docker = self._addSourceDock()
        comment_docker = self._addCommentDock()
        self.resizeDocks([source_docker, comment_docker], [
                         7, 3], Qt.Orientation.Vertical)
        
        commentIcon = QStyle.SP_FileDialogDetailedView
        self.icon = self.style().standardIcon(commentIcon)
        
        self.tempdir = None
        self.filename = ''

    def _addSourceDock(self):
        source_edit = SourceEdit()
        docker = QDockWidget('source', self)
        docker.setWidget(source_edit)
        docker.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, docker)
        self.tree_view.selectionModel().selectionChanged.connect(
            source_edit.selectionChanged)
        self.source_edit: SourceEdit = source_edit
        return docker

    def _addCommentDock(self):
        comment_edit = CommentEdit()
        docker = QDockWidget('comment', self)
        docker.setWidget(comment_edit)
        docker.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable |
                           QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, docker)
        self.tree_view.selectionModel().selectionChanged.connect(
            comment_edit.selectionChanged)
        self.comment_docker = docker
        self.comment_edit = comment_edit
        comment_edit.textChanged.connect(self.onCommentChanged)
        self.beforeSave.connect(comment_edit.beforeSave)
        return docker

    def _fillContent(self, rootNode) -> None:
        filepath = ''
        if (len(sys.argv) == 2):
            filepath = adjust_file_path(sys.argv[1])

        if filepath:
            self._parse_file(rootNode, filepath)

    def _createMenuBar(self) -> None:
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')

        openAct = QAction('&Open', self)
        openAct.triggered.connect(self._open_file)
        fileMenu.addAction(openAct)

        saveAct = QAction('&Save', self)
        saveAct.triggered.connect(self._save_file)
        fileMenu.addAction(saveAct)

        viewMenu = menuBar.addMenu('&View')
        showAct = QAction('&Comment Window', self)
        showAct.triggered.connect(self._show_comment)
        viewMenu.addAction(showAct)

        helpMenu = menuBar.addMenu('&Help')
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        statusBar.showMessage('')

    def _save_file(self) -> None:
        # 保存代码到零时目录
        functionData = self.tree_view.getCurrentFunctionData()
        self.beforeSave.emit(functionData)
        self.tree_view._save(self.tempdir.name)
        zipDir(self.tempdir.name, self.filename)

    def _open_file(self) -> None:
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open cst file', '', 'cst Files (*.cst)')
        if filename:
            self.setWindowTitle(f"CodeBook: {Path(filename).stem}")
            zf = zipfile.ZipFile(filename)
            self.tempdir = tempfile.TemporaryDirectory()
            zf.extractall(self.tempdir.name)
            self.tree_view.clear()
            self.source_edit.setWorkDir(self.tempdir.name)
            self.comment_edit.setWorkDir(self.tempdir.name)
            rootNode = self.tree_view.model().invisibleRootItem()
            self._parse_file(rootNode)
            self.tree_view.expandAll()
            self.filename = filename

    def _show_comment(self) -> None:
        visible = self.comment_docker.isVisible()
        if visible:
            self.comment_docker.hide()
        else:
            self.comment_docker.show()

    def get_breakpoints(self) -> tuple:
        monitor_file = Path(self.tempdir.name).joinpath('monitor.json')
        with open(monitor_file, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            hits = data['hits']
            functions = keystoint(data['functions'])

            breakpoints = {}
            for item in hits:
                hit = BreakPointHit()
                hit.assign(item)
                breakpoints[hit.id] = hit

            functionDict = {}
            for k, v in functions.items():
                func = FunctionData()
                func.assign(v)
                functionDict[k] = func
            return breakpoints, functionDict

    def split_line(self, line: str) -> tuple:
        depth = 0
        for c in line:
            if c == '\t':
                depth = depth + 1
            else:
                break

        arr = line.split(' ')
        id = int(arr[0])
        fname = arr[1].rstrip()
        return depth, id, fname

    def _parse_file(self, rootNode: StandardItem) -> None:
        breakpoints, functions = self.get_breakpoints()

        treefname = Path(self.tempdir.name).joinpath('tree.txt')
        with open(treefname, 'r', encoding='utf-8') as f:
            data = f.readlines()
            stack = [(-1, rootNode)]

            for line in data:
                depth, id, fname = self.split_line(line)
                node = StandardItem(fname)
                node.id = id
                node.offset = breakpoints[id].offset
                node.functionData = functions[node.offset]

                cmt_filename = Path(self.tempdir.name).joinpath(f"comment/{node.offset}.txt")
                if cmt_filename.exists():
                    node.setIcon(self.icon)
                    with open(cmt_filename.absolute(), 'r', encoding='utf-8') as f:
                        comment = f.read()
                        node.functionData.comment = comment

                preDepth, preNode = stack[-1]
                while depth <= preDepth:
                    stack.pop()
                    preDepth, preNode = stack[-1]
                preNode.appendRow(node)
                stack.append((depth, node))

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

    def onCommentChanged(self):
        if not self.tree_view.selectedIndexes():
            return

        index = self.tree_view.selectedIndexes()[0]
        item: StandardItem = index.model().itemFromIndex(index)
        functionData = item.functionData
        if not functionData:
            return

        items = self.tree_view.getSameItems(item)
        comment = self.comment_edit.document().toPlainText()
        for item in items:
            icon = self.icon if comment else QIcon()
            item.setIcon(icon)
