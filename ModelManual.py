# -*- coding: utf-8 -*-
# manual_model.py

import numpy as np
import scipy.optimize as opt
from scipy.optimize import Bounds
import logging
import inspect
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication

# "Bounds are sacled. Need to add padding for 0 values, handle Qei, and implement a way of making Rinf negative"

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
        self.negative_rinf = False

        # We'll keep a copy of the secondary variables from the last run
        self._q = {}
        self._v_second = {}
        
    # ----------------------------------------------------
    # Public Method
    # ----------------------------------------------------    

    def initialize_expdata(self, file_data: dict):
        self._experiment_data= file_data
        
    def set_disabled_variables(self, key, disabled):
        if disabled:
            self.disabled_variables.add(key)  
        else:
            self.disabled_variables.discard(key)
        
    def set_rinf_negative(self, state: bool):
        
        print(f" set rinf {state}")
        self.negative_rinf= state
        
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
        print(f"outside the method, where it should not matter {v['Rinf']}")
        return result

    def get_latest_secondaries(self):
        """
        Return the most recent dictionary of secondary variables
        that was computed in run_model.
        """
        return dict(self._v_second)

    def get_model_parameters(self):
        return self._q | self._v_second  
    
    
    # ----------------------------------------------------
    # Fit Methods
    # ----------------------------------------------------
    # Private Methods
    def _fit_model(self, cost_func, v_given):
        
        #Select th keys of variables to be optimized (those not locked)
        all_keys = list(v_given.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
        
        # for readability v will be actual values and x will be logs
        # x represents the free v that minimize will "guess"
        # x0 represents the initial guesses for the free.
        # This line prepares them as the log of the free keys
        x0 =self._scale_v_to_x(free_keys, v_given)

#remember to set the limmits as logs as well, I think?
        #This line sets the bounds. Note, Nelder-Mead ignores bounds. Boudns work for "SLSQP", "trust-constr", or "TNC"
        lower_bounds, upper_bounds = self._build_bounds(free_keys)
        bounds = Bounds(lower_bounds, upper_bounds)
        
        #wraps cost function for use. Defined nested for a more complete view of fit_model's functioning
        #minimize "sends" different values for x_guessing.
        #cost wrapper wraps them into dictionary form, which is what the _run_model
        #and cost functions need to run, runs the cost function, and returns it's result.
        def _cost_wrapper(x_guessing):
            try:
                free_v_dict = self._descale_x_to_v(free_keys,x_guessing)
                
                locked_v_dict = {k: v_given[k] for k in self.disabled_variables if k in all_keys}
                full_v_dict = free_v_dict | locked_v_dict
                
                cost = cost_func(full_v_dict)
                return cost
            
            except ValueError:
                # Force a huge cost whenever errors are thrown, etc.
                return 1e20

        result = opt.minimize(
            _cost_wrapper,  #Objective function:_cost_wrapper (returns a single scalar)
            x0=x0,          #x0 (starting values for FREE parameters).
            method='Nelder-Mead',
#            bounds=bounds,
            options={'maxfev': 2000}
        )

        if not result.success:
            print("Optimization failed:", result.message)
            raise RuntimeError("Optimization did not converge.")

        best_fit_free = self._descale_x_to_v(free_keys , result.x)
        best_fit_locked = {k: v_given[k] for k in self.disabled_variables if k in all_keys}
        best_fit_dict = best_fit_free | best_fit_locked
        
        self.model_manual_values.emit(best_fit_dict)
        return best_fit_dict

    def _build_bounds(self, free_keys):
        lower_bounds = []
        upper_bounds = []
        
        dictionary_lower = {
            'Linf':1e-12,'Rinf': 1e-2, 
            'Rh': 1e-2,'Fh': 1e-2,'Ph': 0.0, 
            'Rm': 1e-2,'Fm': 1e-2, 'Pm': 0.0,
            'Rl': 1e-2,'Fl': 1e-2,'Pl': 0.0,
            'Re': 1e-2,'Qe': 1e-8,'Pef': 0.0, 'Pei': -3.2,
        }
        
        dictionary_upper= {
            'Linf':1e-3,'Rinf':1e8,
            'Rh': 1e8,'Fh': 1e8,'Ph': 1.0,
            'Rm': 1e8,'Fm': 1e8,'Pm': 1.0,
            'Rl': 1e8,'Fl': 1e8,'Pl': 1.0,
            'Re': 1e8,'Qe': 1e2,'Pef': 1.0,'Pei': 0.8,
        }
        
        
        lower_bounds = self._scale_v_to_x(free_keys, dictionary_lower)
        upper_bounds = self._scale_v_to_x(free_keys, dictionary_upper)

                
        return lower_bounds, upper_bounds
   
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
    # Models
    # ----------------------------------------------------
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

    #MM CHECK THAT HIS DOE SNOT CAUSE CHAOS
    def _run_model(self, v: dict, freq_array: np.ndarray):
        """
        The main model used in cost functions.
        """
        print("ENTERING RUN MODEL")
        print(f"{v['Rinf']}, boolean{ self.negative_rinf}")
        
        v_l = v.copy()
    
        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
    
        self._calculate_secondary_variables(v_l)  # ✅ Pass v_l instead of v
        v2 = self._v_second
    
        zr_list = []
        zi_list = []
    
        for f in freq_array:
            # Inductor
            zinf = self._inductor(f, v_l["Linf"])
    
            # Parallel system
            z_line_h = v2["pRh"] + self._cpe(f, v2["pQh"], v_l["Ph"], v_l["Ph"])
            z_line_m = v2["pRm"] + self._cpe(f, v2["pQm"], v_l["Pm"], v_l["Pm"])
            z_line_l = v2["pRl"] + self._cpe(f, v2["pQl"], v_l["Pl"], v_l["Pl"])
    
            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, v2["R0"])
            zparallel = self._parallel(z_line_h, z_rock)
    
            z_cpee = self._cpe(f, v_l["Qe"], v_l["Pef"], v_l["Pei"])
            zarce = self._parallel(z_cpee, v_l["Re"])
    
            z_total = zinf + zparallel + zarce
            zr_list.append(z_total.real)
            zi_list.append(z_total.imag)
    
        print(f"afterwards {v_l['Rinf']}")
        return np.array(zr_list), np.array(zi_list)

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

    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
    
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

    def _scale_v_to_x(self,keys, v):
        "Receives a list of keys and a dictionary. Returns a scaled list"
        print(" _scale_v_to_x")
        print(v)
        print("**********************")
        
        x = []
        for k in keys:
            if k.startswith('P'):
                # Linear scaling
                x.append(v[k] * 100.0)
            else:
                # Logarithmic scaling
                x.append(np.log10(v[k]))
        print(x)
        print("=====================")
        return x
    
    def _descale_x_to_v(self, keys, x):
        print("_descale_x_to_v")
        print(x)
        print("**********************")
        
        "Receives a list of keys and a list fo values. Returns a de-scaled dictionary"
        v = {}
        for i, k in enumerate(keys):
            if k.startswith('P'):
                v[k] = x[i] / 100.0
            else:
                v[k] = 10.0 ** (x[i])
        print(v)
        print("=====================")
        return v
   
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
    A simple widget to display the results in a grid format
    and add sliders for parameter control within known bounds.
    """
    def __init__(self, model, v_init, results_callback):
        super().__init__()
        self.setWindowTitle("Interactive Model Viewer")

        self.model = model
        self.results_callback = results_callback

        self.layout = QVBoxLayout(self)
        self.slider_grid = QGridLayout()
        self.layout.addLayout(self.slider_grid)

        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)

        self.sliders = {}
        self.v_init = dict(v_init)  # copy so we can mutate

        # Hardcoded dictionary of physical bounds so we can clamp slider range
        self.physical_bounds = {
            "Rinf": (1e-2, 1e8),
            "Linf": (1e-12, 1e-3),
            "Rh":   (1e-2, 1e8),
            "Fh":   (1e-2, 1e8),
            "Ph":   (1e-9, 1.0),
            "Rm":   (1e-2, 1e8),
            "Fm":   (1e-2, 1e8),
            "Pm":   (1e-9, 1.0),
            "Rl":   (1e-2, 1e8),
            "Fl":   (1e-2, 1e8),
            "Pl":   (1e-9, 1.0),
            "Re":   (1e-2, 1e8),
            "Qe":   (1e-8, 1e2),
            "Pef":  (1e-9, 1.0),
            "Pei":  (-3.2, 0.8),  # linear
        }

        # Add sliders for each parameter in v_init
        row = 0
        for param, value in self.v_init.items():
            self.add_slider(param, value, row)
            row += 1

        # Initial run
        self.update_results(self.run_model())

    def add_slider(self, param, initial_value, row):
        """
        Add a slider that maps a 1..1000 integer range onto
        the [lower, upper] bounds in physical space.
        """
        lower, upper = self.physical_bounds.get(param, (1e-3, 1e3))

        # We'll store them so we can do the linear mapping
        # param_value = lower + (slider_value/1000)*(upper - lower)
        self.sliders[param] = {}

        label = QLabel(f"{param}: {initial_value:.3g}", self)
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(1)
        slider.setMaximum(1000)

        # Find an integer that corresponds to initial_value
        # param_value -> slider_value = (param - lower)/(upper - lower)*1000
        s_val = int( (initial_value - lower)/(upper - lower)*1000 ) 
        s_val = max(min(s_val, 1000), 1)  # clamp to 1..1000

        slider.setValue(s_val)

        # store references
        self.sliders[param]["slider"] = slider
        self.sliders[param]["label"]  = label
        self.sliders[param]["lower"]  = lower
        self.sliders[param]["upper"]  = upper

        slider.valueChanged.connect(lambda val, p=param: self.update_parameter(p, val))

        self.slider_grid.addWidget(label, row, 0)
        self.slider_grid.addWidget(slider, row, 1)

    def update_parameter(self, param, slider_value):
        """
        Convert slider_value (1..1000) back to physical param in [lower, upper].
        Re-run the model, update table, etc.
        """
        bounds = self.sliders[param]
        lower  = bounds["lower"]
        upper  = bounds["upper"]

        # Map the slider to param_value
        param_value = lower + (slider_value/1000.0)*(upper - lower)
        self.v_init[param] = param_value

        # Update label
        label = bounds["label"]
        label.setText(f"{param}: {param_value:.3g}")

        # Re-run model
        self.update_results(self.run_model())

    def run_model(self):
        return self.model.run_model_manual(self.v_init)

    def update_results(self, calculation_result):
        result_dict = asdict(calculation_result)
        self.table.setRowCount(len(result_dict))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])

        for row, (key, value) in enumerate(result_dict.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            # Convert arrays to a short string
            if isinstance(value, np.ndarray):
                value_str = np.array2string(value, precision=4)
            else:
                value_str = str(value)
            self.table.setItem(row, 1, QTableWidgetItem(value_str))

        # Fire callback
        self.results_callback(calculation_result)

def test_model_manual_with_sliders():
    app = QApplication([])

    # Create the model
    model = ModelManual()

    # Example experimental data
    test_freq = np.array([1, 10, 100, 1000, 10000, 100000], dtype=float)
    test_Zr   = np.array([1.9, 1.24, 1.23, 1.21, 1.14, 8.03], dtype=float)
    test_Zi   = np.array([-1.09, -1.12, -1.46, -3.31, -1.06, -3.85], dtype=float)

    file_data = {
        "freq":   test_freq,
        "Z_real": test_Zr,
        "Z_imag": test_Zi,
    }
    model.initialize_expdata(file_data)

    # Example initial guesses (in physical space, within the declared bounds)
    v_init = {
        "Rinf": 1.0e3,
        "Linf": 1.0e-6,
        "Rh":   1.0e5,
        "Fh":   5.0e3,
        "Ph":   0.7,
        "Rm":   10.0,
        "Fm":   100.0,
        "Pm":   0.5,
        "Rl":   100.0,
        "Fl":   1000.0,
        "Pl":   0.8,
        "Re":   50.0,
        "Qe":   1e-5,
        "Pef":  0.8,
        "Pei":  0.1,   # can be negative or positive
    }

    def print_results_to_terminal(calc_result):
        print("\nUpdated Calculation Result:")
        for k, val in asdict(calc_result).items():
            if isinstance(val, np.ndarray):
                print(f"{k}: {np.array2string(val, precision=4)}")
            else:
                print(f"{k}: {val}")

    w = ResultsWidget(model, v_init, results_callback=print_results_to_terminal)
    w.resize(800, 600)
    w.show()
    app.exec_()


if __name__ == "__main__":
    test_model_manual_with_sliders()



