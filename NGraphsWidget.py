# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 08:27:11 2024

@author: agarcian
"""

#I am going to start with a widget that does everything, maybe including the calculators
#then I am going to re arrange the calculators of each type of graph n their class with their matching graph
#if that is pertinent
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 

import pyqtgraph as pg
import numpy as np


#MM
#Refreshing completely ensures the plot's integrity, if filtering conditions change dynamically.
#Dropping points directly could be more efficient but complicates the logic when multiple filters are applied.
#since efficiency does not seem to be an issue, I am opting for refreshing fully
#If it were to become an issue, or if filtering becomes a feature, this poitn shall be reviewed



##MM
#I can pass the label names and titles at construction, as variables, or I
#can use the init file, or I can leave it as they are

class ParentGraph(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        #MM
        #figure out a better set of initialization values
        self._freq = np.array([1, 10, 100, 1000, 10000])  
        self._Z_real = np.array([100, 80, 60, 40, 20]) 
        self._Z_imag = np.array([-50, -40, -30, -20, -10]) 

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)
        
        # Initial graph display
        self.refresh_graph(self._freq, self._Z_real, self._Z_imag)

    def refresh_graph(self,freq,Z_real ,Z_imag):
        pass
        
    ##MM if I do not reset the frequency slider for any new file, I need to
    #ensure that this method is called at initialization
    def filter_frequency_range(self, f_min, f_max):
        """
        Filters the data to display only points within the specified frequency range.
        """
        mask = (self._freq >= f_min) & (self._freq <= f_max)
        filtered_freq = self._freq[mask]
        filtered_Z_real = self._Z_real[mask]
        filtered_Z_imag = self._Z_imag[mask]
        
        self.refresh_graph(filtered_freq, filtered_Z_real, filtered_Z_imag)

    def setter_parameters(self,freq,Z_real ,Z_imag):
        
        #MM
        #I dont think i will need to refresha fter this, but keep an eye just in case

        self._freq=freq
        self._Z_real=Z_real
        self._Z_imag= Z_imag
     



class PhaseGraph(ParentGraph):
    def __init__(self): 
        super().__init__()

        self.setTitle("Phase")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "Phase [degrees]")
        
        # Initial graph display
        # Initial graph display

    def refresh_graph(self,freq,Z_real,Z_imag):
        
        phase = np.arctan2(Z_imag, Z_real) * 180 / np.pi  # Phase of Z (in degrees)
        self.clear()  # Clear previous plot
        self.plot(freq, phase)
        #self.plot(freq, phase,pen=None, symbol='o', symbolSize=10, symbolBrush='r')


class BodeGraph(ParentGraph):
    def __init__(self):
        super().__init__()

        self.setTitle("Bode Graph")
        self.setLabel('bottom', "Freq [Hz]")
        self.setLabel('left', "Total Impedance [Ohms]")
        #self.setAspectLocked(True)  # Lock aspect ratio to 1:1

    def refresh_graph(self,freq,Z_real,Z_imag):
        
        magnitude = np.sqrt(Z_real**2 + Z_imag**2)

        self.clear()  # Clear previous plot
        self.plot(freq, 20 * np.log10(magnitude))  # Plot magnitude in dB
        #self.plot(freq, 20 * np.log10(magnitude), pen=None, symbol='o', symbolSize=10, symbolBrush='r')

class ColeColeGraph(ParentGraph):
    def __init__(self):
        super().__init__()
          
        self.setTitle("Cole-cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")
        #self.setAspectLocked(True)  # Lock aspect ratio to 1:1

    def refresh_graph(self, frec, Z_real, Z_imag):
        """
        Updates the graph display with the latest computed data.
        """
        self.clear()  # Clear previous plot
        #self.plot(Z_real, Z_imag)  # Plot the points
        self.plot(Z_real, Z_imag, pen=None, symbol='o', symbolSize=10, symbolBrush='r')  # Plot the points


    

#MM
#this widget will ened to be refactored but 
#right now I don't want to over engineer things
#I will make it mor eflexible later on too?
"""
A Widget displaying three graphs
"""
class GraphsWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the graph widgets
        self.big_graph = ColeColeGraph()
        self.small_graph_1 = BodeGraph()
        self.small_graph_2 = PhaseGraph()

        # Layout for the stacked small graphs on the right
        right_graphs_layout = QVBoxLayout()
        right_graphs_layout.addWidget(self.small_graph_1)
        right_graphs_layout.addWidget(self.small_graph_2)

        # Layout for all graphs
        graphs_layout = QHBoxLayout()
        big_graph_layout = QVBoxLayout()
        big_graph_layout.addWidget(self.big_graph)

        graphs_layout.addLayout(big_graph_layout)
        graphs_layout.addLayout(right_graphs_layout)

        # Set the main layout
        self.setLayout(graphs_layout)
        
    def apply_filter_frequency_range(self, f_min, f_max):
        
        self.big_graph.filter_frequency_range(f_min, f_max)
        self.small_graph_1.filter_frequency_range( f_min, f_max)
        self.small_graph_2.filter_frequency_range( f_min, f_max)
        
        
        
if __name__ == "__main__":

       # Create a QApplication instance
       app = QApplication(sys.argv)

       # Create and show an instance of SliderWithTicks
       graph_widget = GraphsWidget()
       graph_widget.resize(200, 300)
       graph_widget.show()
       graph_widget.apply_filter_frequency_range(10, 100)
       # Run the application
       sys.exit(app.exec_())