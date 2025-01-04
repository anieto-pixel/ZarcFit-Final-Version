"""
Created on Mon Dec  9 09:28:03 2024

A vertical column of buttons for quick actions.
Renamed from 'ButtonsWidgetRow' to 'WidgetButtonsRow' for consistency.
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

# Renamed imports (if needed; remove if not used)
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from WidgetOutputFile import WidgetOutputFile


class WidgetButtonsRow(QWidget):
    """
    A simple widget providing a vertical layout of buttons (F1, F2, F3, etc.).
    """

    def __init__(self):
        super().__init__()

        # Create buttons
        self.f1_button = QPushButton("F1")
        self.f2_button = QPushButton("F2")
        self.f3_button = QPushButton("F3")
        self.save_button = QPushButton("Save plot")
        self.f5_button = QPushButton("F5")
        self.f6_button = QPushButton("F6")
        self.f7_button = QPushButton("F7")
        self.f8_button = QPushButton("F8")
        self.f9_button = QPushButton("F9")

        # Group all buttons into a list for easy iteration
        self._buttons_list = [
            self.f1_button, self.f2_button, self.f3_button,
            self.save_button, self.f5_button, self.f6_button,
            self.f7_button, self.f8_button, self.f9_button
        ]

        # Build the layout
        self._setup_layout()

    def _setup_layout(self):
        """
        Creates a vertical box layout, adds each button, and configures sizing.
        """
        layout = QVBoxLayout()
        for button in self._buttons_list:
            layout.addWidget(button)

        self.setLayout(layout)

        # Constrain width and overall size
        self.setMaximumWidth(150)
        self.setMinimumSize(90, 35 * len(self._buttons_list))

    # (Optional) Public methods or signals could go here


# -----------------------------------------------------------------------
#  Quick Test
# -----------------------------------------------------------------------
if __name__ == "__main__":
    def test_buttons_widget_row():
        """
        Demonstrates the WidgetButtonsRow in a standalone window,
        printing size details for the 'Save plot' button.
        """
        app = QApplication(sys.argv)

        widget = WidgetButtonsRow()

        # Example: print size details of the 'save_button'
        min_size = widget.save_button.minimumSize()
        print(f"Minimum size: {min_size.width()}px x {min_size.height()}px")

        widget.setWindowTitle("Test WidgetButtonsRow")
        widget.show()

        sys.exit(app.exec_())

    test_buttons_widget_row()