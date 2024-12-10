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
    
    def create_graphs_widget(self):
        self.big_graph = GraphWidget(self.calculator)
        self.small_graph_1 = GraphWidget(self.calculator)
        self.small_graph_2 = GraphWidget(self.calculator)
        
        # Layout for the two stacked graqphs to the left
        right_graphs_layout=QVBoxLayout()
        right_graphs_layout.addWidget(self.small_graph_1)
        right_graphs_layout.addWidget(self.small_graph_2)
        
        #layout for all graphs
        graphs_layout = QHBoxLayout()
        graphs_layout.addWidget(self.big_graph)
        graphs_layout.addLayout(right_graphs_layout)
        
        return self.create_widget_from_layout(graphs_layout)
    
    def create_sliders_widget(self):
        default_slider_range = (0, 100)
        
        slider_specs = [
            (1, "black"), (1, "black"), (3, "red"),
            (3, "green"), (3, "blue"), (4, "black")
        ]
        self.list_of_sliders = [
            NSlidersWidget(num, *default_slider_range, color)
            for num, color in slider_specs
        ]
    
        layout = QHBoxLayout()
        for slider in self.list_of_sliders:
            layout.addWidget(slider)
            
        return self.create_widget_from_layout(layout)
    
    def create_files_options_widget(self):
        
        layout = QHBoxLayout()
        layout.addWidget(self.input_file_widget)
        layout.addStretch()  #keeps both widgets separate in the layout
        layout.addWidget(self.output_file_widget)
        
        return self.create_widget_from_layout(layout)
    
    
    def __init__(self):
        
        super().__init__()
        self.input_content="patatito"

        #Would initializing help me with my issues?

        #self.patatito = "pattito"  # Dummy Variable to write to file
        self.calculator=None
        self.list_of_sliders=[]

        #top bar deals with input and output files
        self.input_file_widget = InputFileWidget()
        self.output_file_widget = OutputFileWidget()
        
        self.input_file_widget.file_selected.connect(self.update_patatito)
        
        self.top_bar_widget= self.create_files_options_widget()

        # Buttons Widget
        self.buttons_widget = ButtonsWidgetRow()  

        # Slider widgets
        #frequency = l_inf = NSlidersWidget(1, 0, 100, "orange")
        self.sliders_widget=self.create_sliders_widget()

        # Calculators
        self.calculator = GraphCalculator(self.list_of_sliders[5])
        for slider in self.list_of_sliders[5].list_of_sliders:
            slider.valueChanged().connect(self.calculator.update_graph)

        # Graphs
        graphs_widget=self.create_graphs_widget()

        ###########################
        #bttom half layout
        ##########################
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.sliders_widget)
        bottom_half_layout.addWidget(self.buttons_widget)  # Add the button layout here

        ##################
        # Main Layout
        ####################
        main_layout = QVBoxLayout()
        # Create a QSplitter to make graph_layout and bottom_half_layout adjustable
        splitter = QSplitter(Qt.Vertical)

        # Add both layouts to the splitter
        splitter.addWidget(graphs_widget)
        splitter.addWidget(self.create_widget_from_layout(bottom_half_layout))

        # Set the initial size for each layout (optional)
        splitter.setSizes([500, 300])  # Change the values to whatever ratio you want
        
        # Add output file widget and the splitter to the main layout
        main_layout.addWidget(self.top_bar_widget)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        
    def update_patatito(self, file_path):
        try:
            with open(file_path, 'r') as file:
                contents = file.read()
            self.patatito = contents  # Update patatito with the file contents
            print(f"File contents loaded into patatito:\n{self.patatito}")  # Optional: to check the result
        except Exception as e:
            print(f"Error reading file: {e}")
            self.patatito = "Error loading file."  # Fallback text


    
# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWidget()
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    