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
from NGraphsWidget import *



class MainWidget(QWidget):
    
    def create_widget_from_layout(self, layout):
        """
        Helper method to create a QWidget from a layout so that it can be added to the QSplitter.
        """
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    
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
        
        self.input_file_widget.file_contents_updated.connect(self.update_filecontent)
        
        self.top_bar_widget= self.create_files_options_widget()

        # Buttons Widget
        self.buttons_widget = ButtonsWidgetRow()  

        # Slider widgets
        #frequency = l_inf = NSlidersWidget(1, 0, 100, "orange")
        self.sliders_widget=self.create_sliders_widget()

        # Calculators
        self.calculator = GraphCalculator(self.list_of_sliders[5])
        for slider in self.list_of_sliders[5].list_of_sliders:
            slider.value_changed().connect(self.calculator.update_graph)

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
        
    def update_filecontent(self, file_path):
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
    