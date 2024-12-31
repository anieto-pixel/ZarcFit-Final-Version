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
    def __init__(self, slider_configurations, parent=None):
        super().__init__(parent)
        self.slider_configurations = slider_configurations
        self.sliders = self._create_sliders()
        self._setup_layout()
    
    def _create_sliders(self):
        """
        Creates sliders based on the provided slider configurations.
        """
        sliders = []
        for slider_type, min_value, max_value, color in self.slider_configurations:
            sliders.append(slider_type(min_value, max_value, color))
        return sliders
    
    def _setup_layout(self):
        """
        Creates a layout and adds all sliders to it.
        """
        layout = QHBoxLayout()
        for slider in self.sliders:
            layout.addWidget(slider)
        layout.setContentsMargins(0, 0, 15, 0)# Set top, left, right, and bottom margins
        #(for horizontal distribution: left , top, right, bottom)
        
        self.setLayout(layout)
            
        
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QColor

    # Manual test method
    def test_n_sliders_widget():
        app = QApplication(sys.argv)
        
        slider_configurations = [
            (EPowerSliderWithTicks, -10, 0, 'black'),
            (EPowerSliderWithTicks, -10, 10, 'black'),
            (DoubleSliderWithTicks, 0.0, 1.0, 'red'),
            (DoubleSliderWithTicks, -10.00, 1.0, 'green')
            ]

        widget = NSlidersWidget(slider_configurations)
        widget.setWindowTitle("Test NSlidersWidget")
        
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