import sys
from gui.MainWindow import MainWindow
from PyQt5 import QtCore
import qdarkstyle
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import ctypes
from pathlib import Path


def main():
    appid = 'cjtool.junchen.1.0'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    logo_path = str((Path(__file__).parent/'image/logo.png').absolute())
    app.setWindowIcon(QIcon(logo_path))

    demo = MainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
