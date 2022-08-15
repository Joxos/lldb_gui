import subprocess, sys, os
from loguru import logger

from PySide6.QtWidgets import *
from PySide6.QtCore import QFile
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
# debugger.setAsync(False)
logger.debug("Finished initializing lldb.")


class Window:

    def __init__(self):
        super(Window, self).__init__()

        qfile = QFile("lldb_gui.ui")
        self.ui = QUiLoader().load(qfile)
        # self.ui.button.clicked.connect(self.btnClick)
        self.ui.attach_lldb.clicked.connect(self.attach_lldb)
        self.ui.run_exec.clicked.connect(self.run_exec)

    def attach_lldb(self):
        global debugger
        self.exec_path = self.ui.exec_path.toPlainText()
        logger.debug(f"Exec path: {self.exec_path}")
        if not os.path.isfile(self.exec_path):
            # show_message(
            #     f"Executable {exec_path} doesn't exsist! LLDB process is now unstarted"
            # )
            logger.error(f"{self.exec_path} isn't a file. Stopped operation!")
            return
        self.target = debugger.CreateTargetWithFileAndArch(
            self.exec_path, lldb.LLDB_ARCH_DEFAULT)
        if not self.target:
            logger.error(f"Failed to attach {self.exec_path}")

    def run_exec(self):
        self.process = self.target.LaunchSimple(None, None, os.getcwd())
        logger.debug(f"Successfully run {self.exec_path}")
        logger.debug(f"Successfully run {self.exec_path}")


if __name__ == '__main__':
    app = QApplication([])
    w = Window()
    w.ui.show()
    app.exec()

# import os, subprocess, sys

# gui = Gui(["LLDB GUI Debug Tool", _, "Author Joxos"],
#           ["LLDB Process Status: ", ("Unactivated", "status"), _],
#           ["Executable Path:", "__exec_path__", ["Run LLDB"]],
#           [(["Run Executable"], "run"), _, _])
# global p_lldb
# p_lldb = None
# logger.debug("Initialize done.")

# gui.RunLLDB = run_lldb

# def run_exec(gui, *args):
#     global p_lldb
#     if p_lldb == None:
#         show_message("LLDB process hasn't started yet!")
#         return
#     print(p_lldb.communicate("run"))

# gui.run = run_exec

# gui.run()
# # Ensure that lldb process is terminated.
# # if p_lldb != None:
# #     p_lldb.terminate()
# #     logger.debug("LLDB process terminated. Really exit now.")
# # logger.debug("LLDB process hasn't started yet. Exit directly.")
