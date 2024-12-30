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
        self.base_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([100, 80, 60, 40, 20]),
            'Z_imag': np.array([-50, -40, -30, -20, -10]),
        }

        self.manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)

        # Plot objects for static and dynamic lines
        self.static_plot = None
        self.dynamic_plot = None

        # Initial graph display
        self.refresh_graph()

    """
    Prepares the X and Y values for plotting from impedance data.
    Overriden in subclasses.
    """
    def prepare_xy(self, freq, Z_real, Z_imag):
        return Z_real, Z_imag

    """
    Refreshes a specific plot with the given data.
    Arguments:
    - data: A dictionary containing 'freq', 'Z_real', and 'Z_imag'.
    - plot: The specific plot object to update (static or dynamic).
    """
    def refresh_plot(self, data, plot):

        x, y = self.prepare_xy(data['freq'], data['Z_real'], data['Z_imag'])
        if plot:
            plot.setData(x, y)

    """
    Refreshes the entire graph by replotting both the static and dynamic data.
    """
    def refresh_graph(self):
        self.clear()  # Clear the plot area

        # Plot static (base) data
        self.static_plot = self.plot(pen=None, symbol='o', symbolSize=8, symbolBrush='g')  # Green dots
        self.refresh_plot(self.base_data, self.static_plot)

        # Plot dynamic (model) data
        self.dynamic_plot = self.plot(pen=None, symbol='x', symbolSize=8, symbolBrush='b')  # Blue x's
        self.refresh_plot(self.manual_data, self.dynamic_plot)

    """
    Filters the data to display only points within the specified frequency range.
    """
    def filter_frequency_range(self, f_min, f_max):
        # Filter static (base) data
        base_mask = (self.base_data['freq'] >= f_min) & (self.base_data['freq'] <= f_max)
        filtered_base = {
            'freq': self.base_data['freq'][base_mask],
            'Z_real': self.base_data['Z_real'][base_mask],
            'Z_imag': self.base_data['Z_imag'][base_mask],
        }

        # Filter dynamic (model) data
        model_mask = (self.manual_data['freq'] >= f_min) & (self.model_data['freq'] <= f_max)
        filtered_model = {
            'freq': self.manual_data['freq'][model_mask],
            'Z_real': self.manual_data['Z_real'][model_mask],
            'Z_imag': self.manual_data['Z_imag'][model_mask],
        }

        # Update data and refresh graph
        self.base_data = filtered_base
        self.manual_data = filtered_model
        self.refresh_graph()

    """
    Sets new static data (base impedance) and refreshes the entire graph.
    """
    def setter_parameters_base(self, freq, Z_real, Z_imag):
        self.base_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self.refresh_graph()  # Reset the entire graph

    """
    Sets new dynamic data (model impedance) and refreshes only the dynamic plot.
    """
    def setter_parameters_model(self, freq, Z_real, Z_imag):

        self.manual_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self.refresh_plot(self.model_data, self.dynamic_plot)  # Refresh only the dynamic plot


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