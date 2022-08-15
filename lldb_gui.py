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


def log_and_show_message(message, level="error"):
    show_message(message)
    if level == "error":
        logger.error(message)
    elif level == "info":
        logger.info(message)
    else:
        raise ValueError("level must be \"error\" or \"info\"")


class Window(QWidget):

    def __init__(self):
        super().__init__()

        # load ui
        self.ui = QUiLoader().load(QtCore.QFile("lldb_gui.ui"))

        # init variables
        self.target = None
        self.breakpoints = []
        self.base_path = self.ui.base_path.placeholderText()
        self.exec_path = ""
        self.full_path = self.base_path + self.exec_path
        self.process = lldb.SBProcess()

        # init breakpoints table
        self.ui.breakpoints.setColumnCount(4)
        self.ui.breakpoints.setHorizontalHeaderLabels(
            ["Id", "Name", "Module", "Locations"])
        # set stretch
        self.ui.breakpoints.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.ui.breakpoints.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch)

        # connect
        self.ui.attach_lldb.clicked.connect(self.attach_lldb)
        self.ui.run_exec.clicked.connect(self.run_exec)
        self.ui.stop_exec.clicked.connect(self.stop_exec)

    @QtCore.Slot()
    def attach_lldb(self):
        # get variables
        global debugger
        base_path = self.ui.base_path.toPlainText()
        if len(base_path) > 0:
            if base_path[-1] not in ["\\", "/"]:
                base_path += "/"
        exec_path = self.ui.exec_path.toPlainText()
        full_path = base_path + exec_path
        logger.debug(f"Base path: {base_path}")
        logger.debug(f"Exec path: {exec_path}")
        logger.debug(f"Full path: {full_path}")

        # verify executable file
        if not os.path.isfile(full_path):
            log_and_show_message(
                f"{full_path} isn't a file. LLDB process not changed.")
            return

        # create target
        self.target = debugger.CreateTargetWithFileAndArch(
            full_path, lldb.LLDB_ARCH_DEFAULT)
        # LLDB failed to attach the target
        if not self.target:
            log_and_show_message(
                f"LLDB failed to attach {full_path}. LLDB process not changes."
            )

        # update variables
        self.exec_path = exec_path
        self.base_path = base_path
        self.full_path = full_path

        # enable some buttons
        self.ui.run_exec.setEnabled(True)
        # self.ui.step_into.setEnabled(True)
        # self.ui.step_over.setEnabled(True)
        # self.ui.continue_exec.setEnabled(True)
        self.ui.add_breakpoint.setEnabled(True)
        # update attatch button to "Reattach"
        self.ui.attach_lldb.setText("Reattach")

        # log
        logger.debug(f"Succeeded to attach {full_path} to LLDB.")

    @QtCore.Slot()
    def run_exec(self):
        # stop the process first everytime to reduce codes to detect whether started or not
        self.stop_process()
        # create process
        self.process = self.target.LaunchSimple(None, None, os.getcwd())
        # set start button to "Restart"
        self.ui.run_exec.setText("Restart")
        # change the status of some buttons
        self.ui.stop_exec.setEnabled(True)
        # log
        logger.debug(f"Successfully run {self.exec_path}")

    # note that this isn't connected to a button
    def stop_process(self):
        # destroy the process
        self.process.Destroy()
        logger.debug("Destroy process.")

    # real stop_exec which connected to the button
    @QtCore.Slot()
    def stop_exec(self):
        self.stop_process()
        # change the status of some buttons
        # convert restart button to "Start"
        self.ui.run_exec.setText("Start")
        self.ui.stop_exec.setEnabled(False)
        # log
        logger.debug("Stopped debugging.")

    @QtCore.Slot()
    def add_breakpoint(self):
        # messagebox to get data
        # create breakpoint and add it to self.breakpoints
        # redisplay self.ui.breakpoints
        # log
        pass


if __name__ == "__main__":
    app = QApplication([], WindowFlags=QtCore.Qt.WindowStaysOnTopHint)
    w = Window()
    w.setWindowTitle("LLDB Debugger GUI")
    w.ui.show()
    app.exec()
"""
Testing:
1. base path not set and exec path is wrong
2. base path is set without any delimiter and exec_path is wrong
   take a look at full_path in console
3. correct path to an executable file
   then run it
"""
