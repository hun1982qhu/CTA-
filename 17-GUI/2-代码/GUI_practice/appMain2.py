#%%
import sys
from PyQt5.QtWidgets import QWidget, QApplication
from ui_FormHello import Ui_FormHello


class QmyWidget(QWidget, Ui_FormHello):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.Lab = "多重继承的QmyWidget"
        self.setupUi(self)
        self.LabelHello.setText(self.Lab)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建app
    myWidget = QmyWidget()
    myWidget.show()
    myWidget.btnClose.setText("不关闭了")
    sys.exit(app.exec_())