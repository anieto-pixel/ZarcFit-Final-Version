# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 11:27:04 2024

@author: agarcian
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 


"""
Class contains a QWidget with a graduated slider with range min_value, max_value, and colour
"""
class SliderWithTicks(QWidget):
    def __init__(self,min_value, max_value, colour):
        super().__init__()

        # Private attributes
        self._min_value= min_value
        self._max_value= max_value
        self._slider = QSlider(Qt.Vertical, self)
        self._value_label = QLabel(f"Slider: {self._slider.value()}", self)
        self._layout = QVBoxLayout()
        
        #Connect Slider and Label
        self._slider.valueChanged.connect(self._update_label)
        
        #Setup slidet's characteristics
        self._setup_slider(colour)
        
        #Setup widget's layout
        self._setup_layout()
        
    def _setup_layout(self):
        """
        Configure the layout and add widgets.
        """
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._value_label)
        self.setLayout(self._layout)
        
        
    def _setup_slider(self, colour):
        """
        Configure the slider's properties.
        """
        
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        self._slider.setTickInterval(round((self._max_value - self._min_value) / 10))

        self._slider.setStyleSheet(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }}
            QSlider::add-page:vertical {{
                background: #d3d3d3;
                border-radius: 5px;
            }}
        """)

        self.setMinimumWidth(75)
        
        
    def _update_label(self):
        """
        Update the label when the slider value changes.
        """
        self._value_label.setText(f"Slider: {self._slider.value()}")

    def get_value(self):
        """
        Returns the current value of the slider.
        """
        return self._slider.value()

    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external use.
        """
        return self._slider.valueChanged

    def paintEvent(self, event):
        """
        Custom painting for drawing tick labels.
        """
        super().paintEvent(event)

        #Create a painter object to paint on the Widget
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 6))
        painter.setPen(QColor(0, 0, 0))

        #gets min, max and tick interval values from slider

        tick_interval = self._slider.tickInterval()

        height = self._slider.height()
        top_offset = 5
        bottom_offset = 5
        effective_height = height - top_offset - bottom_offset

        for i in range(self._min_value, self._max_value + 1, tick_interval):
            tick_pos = (
                height - bottom_offset - (effective_height * (i - self._min_value)) // (self._max_value - self._min_value)
            )
            text_rect = QRect(30, tick_pos, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, str(i))



#class SliderForFrequency(QWidget):
        
    #https://stackoverflow.com/questions/17361885/range-slider-in-qt-two-handles-in-a-qslider 
    #https://stackoverflow.com/questions/47342158/porting-range-slider-widget-to-pyqt5

    #https://pypi.org/project/QtRangeSlider/

   
   ########################################
   #manual test method child
   ######################################
   
if __name__ == "__main__":

       # Create a QApplication instance
       app = QApplication(sys.argv)

       # Create and show an instance of SliderWithTicks
       slider_widget = SliderWithTicks(0,10,"red")
       slider_widget.resize(200, 300)
       slider_widget.show()
       # Run the application
       sys.exit(app.exec_())
  