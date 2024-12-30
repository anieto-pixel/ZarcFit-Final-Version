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


class ParentGraph(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        #MM
        #figure out a better set of initialization values
        freq = np.array([1, 10, 100, 1000, 10000])  
        Z_real = np.array([100, 80, 60, 40, 20]) 
        Z_imag = np.array([-50, -40, -30, -20, -10]) 

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)
        
        # Initial graph display
        self.refresh_graph(freq,Z_real,Z_imag)

    def refresh_graph(self,freq,x ,y):
        #MM
        #should I jsut write pass in here?
        self.clear()  # Clear previous plot
        self.plot(x, y)





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
        self.plot(Z_real, Z_imag)  # Plot the points

    

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
        
        
if __name__ == "__main__":

       # Create a QApplication instance
       app = QApplication(sys.argv)

       # Create and show an instance of SliderWithTicks
       graph_widget = GraphsWidget()
       graph_widget.resize(200, 300)
       graph_widget.show()
       # Run the application
       sys.exit(app.exec_())