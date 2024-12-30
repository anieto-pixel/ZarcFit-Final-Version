import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 
from SliderWithTicks import SliderWithTicks


class DoubleSliderWithTicks(SliderWithTicks):
    
    def __init__(self,min_value, max_value, colour):
        
        self._scale_factor = 1000  # Scale factor for converting doubles to integers

        super().__init__(min_value, max_value, colour)
            
    def _setup_slider(self, colour):
        """
        Configure the slider's properties.
        """
        print("child setup slider")
        
        int_min = int(self._min_value * self._scale_factor)
        int_max = int(self._max_value * self._scale_factor)
        
        self._slider.setRange(int_min, int_max)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        self._slider.setTickInterval((int_max - int_min) // 10)

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
        scaled_value = self._slider.value() / self._scale_factor
        self._value_label.setText(f"Slider: {scaled_value:.2f}")

    def get_value(self):
        """
        Returns the current value of the slider.
        """
        return self._slider.value() / self._scale_factor
    
    def _string_by_tick(self, i):
        return str(i/self._scale_factor)
    

if __name__ == "__main__":

    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Create and show an instance of SliderWithTicks with float range
    slider_widget = DoubleSliderWithTicks(0, 0.9, "red")
    slider_widget.resize(200, 300)
    slider_widget.show()

    # Run the application
    sys.exit(app.exec_())
