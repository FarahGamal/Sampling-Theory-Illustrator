
import sys
from time import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph
from pyqtgraph import PlotWidget
import pandas as pd
from GUI import Ui_MainWindow
import csv
import numpy as np

SignalsCounter = -1



class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Variables Initialization
        global time
        self.time = np.linspace(-2.5, 2.5, 1000)
        self.added_composer_signals=0
        self.added_signals_list=[]
        # self.added_composer_signals_frequency=[]
        self.signal_index=None
        self.signal_to_delete=None
        # Links of GUI Elements to Methods:
        #! Update 
        self.ui.pushButton.setCheckable(True)
        self.ui.actionOpen.triggered.connect(lambda: self.openFile())
        self.ui.pushButton.clicked.connect(lambda: self.showHideGraph())
        self.ui.plot_button.clicked.connect(self.signal_composer)
        self.ui.add_button.clicked.connect(self.signal_summation)
        self.ui.delete_button.clicked.connect(self.signal_deletion)
        self.ui.comboBox.activated.connect(self.select_signal)
        self.ui.saveButton_3.clicked.connect(self.save_signal)
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
        self.ui.graphicsView.clear()
        self.ui.graphicsView.plot(self.TimeReadings, self.AmplitudeReadings, pen=pyqtgraph.mkPen('r', width=1.5))
        # self.ui.graphicsView.plot(self.TimeReadings, self.AmplitudeReadings, pen=pyqtgraph.mkPen('b', width=1.5), symbol='o', symbolPen ='b', symbolBrush = 0.9)
    
    def showHideGraph(self):
        if self.ui.pushButton.isChecked():
            self.ui.graphicsView_2.hide()
        else:
            self.ui.graphicsView_2.show()

    def signal_composer(self):
        global SignalsCounter
        self.ui.graphicsView_3.clear()
        self.frequency= float(self.ui.lineEdit.text())
        self.amplitude= float(self.ui.lineEdit_2.text()) 
        self.phase_shift= float(self.ui.lineEdit_3.text())
        self.signal = self.amplitude * np.sin(2 * np.pi * self.frequency * self.time + self.phase_shift)
        self.ui.graphicsView_3.plot(self.time, self.signal, pen=pyqtgraph.mkPen('r', width=1.5))
        SignalsCounter = SignalsCounter + 1

    def signal_summation(self):
        self.added_composer_signals+=self.signal
         #frequency stored in a list for later sampling
        # self.added_composer_signals_frequency.append(self.frequency)
        self.added_signals_list.append(self.signal)
        self.ui.comboBox.addItem('F='+ str(self.frequency)+ 'A=' +str(self.amplitude) + 'PS='+ str(self.phase_shift))
        self.ui.graphicsView_4.clear() #adjust it to the right graph
        # self.ui.graphicsView_4.plot(self.time, signal1+signal2, pen=pyqtgraph.mkPen('r', width=1.5))
        self.ui.graphicsView_4.plot(self.time, self.added_composer_signals, pen=pyqtgraph.mkPen('r', width=1.5))
       
        #get maximum frequency for sampling
        # maximum_frequency=np.max(self.added_composer_signals_frequency)

    def select_signal(self):
        self.signal_index=self.ui.comboBox.currentIndex()
    def signal_deletion(self):
        self.ui.graphicsView_4.clear()
        self.signal_to_delete=self.added_signals_list.pop(self.signal_index)
        # self.added_composer_signals_frequency.pop(self.signal_index)
        self.ui.comboBox.removeItem(self.signal_index)
        if self.ui.comboBox.count()==0:
            self.ui.graphicsView_4.clear()
        else:
            self.added_composer_signals-=self.signal_to_delete
            self.ui.graphicsView_4.plot(self.time, self.added_composer_signals, pen=pyqtgraph.mkPen('r', width=1.5))
    
    def save_signal(self):  
        SavedSignal = np.asarray([self.time,sum(self.added_signals_list)])
        np.savetxt('Synthetic Signal '+str(SignalsCounter)+'.csv', SavedSignal.T,header="t,x", delimiter=",") 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
