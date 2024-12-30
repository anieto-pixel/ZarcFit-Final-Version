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
from NGraphsWidget import GraphsWidget


"""
Main application widget that handles the interactions between 
file management, sliders, buttons, and graphs into a unified layout.
"""
class MainWidget(QWidget):

    def __init__(self):
        super().__init__()

        # Initialize attributes
        self.file_content = ""
        self.calculator = None
        self.list_of_sliders = []

        # Initialize UI components
        self.input_file_widget = InputFileWidget()
        self.output_file_widget = OutputFileWidget()
        self.sliders_widget = None
        self.buttons_widget = ButtonsWidgetRow()
        self.graphs_widget = GraphsWidget()

        # Setup the UI
        self._initialize_ui()

    def _initialize_ui(self):
        """
        Organizes the layout and settings for the MainWidget.
        """
        # Connect input file widget to update the file content
        self.input_file_widget.file_contents_updated.connect(self.update_file_content)

        # Create the top bar widget
        self.top_bar_widget = self._create_file_options_widget()

        # Create sliders widget
        self.sliders_widget = self._create_sliders_widget()

        # Create the bottom half layout (sliders and buttons)
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.sliders_widget)
        bottom_half_layout.addWidget(self.buttons_widget)

        # Wrap bottom_half_layout in a QWidget
        bottom_half_widget = self._create_widget_from_layout(bottom_half_layout)

        # Create a splitter for graphs and bottom half layout
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.graphs_widget)
        splitter.addWidget(bottom_half_widget)
        splitter.setSizes([500, 300])  # Set initial size proportions

        # Main layout combining the top bar and splitter
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_bar_widget)
        main_layout.addWidget(splitter)

        # Reduce margins around main components
        main_layout.setContentsMargins(5, 5, 5, 5)  # Left, Top, Right, Bottom margins

        self.setLayout(main_layout)
    

    def _create_file_options_widget(self):
        """
        Creates the top bar widget containing input and output file widgets.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.input_file_widget)
        layout.addStretch()  # Separates the input and output widgets visually
        layout.addWidget(self.output_file_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        return self._create_widget_from_layout(layout)

    def _create_sliders_widget(self):
        """
        Creates the sliders widget based on specified configurations.
        """
        default_slider_range = (0, 100)
        slider_specs = [
            (1, "black"), (1, "black"), (3, "red"),
            (3, "green"), (3, "blue"), (4, "black"),
        ]

        # Initialize sliders
        self.list_of_sliders = [
            NSlidersWidget(num_sliders, *default_slider_range, color)
            for num_sliders, color in slider_specs
        ]

        # Add sliders to a horizontal layout
        layout = QHBoxLayout()
        for slider in self.list_of_sliders:
            layout.addWidget(slider)
        layout.setContentsMargins(0, 0, 0, 0)

        return self._create_widget_from_layout(layout)

    def _create_widget_from_layout(self, layout):
        """
        Helper method to wrap a layout in a QWidget.
        """
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def update_file_content(self, file_path):
        """
        Updates the file content by reading from the provided file path.
        """
        try:
            with open(file_path, 'r') as file:
                self.file_content = file.read()
            print(f"File contents loaded:\n{self.file_content}")
        except Exception as e:
            print(f"Error reading file: {e}")
            self.file_content = "Error loading file."

# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWidget()
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    