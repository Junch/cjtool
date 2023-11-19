import sys
from gui.MainWindow import MainWindow
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication


def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
