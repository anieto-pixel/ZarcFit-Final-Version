# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 11:27:04 2024

@author: agarcian
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 


"""
Class contains a QWidget with a graduated slider with range min_value, max_value, and colour
"""
class SliderWithTicks(QWidget,):
    def __init__(self,min_value, max_value, colour):
        super().__init__()

        # Set up the slider
        self.s = QSlider(Qt.Vertical, self)
        self.s.setRange(min_value, max_value)  # Min and Max values
        self.s.setTickPosition(QSlider.TicksBothSides)  # Display ticks on both sides
        self.s.setTickInterval(round((max_value-min_value)/10))  # Set interval for ticks
        
        #customize slider appeareance
        self.s.setStyleSheet(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }}
        """)

        # Set up the label
        self.value_label = QLabel(f"Slider: {self.s.value()}", self)

        # Layout for slider and label
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.s)
        self.layout.addWidget(self.value_label)
        self.setLayout(self.layout)

        # Connect slider to label update
        self.s.valueChanged.connect(self.update_label)
        
        
    def get_value(self):
        """
        Returns the current value of the slider.
        """
        return self.s.value()
    
    def valueChanged(self):
        """
        Exposes the slider's valueChanged signal for external use.
        """
        return self.s.valueChanged

    def update_label(self):
        """
        Update the label when slider value changes.
        """
        self.value_label.setText(f"Slider: {self.s.value()}")
    
    def paintEvent(self, event):
        """
        Custom painting for drawing tick labels.
        """
        super().paintEvent(event)
    
        # Create a painter object to draw on the widget
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 6))  # Set font for tick labels
        painter.setPen(QColor(0, 0, 0))  # Set text color to black
    
        # Get slider range
        min_value = self.s.minimum()
        max_value = self.s.maximum()
    
        # Get tick interval
        tick_interval = self.s.tickInterval()
    
        # Get the height of the slider widget
        height = self.s.height()
    
        # Add top offset to account for padding
        top_offset = 5  # Adjust this value based on observed misalignment
        bottom_offset = 5  # Adjust this as well if needed
    
        # Calculate effective height, excluding offsets
        effective_height = height - top_offset - bottom_offset
    
        # Iterate over the range and draw numbers
        for i in range(min_value, max_value + 1, tick_interval):
            # Adjust the vertical position to account for offsets
            tick_pos = (
                height - bottom_offset - (effective_height * (i - min_value)) // (max_value - min_value)
            )
    
            # Draw the number as text next to the tick mark
            text_rect = QRect(30, tick_pos, 50, 20)  # Position text to the right
            painter.drawText(text_rect, Qt.AlignCenter, str(i))


########################################
#manual test method
######################################
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Create and show an instance of SliderWithTicks
    slider_widget = SliderWithTicks(0, 100, "blue")
    slider_widget.resize(200, 300)
    slider_widget.show()

    # Run the application
    sys.exit(app.exec_())