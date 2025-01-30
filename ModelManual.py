# -*- coding: utf-8 -*-
# manual_model.py

import numpy as np
import scipy.optimize as opt
from scipy.optimize import Bounds
import logging
import inspect
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication

#
@dataclass
class CalculationResult:
    """
    Container for main and special impedance data.
    """
    main_freq:      np.ndarray   # The frequency array used for the main curve
    main_z_real:    np.ndarray
    main_z_imag:    np.ndarray
    special_freq:   np.ndarray   # The 3 special frequencies
    special_z_real: np.ndarray
    special_z_imag: np.ndarray
    

class ModelManual(QObject):
    """
    This class replicates the circuit calculation by evaluating
    formulas from config.ini (compiled by ConfigImporter).
    Now it also calculates 'secondary variables' that used to be in Main.
    It is hardcoded because my boss made me do it :) .
    """
    model_manual_result = pyqtSignal(CalculationResult)
    model_manual_values = pyqtSignal(dict)

    def __init__(self):

        super().__init__()

        self._experiment_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.zeros(5),
            "Z_imag": np.zeros(5),
        }
        self.disabled_variables = set()

        # We'll keep a copy of the secondary variables from the last run
        self._q = {}
        self._v_second = {}

    def initialize_expdata(self, file_data: dict):
        self._experiment_data= file_data

    def run_model_manual(self,v):
        """
        Main entry point to run the model with the given slider/fit parameters `v`.
        1) Computes main impedance arrays over self._experiment_data['freq'].
        2) Computes special frequencies + their impedance.
        3) Packs all into a CalculationResult.
        4) Emits signals, stores _modeled_data for cost-function usage.
        5) Returns the CalculationResult for direct inspection.
        """
        
        freq_array = self._experiment_data["freq"] 
        z_real, z_imag = self._run_model(v, freq_array)
        
        # 2) Compute the special frequencies based on the slider dict
        special_freq = self._get_special_freqs(v) 
        spec_zr, spec_zi = self._run_model(v, special_freq)

        # 3) Create a new CalculationResult
        result = CalculationResult(
            main_freq = freq_array,
            main_z_real   = z_real,
            main_z_imag   = z_imag,
            special_freq  = special_freq,
            special_z_real = spec_zr,
            special_z_imag = spec_zi
        )
        
        self.model_manual_result.emit(result)
        return result

    def get_latest_secondaries(self):
        """
        Return the most recent dictionary of secondary variables
        that was computed in run_model.
        """
        return dict(self._v_second)

    def fit_model_cole(self, v_initial_guess):
        """
        Fit the model using the 'Cole' cost function.
        """
        
        return self._fit_model(self._cost_function_cole, v_initial_guess)
    

    def fit_model_bode(self, v_initial_guess):
        """
        Fit the model using the 'Bode' cost function.
        """
        return self._fit_model(self._cost_function_bode, v_initial_guess)

    def get_model_parameters(self):
        return self._q | self._v_second  
        
    def set_disabled_variables(self, key, disabled):
        if disabled:
            self.disabled_variables.add(key)  
        else:
            self.disabled_variables.discard(key)
    
    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
        
    def _fit_model(self, cost_func, v_initial_guess):
        """
        Single private helper that removes code duplication.  
        It calls the provided cost_func, e.g. _cost_function_cole or _cost_function_bode,
        omitting any variables in self.disabled_variables from the optimizer.
        """
    
        # 1) Build a list of "free" keys that are not disabled
        all_keys = list(v_initial_guess.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
    
        # 2) Build an initial guess array (x0) only for free parameters
        x0 = [v_initial_guess[k] for k in free_keys]
    
        # 3) Build bounds only for the free parameters
        lower_bounds = []
        upper_bounds = []
        for name in free_keys:
            if name.startswith("F"):
                lower_bounds.append(1e-2)    # Frequency > 0
                upper_bounds.append(1e8)     # Arbitrary large
            elif name.startswith("P"):
                lower_bounds.append(0.0)     # Phase exponent
                upper_bounds.append(1.0)     # Add different clause for pei
            elif name.startswith("R"):
                lower_bounds.append(1e-2)    # Resistances can't be zero
                upper_bounds.append(1e8)
            elif name.startswith("L"):
                lower_bounds.append(1e-12)   
                upper_bounds.append(1e-3)    # Example domain
            elif name.startswith("Q"):
                lower_bounds.append(1e-8)    
                upper_bounds.append(1e2)     
            else:
                # Fallback
                lower_bounds.append(-1e9)
                upper_bounds.append(1e9)
    
        bounds = Bounds(lower_bounds, upper_bounds)
    
        # 4) Define a cost_wrapper that merges free parameters (from x_array)
        #    with locked/disabled ones (from v_initial_guess).
        def cost_wrapper(x_array):
            # Reconstruct dict for free params from x_array
            free_v_dict = {k: x_array[i] for i, k in enumerate(free_keys)}
            # Locked params remain at their original values:
            locked_v_dict = {
                k: v_initial_guess[k] 
                for k in self.disabled_variables if k in all_keys
            }
            # Merge both into one dict
            full_v_dict = {**free_v_dict, **locked_v_dict}
    
            return cost_func(full_v_dict)
    
        # 5) Call scipy.optimize.minimize using only free parameters
        result = opt.minimize(
            cost_wrapper,
            x0=x0,
            method='Nelder-Mead',
            bounds=bounds,          # Only meaningful if your chosen method respects bounds
            options={'maxfev': 2000}
        )
    
        # 6) Check optimization success
        if not result.success:
            print("Optimization failed:", result.message)
            raise RuntimeError("Optimization did not converge.")
    
        # 7) Reconstruct best-fit params for the free variables
        best_fit_free = {k: result.x[i] for i, k in enumerate(free_keys)}
        # For locked variables, keep them at their initial guess
        best_fit_locked = {
            k: v_initial_guess[k] 
            for k in self.disabled_variables if k in all_keys
        }
    
        # 8) Combine free + locked into a final result dict
        best_fit_dict = {**best_fit_free, **best_fit_locked}
        
        # 9) Use the final result in run_model_manual and return
        self.model_manual_values.emit(best_fit_dict)
        
        return best_fit_dict

        
    def _calculate_secondary_variables(self, v):
        """
        Computes 'series' and 'parallel' secondary variables
        Returns a dict of newly calculated secondary variables.
        """
        
        #print(v)
        Qh = self._q_from_f0( v["Rh"], v["Fh"], v["Ph"])
        Qm = self._q_from_f0( v["Rm"], v["Fm"], v["Pm"])
        Ql = self._q_from_f0( v["Rl"], v["Fl"], v["Pl"])
        
        self._q["Qh"]=Qh
        self._q["Qm"]=Qm
        self._q["Ql"]=Ql
        #print(self._q)
        
        self._v_second["R0"] = v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]
        self._v_second["pRh"] = v["Rinf"]*(v["Rinf"] + v["Rh"])/v["Rh"]
        self._v_second["pQh"] = Qh*(v["Rh"]/(v["Rinf"] + v["Rh"]))**2
        self._v_second["pRm"] = (v["Rinf"] + v["Rh"])*(v["Rinf"] + v["Rh"] +v["Rm"])/v["Rm"]
        self._v_second["pQm"] = Qm*(v["Rm"]/(v["Rinf"] + v["Rh"] + v["Rm"]))**2
        self._v_second["pRl"] = (v["Rinf"] + v["Rh"] + v["Rm"])*(v["Rinf"] + v["Rh"] + v["Rm"] +v["Rl"])/v["Rl"]
        self._v_second["pQl"] = Ql*(v["Rl"]/(v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]))**2

    def _get_special_freqs(self, slider_values: dict) -> np.ndarray:
        """
        Pseudocode that yields 3 freq points based on your domain logic.
        E.g. perhaps you pick them from slider ranges or some formula.
        """
        f1 = slider_values["Fh"] 
        f2 = slider_values["Fm"] 
        f3 = slider_values["Fl"]
        
        return np.array([f1, f2, f3], dtype=float)
    
    # Mostly for testing purposes
    def _run_model_series(self, v):
        
        """
        Alternative model path for testing (not used in cost functions directly).
        """
        self._calculate_secondary_variables(v)

        zr_list = []
        zi_list = []

        # Combine the user’s slider dictionary with v_seco
        for freq in self._experiment_data["freq"]:
            zinf = self._inductor(freq, v["Linf"]) + v["Rinf"]
            
            z_cpeh = self._cpe(freq, self._q["Qh"], v["Ph"], v["Ph"])
            zarch = self._parallel(z_cpeh, v["Rh"])
            
            z_cpem = self._cpe(freq, self._q["Qm"], v["Pm"], v["Pm"])
            zarcm =  self._parallel(z_cpem, v["Rm"])
            
            z_cpel = self._cpe(freq, self._q["Ql"], v["Pl"], v["Pl"])
            zarcl = self._parallel(z_cpel, v["Rl"])
            
            z_cpee = self._cpe(freq, v["Qe"], v["Pef"], v["Pei"])
            zarce = self._parallel(z_cpee, v["Re"])

            # Evaluate final formula
            z_total = zinf + zarch + zarcm + zarcl + zarce

            zr_list.append(z_total.real)
            zi_list.append(z_total.imag)

        # Update the arrays
        return np.array(zr_list), np.array(zi_list)

    def _run_model(self, v: dict, freq_array: np.ndarray):
        """
        The main model used in cost functions.
        """
        self._calculate_secondary_variables(v)
        v2 = self._v_second

        zr_list = []
        zi_list = []

        for f in freq_array:
            # Inductor
            zinf = self._inductor(f, v["Linf"])

            # Parallel system
            z_line_h = v2["pRh"] + self._cpe(f, v2["pQh"], v["Ph"], v["Ph"])
            z_line_m = v2["pRm"] + self._cpe(f, v2["pQm"], v["Pm"], v["Pm"])
            z_line_l = v2["pRl"] + self._cpe(f, v2["pQl"], v["Pl"], v["Pl"])

            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, v2["R0"])
            zparallel = self._parallel(z_line_h, z_rock)

            z_cpee = self._cpe(f, v["Qe"], v["Pef"], v["Pei"])
            zarce = self._parallel(z_cpee, v["Re"])

            z_total = zinf + zparallel + zarce
            zr_list.append(z_total.real)
            zi_list.append(z_total.imag)

        return np.array(zr_list), np.array(zi_list)
        
    def _cost_function_cole(self, v: dict) -> float:
        """
        EIS cost function with separate comparisons for real and imaginary parts.
        """
        
        freq_array = self._experiment_data["freq"]
        
        z_real, z_imag = self._run_model(v, freq_array)
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]

        diff_real = (z_real - exp_real) ** 2
        diff_imag = (z_imag - exp_imag) ** 2

        return np.sum(diff_real + diff_imag)
    
    def _cost_function_bode(self, v: dict) -> float:
        """
        Bode cost function that compares magnitude and phase.
        """
        freq_array = self._experiment_data["freq"]
        
        z_real, z_imag = self._run_model(v, freq_array)
        z_absolute = np.sqrt(z_real**2 + z_imag**2)
        z_phase_deg = np.degrees(np.arctan2(z_imag, z_real))

        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        exp_absolute = np.sqrt(exp_real**2 + exp_imag**2)
        exp_phase_deg = np.degrees(np.arctan2(exp_imag, exp_real))

        diff_absolute = (exp_absolute - z_absolute) ** 2
        diff_phase_deg = (exp_phase_deg - z_phase_deg) ** 2

        return np.sum(diff_absolute + diff_phase_deg)
    
    # ----------------------------------------------------
    # Circuit Methods
    # ----------------------------------------------------

    def _inductor(self, freq, linf):
        if linf == 0:
            raise ValueError("Inductance (linf) cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency cannot be negative.")
        
        result = (2 * np.pi * freq) * linf *1j
        return result
        
    def _q_from_f0(self, r , f0, p):
        if r == 0:
            raise ValueError("Resistance r cannot be zero.")
        if f0 <= 0:
            raise ValueError("Resonant frequency f0 must be positive.")
    
        result= 1.0 / (r * (2.0 * np.pi * f0)**p)
        return result
    
    def _cpe(self, freq , q, pf, pi):
        if q == 0:
            raise ValueError("Parameter q cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency must be non-negative for CPE model.")
        if freq == 0 and pf > 0:
            raise ValueError("freq=0 and pf>0 results in division by zero in CPE.")
        if freq == 0 and pf < 0:
            raise ValueError("freq=0 and pf<0 is undefined (0 to a negative power).")
        
        phase_factor = (1j)**pi
        omega_exp = (2.0 * np.pi * freq)**pf
        result= 1.0 / (q * phase_factor * omega_exp)
        return result
        
    def _parallel(self,z_1, z_2):
        if z_1 == 0 or z_2 == 0:
            raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")

        denominator= (1/z_1) + (1/z_2)
        result= 1/denominator
        return result
    
