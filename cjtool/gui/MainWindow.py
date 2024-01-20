from debuger import FunctionData
from .CallStackView import CallStackView, StandardItem
from .SourceEdit import SourceEdit
from .CommentEdit import CommentEdit
from .Document import Document
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QWidget, QMessageBox, QStatusBar, QFileDialog, QAction, QDockWidget
from PyQt5.QtGui import QCloseEvent
from pathlib import Path


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
        self.setWindowTitle('CodeBook')
        self.resize(1200, 900)

        # You can't set a QLayout directly on the QMainWindow. You need to create a QWidget
        # and set it as the central widget on the QMainWindow and assign the QLayout to that.
        self.tree_view = CallStackView()
        self.tree_view.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.setCentralWidget(self.tree_view)
        self.setContentsMargins(4, 0, 4, 0)

        source_docker = self._addSourceDock()
        comment_docker = self._addCommentDock()
        self.resizeDocks([source_docker, comment_docker], [
                         7, 3], Qt.Orientation.Vertical)
        self._createMenuBar()
        self.document: Document = None

    def closeEvent(self, a0: QCloseEvent) -> None:
        self._close_file()
        if self.document:
            a0.ignore()
        else:
            super().closeEvent(a0)

    def _addSourceDock(self):
        source_edit = SourceEdit()
        docker = QDockWidget('source', self)
        docker.setWidget(source_edit)
        docker.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, docker)
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
        self.comment_docker = docker
        self.comment_edit = comment_edit
        comment_edit.commentChanged.connect(self.tree_view.onCommentChanged)
        return docker

    # def _fillContent(self, rootNode) -> None:
    #     filepath = ''
    #     if (len(sys.argv) == 2):
    #         filepath = adjust_file_path(sys.argv[1])

    #     if filepath:
    #         self._parse_file(rootNode, filepath)

    def _createMenuBar(self) -> None:
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')

        openAct = QAction('&Open', self)
        openAct.triggered.connect(self._open_file)
        fileMenu.addAction(openAct)

        saveAct = QAction('&Save', self)
        saveAct.triggered.connect(self._save_file)
        fileMenu.addAction(saveAct)

        saveAsAct = QAction('Save &As', self)
        saveAsAct.triggered.connect(self._save_as_file)
        fileMenu.addAction(saveAsAct)

        closeAct = QAction('&Close', self)
        closeAct.triggered.connect(self._close_file)
        fileMenu.addAction(closeAct)

        fileMenu.addSeparator()
        exitAct = QAction('&Exit', self)
        exitAct.triggered.connect(self._exit)
        fileMenu.addAction(exitAct)

        viewMenu = menuBar.addMenu('&View')
        toggleAction = self.comment_docker.toggleViewAction()
        viewMenu.addAction(toggleAction)

        helpMenu = menuBar.addMenu('&Help')
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        statusBar.showMessage('')

    def _save_file(self) -> None:
        self.document.save()

    def _save_as_file(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Save cst file', '', 'cst Files (*.cst)')
        if filename:
            self.document.save_as(filename)

    def _exit(self):
        self.close()
        if not self.document:
            QCoreApplication.instance().quit()

    def _close_file(self) -> None:
        if not self.document:
            return

        if self.document.isDirty:
            reply = QMessageBox.warning(self, 'File is modified but not saved',
                                        'Yes to Save, No to Ignore', QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.document.save()
            elif reply == QMessageBox.Abort:
                return

        self.document.close()
        self.document = None
        self.tree_view.clear()
        self.source_edit.clear()
        self.comment_edit.clear()
        self.setWindowTitle(f"CodeBook")

    def _open_file(self) -> None:
        if self.document:
            self._close_file()
            if self.document:
                return

        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open cst file', '', 'cst Files (*.cst)')
        if filename:
            self.setWindowTitle(f"CodeBook: {Path(filename).stem}")
            rootNode = self.tree_view.model().invisibleRootItem()

            self.document = Document(filename, rootNode)
            self.document.open()
            self.document.fill_tree()

            self.tree_view.expandAll()
            self.source_edit.setDocument(self.document)
            self.comment_edit.setDocument(self.document)
            self.tree_view.setDocument(self.document)
            self.document.contentChanged.connect(self.onContentChanged)
            self.tree_view.selectionModel().selectionChanged.connect(
                self.document.onSelectionChanged)

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

    def onContentChanged(self):
        if not self.document:
            return
        filename = self.document.filename
        if self.document.isDirty:
            self.setWindowTitle(f"CodeBook: {Path(filename).stem} *")
        else:
            self.setWindowTitle(f"CodeBook: {Path(filename).stem}")
