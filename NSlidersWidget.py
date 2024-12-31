# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 09:32:47 2024

@author: agarcian
"""
import sys
from PyQt5.QtWidgets import *

#my own classes
from SubclassesSliderWithTicks import *
from OutputFileWidget import OutputFileWidget


class NSlidersWidget(QWidget):
    # Signal to emit when a slider changes value
    slider_value_updated = pyqtSignal(str, float)

    def __init__(self, slider_configurations, parent=None):
        super().__init__(parent)
        self.sliders = self._create_sliders(slider_configurations)
        self._setup_layout()
        self._connect_signals()

    def _create_sliders(self, slider_configurations):
        """
        Creates a dictionary of sliders based on the provided slider configurations.
        """
        sliders = {}
        for key, (slider_type, min_value, max_value, color) in slider_configurations.items():
            sliders[key] = slider_type(min_value, max_value, color)
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
            slider.value_changed().connect(lambda value, k=key: self.slider_value_updated.emit(k, value))

    def get_slider(self, key):
        """
        Retrieves a slider by its key.
        """
        return self.sliders.get(key)
    
    
        
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
        widget = NSlidersWidget(slider_configurations)
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