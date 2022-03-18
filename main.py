
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph
from pyqtgraph import PlotWidget
import pandas as pd
from GUI import Ui_MainWindow
import csv

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Variables Initialization
    
        # Links of GUI Elements to Methods:
        #! Update 
        self.ui.pushButton.setCheckable(True)
        self.ui.actionOpen.triggered.connect(lambda: self.openFile())
        self.ui.pushButton.clicked.connect(lambda: self.showHideGraph())
        #! Make it ratio from fmax
        self.ui.horizontalSlider.valueChanged['int'].connect(self.ui.lcdNumber.display)
    # Methods

    # def open(self):
    #     self.filenames = QtWidgets.QFileDialog.getOpenFileName(
    #         None, 'Load Signal', './', "(*.csv *.xls *.txt)")
    #     path = self.filenames[0]
    #     self.openfile(path)
    def openFile(self):
        self.file_name = QtWidgets.QFileDialog.getOpenFileName(caption="Choose Signal", directory="", filter="csv (*.csv)")[0]
        self.data_frame = pd.read_csv(self.file_name, encoding = 'utf-8').fillna(0)
        self.TimeReadings = self.data_frame.iloc[:,0].to_numpy()
        self.AmplitudeReadings = self.data_frame.iloc[:,1].to_numpy()
        #! Update 
        self.ui.graphicsView.plot(self.TimeReadings, self.AmplitudeReadings, pen=pyqtgraph.mkPen('b', width=1.5), symbol='o', symbolPen ='b', symbolBrush = 0.9)
    
    def showHideGraph(self):
        if self.ui.pushButton.isChecked():
            self.ui.graphicsView_2.hide()
        else:
            self.ui.graphicsView_2.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())