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


def load_ui(file_name):
    ui_file = QtCore.QFile(file_name)
    if not ui_file.open(QtCore.QIODevice.ReadOnly):
        logger.error(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    ui = QUiLoader().load(ui_file)
    ui_file.close()
    if not ui:
        logger.error(f"Failed to load ui: {loader.errorString()}")
        sys.exit(-1)
    return ui


class AddBreakpoint(QDialog):

    def __init__(self):
        super().__init__()

        # load ui
        self.ui = load_ui("add_breakpoint.ui")
        self.ui.cancel.clicked.connect(self.window_close)

        # fn
        self.ui.by_fn.clicked.connect(self.fn_clicked)

        # ln
        self.ui.by_ln.clicked.connect(self.ln_clicked)

    @QtCore.Slot()
    def window_close(self):
        self.ui.close()
        logger.debug("Add breakpoint canceled.")

    @QtCore.Slot()
    def fn_clicked(self):
        self.ui.file_name.setEnabled(False)
        self.ui.line_number.setEnabled(False)
        self.ui.label.setEnabled(False)
        self.ui.label_2.setEnabled(False)

        self.ui.function_name.setEnabled(True)
        self.ui.label_3.setEnabled(True)

    @QtCore.Slot()
    def ln_clicked(self):
        self.ui.function_name.setEnabled(False)
        self.ui.label_3.setEnabled(False)

        self.ui.file_name.setEnabled(True)
        self.ui.line_number.setEnabled(True)
        self.ui.label.setEnabled(True)
        self.ui.label_2.setEnabled(True)


# definition of w_add_breakpoint which holds the window of add_breakpoint
global w_add_breakpoint


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # load ui
        self.ui = load_ui("lldb_gui.ui")

        # init variables
        self.target = None
        self.breakpoints = []
        self.base_path = ""
        self.exec_path = ""
        self.full_path = ""
        self.process = lldb.SBProcess()

        # init breakpoints table
        self.ui.breakpoints.setColumnCount(4)
        self.ui.breakpoints.setHorizontalHeaderLabels(
            ["Id", "Location(s)", "Hit Count", "Target"])
        self.ui.breakpoints.setColumnWidth(0, self.ui.breakpoints.width() / 4)
        self.ui.breakpoints.setColumnWidth(1, self.ui.breakpoints.width() / 4)
        self.ui.breakpoints.setColumnWidth(2, self.ui.breakpoints.width() / 4)
        self.ui.breakpoints.setColumnWidth(3, self.ui.breakpoints.width() / 4)

        self.ui.breakpoints.horizontalHeader().ResizeMode(
            QHeaderView.Interactive)
        self.ui.breakpoints.verticalHeader().ResizeMode(
            QHeaderView.Interactive)

        # set stretch
        # self.ui.breakpoints.horizontalHeader().setSectionResizeMode(
        #     QHeaderView.Stretch)

        # connect
        self.ui.attach_lldb.clicked.connect(self.attach_lldb)
        self.ui.run_exec.clicked.connect(self.run_exec)
        self.ui.stop_exec.clicked.connect(self.stop_exec)
        self.ui.add_breakpoint.clicked.connect(self.add_breakpoint)

        self.ui.show()

    @QtCore.Slot()
    def attach_lldb(self):
        # get variables
        global debugger
        base_path = self.ui.base_path.toPlainText()
        logger.debug(f"Original base_path={base_path}")
        if len(base_path) > 0:
            if base_path[-1] not in ["\\", "/"]:
                base_path += "/"
        logger.debug(f"Fixed base_path={base_path}")
        exec_path = self.ui.exec_path.toPlainText()
        full_path = base_path + exec_path
        logger.debug(f"exec_path={exec_path}")
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
                f"LLDB failed to attach {full_path}. LLDB process not changed."
            )

        # update variables
        self.exec_path = exec_path
        self.base_path = base_path
        self.full_path = full_path

        # enable some buttons
        self.ui.run_exec.setEnabled(True)
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
        logger.debug(f"Successfully (re)run {self.exec_path}")

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
        # configure trigger function
        w_add_breakpoint.ui.add.clicked.connect(
            w_main_window.trigger_add_breakpoint)
        # show add window
        w_add_breakpoint.ui.show()
        # now the control is handled to that window
        # log
        logger.debug(
            "Trigger add_breakpoint action and succeeded to pop the instruction window."
        )

    @QtCore.Slot()
    def trigger_add_breakpoint(self):
        # get the window of add_breakpoint
        global w_add_breakpoint
        # get current selected and create breakpoint
        if w_add_breakpoint.ui.by_fn.isChecked():
            function_name = w_add_breakpoint.ui.function_name.text()

            logger.debug(f"by_fn is checked. function_name={function_name}")

            new_breakpoint = self.target.BreakpointCreateByName(
                function_name,
                self.target.GetExecutable().GetFilename())
            self.breakpoints.append(new_breakpoint)
            self.update_breakpoints_table()
            logger.info(f"New breakpoint: {str(new_breakpoint)}")
        elif w_add_breakpoint.ui.by_ln.isChecked():
            file_name = w_add_breakpoint.ui.file_name.text()
            line_number = w_add_breakpoint.ui.line_number.text()
            logger.debug(
                f"by_ln is checked. file_name={file_name}, line_number={line_number}"
            )
            new_breakpoint = self.target.BreakpointCreateByLocation(
                file_name, int(line_number))
            if not new_breakpoint:
                log_and_show_message(
                    f"{file_name}:{line_number} doesn't exsist!")
                return
            self.breakpoints.append(new_breakpoint)
            self.update_breakpoints_table()
            logger.info(f"New breakpoint: {str(new_breakpoint)}")
        w_add_breakpoint.ui.close()

    def update_breakpoints_table(self):
        # update row count
        self.ui.breakpoints.setRowCount(len(self.breakpoints))
        for i, brk in enumerate(self.breakpoints):
            self.ui.breakpoints.setItem(i, 0, QTableWidgetItem(brk.id))


if __name__ == "__main__":
    app = QApplication(
        [], WindowFlags=QtCore.Qt.WindowStaysOnTopHint)  # fix casade
    # initialization of components must be after QApplication got initialize
    w_add_breakpoint = AddBreakpoint()
    w_main_window = MainWindow()
    app.exec()
"""
Testing:
1. base path not set and exec path is wrong
2. base path is set without any delimiter and exec_path is wrong
   take a look at full_path in console
3. correct path to an executable file
   then run it
4. start, restart and stop
"""
