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

from sympy import sympify, symbols, lambdify
from sympy.core.sympify import SympifyError

from PyQt5.QtWidgets import * #clean up with IA eventually
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import * #clean up with IA eventually

# Updated Imports with Renamed Classes
from ConfigImporter import ConfigImporter
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
#from ModelCalculator import ModelCalculator
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
        
        # Pre-compile SymPy expressions
        self.compiled_expressions = {}
        self._compile_secondary_expressions()

        # Data placeholders for file & model outputs
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}
        self.modeled_data = {"freq": None, "Z_real": None, "Z_imag": None}
        
        # Dictionary of variables
        self.v_sliders=dict(zip(self.config.slider_configurations.keys(),self.config.slider_default_values)) #variables of the sliders
        self.v_second={} #variables secondary 

        #print(self.config.slider_configurations.keys())

        # Initialize core widgets #
        self.widget_input_file = WidgetInputFile(config_file)
        self.widget_output_file = WidgetOutputFile()
        self.widget_graphs = WidgetGraphs()
        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations,
            self.config.slider_default_values
        )#since I am going to initialize v_should I change this? nah, no need
        
        self.widget_buttons = WidgetButtonsRow()
        self.widget_at_bottom = self._create_bottom_text_widget()


        # Model for manual and automatic computations
        self.model_manual = ModelManual(
            list(self.config.slider_configurations.keys()),
            self.config.slider_default_values
        )
        
#        self.model_calculator = ModelCalculator(
#            list(self.config.slider_configurations.keys()),
#            self.config.slider_default_values,
#            self.file_data
#        )

        #calculate secondary variables
        self._calculate_secondary_variables()

        # Layout the UI
        self._initialize_ui()
        

        ### Connect signals ###
        #Connecting hotkeays
        self._initialize_hotkeys()
        
        #Updates dictionaries in main
        self.widget_input_file.file_data_updated.connect(self._update_file_data)
#        self.model_manual.modeled_data_updated.connect(self._update_modeled_data)
#        self.model_calculator.modeled_data_updated.connect(self._update_modeled_data)
        
        #connects manual model to the values in the sliders
#        self.widget_sliders.slider_value_updated.connect(self.model_manual.update_variable)
        self.widget_sliders.slider_value_updated.connect(self._update_variable)
        
        #connects both models to eachother and the sliders so vairables are consistent
#        self.model_manual.modeled_data_variables_updated.connect(self.model_calculator.listen_change_variables_signal)
#        self.model_calculator.modeled_data_variables_updated.connect(self.model_manual.listen_change_variables_signal)
#        self.model_calculator.modeled_data_variables_updated.connect(self.widget_sliders.update_all_variables)

        


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
    """
    def _create_bottom_text_widget(self):
        
        widget = QWidget()
        
        # Initialize the dictionary to store value labels
        self.value_labels = {}
        
        # Create a grid layout for alignment
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        #grid_layout.setSpacing(10)  # Space between labels
        
        # Iterate over each secondary variable and create labels
        for row, (var, expr) in enumerate(self.config.secondary_variables.items()):
            # Key Label
            key_label = QLabel(f"<b>{var}:</b>")
            key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Value Label
            value_label = QLabel("0.000000")  # Initialize with default value
            value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Optionally, set a fixed width for key labels for better alignment
            key_label.setFixedWidth(100)
            value_label.setFixedWidth(150)
            
            # Add labels to the grid
            grid_layout.addWidget(key_label, row, 0)
            grid_layout.addWidget(value_label, row, 1)
            
            # Store the value label in the dictionary for easy access
            self.value_labels[var] = value_label
        
        # Set the grid layout to the widget
        widget.setLayout(grid_layout)
        
        return widget
    """
    def _create_bottom_text_widget(self):
        """
        Creates the bottom text widget containing labels to display secondary variables.
        All variables are displayed in a single horizontal row with fixed positions.
        """
        widget = QWidget()
        
        # Initialize the dictionary to store value labels for quick access
        self.value_labels = {}
        
        # Create a horizontal box layout
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tight alignment
        
        # Iterate over each secondary variable and create key and value labels
        for var in self.config.secondary_variables.keys():
            # Create a container widget for each variable to group key and value labels
            var_widget = QWidget()
            var_layout = QHBoxLayout()
            var_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            var_layout.setSpacing(0)  # Space between key and value labels
            
            # Key Label
            key_label = QLabel(f"<b>{var}:</b>")
            key_label.setAlignment(Qt.AlignCenter)
            #key_label.setFixedWidth(50)  # Fixed width for consistency
            
            # Value Label
            value_label = QLabel("0.000000")  # Initialize with default value
            value_label.setAlignment(Qt.AlignCenter)
            #value_label.setFixedWidth(50)  # Fixed width to prevent shifting
            
            # Add labels to the variable layout
            var_layout.addWidget(key_label)
            var_layout.addWidget(value_label)
            
            # Set the layout to the variable widget
            var_widget.setLayout(var_layout)
            
            # Add the variable widget to the main horizontal layout
            h_layout.addWidget(var_widget)
            
            # Store the value label in the dictionary for easy updates
            self.value_labels[var] = value_label
        
        # Add a stretch at the end to push all variable widgets to the left
       # h_layout.addStretch()
        
        # Set the layout to the bottom text widget
        widget.setLayout(h_layout)
        
        return widget

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
        
#        shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
#        shortcut_f1.activated.connect(lambda: self.model_calculator._fit_model())
        
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




    def _compile_secondary_expressions(self):
        """
        Compiles the SymPy expressions for secondary variables to speed up evaluations.
        """
        self.compiled_expressions = {}
        variables = symbols(list(self.config.slider_configurations.keys()))
        
        for var, expr in self.config.secondary_variables.items():
            
            try:
                sympy_expr = sympify(expr)
                # Create a lambda function for faster evaluation
                func = lambdify(variables, sympy_expr, 'numpy')
                self.compiled_expressions[var] = func
            
            except SympifyError as e:
                print(f"Error parsing equation for {var}: {e}")
                self.compiled_expressions[var] = None
            except Exception as e:
                print(f"Unexpected error compiling equation for {var}: {e}")
                self.compiled_expressions[var] = None

    
    def _calculate_secondary_variables(self):
        """
        Calculates secondary variables using pre-compiled equations.
        """
        if not self.compiled_expressions:
            print("No compiled expressions available.")
            return

        self.v_second = {}
        slider_values = [self.v_sliders[key] for key in self.config.slider_configurations.keys()]
        
        for var, func in self.compiled_expressions.items():
            if func is not None:
                try:
                    result = func(*slider_values)
                    self.v_second[var] = float(result)
                except Exception as e:
                    print(f"Error evaluating compiled equation for {var}: {e}")
                    self.v_second[var] = None
            else:
                self.v_second[var] = None

    
    # -----------------------------------------------------------------------
    #  Private Conections Methods
    # -----------------------------------------------------------------------
   
        
    
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
        
    
    def _update_variable(self, key, value):
        """
        Updates the value of primary and secondary variables.
        """
        self.v_sliders[key] = value
        self._calculate_secondary_variables()
        
        # Iterate over each secondary variable and update its corresponding label
        for var, val in self.v_second.items():
            if var in self.value_labels:
                if val is not None:
                    # Format the value to 6 significant figures
                    formatted_val = f"{val:.4g}"
                    self.value_labels[var].setText(formatted_val)
                else:
                    # Display 'Error' if the value is None or invalid
                    self.value_labels[var].setText("Error")
        
        


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