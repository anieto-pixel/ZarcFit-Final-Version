"""
Optimized MainWidget and ConfigImporter Classes
"""
# Main.py

import os
import sys
import logging
import inspect
import numpy as np
from sympy import pi
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QShortcut
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QFontMetrics, QFont

# Updated Imports with Renamed Classes
from ConfigImporter import ConfigImporter
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ModelManual import ModelManual
from WidgetOutputFile import WidgetOutputFile
from WidgetInputFile import WidgetInputFile
from WidgetSliders import WidgetSliders
from WidgetButtonsRow import WidgetButtonsRow
from WidgetGraphs import WidgetGraphs
from WidgetTextBar import WidgetTextBar

class MainWidget(QWidget):
    """
    The main application window, responsible for:
      - File I/O widgets
      - Graph display
      - Sliders
      - Bottom text bar
      - Delegating all formula math to ModelManual
    """
    def __init__(self, config_file: str):
        super().__init__()

        # Initialize config + importer
        self.config = ConfigImporter(config_file)

        # Sliders dictionary
        self.v_sliders = dict(zip(
            self.config.slider_configurations.keys(),
            self.config.slider_default_values
        ))

        # Timer for debouncing slider updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_sliders_data)
        self.pending_updates = {}

        # Initialize ModelManual
        from ModelManual import ModelManual  # or remove if in same file
        self.model_manual = ModelManual(self.config)

        # We'll store file data from the input widget
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}

        # Create the top-level widgets
        self.widget_input_file = WidgetInputFile(self.config.input_file_widget_config)
        self.widget_output_file = WidgetOutputFile()
        self.widget_graphs = WidgetGraphs()
        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )
        self.widget_buttons = WidgetButtonsRow()
        self.widget_at_bottom = WidgetTextBar(
            # We can pass the keys we want displayed
            self.config.parallel_model_secondary_variables.keys()
        )

        # Connect signals
        self._connect_signals()

        # Layout
        self._initialize_ui()

        # Possibly set up file paths from config
        self.widget_input_file.setup_current_file(self.config.input_file)
        self.widget_output_file.setup_current_file(self.config.output_file)

        # Initialize ModelManual frequencies
        # (If freq is loaded from file, you can do it in _update_file_data)
        dummy_freqs = np.array([1,10,100,1000,10000])
        self.model_manual.initialize_frequencies(dummy_freqs)

        # Do an initial run so everything is in sync
        self._update_sliders_data()

    # -----------------------------------------------------------------------
    #  Private UI Methods
    # -----------------------------------------------------------------------
    def _initialize_ui(self):
        """
        Assembles the main layout, placing the top bar and bottom splitter.
        """
        top_bar_widget = self._create_file_options_widget()

        # Bottom area: sliders + buttons side by side
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.widget_sliders)
        bottom_half_layout.addWidget(self.widget_buttons)
        bottom_half_layout.setContentsMargins(0, 0, 0, 0)
        bottom_half_layout.setSpacing(0)
        bottom_half_widget = QWidget()
        bottom_half_widget.setLayout(bottom_half_layout)

        # Bottom-most area: bottom area + text bar
        bottom_and_text_layout = QVBoxLayout()
        bottom_and_text_layout.addWidget(bottom_half_widget)
        bottom_and_text_layout.addWidget(self.widget_at_bottom)
        bottom_and_text_widget = QWidget()
        bottom_and_text_widget.setLayout(bottom_and_text_layout)

        # Splitter: top for graphs, bottom for sliders+buttons+text
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.widget_graphs)
        splitter.addWidget(bottom_and_text_widget)
        splitter.setSizes([500, 300])

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_bar_widget)
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

        container = QWidget()
        container.setLayout(layout)
        return container

    # -----------------------------------------------------------------------
    #  Private Helper Methods
    # -----------------------------------------------------------------------
    def _connect_signals(self):
        """
        Sets up signal connections for file data, output, sliders, etc.
        """
        # Listen for new input file data
        self.widget_input_file.file_data_updated.connect(self._update_file_data)

        # Connect output file selection
        self.widget_output_file.output_file_selected.connect(
            self.config.set_output_file
        )

        # Connect slider updates
        self.widget_sliders.slider_value_updated.connect(self._handle_slider_update)

        # Connect the model to the graph: we only update the 'manual' line
        # (The 'base' line is updated in _update_file_data or set manually)
        self.model_manual.model_manual_updated.connect(
            self.widget_graphs.update_manual_plot
        )

        # Optionally add hotkeys
        self._initialize_hotkeys()

    def _initialize_hotkeys(self):
        """
        Initializes keyboard shortcuts (example).
        """
        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(lambda: self.model_manual.run_model(self.v_sliders))

    def _update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when WidgetInputFile emits new file data.
        """
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        # Update 'base' data in the graphs
        self.widget_graphs.update_graphs(freq, Z_real, Z_imag)
        # Tell the model about the new freq array
        self.model_manual.initialize_frequencies(freq)

        # Save config
        self.config.set_input_file(self.widget_input_file.get_current_file_path())

    def _handle_slider_update(self, key, value):
        """
        Batches slider updates using a short debounce.
        """
        self.pending_updates[key] = value
        self.update_timer.start(5)  # 5ms debounce

    def _update_sliders_data(self):
        """
        Called once the debounce timer fires:
        - We update self.v_sliders
        - We run the model in ModelManual
        - We get the newly computed secondaries and show them
        """
        # 1) Merge the slider updates into self.v_sliders
        for k, v in self.pending_updates.items():
            self.v_sliders[k] = v
        self.pending_updates.clear()

        # 2) Run the model, which also calculates secondaries
        self.model_manual.run_model(self.v_sliders)

        # 3) Grab the newly calculated secondaries to display in bottom text
        v_second = self.model_manual.get_latest_secondaries()
        self.widget_at_bottom._update_text(v_second)


        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels (Optimized)")
    
    window.setGeometry(0, 0, 800, 00)  # Set the initial size and position (x=0, y=0, width=800, height=600)
    window.show()

    sys.exit(app.exec_())
