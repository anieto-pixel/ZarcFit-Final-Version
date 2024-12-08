import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 

import pyqtgraph as pg

import os
import numpy as np

#my own classes
from SliderWithTicks import SliderWithTicks
from OutputFileWidget import OutputFileWidget

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

#NSlidersWidget####################################################################

"""
Class for pack of n vertical sliders
"""
class NSlidersWidget(QWidget):
    def __init__(self, n, min_value, max_value, colour):
        super().__init__()

        # Creates list of n wrapped sliders
        self.list_of_sliders = []
        for x in range(n):
            slider = SliderWithTicks(min_value, max_value, colour)
            self.list_of_sliders.append(slider)

        # Connect sliders to update total value
        self.value_label_total = QLabel(f"Total: {self.calculate_total()}")
        for slider in self.list_of_sliders:
            slider.valueChanged().connect(self.update_labels)

        # Layout
        main_layout = QHBoxLayout()

        # Add spacer item to push sliders apart if needed
        #main_layout.addSpacerItem(QSpacerItem(10, 0))  # Adjust as needed for horizontal spacing
        for s in self.list_of_sliders:
            main_layout.addWidget(s)
        main_layout.addSpacerItem(QSpacerItem(10, 0))  # Add space after sliders

        # Set margins to the layout
        main_layout.setContentsMargins(0, 10, 10, 0)  # Set top, left, right, and bottom margins
                                                        #(for horizontal distribution: left , top, right, bottom)

        self.setLayout(main_layout)

    def calculate_total(self):
        return sum(slider.get_value() for slider in self.list_of_sliders)

    def update_labels(self):
        total = self.calculate_total()
        self.value_label_total.setText(f"Total: {total}")
#######################################
#Files
######################################


###############################################
#Buttons Sidebar
####################################################

class ButtonsWidgetRow(QWidget):
    def __init__(self):
        super().__init__()
    
        #save buttons(eventually buttons, or sets of themed buttons, will have their class)
        self.f1_button = QPushButton("F1")
        self.f2_button = QPushButton("F2")
        self.f3_button = QPushButton("F3")
        self.save_button = QPushButton("Save plot")
        self.f5_button = QPushButton("F5")
        self.f6_button = QPushButton("F6")
        self.f7_button = QPushButton("F7")
        self.f8_button = QPushButton("F8")
        self.f9_button = QPushButton("F9")
        
        self.list_of_buttons=[self.f1_button, self.f2_button, self.f3_button,
                         self.save_button,self.f5_button,self.f6_button,
                         self.f7_button,self.f8_button,self.f9_button,
                         ]
        buttons_column_layout= QVBoxLayout()
        for b in self.list_of_buttons:
            buttons_column_layout.addWidget(b)
            
        #buttons_column_layout.setSpacing(5) 

        # Set the layout of the widget
        self.setLayout(buttons_column_layout)
        self.setMaximumWidth(100)
  



class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        ##################
        # Files
        ####################
        self.patatito = "pattito"  # Variable to write to file

        self.output_file_widget = OutputFileWidget()

        ##################
        # Button Widget
        ####################
        self.buttons_widget = ButtonsWidgetRow()  # Create the buttons widget
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.buttons_widget)  # Add the buttons_widget to the layout

        ##################
        # Sliders
        ####################
        # Slider widgets
        sliders_layout = QHBoxLayout()
        
        frequency = NSlidersWidget(1, 0, 100, "orange")
        l_inf = NSlidersWidget(1, 0, 100, "black")
        r_inf = NSlidersWidget(1, 0, 100, "black")
        r_h = NSlidersWidget(3, 0, 100, "red")
        r_m = NSlidersWidget(3, 0, 100, "green")
        r_l = NSlidersWidget(3, 0, 100, "blue")
        r_extra = NSlidersWidget(4, 0, 100, "black")

        # Horizontal layout for sliders
        self.list_of_sliders = [frequency, l_inf, r_inf,
                                r_h, r_m, r_l, r_extra]
        sliders_layout = QHBoxLayout()
        for s in self.list_of_sliders:
            sliders_layout.addWidget(s)
            
        #sliders_layout.setSpacing(2) 

        ##################
        # Graphs
        #################### 
        # Calculators
        self.calculator = GraphCalculator(r_extra)
        for slider in r_extra.list_of_sliders:
            slider.valueChanged().connect(self.calculator.update_graph)

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

        ###bottom half of the screen
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addLayout(sliders_layout)
        bottom_half_layout.addLayout(buttons_layout)
        bottom_half_layout.setContentsMargins(10, 0, 0, 10)
        
#        bottom_half_layout.addLayout(sliders_layout, 24)
#        bottom_half_layout.addLayout(buttons_layout, 1)


        ##################
        # Main Layout
        ####################
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.output_file_widget)
        main_layout.addLayout(all_graphs_layout)
        main_layout.addLayout(bottom_half_layout)

        self.setLayout(main_layout)

    
# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWidget()
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    
