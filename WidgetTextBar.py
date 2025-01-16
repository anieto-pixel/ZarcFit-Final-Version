# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 11:37:36 2025

@author: agarcian
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 11:37:36 2025

@author: agarcian
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import sys

class WidgetTextBar(QWidget):
    def __init__(self, keys_1=[], keys_2=[]):
        super().__init__()
        self.value_labels = {}  # Dictionary to store key-to-label mapping

        # Create a horizontal layout for the widget
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tight alignment
        h_layout.setSpacing(20)  # Set fixed spacing between labels

        # Combine and sort keys from both lists
        keys = sorted(list(keys_1) + list(keys_2))

        for key in keys:
            # Create a QLabel for the variable
            value_label = QLabel(f"<b>{key}:</b> 0.000000")  # Initialize with default value
            value_label.setAlignment(Qt.AlignLeft)

            # Set a fixed width for the label to prevent shifting
            value_label.setFixedWidth(130 + len(key))  # Adjust this value as needed for your content

            # Add the label to the layout
            h_layout.addWidget(value_label)

            # Store the label in the dictionary for later updates
            self.value_labels[key] = value_label

        # Add a stretch to push all items to the left
        h_layout.addStretch()

        # Set the layout for the widget
        self.setLayout(h_layout)

    def _update_text(self, dictionary):
        """
        Updates the text of labels based on the given dictionary.
        """
        for key, value in dictionary.items():
            if key in self.value_labels:
                # Format and update the label text
                formatted_string = f"<b>{key}:</b> {value:.5g}"
                self.value_labels[key].setText(formatted_string)
            else:
                print(f"Warning: Key '{key}' not found in value_labels.")
#########################
# Testing
#########################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dic_1 = {"pQh": 2.0067, "pQm": 0.00008, "pQl": 20.450004}
    dic_2 = {"pRh": 0.0067, "pRm": 1.00008, "pRl": 0.450004}
    dic_3 = dic_1 | dic_2

    # MainWindow container
    window = QMainWindow()

    # Create the WidgetTextBar
    text_bar = WidgetTextBar(dic_1.keys(), dic_2.keys())
    text_bar._update_text(dic_3)

    # Create sliders directly in the test script
    sliders = {}
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    for key, value in dic_3.items():
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-100000)
        slider.setMaximum(100000)
        slider.valueChanged.connect(lambda val, k=key: (dic_3.update({k: val}), text_bar._update_text(dic_3)))  
        sliders[key] = slider

        central_layout.addWidget(QLabel(key))
        central_layout.addWidget(slider)

    central_widget.setLayout(central_layout)

    window.setCentralWidget(central_widget)
    window.setWindowTitle("Testing WidgetTextBar with Sliders")
    window.show()

    sys.exit(app.exec_())
