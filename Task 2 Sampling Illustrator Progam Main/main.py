########## Imports ##########

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scipy.fft
import operator
import pyqtgraph
import numpy as np
import pandas as pd
from GUI import Ui_MainWindow
from scipy.special import sinc
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox


########## Global Variables Initialization ##########

composedSignalsCounter = -1
isComposerPlotNotEmpty, isSummedSinusoidalsPlotNotEmpty = False, False

# --------------------------------------------------------------------------------------------------------------------------------------------------- #

                                                        ########## Class Definition ##########

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        ########## Class Attributes Initialization ##########

        self.isMainPlotNotEmpty = False
        self.summedComposerSinusoidals, self.summedSinusoidalsList = 0, []
        self.composedSinusoidalIndex, self.sinusoidalToDelete = None, None
        self.readSignalTimeReadings, self.readSignalAmplitudeReadings = [], []
        self.minimumVisibleX, self.maximumVisibleX, self.viewRangePadding, self.pointsNumberInSignal = -2, 2, 0.2, 1000
        self.applicationTimeAxis = np.linspace(self.minimumVisibleX, self.maximumVisibleX, self.pointsNumberInSignal, endpoint=False)

        ########## Links of GUI Elements to Methods ##########

        self.ui.showHidePushButton.setCheckable(True)
        self.ui.samplingHorizontalSlider.setMinimum(0)
        self.ui.samplingHorizontalSlider.setMaximum(9)
        self.ui.plotPushButton.clicked.connect(self.SignalComposer)
        self.ui.mainGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.actionOpen.triggered.connect(lambda: self.OpenFile())
        self.ui.addPushButton.clicked.connect(self.SinuoidalsSummation)
        self.ui.deletePushButton.clicked.connect(self.DeleteSinusoidal)
        self.ui.savePushButton.clicked.connect(self.SaveSyntheticSignal)
        self.ui.composerGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.summationGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.reconstrucedGraphicsView.showGrid(x=True, y=True, alpha=0.5)
        self.ui.confirmPushButton.clicked.connect(self.ComposerConfirmButtonAction)
        self.ui.deleteSignalComboBox.activated.connect(self.SelectSinusoidalToDelete)
        self.ui.showHidePushButton.clicked.connect(lambda: self.ShowHideGraphButtonAction())
        self.ui.samplingHorizontalSlider.valueChanged.connect( self.ResampleAndReconstructSignalBasedOnSliderValue)

    # ---------------------------------------------------------------------------------------------------------------------------------------------- #

                                                        ########## Class Methods ##########

                                                ###### Sampling & Reconstruction Partition: ######

    #### Main Methods ####

    # Loading any Signal File into Application on Main Graph
    def OpenFile(self):
        self.ResetSliderAndMainGraph()
        self.fileName = QtWidgets.QFileDialog.getOpenFileName(caption="Choose Signal", directory="", filter="csv (*.csv)")[0]
        if  self.fileName:
            self.loadedDataFrame = pd.read_csv(self.fileName, encoding = 'utf-8').fillna(0)
            self.ReadAndPlotMainSignal(self.loadedDataFrame.iloc[:,0].to_numpy(), self.loadedDataFrame.iloc[:,1].to_numpy())

    # Getting Slider Value (Sampling Ratio) from User Interaction for Sampling and Reconstruction
    def ResampleAndReconstructSignalBasedOnSliderValue(self,sliderValue):
        if self.isMainPlotNotEmpty == False: return
        if sliderValue == 0:
            self.ui.reconstrucedGraphicsView.clear()
            self.ui.maximumFrequencyLabel.setText('0 Fmax')
            self.PlotAnySignal(self.ui.mainGraphicsView, self.readSignalTimeReadings, self.readSignalAmplitudeReadings, 'r', 1.5, None, None, None, None, False)
            return
        maximumFrequencyRatio = round(sliderValue/3, 3)
        self.ui.maximumFrequencyLabel.setText(f'{maximumFrequencyRatio} Fmax')
        self.ReconstructSignal(self.readSignalTimeReadings, self.readSignalAmplitudeReadings, maximumFrequencyRatio)

    #### Helper Methods ####

    # Transforming Signal to Frequency Domain to Capture Value of Maximum Frequency
    def GetMaximumFrequencyComponent(self, timeReadings, amplitudeReadings):
        magnitudes = np.abs(scipy.fft.rfft(amplitudeReadings))/np.max(np.abs(scipy.fft.rfft(amplitudeReadings)))
        frequencies = scipy.fft.rfftfreq(len(timeReadings), (timeReadings[1] - timeReadings[0]))
        for index, frequency in enumerate(frequencies):
            if magnitudes[index] >= 0.05: maximumFrequency = frequency
        return round(maximumFrequency)

    # Getting Smaller/Larger-Valued Samples with Respect to Targetted Sample to be Generated
    def GetNearestTimestepAndAmplitude(self, timeReadings, amplitudeReadings, currentTimestep, operator, getExtremeMethod):
        NearestTimestep = getattr(timeReadings[operator(timeReadings, currentTimestep)], getExtremeMethod)()
        return NearestTimestep, amplitudeReadings[np.where(timeReadings == NearestTimestep)]

    # Mathematical Linear Interpolation
    def InterpolateDataPoints(self, dataPointsToInterpolate, timestepToFindSampleValueAt):
        sampleValue = dataPointsToInterpolate[0][1] + ( timestepToFindSampleValueAt - dataPointsToInterpolate[0][0] ) * ( (dataPointsToInterpolate[1][1] - dataPointsToInterpolate[0][1] ) / ( dataPointsToInterpolate[1][0] - dataPointsToInterpolate[0][0] ) )
        return sampleValue[0]

    # Using Mathematical Linear Interpolation to Generate Samples According to Chosen Sampling Frequency
    def ResampleSignal(self, timeReadings, amplitudeReadings, maximumFrequencyRatio):
        maximumFrequencyComponent = self.GetMaximumFrequencyComponent(timeReadings, amplitudeReadings)
        samplingInterval = abs(1/(maximumFrequencyRatio * maximumFrequencyComponent))
        signalTimeInterval, resampledAmplitude = timeReadings[-1], []
        samplingTime = np.arange(-signalTimeInterval, signalTimeInterval, samplingInterval)
        for currentTimestep in samplingTime:
            nearestSmallerTimestep, nearestSmallerAmplitude = self.GetNearestTimestepAndAmplitude(timeReadings, amplitudeReadings, currentTimestep, operator.lt, "max")
            nearestLargerTimestep, nearestLargerAmplitude = self.GetNearestTimestepAndAmplitude(timeReadings, amplitudeReadings, currentTimestep, operator.gt, "min")
            sampleValue = self.InterpolateDataPoints([[nearestSmallerTimestep, nearestSmallerAmplitude],[nearestLargerTimestep, nearestLargerAmplitude]], currentTimestep)
            resampledAmplitude.append(sampleValue)
        self.PlotAnySignal(self.ui.mainGraphicsView, timeReadings, amplitudeReadings, 'r', 1.5, None, None, None, None, False)
        self.PlotAnySignal(self.ui.mainGraphicsView, samplingTime, resampledAmplitude, 'g', 0.001, None, 'o', 'g', 0.9, True)
        return resampledAmplitude, samplingInterval

    # Applying Sinc Interpolation Reconstruction to Samples and Plotting it in Secondary Graph
    def ReconstructSignal(self, timeReadings, amplitudeReadings, maximumFrequencyRatio):
        resampledAmplitude, samplingInterval = self.ResampleSignal(timeReadings, amplitudeReadings, maximumFrequencyRatio)
        reconstructedAmplitude = [resampledAmplitude[discreteTimestep] * sinc( (timeReadings - discreteTimestep*samplingInterval) / samplingInterval ) for discreteTimestep in range(-len(resampledAmplitude), len(resampledAmplitude))]
        reconstructedAmplitude = np.sum(reconstructedAmplitude, axis=0)
        self.PlotAnySignal(self.ui.reconstrucedGraphicsView, timeReadings, reconstructedAmplitude, 'b', 1.5, None, None, None, None, False)
        self.PlotAnySignal(self.ui.mainGraphicsView, timeReadings, reconstructedAmplitude, 'g', 1.5, QtCore.Qt.DotLine, None, None, None, True)

    # Executing Show or Hide Method on Secondary Graph Related UI Elements
    def ReconstructedSignalGraphShowHideControl(self, displayMethod):
        getattr(self.ui.reconstrucedGraphicsView, displayMethod)()
        getattr(self.ui.reconstructedSignalGraphLabel, displayMethod)()

    # Showing or Hiding Secondary Graph According to User Input
    def ShowHideGraphButtonAction(self):
        if self.ui.showHidePushButton.isChecked(): self.ReconstructedSignalGraphShowHideControl("hide")
        else: self.ReconstructedSignalGraphShowHideControl("show")

    # --------------------------------------------------------------------------------------------------------------------------------------------- #

                                                            ###### Sinusoidals Composer Partition: ######

    #### Main Methods ####

    # Constructing User-Defined Sinusoidal and Plotting it
    def SignalComposer(self):
        global composedSignalsCounter; global isComposerPlotNotEmpty
        self.frequency, self.amplitude, self.phaseShift = self.GetComposedSignalParameterFromUser(self.ui.frequencyDoubleSpinBox, 1), self.GetComposedSignalParameterFromUser(self.ui.amplitudeDoubleSpinBox, 1), self.GetComposedSignalParameterFromUser(self.ui.phaseShiftDoubleSpinBox, (np.pi/180))
        self.composedSinusoidal = self.amplitude * np.cos(2 * np.pi * self.frequency * self.applicationTimeAxis + self.phaseShift)
        self.PlotAnySignal(self.ui.composerGraphicsView, self.applicationTimeAxis, self.composedSinusoidal, 'r', 1.5, None, None, None, None, False)
        composedSignalsCounter += 1
        isComposerPlotNotEmpty = True

    # Summing Composed Sinusoidal to others Being Plotted
    def SinuoidalsSummation(self):
        global isSummedSinusoidalsPlotNotEmpty
        if isComposerPlotNotEmpty == True:
            self.summedComposerSinusoidals += self.composedSinusoidal
            self.summedSinusoidalsList.append(self.composedSinusoidal)
            self.ui.deleteSignalComboBox.addItem(str(self.amplitude) + ' * cos ( ' + str(self.frequency) + 't + ' + str(self.phaseShift) + ' )')
            self.PlotAnySignal(self.ui.summationGraphicsView, self.applicationTimeAxis, self.summedComposerSinusoidals, 'r', 1.5, None, None, None, None, False)
            isSummedSinusoidalsPlotNotEmpty= True
        elif isComposerPlotNotEmpty == False: self.ShowPopUpMessage("No Signal is Plotted!      ")

    # Getting Selected Sinusoidal from User to be Deleted
    def SelectSinusoidalToDelete(self):
        self.composedSinusoidalIndex = self.ui.deleteSignalComboBox.currentIndex()

    # Deleting a User Selected Sinusoidal Component After Summtion
    def DeleteSinusoidal(self):
        global isSummedSinusoidalsPlotNotEmpty
        if isSummedSinusoidalsPlotNotEmpty == False:self.ShowPopUpMessage("No Signal to Delete!      ")
        else:
            self.sinusoidalToDelete=self.summedSinusoidalsList.pop(self.composedSinusoidalIndex)
            self.ui.deleteSignalComboBox.removeItem(self.composedSinusoidalIndex)
            if self.ui.deleteSignalComboBox.count() == 0:
                self.summedComposerSinusoidals = 0
                self.ui.summationGraphicsView.clear()
                isSummedSinusoidalsPlotNotEmpty = False
            else:
                self.summedComposerSinusoidals -= self.sinusoidalToDelete
                self.PlotAnySignal(self.ui.summationGraphicsView, self.applicationTimeAxis, self.summedComposerSinusoidals, 'r', 1.5, None, None, None, None, False)

    # Moving Composed Sinusoidals to Sampling and Reconstruction Part of Application
    def ComposerConfirmButtonAction(self):
        if isSummedSinusoidalsPlotNotEmpty == False: self.ShowPopUpMessage("No Signal to Sample!      ")
        else:
            self.ReadAndPlotMainSignal(self.applicationTimeAxis, self.summedComposerSinusoidals)
            self.ResetSliderAndMainGraph()
            self.ui.maximumFrequencyLabel.setText('0 Fmax')

    # Saving Composed Sinusoidals in Same Directory
    def SaveSyntheticSignal(self):
        global isSummedSinusoidalsPlotNotEmpty
        if isSummedSinusoidalsPlotNotEmpty == False: self.ShowPopUpMessage("No Signal to Save!      ")  
        else:
            SavedSignal = np.asarray([self.applicationTimeAxis, sum(self.summedSinusoidalsList)])
            np.savetxt('Synthetic Signal '+str(composedSignalsCounter)+'.csv', SavedSignal.T, header="t,x", delimiter=",")

    #### Helper Methods ####

    # Getting Sinusoidal Component Parameters from User and Assigning them
    def GetComposedSignalParameterFromUser(self, signalParameterSpinBox, parameterScaleValue):
        return float( getattr(signalParameterSpinBox, "text")() ) * parameterScaleValue
    
    # Showing an Error Message for Handling Invalid User Actions
    def ShowPopUpMessage(self, popUpMessage):
        messageBoxElement = QMessageBox()
        messageBoxElement.setWindowTitle("ERROR!")
        messageBoxElement.setText(popUpMessage)
        execute = messageBoxElement.exec_()

    # -------------------------------------------------------------------------------------------------------------------------------------------- #

                                                                        ###### General Helper Functions: ######

    # Setting Limits and Visible Range of any Graph in Application
    def setGraphRange(self, plotWidget, timeReadings, amplitudeReadings):
        plotWidget.setLimits(xMin=np.min(timeReadings), xMax=np.max(timeReadings), yMin=np.min(amplitudeReadings) - self.viewRangePadding, yMax=np.max(amplitudeReadings) + self.viewRangePadding, minXRange = self.viewRangePadding * 0.5, maxXRange=np.max(timeReadings) - np.min(timeReadings), minYRange = self.viewRangePadding * 0.5, maxYRange=(np.max(amplitudeReadings) + self.viewRangePadding)-((np.min(amplitudeReadings) - self.viewRangePadding)))
        plotWidget.setRange(xRange=(self.minimumVisibleX, self.maximumVisibleX), yRange=(np.min(amplitudeReadings) - self.viewRangePadding, np.max(amplitudeReadings) + self.viewRangePadding), padding=0)

    # Plotting any Signal or Sinusoidal in Applicatiom
    def PlotAnySignal(self, plotWidget, timeReadings, amplitudeReadings, penColor, penWidth, penStyle, symbol, symbolPen, symbolBrush, secondPlot):
        if not secondPlot: self.setGraphRange(plotWidget, timeReadings, amplitudeReadings); plotWidget.clear()
        plotWidget.plot(timeReadings, amplitudeReadings, pen=pyqtgraph.mkPen(penColor, width=penWidth, style=penStyle), symbol=symbol, symbolPen=symbolPen, symbolBrush=symbolBrush)

    # Assigning Time and Amplitude Readings to their Class Attributes to be Plotted on Main Graph
    def ReadAndPlotMainSignal(self, timeReadings, amplitudeReadings):
        self.readSignalTimeReadings = timeReadings
        self.readSignalAmplitudeReadings = amplitudeReadings
        self.PlotAnySignal(self.ui.mainGraphicsView, self.readSignalTimeReadings, self.readSignalAmplitudeReadings, 'r', 1.5, None, None, None, None, False)
        self.isMainPlotNotEmpty = True

    # Resetting Slider and Clearing Main Graph
    def ResetSliderAndMainGraph(self):
        self.ui.reconstrucedGraphicsView.clear()
        self.ui.samplingHorizontalSlider.setValue(0)

    # --------------------------------------------------------------------------------------------------------------------------------------------- #

########## Application Main ##########

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