####################################################################
# -----------------------------------------------------------------------
#  TEST FOR UPDATED ModelManual
# -----------------------------------------------------------------------
########################################################################




from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QSlider, QLabel, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt
import numpy as np
from dataclasses import asdict

class ResultsWidget(QWidget):
    """
    A simple widget to display the results in a grid format and add sliders for parameter control.
    """
    def __init__(self, model, v_init, results_callback):
        super().__init__()
        self.setWindowTitle("Interactive Model Viewer")

        # Store model and callback
        self.model = model
        self.results_callback = results_callback

        # Main layout
        self.layout = QVBoxLayout(self)

        # Grid for sliders
        self.slider_grid = QGridLayout()
        self.layout.addLayout(self.slider_grid)

        # Table to display results
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)

        # Store slider references
        self.sliders = {}
        self.v_init = v_init

        # Add sliders for each parameter
        row = 0
        for param, value in v_init.items():
            self.add_slider(param, value, row)
            row += 1

        # Initialize results table
        self.update_results(self.run_model())

    def add_slider(self, param, initial_value, row):
        """
        Add a slider to the grid for controlling a parameter.
        """
        label = QLabel(f"{param}: {initial_value:.3e}", self)
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(1)
        slider.setMaximum(1000)
        slider.setValue(int(initial_value * 10 if initial_value > 0 else 1))
        slider.valueChanged.connect(lambda value, p=param, lbl=label: self.update_parameter(p, value, lbl))

        self.slider_grid.addWidget(label, row, 0)
        self.slider_grid.addWidget(slider, row, 1)
        self.sliders[param] = slider

    def update_parameter(self, param, value, label):
        """
        Update the parameter value and rerun the model.
        """
        # Scale value back to the original range
        scaled_value = value / 10 if "F" in param or "L" in param else value
        self.v_init[param] = scaled_value
        label.setText(f"{param}: {scaled_value:.3e}")

        # Rerun the model with updated parameters
        self.update_results(self.run_model())

    def run_model(self):
        """
        Run the model with the current parameter values.
        """
        return self.model.run_model_manual(self.v_init)

    def update_results(self, calculation_result):
        """
        Update the grid display with new results and invoke the callback.
        """
        # Convert the CalculationResult to a dictionary for easier iteration
        result_dict = asdict(calculation_result)

        # Prepare the table dimensions
        self.table.setRowCount(len(result_dict))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])

        # Populate the table
        for row, (key, value) in enumerate(result_dict.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            # Format the array values as strings
            value_str = str(value) if not isinstance(value, np.ndarray) else np.array2string(value, precision=4)
            self.table.setItem(row, 1, QTableWidgetItem(value_str))

        # Invoke the callback (e.g., for printing to terminal)
        self.results_callback(calculation_result)


def test_model_manual_with_sliders():
    """
    Interactive test with sliders, displaying the evolution of results in a grid and printing them to the terminal.
    """
    # Initialize Qt application
    app = QApplication([])

    # Create the model
    model = ModelManual()

    # Example experimental data
    test_freq = np.array([1, 10, 100, 1000, 10000, 100000], dtype=float)
    test_Zr = np.array([1.9, 1.24, 1.23, 1.21, 1.14, 8.03], dtype=float)
    test_Zi = np.array([-1.09, -1.12, -1.46, -3.31, -1.06, -3.85], dtype=float)
    file_data = {
        "freq": test_freq,
        "Z_real": test_Zr,
        "Z_imag": test_Zi,
    }
    model.initialize_expdata(file_data)

    # Example slider/initial guess
    v_init = {
        "Rinf": 671,
        "Linf": 1e-6,
        "Rh":   120000,
        "Fh":   178000,
        "Ph":   0.7,
        "Rm":   1.0,
        "Fm":   0.1,
        "Pm":   0.5,
        "Rl":   100.0,
        "Fl":   1000.0,
        "Pl":   0.8,
        "Re":   50.0,
        "Qe":   1e-5,
        "Pef":  0.8,
        "Pei":  0.8,
    }

    # Function to print results in the terminal
    def print_results_to_terminal(calc_result):
        print("\nFull Calculation Result:")
        for key, value in asdict(calc_result).items():
            if isinstance(value, np.ndarray):
                print(f"{key}: {np.array2string(value, precision=4)}")
            else:
                print(f"{key}: {value}")

    # Create the GUI for displaying results and interacting with sliders
    results_widget = ResultsWidget(model, v_init, results_callback=print_results_to_terminal)
    results_widget.resize(800, 600)
    results_widget.show()

    # Run the application loop
    app.exec_()


if __name__ == "__main__":
    test_model_manual_with_sliders()



