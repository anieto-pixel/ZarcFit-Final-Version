"""
Optimized MainWidget and ConfigImporter Classes
"""

import os
import sys
import numpy as np
from sympy import sympify, symbols, lambdify, pi
from sympy.core.sympify import SympifyError
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

    def __init__(self, config_file: str):
        super().__init__()

        """ini file related"""
        # Parse config settings
        self.config = ConfigImporter(config_file)

        # Pre-compile SymPy expressions
        self.compiled_expressions = {}
        self.dependent_compiled_expressions = {}
        self._compile_secondary_expressions()

        """Data attributes"""
        # Data placeholders for file & model outputs
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}
        self.modeled_data = {"freq": None, "Z_real": None, "Z_imag": None}

        # Dictionary of variables
        self.v_sliders = dict(zip(self.config.slider_configurations.keys(),
                                  self.config.slider_default_values))  # variables of the sliders
        self.v_second = {}  # variables secondary 

        """Initialize core widgets"""
        self.widget_input_file = WidgetInputFile(config_file)
        self.widget_output_file = WidgetOutputFile()

        self.widget_graphs = WidgetGraphs()

        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )

        self.widget_buttons = WidgetButtonsRow()

        self.widget_at_bottom = WidgetTextBar(self.config.series_secondary_variables.keys(), 
                                              self.config.parallel_model_secondary_variables.keys()
                                              )

        """Initialize Models"""
        # Model for manual and automatic computations
        self.model_manual = ModelManual(
            list(self.config.slider_configurations.keys()),
            self.config.slider_default_values
        )

        """Optimize Sliders Signaling"""
        # Initialize a timer for debouncing slider updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_slider_updates)
        self.pending_updates = {}
        self.value_labels = {}

        """Methods"""

        # Calculate secondary variables initially
        self._calculate_secondary_variables()
        self.widget_at_bottom._update_text(self.v_second)

        # Layout the UI
        self._initialize_ui()

        ### Connect signals ###
        # Connecting hotkeys
        self._initialize_hotkeys()

        # Updates dictionaries in main
        self.widget_input_file.file_data_updated.connect(self._update_file_data)

        # Connects sliders to update handler with debouncing
        self.widget_sliders.slider_value_updated.connect(self._handle_slider_update)

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
        bottom_half_widget = self._create_widget_from_layout(bottom_half_layout)

        # Bottom-most area: bottom area + text
        bottom_and_text_layout = QVBoxLayout()
        bottom_and_text_layout.addWidget(bottom_half_widget)
        bottom_and_text_layout.addWidget(self.widget_at_bottom)
        bottom_and_text_widget = self._create_widget_from_layout(bottom_and_text_layout)

        # Splitter: top for graphs, bottom for sliders+buttons
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
        return self._create_widget_from_layout(layout)


    def _create_widget_from_layout(self, layout: QHBoxLayout) -> QWidget:
        """
        Helper to wrap a given layout into a QWidget.
        """
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
        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(lambda: self.model_manual._fit_model())

        shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        shortcut_f4.activated.connect(self._print_model_parameters)

        shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_f5.activated.connect(self._print_model_parameters)

    def _compile_secondary_expressions(self):
        """
        Compiles the SymPy expressions for secondary variables to speed up evaluations.
        Processes independent and dependent variables based on configuration sections.
        """
        self.compiled_expressions = {}
        self.dependent_compiled_expressions = {}

        try:
            # Define symbols for primary slider variables
            primary_vars = list(self.config.slider_configurations.keys())
            self.symbols_dict = symbols(primary_vars)
            self.symbols_list = list(self.symbols_dict)
        except Exception as e:
            print(f"Error initializing symbols: {e}")
            return

        # Process SeriesSecondaryVariables (independent)
        for var, expr in self.config.series_secondary_variables.items():
            try:
                sympy_expr = sympify(expr)
                # Create a lambda function using 'numpy' for numerical operations
                func = lambdify(self.symbols_list, sympy_expr, 'numpy')
                self.compiled_expressions[var] = func
            except SympifyError as e:
                print(f"Error parsing equation for {var}: {e}")
                self.compiled_expressions[var] = None
            except Exception as e:
                print(f"Unexpected error compiling equation for {var}: {e}")
                self.compiled_expressions[var] = None

        # Process ParallelModelSecondaryVariables (dependent) by compiling them
        for var, expr in self.config.parallel_model_secondary_variables.items():
            try:
                sympy_expr = sympify(expr)
                # Include both primary and secondary variables in symbols
                all_vars = self.symbols_list + list(self.config.series_secondary_variables.keys())
                func = lambdify(all_vars, sympy_expr, 'numpy')
                self.dependent_compiled_expressions[var] = func
            except SympifyError as e:
                print(f"Error parsing equation for {var}: {e}")
                self.dependent_compiled_expressions[var] = None
            except Exception as e:
                print(f"Unexpected error compiling equation for {var}: {e}")
                self.dependent_compiled_expressions[var] = None

    def _handle_slider_update(self, key, value):
        """
        Handles incoming slider updates by storing them and starting the debounce timer.
        """
        self.pending_updates[key] = value
        self.update_timer.start(50)  # Adjust the timeout as needed

    def _process_slider_updates(self):
        """
        Processes all pending slider updates at once.
        """
        # Update slider values
        for key, value in self.pending_updates.items():
            self.v_sliders[key] = value
        self.pending_updates.clear()

        # Recalculate secondary variables
        self._calculate_secondary_variables()

        # Update the UI labels
        for var, val in self.v_second.items():
            if var in self.value_labels:
                if val is not None:
                    # Format the value to 4 significant figures
                    formatted_val = f"{val:.4g}"
                    self.value_labels[var].setText(formatted_val)
                else:
                    # Display 'Error' if the value is None or invalid
                    self.value_labels[var].setText("Error")

    def _calculate_secondary_variables(self):
        """
        Calculates secondary variables using pre-compiled and dependent expressions.
        """
        if not self.compiled_expressions and not self.dependent_compiled_expressions:
            print("No compiled expressions available.")
            return

        self.v_second = {}
        slider_values = [self.v_sliders[key] for key in self.config.slider_configurations.keys()]

        # Compute independent secondary variables (SeriesSecondaryVariables)
        for var, func in self.compiled_expressions.items():
            if func is not None:
                try:
                    result = func(*slider_values)
                    if isinstance(result, complex):
                        # Take the real part if result is complex
                        self.v_second[var] = float(result.real)
                    elif isinstance(result, (int, float, np.float64, np.int64)):
                        self.v_second[var] = float(result)
                    else:
                        # Attempt to convert, catch potential errors
                        self.v_second[var] = float(result)
                except Exception:
                    # In case of any error, set to None
                    self.v_second[var] = None
            else:
                # If no compiled function, set to None
                self.v_second[var] = None

        # Prepare arguments for dependent expressions
        # Assuming dependent expressions may depend on both primary sliders and independent secondaries
        dependent_args = slider_values + [self.v_second.get(var, 0) for var in self.config.series_secondary_variables.keys()]

        # Compute dependent secondary variables (ParallelModelSecondaryVariables)
        for var, func in self.dependent_compiled_expressions.items():
            if func is not None:
                try:
                    result = func(*dependent_args)
                    if isinstance(result, complex):
                        self.v_second[var] = float(result.real)
                    elif isinstance(result, (int, float, np.float64, np.int64)):
                        self.v_second[var] = float(result)
                    else:
                        self.v_second[var] = float(result)
                except Exception:
                    self.v_second[var] = None
            else:
                self.v_second[var] = None

        # At this point, self.v_second contains all secondary variables with computed values

    # -----------------------------------------------------------------------
    #  Private Connections Methods
    # -----------------------------------------------------------------------

    def _print_model_parameters(self):
        """
        Called when Print is requested 
        """
        content, header = self.model_manual.print_model_parameters()
        self.widget_output_file.write_to_file(content, header)

    def _update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when WidgetInputFile emits new file data.
        """
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_graphs(freq, Z_real, Z_imag)
        self.model_manual.initialize_frequencies(freq)
        # Assuming model_manual triggers necessary updates

    def _update_modeled_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Called when ModelManual finishes recalculating with new slider values.
        """
        self.modeled_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_manual_plot(freq, Z_real, Z_imag)

    def _update_variable(self, key, value):
        """
        Updates the value of primary and secondary variables.
        """
        self.v_sliders[key] = value
        self._calculate_secondary_variables()
        self.widget_at_bottom._update_text(self.v_second)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_file = "config.ini"

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("Slider with Ticks and Labels (Optimized)")
    window.show()

    sys.exit(app.exec_())
