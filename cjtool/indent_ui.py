import sys
from gui.MainWindow import MainWindow
from PyQt5 import QtCore
import qdarkstyle
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import ctypes


def main():
    appid = 'cjtool.junchen.1.0' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app_icon = QIcon('image/logo.png')
    app.setWindowIcon(app_icon)

    demo = MainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
