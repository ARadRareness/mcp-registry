import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt


def read_file_content(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r") as file:
        return file.read()


def show_permission_dialog(file_path: str) -> bool:
    app = QApplication(sys.argv)

    description = read_file_content(file_path)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("Permission Request")
    msg_box.setText(description)
    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg_box.setDefaultButton(QMessageBox.Cancel)
    msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

    result = msg_box.exec()
    return result == QMessageBox.Ok


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if show_permission_dialog(sys.argv[1]):
            sys.exit(0)
        else:
            sys.exit(1)
