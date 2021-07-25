#%%
import sys
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, qCompress
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QWidget, QApplication, QDialog
from ui_Dialog import Ui_Dialog


class QmyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.radioButton.clicked.connect(self.do_setTextColor)
        self.ui.radioButton_2.clicked.connect(self.do_setTextColor)
        self.ui.radioButton_3.clicked.connect(self.do_setTextColor)

    def on_pushButton_clicked(self):
        self.ui.plainTextEdit.clear()

    def on_checkBox_3_toggled(self, checked):
        font = self.ui.plainTextEdit.font()
        font.setBold(checked)
        self.ui.plainTextEdit.setFont(font)

    def on_checkBox_clicked(self):
        checked = self.ui.checkBox.isChecked()  # 读取勾选状态
        font = self.ui.plainTextEdit.font()
        font.setUnderline(checked)
        self.ui.plainTextEdit.setFont(font)

    @pyqtSlot(bool)
    def on_checkBox_2_clicked(self, checked):
        font = self.ui.plainTextEdit.font()
        font.setItalic(checked)
        self.ui.plainTextEdit.setFont(font)

    def do_setTextColor(self):  # 设置文本颜色
        plet = self.ui.plainTextEdit.palette()
        if (self.ui.radioButton.isChecked()):
            plet.setColor(QPalette.text, QColor.black)
        elif (self.ui.radioButton_2.isChecked()):
            plet.setColor(QPalette.text, QColor.red)
        elif (self.ui.radioButton_3.isChecked()):
            plet.setColor(QPalette.text, QColor.blue)
        self.ui.plainTextEdit.setPalette(plet)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建app
    form = QmyDialog()
    form.show()
    sys.exit(app.exec_())