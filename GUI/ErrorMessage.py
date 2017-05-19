from PyQt5.QtWidgets import QMessageBox
import traceback
from CustomExceptions import *

# Error message to display when
class ErrorMessage(QMessageBox):
    def __init__(self, err, message):
        super(ErrorMessage, self).__init__()
        # set message info
        self.setWindowTitle('Error!')
        self.setText(message)
        if err is not None:
            self.setDetailedText('{}:\n{}\n{}'.format(
                type(err).__name__, str(err), str(traceback.format_tb(err.__traceback__))))
        # show
        self.exec_()
