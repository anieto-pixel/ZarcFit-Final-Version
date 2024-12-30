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


##MM
#I can pass the label names and titles at construction, as variables, or I
#can use the init file, or I can leave it as they are


#MM
#Do I want to keep six separate atributes for the graphs, or do I want
#to pas themdoel and regular frec,zr,zi as to lists of three arrays each?

import numpy as np
import pyqtgraph as pg

import numpy as np
import pyqtgraph as pg

"""
Parent class for all the graphs.
Defines common methods and default values for all graph classes
"""
class ParentGraph(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        # Default initialization data
        self._freq = np.array([1, 10, 100, 1000, 10000])  
        self._Z_real = np.array([100, 80, 60, 40, 20]) 
        self._Z_imag = np.array([-50, -40, -30, -20, -10]) 
        
        self._mfreq = np.array([1, 10, 100, 1000, 10000])  
        self._mZ_real = np.array([90, 70, 50, 30, 10]) 
        self._mZ_imag = np.array([-45, -35, -25, -15, -5]) 

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)

        # Plot objects for static and dynamic lines
        self.static_plot = None
        self.dynamic_plot = None
        
        # Initial graph display
        self.refresh_graph(self._freq, self._Z_real, self._Z_imag, self._mfreq, self._mZ_real, self._mZ_imag)

    def prepare_xy(self, freq, Z_real, Z_imag):
        """
        Prepares the X and Y values for plotting from impedance data.
        Override this in subclasses if needed.
        """
        return Z_real, Z_imag

    def refresh_m_plot(self, freq, Z_real, Z_imag):
        """
        Updates the dynamic line (model data) on the graph without clearing it.
        """
        x, y = self.prepare_xy(freq, Z_real, Z_imag)
        if self.dynamic_plot:  # Ensure the plot object exists
            self.dynamic_plot.setData(x, y)

    def refresh_graph(self, freq, Z_real, Z_imag, mfreq, mZ_real, mZ_imag):
        """
        Clears and refreshes the entire graph, including both static and dynamic lines.
        """
        self.clear()  # Clear previous plot

        # Prepare and plot static data (base impedance)
        x, y = self.prepare_xy(freq, Z_real, Z_imag)
        self.static_plot = self.plot(x, y, pen=None, symbol='o', symbolSize=8, symbolBrush='g')  # Green dots

        # Prepare and plot dynamic data (model impedance)
        mx, my = self.prepare_xy(mfreq, mZ_real, mZ_imag)
        self.dynamic_plot = self.plot(mx, my, pen=None, symbol='x', symbolSize=8, symbolBrush='b')  # Blue x's

    def filter_frequency_range(self, f_min, f_max):
        """
        Filters the data to display only points within the specified frequency range.
        """
        # Filter static (base) data
        base_mask = (self._freq >= f_min) & (self._freq <= f_max)
        filtered_freq = self._freq[base_mask]
        filtered_Z_real = self._Z_real[base_mask]
        filtered_Z_imag = self._Z_imag[base_mask]

        # Filter dynamic (model) data
        model_mask = (self._mfreq >= f_min) & (self._mfreq <= f_max)
        filtered_mfreq = self._mfreq[model_mask]
        filtered_mZ_real = self._mZ_real[model_mask]
        filtered_mZ_imag = self._mZ_imag[model_mask]

        # Refresh the graph with the filtered data
        self.refresh_graph(filtered_freq, filtered_Z_real, filtered_Z_imag,
                           filtered_mfreq, filtered_mZ_real, filtered_mZ_imag)

    def setter_parameters_base(self, freq, Z_real, Z_imag):
        """
        Sets new static data (base impedance).
        """
        self._freq = freq
        self._Z_real = Z_real
        self._Z_imag = Z_imag

    def setter_manual_parameters(self, freq, Z_real, Z_imag):
        """
        Sets new dynamic data (model impedance).
        """
        self._mfreq = freq
        self._mZ_real = Z_real
        self._mZ_imag = Z_imag


"""
Phase graph class
"""
class PhaseGraph(ParentGraph):
    def __init__(self): 
        super().__init__()

        self.setTitle("Phase")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "Phase [degrees]")
        
        # Initial graph display
        # Initial graph display

    def prepare_xy(self,freq,Z_real,Z_imag):
        
        phase = np.arctan2(Z_imag, Z_real) * 180 / np.pi  # Phase of Z (in degrees)
        return freq, phase

"""
Bode graph class
"""
class BodeGraph(ParentGraph):
    def __init__(self):
        super().__init__()

        self.setTitle("Bode Graph")
        self.setLabel('bottom', "Freq [Hz]")
        self.setLabel('left', "Total Impedance [Ohms]")
        #self.setAspectLocked(True)  # Lock aspect ratio to 1:1

    def prepare_xy(self,freq,Z_real,Z_imag):
        
        magnitude = np.sqrt(Z_real**2 + Z_imag**2)
        return freq, 20 * np.log10(magnitude)

"""
Bode graph class
"""
class ColeColeGraph(ParentGraph):
    def __init__(self):
        super().__init__()
          
        self.setTitle("Cole-cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")
        #self.setAspectLocked(True)  # Lock aspect ratio to 1:1

    def prepare_xy(self, freq, Z_real, Z_imag):

        return Z_real, -Z_imag
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
       #graph_widget.apply_filter_frequency_range(10, 100)
       # Run the application
       sys.exit(app.exec_())