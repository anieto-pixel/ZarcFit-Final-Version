# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

@author: agarcian
"""

#MM
#This class ahs a level of coupling and specificity for the  name of the variables is not ideal. 
#Maybe I shoudl reconsider and define the slider values and everything here?

import numpy as np
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from NSlidersWidget import NSlidersWidget
from SubclassesSliderWithTicks import *
from ConfigImporter import *



class ManualModel(QWidget):
    manual_model_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, variables_keys, variables_default_values):
        super().__init__()
        self._variables_dictionary = {key: 0.0 for key in variables_keys}
        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values

        # Default frequency data
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        # Set default values
        self._set_default_values()

    def _calculate_Zarc(self, frec, r, fo, p):
        """
        Calculate the real and imaginary components of impedance for a Zarc circuit.
        """
        omega = 2 * np.pi * frec
        omega_h = 2 * np.pi * fo
        Q = 1 / (omega_h ** p)  # CPE scaling constant approximation
        
        print(omega, omega_h, Q)

        Z_cpe_mag = 1 / (Q * omega ** p)
        Z_cpe_real = Z_cpe_mag * np.cos(-np.pi * p / 2)
        Z_cpe_imag = Z_cpe_mag * np.sin(-np.pi * p / 2)

        Z_real = 1 / (1 / r + 1 / Z_cpe_real)
        Z_imag = 1 / (1 / Z_cpe_imag)

        return Z_real, Z_imag

    def _run_model(self):
        pass
        
        """ 
        zarc_h_real=[]
        zarc_h_imag=[]
        for freq in self._manual_data['freq']:
            z_real,z_imag = self._calculate_Zarc(freq, 
                                 self._variables_dictionary['rh'], 
                                 self._variables_dictionary['fh'], 
                                 self._variables_dictionary['ph']
                                 )
            zarc_h_real.append(z_real)
            zarc_h_imag.append(z_imag)
        
                            
        zarc_m_real=[]
        zarc_m_imag=[]
        for freq in self._manual_data['freq']:
            z_real,z_imag = self._calculate_Zarc(freq, 
                                 self._variables_dictionary['rm'], 
                                 self._variables_dictionary['fm'], 
                                 self._variables_dictionary['pm']
                                 )
            zarc_m_real.append(z_real)
            zarc_m_imag.append(z_imag)
            
        zarc_l_real=[]
        zarc_l_imag=[]
        for freq in self._manual_data['freq']:
            z_real,z_imag = self._calculate_Zarc(freq, 
                                 self._variables_dictionary['rl'], 
                                 self._variables_dictionary['fl'], 
                                 self._variables_dictionary['pl']
                                 )
            zarc_l_real.append(z_real)
            zarc_l_imag.append(z_imag)
    
        self._manual_data['Z_real'] = zarc_h_real+zarc_m_real+zarc_l_real
        self._manual_data['Z_imag'] = zarc_h_imag+zarc_m_imag+zarc_l_imag
      
        self._manual_data['Z_real'] = np.array(zarc_h_real)
        self._manual_data['Z_imag'] = np.array(zarc_h_imag)
    
    
        # Emit the updated data
        self.manual_model_updated.emit(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
        )
        """
        

    def _set_default_values(self):
        """
        Sets the variables to the default values.
        """
        for key, default_value in zip(self._variables_keys, self._variables_default_values):
            self._variables_dictionary[key] = default_value

    def initialize_frequencies(self, freq_array):
        """
        Initializes the frequency array and re-runs the model calculations.
        """
        self._manual_data['freq'] = freq_array
        self._set_default_values()  # Optionally reset variables to defaults
        self._run_model()

    def update_variable(self, key, new_value):
        """
        Updates a variable in the dictionary and re-runs the model.
        """
        if key in self._variables_dictionary:
            self._variables_dictionary[key] = new_value
            self._run_model()
        else:
            raise KeyError(f"Variable '{key}' not found in the model.")
            
        #test method
        def print_manual_value(self):
            print(self._manual_data)


#################################################################################################################################              

"""TEST"""
    
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Load config
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # 2. Create the ManualModel instance
    manual_model = ManualModel(
        list(config.slider_configurations.keys()),
        config.slider_default_values
    )

    # 3. Create the NSlidersWidget instance
    sliders_widget = NSlidersWidget(
        config.slider_configurations,
        config.slider_default_values
    )

    # 4. Build a test window and layout
    test_window = QWidget()
    test_window.setWindowTitle("Test ManualModel - Side-by-side Display")
    test_window.setGeometry(100, 100, 800, 900)
    main_layout = QVBoxLayout(test_window)

    # Add the sliders widget on top
    main_layout.addWidget(sliders_widget)

    # 5. Create a QTableWidget to display variable info side by side
    variables_keys = list(manual_model._variables_dictionary.keys())
    table = QTableWidget(len(variables_keys), 3)
    table.setHorizontalHeaderLabels(["Variable", "Slider Value", "Model Value"])

    # Map each variable to a row index
    row_index_map = {}
    for i, key in enumerate(variables_keys):
        row_index_map[key] = i
        # Column 0: Variable name
        table.setItem(i, 0, QTableWidgetItem(key))
        # Pre-fill columns 1 and 2 with defaults
        # (Slider Value, Model Value)
        slider_val = str(manual_model._variables_dictionary[key])
        table.setItem(i, 1, QTableWidgetItem(slider_val))
        table.setItem(i, 2, QTableWidgetItem(slider_val))

    main_layout.addWidget(table)

    # 6. Define a slot to handle slider_value_updated from NSlidersWidget
    def on_slider_value_updated(key, new_value):
        """
        Updates the ManualModel with the new slider value, then
        displays both the slider value and model value in the table.
        """
        manual_model.update_variable(key, new_value)
        row = row_index_map[key]
        # Update 'Slider Value' column
        table.setItem(row, 1, QTableWidgetItem(str(new_value)))
        # Update 'Model Value' column (from the model)
        model_val = str(manual_model._variables_dictionary[key])
        table.setItem(row, 2, QTableWidgetItem(model_val))

    # 7. Connect NSlidersWidget signal to the slot
    #    Note that NSlidersWidget has slider_value_updated, not slider_value_changed
    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    # 8. Show the test window
    test_window.show()
    sys.exit(app.exec_())