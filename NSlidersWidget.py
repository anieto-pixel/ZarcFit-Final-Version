# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 09:32:47 2024

@author: agarcian
"""
import sys
from PyQt5.QtWidgets import *

#my own classes
from SliderWithTicks import SliderWithTicks
from OutputFileWidget import OutputFileWidget


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
            slider.value_changed().connect(self.update_labels)

        # Layout
        main_layout = QHBoxLayout()

        # Add spacer item to push sliders apart if needed
        #main_layout.addSpacerItem(QSpacerItem(10, 0))  # Adjust as needed for horizontal spacing
        for s in self.list_of_sliders:
            main_layout.addWidget(s)

        # Set margins to the layout
        main_layout.setContentsMargins(0, 10, 10, 0)  # Set top, left, right, and bottom margins
                                                        #(for horizontal distribution: left , top, right, bottom)

        self.setLayout(main_layout)

    def calculate_total(self):
        return sum(slider.get_value() for slider in self.list_of_sliders)

    def update_labels(self):
        total = self.calculate_total()
        self.value_label_total.setText(f"Total: {total}")
        
        
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QColor

    # Manual test method
    def test_n_sliders_widget():
        app = QApplication(sys.argv)
        
        # Create and show the NSlidersWidget
        n_sliders = 5  # Number of sliders
        min_value = 0  # Minimum slider value
        max_value = 100  # Maximum slider value
        colour = "red"  # Example slider color

        widget = NSlidersWidget(n=n_sliders, min_value=min_value, max_value=max_value, colour=colour)
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