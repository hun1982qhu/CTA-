#%%
import sys
from PyQt5 import QtWidgets
import ui_FormHello

app = QtWidgets.QApplication(sys.argv)
baseWidget = QtWidgets.QWidget()

ui = ui_FormHello.Ui_FormHello()
ui.setupUi(baseWidget)  # 创建各组件的窗体容器

baseWidget.show()

sys.exit(app.exec_())