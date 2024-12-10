import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 

import pyqtgraph as pg

import os
import numpy as np

#my own classes
from OutputFileWidget import OutputFileWidget
from InputFileWidget import InputFileWidget
from SliderWithTicks import SliderWithTicks
from NSlidersWidget import NSlidersWidget
from ButtonsWidgetRow import ButtonsWidgetRow


#########################################################################       
#############################################################################        
#Graphs Stuff
#############################################################################        
################################################################
class GraphCalculator(QObject):
    """
    Handles the computation for the graph based on sliders.
    """
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


class GraphWidget(pg.PlotWidget):
    """
    Displays the graph based on computed data from GraphCalculator.
    """
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
  
################################################################
#Sliders
################################
      

#######################################
#Files
######################################


###############################################
#Buttons Sidebar
####################################################


###################################
#Files
###################################

class MainWidget(QWidget):
    
    def create_widget_from_layout(self, layout):
        """
        Helper method to create a QWidget from a layout so that it can be added to the QSplitter.
        """
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    def create_sliders_layout(self):
        l_inf = NSlidersWidget(1, 0, 100, "black")
        r_inf = NSlidersWidget(1, 0, 100, "black")
        r_h = NSlidersWidget(3, 0, 100, "red")
        r_m = NSlidersWidget(3, 0, 100, "green")
        r_l = NSlidersWidget(3, 0, 100, "blue")
        r_extra = NSlidersWidget(4, 0, 100, "black")

        # Horizontal layout for sliders
        self.list_of_sliders = [ l_inf, r_inf,
                                r_h, r_m, r_l, r_extra]
        sliders_layout = QHBoxLayout()
        for s in self.list_of_sliders:
            sliders_layout.addWidget(s)
            
        return sliders_layout
    
    def create_top_bar_layout(self):
        
        layout = QHBoxLayout()
        layout.addWidget(self.input_file_widget)
        layout.addStretch()  #keeps both widgets separate in the layout
        layout.addWidget(self.output_file_widget)
        
        #widget = QWidget()
        #widget.setLayout(layout)
        
        return layout
    
    
    def __init__(self):
        super().__init__()

        ##################
        # Files bar
        ####################
        self.patatito = "pattito"  # Dummy Variable to write to file

        self.input_file_widget = InputFileWidget()
        self.output_file_widget = OutputFileWidget()
        top_bar_layout= self.create_top_bar_layout()

        ##################
        # Buttons Widget
        ####################
        self.buttons_widget = ButtonsWidgetRow()  # Create the buttons widget
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.buttons_widget)  # Add the buttons_widget to the layout

        ##################
        # Sliders
        ####################
        # Slider widgets
        #frequency = l_inf = NSlidersWidget(1, 0, 100, "orange")
        self.list_of_sliders=[]
        sliders_layout=self.create_sliders_layout()

        ##################
        # Graphs
        #################### 
        # Calculators
        self.calculator = GraphCalculator(self.list_of_sliders[5])
        for slider in self.list_of_sliders[5].list_of_sliders:
            slider.valueChanged().connect(self.calculator.update_graph)

        #graphs layouts
        self.big_graph = GraphWidget(self.calculator)
        self.small_graph_1 = GraphWidget(self.calculator)
        self.small_graph_2 = GraphWidget(self.calculator)
        
        # Layout for the two stacked graqphs to the left
        right_graphs_layout=QVBoxLayout()
        right_graphs_layout.addWidget(self.small_graph_1)
        right_graphs_layout.addWidget(self.small_graph_2)
        
        #layout for all graphs
        all_graphs_layout = QHBoxLayout()
        all_graphs_layout.addWidget(self.big_graph)
        all_graphs_layout.addLayout(right_graphs_layout)

        ###########################
        #bttom half layout
        ##########################

        ###bottom half of the screen
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addLayout(sliders_layout)
        bottom_half_layout.addLayout(buttons_layout)  # Add the button layout here

        ##################
        # Main Layout
        ####################
        main_layout = QVBoxLayout()
        # Create a QSplitter to make graph_layout and bottom_half_layout adjustable
        splitter = QSplitter(Qt.Vertical)

        # Add both layouts to the splitter
        splitter.addWidget(self.create_widget_from_layout(all_graphs_layout))
        splitter.addWidget(self.create_widget_from_layout(bottom_half_layout))

        # Set the initial size for each layout (optional)
        splitter.setSizes([500, 300])  # Change the values to whatever ratio you want
        
        # Add output file widget and the splitter to the main layout
        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)


    
# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWidget()
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    