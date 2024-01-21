import sys
from gui.MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from pathlib import Path


def main():
    try:
        # https://www.pythontutorial.net/pyqt/pyqt-qmenu/
        import ctypes
        appid = 'cjtool.codebook.1.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    finally:
        app = QApplication(sys.argv)
        logo_path = str((Path(__file__).parent/'image/logo.png').absolute())
        app.setWindowIcon(QIcon(logo_path))

        font_path = str((Path(__file__).parent/'font/Inconsolata.ttf').absolute())
        id = QFontDatabase.addApplicationFont(font_path)
        assert (id == 0)
        families = QFontDatabase.applicationFontFamilies(id)
        assert (families[0] == 'Inconsolata')

        demo = MainWindow()
        demo.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
