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
from RangeSlider import RangeSlider
from ModelManual import ModelManual
from WidgetOutputFile import WidgetOutputFile
from WidgetInputFile import WidgetInputFile
from WidgetSliders import WidgetSliders
from WidgetButtonsRow import WidgetButtonsRow
from WidgetGraphs import WidgetGraphs
from WidgetTextBar import WidgetTextBar

class MainWidget(QWidget):

    def __init__(self, config_file: str):
        super().__init__()

        """ini file related"""
        # Initialize ConfigImporter
        self.config = ConfigImporter(config_file)

        """Data atributes"""
        # Data placeholders for file & model outputs
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}

        # Dictionary of variables
        self.v_sliders = dict(zip(self.config.slider_configurations.keys(),
                                  self.config.slider_default_values))  # variables of the sliders
        
        """Initialize core widgets"""
        #print(self.config.input_file)
        self.widget_input_file = WidgetInputFile(self.config.input_file_widget_config)
        self.widget_output_file = WidgetOutputFile(self.config.variables_to_print)

        self.widget_graphs = WidgetGraphs()
        self.freq_slider=RangeSlider()

        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )

        self.widget_buttons = WidgetButtonsRow()
        
        self.widget_at_bottom = WidgetTextBar(
            #self.config.series_secondary_variables.keys(), 
            self.config.parallel_model_secondary_variables.keys()
        )

        """Initialize Models"""
        # Model for manual and automatic computations
        self.model_manual = ModelManual()


        """Optimize Sliders Signaling"""
        # Initialize a timer for debouncing slider updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_sliders_data)
        self.pending_updates = {}
        self.value_labels = {}

        # Layout the UI
        self._initialize_ui()

        """Connect signals """
        """may become its own method later on, but not now"""

        # Listens for new input file selected. Updates dictionaries, graphs and config.ini
        self.widget_input_file.file_data_updated.connect(self._update_file_data)

        #Listens for new output file selected.Updates config.ini
        self.widget_output_file.output_file_selected.connect(self.config.set_output_file)

        # Connects sliders to update handler, with debouncing
        self.widget_sliders.slider_value_updated.connect(self._handle_slider_update)
        
        # Connects freq slider to handle_frequencies method
        self.freq_slider.sliderMoved.connect(self._handle_frequency_update)
        
        # Connects model manual with handler (for now)
        self.model_manual.model_manual_updated.connect(self.widget_graphs.update_manual_plot)

        # Connecting hotkeys
        self._initialize_hotkeys()

        "initialization 2.0 I guess? No fucking idea of how to roganize this part"
        self.widget_input_file.setup_current_file(self.config.input_file)
        self.widget_output_file.setup_current_file(self.config.output_file)
        #here I shall initialize the secondary variables and all that 
        
    # -----------------------------------------------------------------------
    #  Private UI Methods
    # -----------------------------------------------------------------------
    def _initialize_ui(self):
        """
        Assembles the main layout, placing the top bar and bottom splitter.
        """
        # Top bar with input/output widgets
        top_bar_widget = self._create_file_options_widget()
    
        # Bottom area: sliders + buttons side by side
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.addWidget(self.widget_sliders)
        bottom_half_layout.addWidget(self.widget_buttons)
        bottom_half_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to save space
        bottom_half_layout.setSpacing(0)  # Remove spacing to save space
    
        bottom_half_widget = QWidget()
        bottom_half_widget.setLayout(bottom_half_layout)
    
        # Bottom-most area: bottom area + text
        bottom_and_text_layout = QVBoxLayout()
        bottom_and_text_layout.addWidget(bottom_half_widget)
        bottom_and_text_layout.addWidget(self.widget_at_bottom)
        bottom_and_text_widget = QWidget()
        bottom_and_text_widget.setLayout(bottom_and_text_layout)
    
        # Middle: Frequency sliders + graphs
        freq_slider_layout = QVBoxLayout()
        freq_slider_layout.addWidget(self.freq_slider)
        freq_slider_layout.setContentsMargins(0, 0, 0, 0)  # Ensure no extra margins
        freq_slider_layout.setSpacing(5)  # Adjust spacing if needed for better visual appeal
    
        middle_layout = QHBoxLayout()
        middle_layout.addLayout(freq_slider_layout)
        middle_layout.setAlignment(freq_slider_layout, Qt.AlignLeft)
        middle_layout.setSpacing(0)  # remove spacing
        middle_layout.addWidget(self.widget_graphs)
        middle_layout.setContentsMargins(0, 0, 0, 0)  # Ensure no additional left margin
    
        middle_widget = QWidget()
        middle_widget.setLayout(middle_layout)
    
        # Splitter: top for graphs, bottom for sliders+buttons
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(middle_widget)
        splitter.addWidget(bottom_and_text_widget)
        splitter.setSizes([500, 300])
    
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_bar_widget)
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Overall margins for the main layout
    
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

    def _initialize_hotkeys(self):
        """
        Initializes keyboard shortcuts.
        """
        shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
        shortcut_f1.activated.connect(lambda: self.model_manual.fit_model_cole(self.v_sliders))
        
        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(lambda: self.model_manual.fit_model_bode(self.v_sliders))

        #f3 is supposed to reset to "all frequencies"

        shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        shortcut_f4.activated.connect(self._print_model_parameters)

        shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_f5.activated.connect(self._print_model_parameters)
        
        shortcut_f6 = QShortcut(QKeySequence(Qt.Key_F6), self)
        shortcut_f6.activated.connect(self.widget_input_file._show_previous_file)
        
        shortcut_f7 = QShortcut(QKeySequence(Qt.Key_F7), self)
        shortcut_f7.activated.connect(self.widget_input_file._show_next_file)
        
        shortcut_f8 = QShortcut(QKeySequence(Qt.Key_F8), self)
        shortcut_f8.activated.connect(self._handle_set_default)

        shortcut_page_down = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        shortcut_page_down.activated.connect(self.freq_slider.downMax)
    
        shortcut_page_up = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        shortcut_page_up.activated.connect(self.freq_slider.upMin)

    # -----------------------------------------------------------------------
    #  Private Connections Methods. Listeners and Handlers
    # -----------------------------------------------------------------------

    def _update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when WidgetInputFile emits new file data.
        """
        #print("signal was received")
        
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_graphs(freq, Z_real, Z_imag)
        self.model_manual.initialize_expdata(self.file_data)
        
        self._update_sliders_data()
        
        self.config.set_input_file(self.widget_input_file.get_current_file_path())

    def _handle_slider_update(self, key, value):
        """
        Handles incoming slider updates by storing them and starting the debounce timer.
        """
        self.pending_updates[key] = value
        self.update_timer.start(5)  # Adjust the timeout as needed

    def _update_sliders_data(self):
        """
        Processes all pending slider updates at once.
        """
        # Update slider values
        for key, value in self.pending_updates.items():
            self.v_sliders[key] = value
        self.pending_updates.clear()

        # Run the model, which also calculates secondaries
        self.model_manual.run_model_manual(self.v_sliders)

        # Grab the newly calculated secondaries to display in bottom text
        v_second = self.model_manual.get_latest_secondaries()
        
        self.widget_at_bottom._update_text(v_second)
        
    def _handle_frequency_update(self, bottom, top):
        
        freq = self.file_data["freq"]  # Assume freq is a list of frequencies
    
        # Initialize index_bottom to start from the last index (highest frequency)
        index_bottom = len(freq) - 1
        while index_bottom > 0 and freq[index_bottom] < bottom:
            index_bottom -= 1
    
        # Initialize index_top to start from the first index (lowest frequency)
        index_top = 0
        while index_top < len(freq) and freq[index_top] > top:
            index_top += 1  # Increment index_top to avoid infinite loop

        # Ensure index_top and index_bottom are within bounds
        index_top = min(len(freq) - 1, index_top)
        index_bottom = max(0, index_bottom)
    
        # Create a mask to filter the arrays
        freq_filtered = freq[index_top:index_bottom + 1] 
        z_real_filtered = freq[index_top:index_bottom + 1] 
        z_imag_filtered = freq[index_top:index_bottom + 1] 

        new_data = { "freq": freq_filtered,"Z_real": z_real_filtered,"Z_imag": z_imag_filtered}

        self.model_manual.initialize_expdata(new_data)
        self.widget_graphs.apply_filter_frequency_range(bottom, top)
        
    def _handle_set_default(self):
        
        self.freq_slider.default()
        self.widget_graphs.update_graphs(
            self.file_data['freq'], 
            self.file_data['Z_real'], 
            self.file_data['Z_imag']
            )
        self.model_manual.initialize_expdata(self.file_data)
        
        self._update_sliders_data()




    def _print_model_parameters(self):
        """
        Called when Print is requested 
        
        (will have to figure out how to get all the dictionaries called, etc)
        """
        content, header = self.model_manual.print_model_parameters()
        self.widget_output_file.write_to_file(content, header)

        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels (Optimized)")
    
    window.setGeometry(0, 0, 1000, 900)  # Set the initial size and position (x=0, y=0, width=800, height=600)
    window.show()

    sys.exit(app.exec_())
