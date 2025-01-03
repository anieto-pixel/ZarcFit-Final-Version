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
            # TEST: We'll store Z_total results here after each run:
            'Z_total': np.zeros(5, dtype=complex)  # A placeholder
        }

        # Set default values
        self._set_default_values()

    def _calculate_Zarc(self, f, r, f0, p):
    
        """
        Calculate the real and imaginary components of impedance for a Zarc circuit.
        """
        
        q = 1.0 / (r * (2*np.pi*f0)**p)
        z_cpe = 1.0 / (q * ((2*np.pi*f*1j) ** p))
        Z_r = r
        
        z_total=(z_cpe*Z_r)/(z_cpe+Z_r)
        
        return z_total

    def _run_model(self):   
         
        zarc_h_real=[]
        zarc_h_imag=[]
        z_totalh_all = []  # TEST USE: store each z_total here
        
        for freq in self._manual_data['freq']:
            z_total = self._calculate_Zarc(freq, 
                        self._variables_dictionary['rh'], 
                        self._variables_dictionary['fh'], 
                        self._variables_dictionary['ph']
                        )
            zarc_h_real.append(np.real(z_total))
            zarc_h_imag.append(np.imag(z_total))
            z_totalh_all.append(z_total) # TEST USE: store each z_total here
        
        """                       
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
    
    """
        self._manual_data['Z_real'] = np.array(zarc_h_real)
        self._manual_data['Z_imag'] = np.array(zarc_h_imag)
        self._manual_data['Z_total'] = np.array(z_totalh_all) # TEST
        
        # Emit the updated data
        self.manual_model_updated.emit(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
            
        )
        
        

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
    import sys
    import numpy as np
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QTableWidget,
        QTableWidgetItem, QHBoxLayout
    )
    from PyQt5.QtCore import Qt
    from ConfigImporter import ConfigImporter
    from NSlidersWidget import NSlidersWidget

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

    # 4. Build the main window and main layout
    test_window = QWidget()
    test_window.setWindowTitle("Test ManualModel - Side-by-side Display")
    test_window.setGeometry(100, 100, 1200, 600)  # Make it a bit wider
    main_layout = QVBoxLayout(test_window)  # Vertical layout

    # Place sliders on top
    main_layout.addWidget(sliders_widget)

    # 5. Create the "Variables" table (Variable, Slider Value, Model Value)
    variables_keys = list(manual_model._variables_dictionary.keys())
    table_vars = QTableWidget(len(variables_keys), 3)
    table_vars.setHorizontalHeaderLabels(["Variable", "Slider Value", "Model Value"])

    # Map each variable to a row index
    row_index_map = {}
    for i, key in enumerate(variables_keys):
        row_index_map[key] = i
        # Column 0: Variable name
        table_vars.setItem(i, 0, QTableWidgetItem(key))
        # Columns 1 & 2: initial slider/model values
        slider_val = str(manual_model._variables_dictionary[key])
        table_vars.setItem(i, 1, QTableWidgetItem(slider_val))
        table_vars.setItem(i, 2, QTableWidgetItem(slider_val))

    # 6. Create the "Impedance" table (Frequency, Z_total, Z_real, Z_imag)
    freq_array = manual_model._manual_data['freq']
    table_imp = QTableWidget(len(freq_array), 4)
    table_imp.setHorizontalHeaderLabels(["Frequency", "Z_total", "Z_real", "Z_imag"])

    # Fill initial values
    for i, f in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(str(f)))
        table_imp.setItem(i, 1, QTableWidgetItem(str(manual_model._manual_data['Z_total'][i])))
        table_imp.setItem(i, 2, QTableWidgetItem(str(manual_model._manual_data['Z_real'][i])))
        table_imp.setItem(i, 3, QTableWidgetItem(str(manual_model._manual_data['Z_imag'][i])))

    # 7. Create a sub-layout to hold the two tables side by side
    tables_layout = QHBoxLayout()
    tables_layout.addWidget(table_vars)
    tables_layout.addWidget(table_imp)

    # Add the sub-layout to the main layout
    main_layout.addLayout(tables_layout)

    # 8. A helper to refresh the impedance table after each slider move
    def update_impedance_table():
        freqs = manual_model._manual_data['freq']
        z_totals = manual_model._manual_data['Z_total']
        z_reals = manual_model._manual_data['Z_real']
        z_imags = manual_model._manual_data['Z_imag']

        for i in range(len(freqs)):
            table_imp.setItem(i, 0, QTableWidgetItem(str(freqs[i])))
            table_imp.setItem(i, 1, QTableWidgetItem(str(z_totals[i])))
            table_imp.setItem(i, 2, QTableWidgetItem(str(z_reals[i])))
            table_imp.setItem(i, 3, QTableWidgetItem(str(z_imags[i])))

    # 9. Slot to handle slider_value_updated from NSlidersWidget
    def on_slider_value_updated(key, new_value):
        """
        Updates the ManualModel with the new slider value, then
        displays both the slider value and model value in the variables table,
        and refreshes the impedance table.
        """
        manual_model.update_variable(key, new_value)

        # Update the 'Variables' table
        row = row_index_map[key]
        table_vars.setItem(row, 1, QTableWidgetItem(str(new_value)))
        model_val = str(manual_model._variables_dictionary[key])
        table_vars.setItem(row, 2, QTableWidgetItem(model_val))

        # Update the impedance table with new results
        update_impedance_table()

    # 10. Connect NSlidersWidget signal to the slot
    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    # 11. Show the test window
    test_window.show()
    sys.exit(app.exec_())