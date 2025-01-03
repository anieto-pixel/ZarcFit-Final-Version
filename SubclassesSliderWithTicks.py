import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 
#from SliderWithTicks import SliderWithTicks


"""
Parent CLass. Contains a QWidget with a graduated slider with range min_value, max_value, and colour
"""
class SliderWithTicks(QWidget):
    def __init__(self,min_value, max_value, colour):
        super().__init__()

        # Private attributes
        self._min_value= min_value
        self._max_value= max_value
        self._slider = QSlider(Qt.Vertical, self)
        self._value_label = QLabel(f"{self._slider.value()}", self)
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
        #self._value_label.setText(f"Slider: {self._slider.value()}")
        self._value_label.setText(f"Slider: {self.get_value()}")
        #Convinient but causes dependency issues between methods
        #reconsider later

    def get_value(self):
        """
        Returns the current value of the slider.
        """
        return self._slider.value()
    
    def set_value(self, value):
        """
        Sets the slider to a given value.
        """
        self._slider.setValue(value)

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
        min_value = self._slider.minimum()
        max_value = self._slider.maximum()
        tick_interval = self._slider.tickInterval()

        height = self._slider.height()
        top_offset = 5
        bottom_offset = 5
        effective_height = height - top_offset - bottom_offset

        for i in range(min_value, max_value + 1, tick_interval):
            tick_pos = (
                height - bottom_offset - (effective_height * (i - min_value)) // (max_value - min_value)
            )
            text_rect = QRect(30, tick_pos, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, self._string_by_tick(i))
            
    def _string_by_tick(self, i):
        return str(i)
        

"""
Subclass of SliderWithTicks that accepts doubles instead of integers
"""
class DoubleSliderWithTicks(SliderWithTicks):
    
    valueChanged = pyqtSignal(float)  # Override the parent class signal with a float signal
    
    def __init__(self,min_value, max_value, colour):
        
        self._scale_factor = 1000  # Scale factor for converting doubles to integers

        super().__init__(min_value, max_value, colour)
        
        # Connect the original slider signal to a custom slot
        self._slider.valueChanged.connect(self._emit_corrected_value)
            
    def _setup_slider(self, colour):
        """
        Configure the slider's properties.
        """
        
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
         self._value_label.setText(f"{self.get_value():.3f}")
    
    def _string_by_tick(self, i):
            return str(i/self._scale_factor)
    
    def get_value(self):
        """
        Returns the current value of the slider.
        USE THIS METHOD. dO NOT ACCES SLIDER DIRECTLY
        """
        return self._slider.value() / self._scale_factor
    
    def set_value(self, value):
        """
        Sets the slider to a given value.
        """
        value=int(value*self._scale_factor)
        self._slider.setValue(value)
        
    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external use.
        """
        return self.valueChanged
    
    def _emit_corrected_value(self, raw_value):
        """
        Emits the corrected value through the overridden valueChanged signal.
        """
        corrected_value = raw_value / self._scale_factor
        self.valueChanged.emit(corrected_value)
        
    
"""
Subclass of DoubleSliderWithTicks that accepts the double exponent of powers of N
"""
class EPowerSliderWithTicks(DoubleSliderWithTicks):
        
    def __init__(self,min_value, max_value, colour):
            
        self._base_power = 10  # base power to use
        super().__init__(min_value, max_value, colour)
        
    def _update_label(self):
        self._value_label.setText(f"{self.get_value():.1e}")
        #return f"{self.get_value():.3e}"  
                
    def _string_by_tick(self, i):
        return f"1E{int(i/self._scale_factor)}"
    
    def _emit_corrected_value(self, raw_value):
        """
        Emits the corrected value through the overridden valueChanged signal.
        """
        n= raw_value / self._scale_factor
        corrected_value=self._base_power**n
        self.valueChanged.emit(corrected_value)
        
    def get_value(self):
        n=self._slider.value()/self._scale_factor
        return self._base_power**n


if __name__ == "__main__":

    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Create and show an instance of SliderWithTicks with float range
    #slider_widget = DoubleSliderWithTicks(0, 0.9, "red")
    #slider_widget = DoubleSliderWithTicks(-2., 2., "red")
    #slider_widget = EPowerSliderWithTicks(0, 10, "red")
    slider_widget = EPowerSliderWithTicks(-10, 10, "red")
    slider_widget.resize(200, 300)
    
    slider_widget.value_changed().connect(print)
    slider_widget.show()
    # Run the application
    sys.exit(app.exec_())
    

