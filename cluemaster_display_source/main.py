import splash_screen
import locale
from PyQt5.QtWidgets import QApplication
import os

snap_version = os.environ.get("SNAP_VERSION")


def main():
    if __name__ == "__main__":
        application = QApplication([])
        locale.setlocale(locale.LC_NUMERIC, 'C')
        application.setApplicationVersion(snap_version)
        application.setApplicationDisplayName("Escape Room Application")
        window = splash_screen.SplashWindow()
        window.show()
        application.exec_()


main()
