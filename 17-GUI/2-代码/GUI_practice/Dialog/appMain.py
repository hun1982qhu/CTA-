#%%
import sys
from PyQt5.QtWidgets import QApplication
from myDialog import QmyDialog

app = QApplication(sys.argv)  # 创建app
form = QmyDialog()
form.show()
sys.exit(app.exec_())