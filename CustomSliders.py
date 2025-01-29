import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics


class CustomSliders(QWidget):
    """
    A basic vertical slider with labeled ticks and a value label.
    This class provides:
      - A slider from min_value to max_value.
      - Tick markings displayed on the widget's paint event.
      - A label showing the current slider value.
    """

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        super().__init__()
        # Setup slider parameters
        self._min_value = min_value
        self._max_value = max_value
        self.colour = colour
        self.disabled_colour = "gray"
        self.number_of_tick_intervals = number_of_tick_intervals

        # Main slider and label
        self._slider = QSlider(Qt.Vertical, self)
        self._value_label = QLabel(str(self._slider.value()), self)

        # Disable button
        self._disable_button = QPushButton("Disable", self)

        # Overall widget layout
        self._layout = QVBoxLayout()
        self._slider.valueChanged.connect(self._update_label)
        self._disable_button.clicked.connect(self._toggle_slider)

        # Configure slider appearance and functionality
        self._setup_slider()
        self._setup_layout()
        
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _setup_layout(self):
        """
        Create and assign a layout containing the slider and the value label.
        """
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._value_label)
        self._layout.addWidget(self._disable_button)
        self.setLayout(self._layout)
        
    def _setup_slider(self):
        """
        Configure the slider's properties (range, ticks, color).
        """
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        # Safely set a tick interval (avoid division by zero if ranges are small)
        interval = max(1, (self._max_value - self._min_value) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)

        self._update_slider_style(self.colour)
        self.setMinimumWidth(75)
        
    def _update_slider_style(self, colour):
        self._slider.setStyleSheet(f"""                      
                 
            QSlider::handle:vertical {{
                background: {colour};
                width: 10px;
                height: 10px;
                border-radius: 20px;
            }}
            QSlider::add-page:vertical {{
                background: #d3d3d3;
                border-radius: 2px;
            }}
        """)
        
    def _toggle_slider(self):
        
        if self._slider.isEnabled():
            self._slider.setEnabled(False)
            self._update_slider_style(self.disabled_colour)
            self._disable_button.setText("Enable")
        else:
            self._slider.setEnabled(True)
            self._update_slider_style(self.colour)
            self._disable_button.setText("Disable")

    def _update_label(self):
        """
        Update the on-screen label whenever the slider value changes.
        """
        self._value_label.setText(f"Slider: {self.get_value()}")

    def _string_by_tick(self, i):
        """
        Return the string to display next to each tick mark.
        In this default implementation, it's just the integer value.
        """
        return str(i)

    def paintEvent(self, event):
        """
        Draw tick labels for the range of values at fixed intervals.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 7))#if changed you may want to change WidgetSliders as well to allow extra space between sliders
        painter.setPen(QColor(0, 0, 0))

        # Gather slider range/tick info
        min_val = self._slider.minimum()
        max_val = self._slider.maximum()
        tick_interval = self._slider.tickInterval()

        # Calculate available space for drawing
        height = self._slider.height()
        top_off = 5
        bottom_off = 5
        effective_height = height - top_off - bottom_off

        # For each tick step, compute its position and draw text
        for i in range(min_val, max_val + 1, tick_interval):
            tick_pos = (
                height - bottom_off - (effective_height * (i - min_val)) // (max_val - min_val)
            )
            text_rect = QRect(25, tick_pos, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, self._string_by_tick(i))

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------

    def get_value(self):
        """
        Returns the current integer value of the slider.
        """
        return self._slider.value()

    def set_value(self, value):
        """
        Programmatically sets the slider to a given integer value.
        """
        self._slider.setValue(int(value))

    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external listeners.
        """
        return self._slider.valueChanged
    
        pass

#############################################################################

