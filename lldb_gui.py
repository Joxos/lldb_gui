import subprocess, sys, os
from loguru import logger

from PySide6.QtWidgets import *
from PySide6 import QtCore
from PySide6.QtUiTools import QUiLoader

logger.debug("Try to get the path of lldb.py...")
lldb_path = subprocess.run("lldb -P",
                           capture_output=True).stdout.decode("utf-8")[:-1]
sys.path.append(lldb_path)
import lldb

logger.debug(f"Succeeded to import module lldb at {lldb_path}")
logger.debug("Initializing LLDB...")
global debugger
debugger = lldb.SBDebugger.Create()
logger.debug("Finished initializing lldb.")


def show_message(message):
    msgBox = QMessageBox()
    msgBox.setText(message)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.setDefaultButton(QMessageBox.Ok)
    msgBox.exec()


class Window(QWidget):

    def __init__(self):
        super().__init__()

        qfile = QtCore.QFile("lldb_gui.ui")
        self.ui = QUiLoader().load(qfile)
        self.ui.attach_lldb.clicked.connect(self.attach_lldb)
        self.ui.run_exec.clicked.connect(self.run_exec)
        self.target = None

        # init breakpoints table
        self.ui.breakpoints.setColumnCount(4)
        self.ui.breakpoints.setHorizontalHeaderLabels(
            ["Id", "Name", "Module", "Locations"])
        # set stretch
        self.ui.breakpoints.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.ui.breakpoints.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch)

    @QtCore.Slot()
    def attach_lldb(self):
        global debugger
        exec_path = self.ui.exec_path.toPlainText()
        logger.debug(f"Exec path: {exec_path}")
        if not os.path.isfile(exec_path):
            show_message(
                f"Executable {exec_path} doesn't exsist! LLDB process is now the same as before."
            )
            logger.error(f"{exec_path} isn't a file. Stopped operation!")
            return
        self.target = debugger.CreateTargetWithFileAndArch(
            exec_path, lldb.LLDB_ARCH_DEFAULT)
        # LLDB failed to attach the target
        if not self.target:
            show_message(
                f"LLDB failed to attach {exec_path}. LLDB process is now the same as before."
            )
            logger.error(f"Failed to attach {exec_path}")
        self.ui.attach_lldb.setText("Reattach")
        self.exec_path = exec_path

    @QtCore.Slot()
    def run_exec(self):
        if self.target:
            self.process = self.target.LaunchSimple(None, None, os.getcwd())
            logger.debug(f"Successfully run {self.exec_path}")
            return
        show_message("There isn't any target to run.")
        logger.error("There isn't any target.")


if __name__ == "__main__":
    app = QApplication([], WindowFlags=QtCore.Qt.WindowStaysOnTopHint)
    w = Window()
    w.setWindowTitle("LLDB Debugger GUI")
    w.ui.show()
    app.exec()
