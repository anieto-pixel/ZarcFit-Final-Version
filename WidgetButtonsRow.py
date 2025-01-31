"""
Created on Mon Dec  9 09:28:03 2024

A vertical column of buttons for quick actions.
Renamed from 'ButtonsWidgetRow' to 'WidgetButtonsRow' for consistency.
"""
from PyQt5.QtWidgets import QGraphicsColorizeEffect
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, 
    )
from PyQt5.QtGui import QColor, QPalette

import sys


class WidgetButtonsRow(QWidget):
    """
    A simple widget providing a vertical layout of buttons (F1, F2, F3, etc.).
    """

    def __init__(self):
        super().__init__()

        # Create buttons
        self.f1_button = QPushButton("F1. Fit Cole")
        self.f2_button = QPushButton("F2 Fit Bode")
        self.f3_button = QPushButton("F3 AllFreqs")
        self.f4_button = QPushButton("F4 Save plot")
        self.f5_button = QPushButton("F5 <file")
        self.f6_button = QPushButton("F6 file>")
        self.f7_button = QPushButton("F7 Recover")
        self.f8_button = QPushButton("F8 Default")
        self.f9_button = QPushButton("F9 -Rinf")
        self.fup_button = QPushButton("PageUp")
        self.fdown_button = QPushButton("PageDown")

        # Group all buttons into a list for easy iteration
        self._buttons_list = [
            self.f1_button, self.f2_button, self.f3_button,
            self.f4_button, self.f5_button, self.f6_button,
            self.f7_button, self.f8_button, self.f9_button,
            self.fup_button, self.fdown_button
        ]
        
        # Setup the buttons
        # Track boolean for the f9_button
        self.f9_active = False

        # Initialize
        self._setup_layout()
        self._setup_connections()


    def _setup_layout(self):
        layout = QVBoxLayout()
        for button in self._buttons_list:
            layout.addWidget(button)

        self.setLayout(layout)
        self.setMaximumWidth(150)
        self.setMinimumSize(90, 35 * len(self._buttons_list))

    def _setup_connections(self):
        # Connect all EXCEPT f9 to a generic click handler
        for btn in self._buttons_list:
            if btn is not self.f9_button:
                btn.clicked.connect(self._on_regular_button_clicked)

        # f9 has a special click handler
        self.f9_button.clicked.connect(self._on_f9_clicked)

    def _on_regular_button_clicked(self):
        """
        Generic slot for all buttons except f9.
        Briefly flashes green if 'task is successful'.
        Shows an error message if not.
        """
        button = self.sender()
        # --- put your "check if order is correct" logic here ---
        order_is_correct = True  # Replace with real check

        if order_is_correct:
            self._flash_button_green(button)
        else:
            QMessageBox.warning(self, "Error", "Order not correctly executed!")

    def _on_f9_clicked(self, duration=500):

        self.f9_active = not self.f9_active
    
        if self.f9_active:
            self.f9_button.setStyleSheet("QPushButton { background-color: red; }")
        else:
            self.f9_button.setStyleSheet("QPushButton { background-color: none; }") 

    def _flash_button_green(self, button, duration=500):

        print("wodgetbuttons")        

        original_effect = button.graphicsEffect()
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(0, 150, 0, 255))  # Custom darker green color
        effect.setStrength(1.0)
        button.setGraphicsEffect(effect)
        
        # Remove the effect after 'duration' milliseconds, restoring the original effect
        QTimer.singleShot(duration, lambda: button.setGraphicsEffect(original_effect))


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