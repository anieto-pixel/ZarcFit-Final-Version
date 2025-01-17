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
    def __init__(self, keys_1=[]):
        super().__init__()
        self.value_labels = {}   # Dictionary to store key-to-label mapping
        self.key_colors = {}     # Store each key's HTML color for use in _update_text

        # Create a horizontal layout for the widget
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(20)

        # 1) Separate keys by suffix, then sort within each group
        keys_h = []
        keys_m = []
        keys_l = []
        keys_other = []

        # If you want to include keys_2 in the same logic, uncomment below:
        # combined_keys = keys_1 + keys_2
        combined_keys = keys_1

        for k in combined_keys:
            if k.endswith('h'):
                keys_h.append(k)
            elif k.endswith('m'):
                keys_m.append(k)
            elif k.endswith('l'):
                keys_l.append(k)
            else:
                keys_other.append(k)

        keys_h.sort()
        keys_m.sort()
        keys_l.sort()
        keys_other.sort()

        # Merge them in desired display order
        ordered_keys = keys_h + keys_m + keys_l + keys_other

        # 2) Create labels in that color order
        for key in ordered_keys:
            # Determine color based on suffix
            if key.endswith('h'):
                color = "red"
            elif key.endswith('m'):
                color = "green"
            elif key.endswith('l'):
                color = "blue"
            else:
                color = "black"

            self.key_colors[key] = color

            # Create a QLabel for the variable (color only for the key text)
            initial_text = f"<b><font color='{color}'>{key}:</font></b> 0.000000"
            value_label = QLabel(initial_text)
            value_label.setAlignment(Qt.AlignLeft)

            # Set a fixed width for the label to prevent shifting
            value_label.setFixedWidth(130 + len(key))  # Adjust as needed

            h_layout.addWidget(value_label)
            self.value_labels[key] = value_label

        h_layout.addStretch()
        self.setLayout(h_layout)

    def _update_text(self, dictionary):
        """
        Updates the text of labels based on the given dictionary.
        The key text keeps its color, while the value text is black.
        """
        for key, value in dictionary.items():
            if key in self.value_labels:
                # Fetch the color assigned in __init__
                color = self.key_colors.get(key, "black")

                # Only the key is colored; the numeric value is black
                formatted_string = (
                    f"<b><font color='{color}'>{key}:</font></b> {value:.3g}"
                )
                self.value_labels[key].setText(formatted_string)
            else:
                print(f"WidgetTectBar Warning: Key '{key}' not found in value_labels.")
                
#########################
# Testing
#########################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Dictionary 1 has keys ending with h, m, l (red, green, blue)
    dic_1 = {"pQh": 2.0067, "pQm": 0.00008, "pQl": 20.450004, "pS": 999.0}

    # Dictionary 2 also has h, m, l, plus a "pS" key
    # which does not end with h/m/l => black
    dic_2 = {"unknown": 0.0067}

    # Merge both into dic_3 for updating
    dic_3 = dic_1 | dic_2

    # MainWindow container
    window = QMainWindow()

    # Create the WidgetTextBar with keys from both dictionaries
    text_bar = WidgetTextBar(dic_1.keys()| dic_2.keys())
    text_bar._update_text(dic_3)

    # Create sliders that modify dic_3 and update text_bar
    sliders = {}
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    # For each key, create a label + slider
    for key, value in dic_3.items():
        # A label to show which key this slider controls
        lbl = QLabel(key)
        central_layout.addWidget(lbl)

        # Horizontal slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-1000000)
        slider.setMaximum(1000000)
        slider.setValue(int(value * 10))  # optional: set an initial position
        # When slider changes, update the dictionary and the text bar
        slider.valueChanged.connect(lambda val, k=key: (
            dic_3.update({k: val / 100.0}),
            text_bar._update_text(dic_3)
        ))
        sliders[key] = slider

        central_layout.addWidget(slider)

    central_widget.setLayout(central_layout)
    window.setCentralWidget(central_widget)
    window.setWindowTitle("Testing WidgetTextBar with Sliders")
    window.show()

    sys.exit(app.exec_())