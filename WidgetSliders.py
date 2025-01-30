
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
    slider_was_disabled = pyqtSignal(str, bool)
    all_sliders_reseted = pyqtSignal(dict)

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

    def _signal_all_sliders_reseted(self):
        pass

    def _create_sliders(self, slider_configurations):
        """
        Creates each slider widget and ensures the button fits completely.
        """
        sliders = {}

        for key, (slider_type, min_value, max_value, color, number_of_tick_intervals) in slider_configurations.items():
            
            slider_widget = slider_type(min_value, max_value, color, number_of_tick_intervals)
            slider_widget.setMinimumWidth(slider_widget._calculate_button_width())  # Ensure button fits fully
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
            
        for key, slider in self.sliders.items():
            # The slider has a signal called iWasToggled (bool) perhaps
            slider.was_disabled.connect(partial(self.slider_was_disabled.emit, key))
 

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_slider(self, key):
        """Retrieves a slider by its key."""
        return self.sliders.get(key)
    
    def get_sliders_keys(self):
        """Retrieves a slider by its key."""
        return self.sliders.keys()

    def get_all_values(self):
        dict_to_emit={} 
        
        for key, default_value in self.slider_default_values.items():
            slider = self.sliders[key] 
            dict_to_emit[key]=slider.get_value()

        return dict_to_emit

    def set_default_values(self):
        """Resets all sliders to their default positions."""
        
        dict_to_emit={}
        
        for key, default_value in self.slider_default_values.items():
        
            slider = self.sliders[key]
            slider.set_value(default_value)
            
            dict_to_emit[key]=slider.get_value()

            
        self.all_sliders_reseted.emit(dict_to_emit)
            
    def set_all_variables(self, dictionary):
        """
        Receives a dict of { variable_key: value }, checks that it matches
        this widget's slider keys, then updates each slider.
        """
        print("update all variables")
        
        # 1) Ensure keys match
        if set(dictionary.keys()) != set(self.sliders.keys()):
            raise ValueError(
                "Incoming dictionary keys do not match the slider keys in WidgetSliders."
            )

        # 2) Update each slider and emit
        dict_to_emit={}
        for key, val in dictionary.items():
            
            slider = self.sliders[key]
            slider.set_value_exact(val)
            dict_to_emit[key]=slider.get_value()
            
        self.all_sliders_reseted.emit(dict_to_emit)
            

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
        sliders_widget.set_all_variables(new_dict)

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
    sliders_widget.slider_was_disabled.connect(print)
    btn_set_0.clicked.connect(lambda: set_all_to_0(sliders_widget))

    test_window.show()
    sys.exit(app.exec_())
    
    
    