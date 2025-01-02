
"""
Created on Mon Dec  9 09:32:47 2024

@author: agarcian
"""
import sys
from PyQt5.QtWidgets import *

#my own classes
from SubclassesSliderWithTicks import *
from OutputFileWidget import OutputFileWidget


from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
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
        
        self._setup_layout()
        self._connect_signals()
        self.set_default_values()

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

    def _setup_layout(self):
        """
        Creates a layout and adds all sliders to it in dictionary order.
        """
        layout = QHBoxLayout()
        for slider in self.sliders.values():
            layout.addWidget(slider)
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

        
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QColor

    # Manual test method
    def test_n_sliders_widget():
        app = QApplication(sys.argv)
        
        slider_configurations = {
                    'linf': (EPowerSliderWithTicks, -9, 0, 'black'),

                    'ph': (DoubleSliderWithTicks, 0.0, 1.0, 'red'),
                    'pm': (DoubleSliderWithTicks, -1.0, 1.0, 'green'),
                    'rl': (EPowerSliderWithTicks, 0, 10, 'blue')
                    }
        
        slider_default_values = [-3.,0.2,0.4,5.]
        
        widget = NSlidersWidget(slider_configurations, slider_default_values)
        widget.setWindowTitle("Test NSlidersWidget")
        widget.setGeometry(100, 100, 800, 900)
        
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

    # Run the test
    test_n_sliders_widget()