class DoubleSliderWithTicks(CustomSliders):
    """
    A slider that internally uses integer steps but represents
    floating-point values by applying a scale factor.
    """

    # We re-declare a PyQt signal, so it emits float instead of int.
    valueChanged = pyqtSignal(float)

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        self._scale_factor = 1000
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)
        # Connect the slider's "raw" integer changes to our float-based signal
        self._slider.valueChanged.connect(self._emit_corrected_value)

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _setup_slider(self):
        """
        Overridden to set slider's range as scaled integers. Ticks also scaled.
        """
        int_min = int(self._min_value * self._scale_factor)
        int_max = int(self._max_value * self._scale_factor)
        self._slider.setRange(int_min, int_max)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        interval = max(1, (int_max - int_min) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)

        self._update_slider_style(self.colour)
        self.setMinimumWidth(75)
        
    def _update_label(self):
        """
        Show the floating-point value with three decimal places.
        """
        self._value_label.setText(f"{self.get_value():.3f}")

    def _emit_corrected_value(self, _):
        """
        Emit the float value via self.valueChanged to external listeners.
        """
        self.valueChanged.emit(self.get_value())

    def _string_by_tick(self, i):
        """
        Convert the scaled integer to a string for tick labeling.
        """
        return str(i / self._scale_factor)
    
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------

    def get_value(self):
        """
        Return the float value, unscaled.
        """
        return self._slider.value() / self._scale_factor

    def set_value(self, value):
        """
        Set the slider to a float, using the scale factor internally.
        """
        
        scaled_val = int(value * self._scale_factor)
        self._slider.setValue(scaled_val)
        
    def set_value_exact(self, value):
        """
        Set the slider to a float, using the scale factor internally.
        """
        self.set_value(value)

    def value_changed(self):
        """
        Return the float-based signal instead of the slider's integer signal.
        """
        return self.valueChanged

##############################################################################

class EPowerSliderWithTicks(DoubleSliderWithTicks):
    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        self._base_power = 10
        super().__init__(min_value, max_value, colour, number_of_tick_intervals)

    def _update_label(self):
        """
        Display the computed exponent value in scientific notation.
        """
        self._value_label.setText(f"{self.get_value():.1e}")

    def _string_by_tick(self, i):
        """
        Show each tick label as "1E<exponent>" based on the scaled integer.
        """
        exponent = int(i / self._scale_factor)
        #exponent = i / self._scale_factor
        return f"1E{exponent}"
    
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------

    def get_value(self):
        """
        Return 10^n, where n is the float value from the slider.
        """
        n = self._slider.value() / self._scale_factor
        return self._base_power ** n
    
    def set_value_exact(self, value):
        self.set_value(math.log10(value))

#######################################################################
# -----------------------------------------------------------------------
#  Test
# -----------------------------------------------------------------------
#######################################################################
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel,
    QHBoxLayout, QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QColor


