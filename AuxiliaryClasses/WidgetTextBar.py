
"""
Created on Tue Jan  7 11:37:36 2025

@author: agarcian
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QSlider, QWidget, QVBoxLayout


class WidgetTextBar(QWidget):
    """A widget that displays key/value pairs with colored labels."""

    def __init__(self, keys_1=None):
        """
        Initialize the WidgetTextBar.

        Parameters:
            keys_1 (list): A list of keys used to create the labels.
        """
        super().__init__()
        if keys_1 is None:
            keys_1 = []
        self.value_labels = {}   # Maps keys to QLabel instances.
        self.key_colors = {}     # Maps keys to HTML colors for label text.

        # Create a horizontal layout for the widget.
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(20)

        # 1) Separate keys by suffix, then sort within each group.
        keys_h = []
        keys_m = []
        keys_l = []
        keys_other = []

        # If you want to include keys_2 in the same logic, uncomment below:
        # combined_keys = keys_1 + keys_2
        combined_keys = keys_1

        for k in combined_keys:
            if k.endswith("h"):
                keys_h.append(k)
            elif k.endswith("m"):
                keys_m.append(k)
            elif k.endswith("l"):
                keys_l.append(k)
            else:
                keys_other.append(k)

        keys_h.sort()
        keys_m.sort()
        keys_l.sort()
        keys_other.sort()

        # Merge keys in the desired display order.
        ordered_keys = keys_h + keys_m + keys_l + keys_other

        # 2) Create labels in that order with corresponding colors.
        for key in ordered_keys:
            if key.endswith("h"):
                color = "red"
            elif key.endswith("m"):
                color = "green"
            elif key.endswith("l"):
                color = "blue"
            else:
                color = "black"

            self.key_colors[key] = color

            # Create a QLabel with colored key text and a default numeric value.
            initial_text = f"<b><font color='{color}'>{key}:</font></b> 0.000000"
            value_label = QLabel(initial_text)
            value_label.setAlignment(Qt.AlignLeft)
            value_label.setFixedWidth(130 + len(key))  # Adjust width as needed.

            h_layout.addWidget(value_label)
            self.value_labels[key] = value_label

        h_layout.addStretch()
        self.setLayout(h_layout)

    def _update_text(self, dictionary):
        """
        Updates the text of labels based on the provided dictionary.

        The key text remains colored, while the value text is displayed in black.
        """
        for key, value in dictionary.items():
            if key in self.value_labels:
                color = self.key_colors.get(key, "black")
                formatted_string = (
                    f"<b><font color='{color}'>{key}:</font></b> {value:.3g}"
                )
                self.value_labels[key].setText(formatted_string)
            else:pass
                #print(
                #    f"WidgetTextBar Warning: Key '{key}' will not be displayed. Add it in config.ini"
                #)


#########################
# Manual Testing
#########################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Dictionary 1 has keys ending with h, m, l (red, green, blue).
    dic_1 = {"pQh": 2.0067, "pQm": 0.00008, "pQl": 20.450004, "pS": 999.0}

    # Dictionary 2 has keys that do not follow the h/m/l suffix convention.
    dic_2 = {"unknown": 0.0067}

    # Merge dictionaries for updating.
    dic_3 = dic_1 | dic_2

    # Create main window.
    window = QMainWindow()

    # Create the WidgetTextBar with keys from both dictionaries.
    text_bar = WidgetTextBar(dic_1.keys() | dic_2.keys())
    text_bar._update_text(dic_3)

    # Create a central widget and layout to hold the text bar and sliders.
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    # For each key, create a label and a corresponding horizontal slider.
    sliders = {}
    for key, value in dic_3.items():
        lbl = QLabel(key)
        central_layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-1000000)
        slider.setMaximum(1000000)
        slider.setValue(int(value * 10))
        # Update the dictionary and text bar when the slider value changes.
        slider.valueChanged.connect(
            lambda val, k=key: (
                dic_3.update({k: val / 100.0}),
                text_bar._update_text(dic_3)
            )
        )
        sliders[key] = slider
        central_layout.addWidget(slider)

    central_widget.setLayout(central_layout)
    window.setCentralWidget(central_widget)
    window.setWindowTitle("Testing WidgetTextBar with Sliders")
    window.show()

    sys.exit(app.exec_())
