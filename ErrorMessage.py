from PyQt5.QtWidgets import QMessageBox

# Error message to display when
class ErrorMessage(QMessageBox):
    def __init__(self, err, message):
        super(ErrorMessage, self).__init__()
        # set message info
        self.setWindowTitle('Error!')
        self.setText(message)
        self.setDetailedText(type(err).__name__ + ':\n' + str(err))
        # show
        self.exec_()