class TestSliders(QWidget):
    """
    Main widget to display and manually test all slider types
    in a less repetitive way, with properly captured QLineEdit
    text.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Manual Test")
        self.setGeometry(100, 100, 1200, 400)

        # Store [Set Value, Min, Max] inputs for each slider type
        self.slider_values = {
            'custom': [None, None, None],
            'double': [None, None, None],
            'epower': [None, None, None],
        }

        # Keep references to slider objects for set_value calls
        self.sliders = {}

        # Keep all info needed to rebuild a slider if Min or Max changes
        self.slider_info = {}

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)  # *** Increased Margins ***
        # (left, top, right, bottom)

        # 1) Custom Slider
        custom_section = self.add_slider_section(
            slider_type='custom',
            slider_class=CustomSliders,
            label_text='Custom Slider',
            min_val=-100, max_val=100, colour='blue', number_of_tick_intervals=9,
            is_float=False
        )
        main_layout.addLayout(custom_section)

        # 2) Double Slider
        double_section = self.add_slider_section(
            slider_type='double',
            slider_class=DoubleSliderWithTicks,
            label_text='Double Slider',
            min_val=-1.0, max_val=1.0, colour='green', number_of_tick_intervals=8,
            is_float=True
        )
        main_layout.addLayout(double_section)

        # 3) E-Power Slider
        epower_section = self.add_slider_section(
            slider_type='epower',
            slider_class=EPowerSliderWithTicks,
            label_text='E-Power Slider',
            min_val=-3, max_val=3, colour='red', number_of_tick_intervals=6,
            is_float=True
        )
        main_layout.addLayout(epower_section)

        self.setLayout(main_layout)

    def add_slider_section(self, slider_type, slider_class,
                           label_text, min_val, max_val, colour,
                           number_of_tick_intervals, is_float=False):
        """
        Creates a slider+label+input-box section.
        slider_type: a string identifier ('custom', 'double', etc.)
        slider_class: the QWidget-based slider class to instantiate
        label_text: text to display above the slider
        min_val, max_val, colour: parameters to pass to slider_class
        is_float: whether inputs should be float or int
        """
        # Outer vertical container
        container = QVBoxLayout()
        container.setSpacing(10)  # *** Increased Spacing ***
        container.setContentsMargins(10, 10, 10, 10)  # *** Increased Margins ***
        # (left, top, right, bottom)

        # Label
        main_label = QLabel(label_text)
        main_label.setAlignment(Qt.AlignCenter)  # *** Center Alignment ***
        main_label.setStyleSheet("font-weight: bold;")  # *** Bold Font for Emphasis ***
        container.addWidget(main_label)

        # Create the slider
        slider = slider_class(min_val, max_val, colour, number_of_tick_intervals)
        self.sliders[slider_type] = slider

        # Store info so we can rebuild if Min or Max changes
        # Note that "layout" is the horizontal layout that holds the slider
        # so we can remove/insert the slider widget there.
        self.slider_info[slider_type] = {
            "slider_class": slider_class,
            "min_val": min_val,
            "max_val": max_val,
            "colour": colour,
            "number_of_tick_intervals": number_of_tick_intervals,
            "is_float": is_float,
            "layout": None,       # We'll fill this in a moment
            "slider_widget": slider,
            "label_text": label_text
        }

        # Connect to print changes
        slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )

        # Horizontal layout: slider on the left, input fields on the right
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)  # *** Increased Spacing ***
        h_layout.setContentsMargins(10, 10, 10, 10)  # *** Increased Margins ***
        # (left, top, right, bottom)

        # *** Fixed Width for Slider Area to Prevent Expansion ***
        slider_container = QVBoxLayout()
        slider_container.setContentsMargins(0, 0, 0, 0)
        slider_container.addWidget(slider)
        # Optionally, set a fixed width or minimum width
        slider.setMinimumWidth(100)  # *** Set Minimum Width ***
        slider.setMaximumWidth(150)  # *** Set Maximum Width ***
        h_layout.addLayout(slider_container)

        # Remember the layout in slider_info so we can manipulate it later
        self.slider_info[slider_type]["layout"] = h_layout

        # A vertical layout for the three input boxes
        input_layout = QVBoxLayout()
        input_layout.setSpacing(5)  # *** Increased Spacing ***
        input_layout.setContentsMargins(10, 10, 10, 10)  # *** Increased Margins ***
        # (left, top, right, bottom)

        # "Set Value", "Min", "Max"
        input_labels = ["Set Value", "Min", "Max"]
        for i, lbl in enumerate(input_labels):
            single_input_layout = QVBoxLayout()
            single_input_layout.setSpacing(2)  # *** Increased Spacing ***
            single_input_layout.setContentsMargins(5, 5, 5, 5)  # *** Increased Margins ***
            single_input_layout.setAlignment(Qt.AlignLeft)  # Align left

            small_label = QLabel(lbl)
            small_label.setAlignment(Qt.AlignLeft)  # Ensure the label is aligned left
            small_label.setFixedHeight(20)  # *** Increased Height for Better Readability ***
            # *** Removed Font Size Adjustment ***
            # small_label.setStyleSheet("font-size: 10px;")  # *** Removed ***
            # (This line has been removed to restore the original font size)

            input_box = QLineEdit()
            input_box.setPlaceholderText(lbl)
            input_box.setFixedWidth(80)  # *** Increased Width ***
            input_box.setMaximumWidth(100)  # *** Maximum Width to Prevent Expansion ***
            input_box.setMinimumWidth(60)  # *** Minimum Width to Maintain Consistency ***

            # *** Proper Variable Binding in Lambda ***
            current_slider_type = slider_type
            current_input_index = i

            input_box.returnPressed.connect(
                lambda box=input_box, idx=current_input_index, st=current_slider_type: self.save_slider_input(
                    st, idx, box, is_float
                )
            )

            single_input_layout.addWidget(small_label)
            single_input_layout.addWidget(input_box)
            input_layout.addLayout(single_input_layout)

        # *** Spacer to Prevent Input Layout from Stretching ***
        input_layout.addStretch()

        # *** Spacer to Allocate Fixed Space and Prevent Shifting ***
        h_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))

        h_layout.addLayout(input_layout)

        container.addLayout(h_layout)

        return container

    def save_slider_input(self, slider_type, input_index, input_box, is_float):
        """
        Called when user hits 'Enter' in one of the input fields.
        Attempts to convert the text to float or int depending on
        is_float, stores it, and prints the value or error message.

        Additional rules:
          - If this is the "Set Value" field (index=0), call slider.set_value(value)
          - If this is the "Min" field (index=1), replace the old slider with
            a new one using the new min and the old max.
          - If this is the "Max" field (index=2), replace the old slider with
            a new one using the old min and the new max.
        """
        text = input_box.text()
        try:
            value = float(text) if is_float else int(text)
            self.slider_values[slider_type][input_index] = value
            print(f"{slider_type.capitalize()} input {input_index} saved: {value}")

            # If index=0 ("Set Value"), also apply it to the slider
            if input_index == 0:
                self.sliders[slider_type].set_value(value)

            # If index=1 ("Min"), rebuild slider
            elif input_index == 1:
                self.replace_slider_min(slider_type, value)

            # If index=2 ("Max"), rebuild slider
            elif input_index == 2:
                self.replace_slider_max(slider_type, value)

        except ValueError:
            print(f"Invalid input for '{slider_type}' at index {input_index}: {text}")

    def replace_slider_min(self, slider_type, new_min):
        """
        Remove the old slider, create a new one with 'new_min'
        as the minimum, and the old slider's maximum, then add
        the new slider to the layout in the same place.
        """
        info = self.slider_info[slider_type]
        old_slider = info["slider_widget"]
        layout = info["layout"]

        old_max = info["max_val"]
        colour = info["colour"]
        slider_class = info["slider_class"]
        label_text = info["label_text"]
        is_float = info["is_float"]
        number_of_tick_intervals = info["number_of_tick_intervals"]

        # Update stored min_val
        info["min_val"] = new_min

        # Remove old slider from layout
        layout.removeWidget(old_slider)
        old_slider.setParent(None)  # Optional; helps Python GC

        # Create the new slider with updated min and existing max
        new_slider = slider_class(new_min, old_max, colour, number_of_tick_intervals)
        self.sliders[slider_type] = new_slider
        info["slider_widget"] = new_slider

        # Connect the same printing logic
        new_slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )

        # Insert the new slider at index 0 in the layout
        layout.insertWidget(0, new_slider)

    def replace_slider_max(self, slider_type, new_max):
        """
        Remove the old slider, create a new one with 'new_max'
        as the maximum, and the old slider's minimum, then add
        the new slider to the layout in the same place.
        """
        info = self.slider_info[slider_type]
        old_slider = info["slider_widget"]
        layout = info["layout"]

        old_min = info["min_val"]
        colour = info["colour"]
        slider_class = info["slider_class"]
        label_text = info["label_text"]
        is_float = info["is_float"]
        number_of_tick_intervals = info["number_of_tick_intervals"]

        # Update stored max_val
        info["max_val"] = new_max

        # Remove old slider from layout
        layout.removeWidget(old_slider)
        old_slider.setParent(None)  # Optional; helps Python GC

        # Create the new slider with existing min and updated max
        new_slider = slider_class(old_min, new_max, colour, number_of_tick_intervals)
        self.sliders[slider_type] = new_slider
        info["slider_widget"] = new_slider

        # Connect the same printing logic
        new_slider.value_changed().connect(
            lambda val, label=label_text: print(f"{label} Changed: {val}")
        )

        # Insert the new slider at index 0 in the layout
        layout.insertWidget(0, new_slider)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestSliders()
    window.setWindowTitle("CustomSliders Manual Testing")  # Set the window title
    window.show()
    sys.exit(app.exec_())
