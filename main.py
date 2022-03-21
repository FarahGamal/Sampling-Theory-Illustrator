import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph
from pyqtgraph import PlotWidget
import pandas as pd
from GUI import Ui_MainWindow
import csv
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.special import sinc
import math
import scipy
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

SignalsCounter = -1
composedSignalIsPlotted= False
signalSumIsPlotted= False

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Variables Initialization
        self.time = np.linspace(-2,2,2000, endpoint=False)
        self.added_composer_signals=0
        self.added_signals_list=[]
        self.signal_index=None
        self.signal_to_delete=None
        self.isOpen = False
        self.noDots = False

        # Links of GUI Elements to Methods:
        self.ui.showHidePushButton.setCheckable(True)
        self.ui.actionOpen.triggered.connect(lambda: self.openFile())
        self.ui.showHidePushButton.clicked.connect(lambda: self.showHideGraph())
        self.ui.plotPushButton.clicked.connect(self.signal_composer)
        self.ui.addPushButton.clicked.connect(self.signal_summation)
        self.ui.deletePushButton.clicked.connect(self.signal_deletion)
        self.ui.deleteSignalComboBox.activated.connect(self.select_signal)
        self.ui.samplingHorizontalSlider.setMinimum(0)
        self.ui.samplingHorizontalSlider.setMaximum(9)
        self.ui.mainGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.reconstrucedGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.composerGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.summationGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.samplingHorizontalSlider.valueChanged.connect( self.ResampleAndReconstructSignalBasedOnSliderValue)
        self.timeReadings = []
        self.amplitudeReadings = []
        self.ui.savePushButton.clicked.connect(self.save_signal)
        self.ui.confirmPushButton.clicked.connect(self.confirm)


    # Methods

    def save_signal(self):
        global signalSumIsPlotted
        if signalSumIsPlotted==False:
            self.show_pop_up_msg("No Signal to Save! ")  
        else:    
            SavedSignal = np.asarray([self.time,sum(self.added_signals_list)])
            np.savetxt('Synthetic Signal '+str(SignalsCounter)+'.csv', SavedSignal.T,header="t,x", delimiter=",")
    
    def reset_slider_and_graph(self):
        self.ui.reconstrucedGraphicsView.clear()
        self.ui.samplingHorizontalSlider.setValue(0)

    def openFile(self):
        self.reset_slider_and_graph()
        self.file_name = QtWidgets.QFileDialog.getOpenFileName(caption="Choose Signal", directory="", filter="csv (*.csv)")[0]
        self.data_frame = pd.read_csv(self.file_name, encoding = 'utf-8').fillna(0)
        self.timeReadings = self.data_frame.iloc[:,0].to_numpy()
        self.amplitudeReadings = self.data_frame.iloc[:,1].to_numpy()
        self.plot()
        self.isOpen = True

    def confirm(self):
        if signalSumIsPlotted==False:
            self.show_pop_up_msg("No Signal to Sample! ")
        else:
            self.timeReadings = self.time
            self.amplitudeReadings = self.added_composer_signals
            self.plot()
            self.isOpen = True
            self.reset_slider_and_graph()
            self.ui.maximumFrequencyLabel.setText('0 fmax')


    def plot(self):
        self.setGraphRange(self.ui.mainGraphicsView, self.timeReadings, self.amplitudeReadings)
        self.ui.mainGraphicsView.clear()
        self.ui.mainGraphicsView.plot(self.timeReadings, self.amplitudeReadings, pen=pyqtgraph.mkPen('r', width=1.5))
    
    def InterpolateDataPoints(self,dataPointsToInterpolate, timestepToFindSampleValueAt):
    
        sampleValue = dataPointsToInterpolate[0][1] + ( timestepToFindSampleValueAt - dataPointsToInterpolate[0][0] ) * ( (dataPointsToInterpolate[1][1] - dataPointsToInterpolate[0][1] ) / ( dataPointsToInterpolate[1][0] - dataPointsToInterpolate[0][0] ) )
        return sampleValue[0]

    def GetMaximumFrequencyComponent(self,timeReadings, amplitudeReadings):
    
        magnitudes = np.abs(scipy.fft.rfft(amplitudeReadings))/np.max(np.abs(scipy.fft.rfft(amplitudeReadings)))
        frequencies = scipy.fft.rfftfreq(len(timeReadings), (timeReadings[1] - timeReadings[0]))
        for index, frequency in enumerate(frequencies):
            if magnitudes[index] >= 0.05:
                fmax = frequencies[index]
        return round(fmax)

    def ResampleSignal(self,timeReadings, amplitudeReadings, maximumFrequencyRatio):

        maximumFrequencyComponent = self.GetMaximumFrequencyComponent(timeReadings, amplitudeReadings)
        #* ts step of sampling
        samplingInterval = abs(1/(maximumFrequencyRatio * maximumFrequencyComponent))
        #
        signalTimeInterval = timeReadings[-1]
        #* list of sampling time
        samplingTime = np.arange(-signalTimeInterval, signalTimeInterval, samplingInterval)
        resampledAmplitude = []
        for currentTimestep in samplingTime:
            nearestSmallerTimestep = timeReadings[timeReadings < currentTimestep].max()
            nearestSmallerAmplitude = amplitudeReadings[np.where(timeReadings == nearestSmallerTimestep)]
            nearestLargerTimestep = timeReadings[timeReadings > currentTimestep].min() 
            nearestLargerAmplitude = amplitudeReadings[np.where(timeReadings == nearestLargerTimestep)]
            sampleValue = self.InterpolateDataPoints([[nearestSmallerTimestep, nearestSmallerAmplitude],[nearestLargerTimestep, nearestLargerAmplitude]], currentTimestep)
            resampledAmplitude.append(sampleValue)
        self.ui.mainGraphicsView.clear()
        self.ui.mainGraphicsView.plot(self.timeReadings, self.amplitudeReadings, pen=pyqtgraph.mkPen('r', width=1.5))
        self.ui.mainGraphicsView.plot(samplingTime, resampledAmplitude, pen=pyqtgraph.mkPen('g', width=1.5, style=QtCore.Qt.DashLine), symbol='o', symbolPen ='b', symbolBrush = 0.9)

        return resampledAmplitude, samplingInterval

    def ReconstructSignal(self,timeReadings, amplitudeReadings, maximumFrequencyRatio):

        resampledAmplitude, samplingInterval = self.ResampleSignal(timeReadings, amplitudeReadings, maximumFrequencyRatio)
        reconstructedAmplitude = [resampledAmplitude[discreteTimestep] * sinc( (timeReadings - discreteTimestep*samplingInterval) / samplingInterval ) for discreteTimestep in range(-len(resampledAmplitude), len(resampledAmplitude))]
        reconstructedAmplitude = np.sum(reconstructedAmplitude, axis=0)
        self.setGraphRange(self.ui.reconstrucedGraphicsView, self.timeReadings, reconstructedAmplitude)
        self.ui.reconstrucedGraphicsView.clear()
        self.ui.reconstrucedGraphicsView.plot(timeReadings, reconstructedAmplitude, pen=pyqtgraph.mkPen('b', width=1.5))

    def ResampleAndReconstructSignalBasedOnSliderValue(self,sliderValue):
        if self.isOpen == False: return
        if sliderValue == 0:
            self.ui.reconstrucedGraphicsView.clear()
            self.ui.maximumFrequencyLabel.setText('0 fmax')
            self.plot()
            return
        maximumFrequencyRatio = round(sliderValue/3, 3)
        self.ui.maximumFrequencyLabel.setText(f'{maximumFrequencyRatio} fmax')
        self.ReconstructSignal(self.timeReadings, self.amplitudeReadings, maximumFrequencyRatio)

    def showHideGraph(self):
        if self.ui.showHidePushButton.isChecked():
            self.ui.reconstrucedGraphicsView.hide()
            self.ui.reconstructedSignalGraphLabel.hide()
        else:
            self.ui.reconstrucedGraphicsView.show()
            self.ui.reconstructedSignalGraphLabel.show()

    def signal_composer(self):
        global SignalsCounter
        global composedSignalIsPlotted
        global SignalsCounter
        self.ui.composerGraphicsView.clear()
        self.frequency= float(self.ui.frequencyDoubleSpinBox.text())
        self.amplitude= float(self.ui.amplitudeDoubleSpinBox.text()) 
        self.phase_shift= float(self.ui.phaseShiftDoubleSpinBox.text()) * (np.pi/180)
        self.signal = self.amplitude * np.cos(2 * np.pi * self.frequency * self.time + self.phase_shift)
        self.setGraphRange(self.ui.composerGraphicsView, self.time, self.signal)
        self.ui.composerGraphicsView.plot(self.time, self.signal, pen=pyqtgraph.mkPen('r', width=1.5))
        SignalsCounter = SignalsCounter + 1
        composedSignalIsPlotted= True

    def signal_summation(self):
        global signalSumIsPlotted
        if composedSignalIsPlotted == True:
            self.added_composer_signals+=self.signal
            #* Frequency stored in a list for later sampling
            self.added_signals_list.append(self.signal)
            self.ui.deleteSignalComboBox.addItem('F='+ str(self.frequency)+ 'A=' +str(self.amplitude) + 'PS='+ str(self.phase_shift))
            self.ui.summationGraphicsView.clear() #* adjust it to the right graph
            self.setGraphRange(self.ui.summationGraphicsView, self.time, self.added_composer_signals)
            self.ui.summationGraphicsView.plot(self.time, self.added_composer_signals, pen=pyqtgraph.mkPen('r', width=1.5))
            signalSumIsPlotted= True
        elif composedSignalIsPlotted== False: 
            self.show_pop_up_msg("No Signal is Plotted! ")

    def select_signal(self):
        self.signal_index=self.ui.deleteSignalComboBox.currentIndex()

    def signal_deletion(self):
        global signalSumIsPlotted
        if signalSumIsPlotted==False:
            self.show_pop_up_msg("No Signal to Delete! ")
        else:
            self.ui.summationGraphicsView.clear()
            self.signal_to_delete=self.added_signals_list.pop(self.signal_index)
            self.ui.deleteSignalComboBox.removeItem(self.signal_index)
            if self.ui.deleteSignalComboBox.count()==0:
                self.added_composer_signals = 0
                self.ui.summationGraphicsView.clear()
                signalSumIsPlotted= False
            else:
                self.added_composer_signals-=self.signal_to_delete
                self.ui.summationGraphicsView.plot(self.time, self.added_composer_signals, pen=pyqtgraph.mkPen('r', width=1.5))
                

    def show_pop_up_msg(self,the_message):
        msg=QMessageBox()
        msg.setWindowTitle("ERROR!!")
        msg.setText(the_message)
        show= msg.exec_()

    def setGraphRange(self, graphicsViewName, time, amplitude):
        graphicsViewName.setLimits(xMin=np.min(time), xMax=np.max(time), yMin=np.min(amplitude) - 0.2, yMax=np.max(amplitude) + 0.2, minXRange=0.1, maxXRange=np.max(time) - np.min(time), minYRange=0.1, maxYRange=(np.max(amplitude) + 0.2)-((np.min(amplitude) - 0.2)))
        graphicsViewName.setRange(xRange=(-2, 2), yRange=(np.min(amplitude) - 0.2, np.max(amplitude) + 0.2), padding=0)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
