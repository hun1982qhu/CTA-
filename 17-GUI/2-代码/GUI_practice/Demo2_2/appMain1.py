import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import ui_FormHello


app = QtWidgets.QApplication(sys.argv)
baseWidget = QtWidgets.QWidget()

ui = ui_FormHello.Ui_FormHello()
ui.setupUi(baseWidget)

baseWidget.show()
ui.LabelHello.setText("            Hello，被程序修改")
sys.exit(app.exec_())
