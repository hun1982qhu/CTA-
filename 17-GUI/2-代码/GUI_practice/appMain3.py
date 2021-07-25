#%%
import sys
from PyQt5.QtWidgets import QWidget, QApplication
from ui_FormHello import Ui_FormHello


class QmyWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__ui = Ui_FormHello()  # 创建UI对象
        self.__ui.setupUi(self)  # 构造UI
        self.Lab = "单继承的QmyWidget"
        self.__ui.LabelHello.setText(self.Lab)

    def setBtnText(self, aText):
        self.__ui.btnClose.setText(aText)



if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建app
    myWidget = QmyWidget()
    myWidget.show()
    myWidget.setBtnText("间接设置")
    sys.exit(app.exec_())