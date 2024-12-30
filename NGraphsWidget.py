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



"""
Handles the computation for the graph based on sliders.
"""
class GraphCalculator(QObject):

    # Declare the signal at the class level
    data_changed = pyqtSignal()
    
    def __init__(self, sliders_widget):
        super().__init__()  # Initialize QObject
        self.sliders_widget = sliders_widget

    def compute_graph_data(self):
        """
        Computes the x and y values for the graph.
        Returns: (x, y) tuple
        """
        suma = sum(slider.get_value() for slider in self.sliders_widget.list_of_sliders)
        x = np.linspace(-100, 100, 1000)
        a = 1  # Quadratic coefficient
        y = a * (x - suma) ** 2  # Quadratic function
        return x, y
    
    def update_graph(self):
        """
        Emits a signal when graph data changes.
        """
        self.data_changed.emit()

"""
Displays the graph based on computed data from GraphCalculator.
"""
class GraphWidget(pg.PlotWidget):
    
    def __init__(self, calculator):
        super().__init__()
        self.calculator = calculator
        self.setTitle("Quadratic Equation: y = ax^2 + bx + c")
        self.setLabel('left', 'y')
        self.setLabel('bottom', 'x')

        # Connect calculator's data_changed signal to refresh_graph
        self.calculator.data_changed.connect(self.refresh_graph)
        
        # Initial graph display
        self.refresh_graph()

    def refresh_graph(self):
        """
        Updates the graph display with the latest computed data.
        """
        x, y = self.calculator.compute_graph_data()
        self.clear()  # Clear previous plot
        self.plot(x, y)


"""
A Widget displaying three graphs
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
import pyqtgraph as pg

class GraphsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._initialize_ui()
        
        self._initialize_ui()
        
        
    def _left_hand_graphs(self):
        self.big_graph = pg.PlotWidget()

        # Create labels for the graphs
        self.big_graph_label = QLabel("Big Graph")
        
        big_graph_layout = QVBoxLayout()
        big_graph_layout.addWidget(self.big_graph_label)
        big_graph_layout.addWidget(self.big_graph)
        
        return big_graph_layout
        
    def _right_hand_graphs(self):
        
        # Initialize the graph widgets
        self.small_graph_1 = pg.PlotWidget()
        self.small_graph_2 = pg.PlotWidget()
        
        # Create labels for the graphs
        self.small_graph_1_label = QLabel("Small Graph 1")
        self.small_graph_2_label = QLabel("Small Graph 2")
        
        # Layout for the stacked small graphs on the right
        right_graphs_layout = QVBoxLayout()
        right_graphs_layout.addWidget(self.small_graph_1_label)
        right_graphs_layout.addWidget(self.small_graph_1)
        right_graphs_layout.addWidget(self.small_graph_2_label)
        right_graphs_layout.addWidget(self.small_graph_2)
        return right_graphs_layout
        

    def _initialize_ui(self):
        left_graphs_layout=self._left_hand_graphs()
        right_graphs_layout=self._right_hand_graphs()

        # Layout for all graphs
        graphs_layout = QHBoxLayout()
        

        graphs_layout.addLayout(left_graphs_layout)
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