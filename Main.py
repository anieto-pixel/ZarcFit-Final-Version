"""
  The primary container for the application UI, assembling all widgets:
    - File input/output
    - Sliders
    - Buttons
    - Graph display
    - Model (ModelManual) for computations
"""


import os
import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter,QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt

# Updated Imports with Renamed Classes
from ConfigImporter import ConfigImporter
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ModelCalculator import ModelCalculator
from ModelManual import ModelManual
from WidgetOutputFile import WidgetOutputFile
from WidgetInputFile import WidgetInputFile
from WidgetSliders import WidgetSliders
from WidgetButtonsRow import WidgetButtonsRow
from WidgetGraphs import WidgetGraphs



class MainWidget(QWidget):

    def __init__(self, config_file: str):
        super().__init__()

        # Parse config settings
        self.config = ConfigImporter(config_file)

        # Data placeholders for file & model outputs
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}
        self.modeled_data = {"freq": None, "Z_real": None, "Z_imag": None}

        # Initialize core widgets
        self.widget_input_file = WidgetInputFile(config_file)
        self.widget_output_file = WidgetOutputFile()
        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )
        
        self.widget_buttons = WidgetButtonsRow()
        self.widget_graphs = WidgetGraphs()

        # Model for manual and automatic computations
        self.model_manual = ModelManual(
            list(self.config.slider_configurations.keys()),
            self.config.slider_default_values
        )
        
        self.model_calculator = ModelCalculator(
            list(self.config.slider_configurations.keys()),
            self.config.slider_default_values,
            self.file_data
        )

        # Layout the UI
        self._initialize_ui()

        # Connect signals
        #Connecting hotkeays
        self._initialize_hotkeys()
        
        #Updates dictionaries in main
        self.widget_input_file.file_data_updated.connect(self._update_file_data)
        self.model_manual.modeled_data_updated.connect(self._update_modeled_data)
        self.model_calculator.modeled_data_updated.connect(self._update_modeled_data)
        
        #connects manual model to the values in the sliders
        self.widget_sliders.slider_value_updated.connect(self.model_manual.update_variable)
        
        #connects both models to eachother and the sliders so vairables are consistent
        self.model_manual.modeled_data_variables_updated.connect(self.model_calculator.listen_change_variables_signal)
        self.model_calculator.modeled_data_variables_updated.connect(self.model_manual.listen_change_variables_signal)
        self.model_calculator.modeled_data_variables_updated.connect(self.widget_sliders.update_all_variables)


        # Hot Keys
        


    # -----------------------------------------------------------------------
    #  Private UI Methods
    # -----------------------------------------------------------------------

    def _initialize_ui(self):
        """
        Assembles the main layout, placing the top bar and bottom splitter.
        """
        # Top bar with input/output widgets
        self.top_bar_widget = self._create_file_options_widget()

        # Bottom area: sliders + buttons side by side
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.widget_sliders)
        bottom_half_layout.addWidget(self.widget_buttons)
        bottom_half_widget = self._create_widget_from_layout(bottom_half_layout)

        # Splitter: top for graphs, bottom for sliders+buttons
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.widget_graphs)
        splitter.addWidget(bottom_half_widget)
        splitter.setSizes([500, 300])

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_bar_widget)
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(main_layout)

    def _create_file_options_widget(self) -> QWidget:
        """
        Builds the top bar containing the file input and file output widgets.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.widget_input_file)
        layout.addStretch()
        layout.addWidget(self.widget_output_file)
        layout.setContentsMargins(0, 0, 0, 0)
        return self._create_widget_from_layout(layout)

    def _create_widget_from_layout(self, layout: QHBoxLayout) -> QWidget:
        """
        Helper to wrap a given layout into a QWidget.
        """
        container = QWidget()
        container.setLayout(layout)
        return container
    
    # -----------------------------------------------------------------------
    #  Private Conections Methods
    # -----------------------------------------------------------------------
    
    def _initialize_hotkeys(self):
        
        shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
        shortcut_f1.activated.connect(lambda: self.model_calculator._fit_model())
        
        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(lambda: self.model_calculator._fit_model())
        
        #f3 is re-show hidden frequencies
        
        shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        shortcut_f4.activated.connect(lambda: self._print_model_parameters())
        
        shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_f5.activated.connect(lambda: self._print_model_parameters())
        
        #f7 is to read values from outphut file
        
        #f8 default stats
        
        #pages up and down, deleting high and low frequencies
        
        #f11 and f12, the tailthing
        
        
        
    
    def _print_model_parameters(self):
        """
        Called when Print is requested 
        """
        content, header= self.model_calculator.print_model_parameters()
        self.widget_output_file.write_to_file(content, header)
    
    
    def _update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when WidgetInputFile emits new file data.
        """
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_graphs(freq, Z_real, Z_imag)
        self.model_manual.initialize_frequencies(freq)
        self.model_calculator.reset_experiment_values(self.file_data)

    def _update_modeled_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when ModelManual finishes recalculating with new slider values.
        """
        self.modeled_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_manual_plot(freq, Z_real, Z_imag)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels (Refactored)")
    #window.setGeometry(100, 100, 800, 900)
    window.show()

    sys.exit(app.exec_())