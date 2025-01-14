
import sys
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics

# Updated import for your custom sliders
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class WidgetSliders(QWidget):
    """
    A widget that displays multiple sliders side by side, each labeled
    with a key and color-coded. Emits the signal `slider_value_updated`
    whenever any slider's value changes.

    Parameters
    ----------
    slider_configurations : dict
      A dict where keys are slider names (str),
      and values are tuples describing the slider setup:
          (slider_class, min_value, max_value, color).

    slider_default_values : list
      A list of default values, in the same order as
      slider_configurations.keys().
    """

    slider_value_updated = pyqtSignal(str, float)

    def __init__(self, slider_configurations: dict, slider_default_values: list):
        super().__init__()

        # Store default values in a dictionary matching each slider key
        self.slider_default_values = dict(
            zip(slider_configurations.keys(), slider_default_values)
        )

        # Create sliders and ensure each is wide enough for 6-digit labels
        self.sliders = self._create_sliders(slider_configurations)

        # Initialize sliders to default values
        self.set_default_values()

        # Build the UI
        self._setup_layout(slider_configurations)
        self._connect_signals()

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    def _create_sliders(self, slider_configurations):
        """
        Creates each slider widget. Also calculates a minimum width sufficient
        to display a "1E-999999" label (6-digit) plus extra space for tick marks.
        """
        sliders = {}

        # 1) Decide on the largest label text you'd need for six digits:
        test_label_text = "-999999999"
        test_label = QLabel(test_label_text)
        font_metrics = QFontMetrics(test_label.font())

        # 2) Measure how wide that text is in pixels
        text_width = font_metrics.horizontalAdvance(test_label_text)

        # 3) Add some margin for painting tick labels at x=30 in CustomSliders
        #    and so the text won't get cut off if we go slightly bigger
        needed_width = text_width

        for key, (slider_type, min_value, max_value, color) in slider_configurations.items():
            slider_widget = slider_type(min_value, max_value, color)

            # 4) Force the slider's minimum width so labels/ticks won't be truncated
            slider_widget.setMinimumWidth(needed_width)

            sliders[key] = slider_widget
        return sliders

    def _setup_layout(self, slider_configurations):
        """
        Creates a horizontal layout and places each slider (and its label)
        in a vertical sub-layout.
        """
        main_layout = QHBoxLayout()

        for key, slider in self.sliders.items():
            # Sub-layout for each labeled slider
            slider_layout = QVBoxLayout()
            label = QLabel(key)
            label.setAlignment(Qt.AlignCenter)

            # Style the label to match the slider's color
            slider_color = slider_configurations[key][3]
            label.setStyleSheet(f"color: {slider_color}; font-weight: bold;")

            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)

            main_layout.addLayout(slider_layout)

        # Add some spacing on the right
        main_layout.setContentsMargins(0, 0, 15, 0)

        self.setLayout(main_layout)

    def _connect_signals(self):
        """
        Connects each slider's value_changed signal to our
        slider_value_updated signal, passing the slider's key.
        """
        for key, slider in self.sliders.items():
            slider.value_changed().connect(partial(self.slider_value_updated.emit, key))

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_slider(self, key):
        """Retrieves a slider by its key."""
        return self.sliders.get(key)
    
    def get_sliders_keys(self):
        """Retrieves a slider by its key."""
        return self.sliders.keys()

    def set_default_values(self):
        """Resets all sliders to their default positions."""
        for key, default_value in self.slider_default_values.items():
            slider = self.sliders[key]
            slider.set_value(default_value)
            
    def update_all_variables(self, dictionary):
        """
        Receives a dict of { variable_key: value }, checks that it matches
        this widget's slider keys, then updates each slider.
        """
        # 1) Ensure keys match
        if set(dictionary.keys()) != set(self.sliders.keys()):
            raise ValueError(
                "Incoming dictionary keys do not match the slider keys in WidgetSliders."
            )

        # 2) Update each slider
        for key, val in dictionary.items():
            slider = self.sliders[key]
            slider.set_value(val)
            

# -----------------------------------------------------------------------
#  Quick Test
# -----------------------------------------------------------------------
if __name__ == "__main__":
    from ConfigImporter import ConfigImporter  # Only needed if testing
    from PyQt5.QtWidgets import QPushButton
    
    #0 . method that sets all the sliders to 0, hopefully
    def set_all_to_0(sliders_widget):
        old_dict= sliders_widget.sliders
        
        new_dict = {k: 0.0 for k in old_dict.keys()}
        sliders_widget.update_all_variables(new_dict)

    app = QApplication(sys.argv)

    # 1. Load config
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # 2. Create WidgetSliders
    sliders_widget = WidgetSliders(config.slider_configurations, config.slider_default_values)
    
    # 3. Create Button Widget
    btn_set_0 = QPushButton("Set All Model Vars to 0.0")
    btn_set_0.clicked.connect(set_all_to_0)
    
    # 4. Create Test Widget
    test_window = QWidget()
    test_window.setWindowTitle("Test ModelManual & WidgetSliders")
    test_window.setGeometry(100, 100, 1200, 600)

    main_layout = QVBoxLayout(test_window)
    main_layout.addWidget(sliders_widget)
    main_layout.addWidget(btn_set_0)
    
    # Connect the signal to a simple print function
    sliders_widget.slider_value_updated.connect(print)
    btn_set_0.clicked.connect(lambda: set_all_to_0(sliders_widget))

    test_window.show()
    sys.exit(app.exec_())
    
    
    