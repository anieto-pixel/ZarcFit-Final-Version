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
from NSlidersWidget import NSlidersWidget
from ButtonsWidgetRow import ButtonsWidgetRow
from NGraphsWidget import GraphsWidget
from SubclassesSliderWithTicks import *
from ManualModel import *

import configparser

class MainWidget(QWidget):
    
    def __init__(self, config_file=None):
        
        
        super().__init__()
        self.file_content = {"freq": None, "Z_real": None, "Z_imag": None}
        self.manual_content = {"freq": None, "Z_real": None, "Z_imag": None}
        self.calculator = None

        # Read slider configurations and defaults
        if config_file is None:
            pass
            #throws error    
        else:
            self.slider_configurations, self.slider_default_values = self._read_config_file(config_file) 
            #here we will get the name of the buttons when it is time
        
        # Initialize widgets
        self.input_file_widget = InputFileWidget(config_file)
        self.output_file_widget = OutputFileWidget()
        self.sliders_widget = NSlidersWidget(self.slider_configurations, self.slider_default_values)
        self.buttons_widget = ButtonsWidgetRow()
        self.graphs_widget = GraphsWidget()

        # Pass configurations and default values to ManualModel
        self.manual_model = ManualModel(
            list(self.slider_configurations.keys()),
            self.slider_default_values)

        # Set up UI
        self._initialize_ui()

        # Connect signals
        self.input_file_widget.file_contents_updated.connect(self.update_file_content)
        self.manual_model.manual_model_updated.connect(self.update_manual_content)
        self.sliders_widget.slider_value_updated.connect(self.manual_model.update_variable)


    def _read_config_file(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
    
        # Read slider configurations
        sliders = {}
        for key, value in config["SliderConfigurations"].items():
            slider_type, min_value, max_value, color = value.split(",")
            sliders[key] = (self._safe_import(slider_type), float(min_value), float(max_value), color)

        defaults_str = config["SliderDefaultValues"]["defaults"]
        defaults = [float(val) for val in defaults_str.split(",")]

        return sliders, defaults
    
    @staticmethod
    def _safe_import(class_name):
        """
        Safely imports and instantiates a class from a string.
        Args:class_name (str): Name of the class to import.
        Returns:type: Class reference.
        """
        classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return classes.get(class_name)

    def _initialize_ui(self):
        """
        Organizes the layout and settings for the MainWidget.
        """
        self.top_bar_widget = self._create_file_options_widget()

        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.sliders_widget)
        bottom_half_layout.addWidget(self.buttons_widget)

        bottom_half_widget = self._create_widget_from_layout(bottom_half_layout)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.graphs_widget)
        splitter.addWidget(bottom_half_widget)
        splitter.setSizes([500, 300])

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_bar_widget)
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(5, 5, 5, 5)

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
    
##
#listeners and conections
##

    """
    Receives the numpy arrays (frequencies, resistances, reactances) from the signal 
    and modifies class parameters necessary.
    """
    def update_file_content(self, freq, Z_real, Z_imag):
    
        self.file_content = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self.graphs_widget.update_graphs(freq,Z_real,Z_imag)
        self.manual_model.initialize_frequencies(freq)
        
    """
    Receives the numpy arrays (frequencies, resistances, reactances) from the signal 
    and modifies class parameters necessary.
    """
    def update_manual_content(self, freq, Z_real, Z_imag):
    
        self.manual_content = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self.graphs_widget.update_manual_plot(freq,Z_real,Z_imag)

##
##utilities
##
    def _create_widget_from_layout(self, layout):
        
        widget = QWidget()
        widget.setLayout(layout)
        return widget
        
            

# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

    # Create the main window and set its properties
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)
    window.show()

    sys.exit(app.exec_())