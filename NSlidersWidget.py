
"""
Created on Mon Dec  9 09:32:47 2024

@author: agarcian
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal

#my own classes
from SubclassesSliderWithTicks import *
from OutputFileWidget import OutputFileWidget
from ConfigImporter import *

from functools import partial



class NSlidersWidget(QWidget):
    # Signal to emit when a slider changes value
    slider_value_updated = pyqtSignal(str, float)

    def __init__(self, slider_configurations, slider_default_values):
        super().__init__()
        # Create a dictionary for slider defaults and initialize sliders
        self.slider_default_values = dict(zip(slider_configurations.keys(), slider_default_values))
        self.sliders = self._create_sliders(slider_configurations)
        self.set_default_values()

        self._setup_layout(slider_configurations)
        self._connect_signals()
      
        
    """
    PRIVATE METHODS
    """
    def _create_sliders(self, slider_configurations):
        """
        Creates a dictionary of sliders based on the provided slider configurations.
        """
        sliders = {}
        for key, (slider_type, min_value, max_value, color) in slider_configurations.items():
            # Ensure slider_type is callable and instantiate the slider
            slider = slider_type(min_value, max_value, color)
            sliders[key] = slider
        return sliders

    def _setup_layout(self, slider_configurations):
        """
        Creates a layout and adds all sliders with styled labels to it in dictionary order.
        """
        layout = QHBoxLayout()
        for key, slider in self.sliders.items():
            # Create a vertical layout for each slider and its label
            slider_layout = QVBoxLayout()
            label = QLabel(key)
            label.setAlignment(Qt.AlignCenter)  # Center the label text

            # Style the label to be bold and match the slider's color
            slider_color = slider_configurations[key][3]  # Retrieve color from configuration
            label.setStyleSheet(f"color: {slider_color}; font-weight: bold;")

            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)
            layout.addLayout(slider_layout)
        layout.setContentsMargins(0, 0, 15, 0)
        self.setLayout(layout)

    def _connect_signals(self):
        """
        Connects the sliders' value change signals to emit their value and key.
        """
        for key, slider in self.sliders.items():
            slider.value_changed().connect(partial(self.slider_value_updated.emit, key))

    """
    PUBLIC METHODS
    """
    def get_slider(self, key):
        """
        Retrieves a slider by its key.
        """
        return self.sliders.get(key)


    def set_default_values(self):
        """
        Sets the default values for all sliders based on the provided defaults.
        """
        for key, default_value in self.slider_default_values.items():
            slider = self.sliders[key]
            slider.set_value(default_value)  # Ensure the slider class has a set_value method




"""QUICK TEST"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    config_file = "config.ini"
    config = ConfigImporter(config_file)
    
    widget = NSlidersWidget(config.slider_configurations, config.slider_default_values)
    widget.setWindowTitle("Test NSlidersWidget")
    widget.setGeometry(100, 100, 800, 900)
    
    # Connect the signal to print directly
    widget.slider_value_updated.connect(print)
    
    #testing for sizing options
    min_size = widget.minimumSize()  # Returns a QSize object
    min_width, min_height = min_size.width(), min_size.height()
    print(f"Minimum size: {min_width}px x {min_height}px")
    max_size = widget.maximumSize()  # Returns a QSize object
    max_width, max_height = max_size.width(), max_size.height()
    print(f"Maximum size: {max_width}px x {max_height}px")
    
    widget.show()
     
    # Run the application event loop
    sys.exit(app.exec_())
