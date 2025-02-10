# -*- coding: utf-8 -*-
# manual_model.py

import scipy.signal as sig
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
    main_freq:      np.ndarray = None  # The frequency array used for the main curve
    main_z_real:    np.ndarray = None
    main_z_imag:    np.ndarray = None
    
    special_freq:   np.ndarray = None  # The 3 special frequencies
    special_z_real: np.ndarray = None
    special_z_imag: np.ndarray = None
    
    timedomain_freq:   np.ndarray = None   # Elements used for the time domain plot
    timedomain_volt:   np.ndarray = None
    timedomain_time:   np.ndarray = None
    
    
import numpy as np

class ModelCircuitParent(object):
    
    def __init__(self, negative_rinf=False, q=None, v_second=None):
        
        super().__init__()
        
        # --- FIX #1: Avoid mutable default arguments, properly assign attributes.
        if q is None:
            q = {}
            
        if v_second is None:
            v_second = {}
            
        self.negative_rinf = negative_rinf
        self.q = q
        self.v_second = v_second

    def run_model(self, v: dict, freq_array: np.ndarray):
        return np.array([])
    
    def run_time_domain(self, v: dict, freq_array: np.ndarray, crit_time=2):
        
        timedomain_freq = None
        timedomain_volt = None
        timedomain_time = None
        
        # 1) Fix some parameters
#        v_copy_fixed={}
        v_copy_fixed = {
#            'Linf': 10**0, 'Rinf': 10**8, 'Re'  : 10**8,
            'Qe'   : 10**2, 'Pef'  : 10**1.0, 'Pei': 10**3.2,
        }
        v_copy = v.copy()
        for key, fixed_value in v_copy_fixed.items():
            if key in v_copy:
                v_copy[key] = fixed_value
                       
        # 2) Define frequency sampling to match "Compute_Chargeability_Voltage_over_I0"
        N = len(freq_array)
        
        # Define sampling_rate, then generate frequencies from 0 to Fs/2
        sampling_rate = N / (1.1 * crit_time)
        timedomain_freq = np.linspace(0, sampling_rate / 2, N)
        timedomain_freq = timedomain_freq[1:]
                
        # 3) Run the model to get frequency-domain impedance Z
        z = self.run_model(v_copy, timedomain_freq)  # <--- frequency-domain impedance
    
        # 4) Perform IFFT to get the unfiltered time-domain response
        z_tilde_unfiltered = np.fft.irfft(z, n=N)
        
        # Determine time-step from Fs and build time array
        # Normalize so that the zero-frequency component is accounted for
        t = np.linspace(0, N / sampling_rate, N)
        dt = t[1] - t[0]
        z_tilde_unfiltered /= dt
        
        # 5) Filter in the TIME domain (Butterworth)
        b, a = sig.butter(2, 0.45, fs=1)
        timedomain_z = sig.filtfilt(b, a, z_tilde_unfiltered)

        # 6) Limit time range to 'crit_time'
        # Find first index where t exceeds crit_time
        w_crit = np.where(t > crit_time)[0][0]
        timedomain_time = t[:w_crit]
        timedomain_z = timedomain_z[:w_crit]

        # 7) Compute the final step response: 1 - ∫Z/∫∞Z
        # The integral up to 'crit_time' for normalization:
        Vm = np.sum(timedomain_z * dt)
        
        # Discrete integration to form the step response
        dV = timedomain_z * dt
        partial_sum = 0.0
        V_of_t = []
        for val in dV:
            partial_sum += val
            V_of_t.append(partial_sum)
        
        V_of_t = np.array(V_of_t)
        timedomain_volt = 1.0 - (V_of_t / Vm)

        return timedomain_freq, timedomain_time, timedomain_volt       


    def init_parameters(self):
        return self.negative_rinf, self.q, self.v_second

    # ------------------------------------------
    # Variable Calculations
    # ------------------------------------------
    def _calculate_secondary_variables(self, v):
        """
        Computes 'series' and 'parallel' secondary variables
        Returns a dict of newly calculated secondary variables.
        """
        # --- FIX #2: Method name mismatch: renamed 'self.q_from_f0' calls
        # to 'self._q_from_f0' for consistency.
        Qh = self._q_from_f0(v["Rh"], v["Fh"], v["Ph"])
        Qm = self._q_from_f0(v["Rm"], v["Fm"], v["Pm"])
        Ql = self._q_from_f0(v["Rl"], v["Fl"], v["Pl"])

        self.q["Qh"] = Qh
        self.q["Qm"] = Qm
        self.q["Ql"] = Ql

        self.v_second["R0"] = v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]
        self.v_second["pRh"] = v["Rinf"] * (v["Rinf"] + v["Rh"]) / v["Rh"]
        self.v_second["pQh"] = Qh * (v["Rh"] / (v["Rinf"] + v["Rh"]))**2
        self.v_second["pRm"] = (v["Rinf"] + v["Rh"]) * (v["Rinf"] + v["Rh"] + v["Rm"]) / v["Rm"]
        self.v_second["pQm"] = Qm * (v["Rm"] / (v["Rinf"] + v["Rh"] + v["Rm"]))**2
        self.v_second["pRl"] = (v["Rinf"] + v["Rh"] + v["Rm"]) * (v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]) / v["Rl"]
        self.v_second["pQl"] = Ql * (v["Rl"] / (v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]))**2

    # ----------------------------------------------------
    # Circuit Methods
    # ----------------------------------------------------
    def _inductor(self, freq, linf):
        if linf == 0:
            raise ValueError("Inductance (linf) cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency cannot be negative.")
        result = (2 * np.pi * freq) * linf * 1j
        return result

    def _q_from_f0(self, r, f0, p):
        if r == 0:
            raise ValueError("Resistance r cannot be zero.")
        if f0 <= 0:
            raise ValueError("Resonant frequency f0 must be positive.")
        result = 1.0 / (r * (2.0 * np.pi * f0)**p)
        return result

    def _cpe(self, freq, q, pf, pi):
        if q == 0:
            raise ValueError("Parameter q cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency must be non-negative for CPE model.")
        if freq == 0 and pf > 0:
            raise ValueError("freq=0 and pf>0 results in division by zero in CPE.")
        if freq == 0 and pf < 0:
            raise ValueError("freq=0 and pf<0 is undefined (0 to a negative power).")

        phase_factor = (1j) ** pi
        omega_exp = (2.0 * np.pi * freq) ** pf
        result = 1.0 / (q * phase_factor * omega_exp)
        return result

    def _parallel(self, z_1, z_2):
        if z_1 == 0 or z_2 == 0:
            raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")
        denominator = (1 / z_1) + (1 / z_2)
        result = 1 / denominator
        return result

# Rinf needs to be able to be negative
class ModelCircuitSeries(ModelCircuitParent):
    # Mostly for testing purposes
    def run_model(self, v: dict, freq_array: np.ndarray):
        """
        Alternative model path for testing (not used in cost functions directly).
        """
        v_l = v.copy()
        
        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        z = []

        for freq in freq_array:
            zinf = self._inductor(freq, v_l["Linf"]) + v_l["Rinf"]

            z_cpeh = self._cpe(freq, self.q["Qh"], v_l["Ph"], v_l["Ph"])
            zarch = self._parallel(z_cpeh, v_l["Rh"])

            z_cpem = self._cpe(freq, self.q["Qm"], v_l["Pm"], v_l["Pm"])
            zarcm = self._parallel(z_cpem, v_l["Rm"])

            z_cpel = self._cpe(freq, self.q["Ql"], v_l["Pl"], v_l["Pl"])
            zarcl = self._parallel(z_cpel, v_l["Rl"])

            z_cpee = self._cpe(freq, v_l["Qe"], v_l["Pef"], v_l["Pei"])
            zarce = self._parallel(z_cpee, v_l["Re"])

            # Evaluate final formula
            z_total = zinf + zarch + zarcm + zarcl + zarce

            z.append(z_total)

        return np.array(z)

class ModelCircuitParallel(ModelCircuitParent):
    
    def run_model(self, v: dict, freq_array: np.ndarray):
        """
        The main model used in cost functions.
        """
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        v2 = self.v_second
        
        z = []

        for f in freq_array:
            zinf = self._inductor(f, v_l["Linf"])

            z_line_h = v2["pRh"] + self._cpe(f, v2["pQh"], v_l["Ph"], v_l["Ph"])
            z_line_m = v2["pRm"] + self._cpe(f, v2["pQm"], v_l["Pm"], v_l["Pm"])
            z_line_l = v2["pRl"] + self._cpe(f, v2["pQl"], v_l["Pl"], v_l["Pl"])

            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, v2["R0"])
            zparallel = self._parallel(z_line_h, z_rock)

            z_cpee = self._cpe(f, v_l["Qe"], v_l["Pef"], v_l["Pei"])
            zarce = self._parallel(z_cpee, v_l["Re"])

            z_total = zinf + zparallel + zarce
            z.append(z_total)

        return np.array(z)

############################################################################3

    
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
        
        self._model_circuit=ModelCircuitParallel()
        
        self.disabled_variables = set()
        
        self.gaussian_prior = False
    
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
        
        self._model_circuit.negative_rinf = state
        
    def set_gaussian_prior(self, state: bool):
            
        self.gaussian_prior = state
        
    def switch_circuit_model(self, state: bool):
            
        neg_rinf, old_q, old_vsec = self._model_circuit.init_parameters()

        if state:
            # If 'state' is True, choose ModelCircuitSeries
            self._model_circuit = ModelCircuitSeries(
                negative_rinf=neg_rinf,
                q=dict(old_q),       # optionally copy to avoid reference confusion
                v_second=dict(old_vsec)
            )
        else:
            # If 'state' is False, choose ModelCircuitParallel
            self._model_circuit = ModelCircuitParallel(
                negative_rinf=neg_rinf,
                q=dict(old_q),         # optionally copy to avoid reference confusion
                v_second=dict(old_vsec)
            )
        
    def fit_model_cole(self, v_initial_guess):
        #MM should pass sigma here, probably?
        """
        Fit the model using the 'Cole' cost function.
        """
        
        print("cole")
        return self._fit_model(self._residual_cole, v_initial_guess, prior_weight=9000000)
    
    def fit_model_bode(self, v_initial_guess):
        #MM should pass sigma here, probably?
        """
        Fit the model using the 'Bode' cost function.
        """
        print("bode")
        return self._fit_model(self._residual_bode, v_initial_guess, prior_weight=500)
        
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
        z = self._model_circuit.run_model(v, freq_array)
        z_real, z_imag =z.real, z.imag
        
        # 2) Compute the special frequencies based on the slider dict 
        special_freq = self._get_special_freqs(v)
        spec_z = self._model_circuit.run_model(v, special_freq)
        spec_zr, spec_zi = spec_z.real, spec_z.imag
        
        # 3) Compute time domain values
        
        tdomain_freq, tdomain_volt, tdomain_time = self._model_circuit.run_time_domain(v, freq_array)
        
        # 4) Create a new CalculationResult
        result = CalculationResult(
            main_freq = freq_array,
            main_z_real   = z_real,
            main_z_imag   = z_imag,
            
            special_freq  = special_freq,
            special_z_real = spec_zr,
            special_z_imag = spec_zi,
            
            timedomain_freq = tdomain_freq,
            timedomain_volt = tdomain_volt,
            timedomain_time = tdomain_time
        )
        
#        print("----------------------")
#        print(tdomain_freq)
#        print('====================')
#        print(tdomain_volt)
#        print('++++++++++++++++++++')
#        print(tdomain_time)
#        print('********************')
        
        self.model_manual_result.emit(result)

        return result

    def get_latest_secondaries(self):
        """
        Return the most recent dictionary of secondary variables
        that was computed in run_model.
        """
        return dict(self._model_circuit.v_second)

    def get_model_parameters(self):
        return self._model_circuit.q | self._model_circuit.v_second  
    
    
    # ----------------------------------------------------
    # Fit Methods
    # ----------------------------------------------------
    
    def _fit_model(self, residual_func, v_given, prior_weight=0):
        """
        Fit the model using a residual function plus (optionally) a Gaussian prior
        that penalizes deviation from the initial guess in scaled space.
        """
        #0) Warning if initial guess is not valid
        if not self._valid_guess(v_given):print("Invalid Initial Guess will prevent fit")
        
        # 1) Determine free vs. locked parameters
        all_keys = list(v_given.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
    
        # 2) Build the initial guess vector (scaled) and bounds (scaled)
        x0 = self._scale_v_to_x(free_keys, v_given)
        lower_bounds, upper_bounds = self._build_bounds(free_keys)
    
        # 3) Define the function that least_squares() will minimize
        def _residual_wrapper(x_guessing):
            """
            Converts x_guessing back to parameter dict, computes the model residual,
            and optionally adds a Gaussian-prior penalty.
            
            """
            # a) Re-map from scaled to actual parameter values
            free_v_dict = self._descale_x_to_v(free_keys, x_guessing)
            locked_v_dict = {
                k: v_given[k] for k in self.disabled_variables if k in all_keys
            }
            full_v_dict = {**locked_v_dict, **free_v_dict}
            

            
            # c) Run Core model residual function
            try:
                model_residual = residual_func(full_v_dict)
    
            except ValueError:
                # MM Consider smooth penalty instead of this
                return np.ones(10_000) * 1e6
            

            # d) Optionally add Gaussian prior
            if self.gaussian_prior:
                print("Gaussian Prior")
                
                # b) Enforces validity crieria 
                if not self._valid_guess(full_v_dict):
                    penalty= np.ones(2*len(self._experiment_data["freq"])) * 1e6
                    
                    if self.gaussian_prior:
                        penalty = np.concatenate([penalty, np.ones(len(free_keys)) * 1e6])
                    return penalty
                
                
                print("actual gaussain part")
                
                prior_residual=self._compute_gaussian_prior(
                    x_guessing, x0, lower_bounds, upper_bounds, prior_weight
                )
            else:
                prior_residual = np.array([], dtype=float)
            
            # e) Return
            return np.concatenate([model_residual, prior_residual])
        
            # -------------------------------
    
        # 4) Run the solver
        result = opt.least_squares(
            _residual_wrapper,
            x0=x0,
            bounds=(lower_bounds, upper_bounds),
            method='trf',
            max_nfev=2000
        )
    
        #if not result.success:
        #   raise RuntimeError("Optimization did not converge: " + result.message)
    
        # 5) prepare results
        best_fit_free = self._descale_x_to_v(free_keys, result.x)
        best_fit_locked = {k: v_given[k] for k in self.disabled_variables if k in all_keys}
        best_fit = {**best_fit_locked, **best_fit_free}
        
        self.model_manual_values.emit(best_fit)
        
        return best_fit
                
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
   
    def _residual_cole(self, v: dict) -> np.ndarray:
        """
        Returns the residual vector [real_res1, real_res2, ..., imag_res1, imag_res2, ...].
        """
        #print("cole")
        
        freq_array = self._experiment_data["freq"]
        
        z = self._model_circuit.run_model(v, freq_array)
        z_real, z_imag=z.real, z.imag
        
        exp_real = self._experiment_data["Z_real"] 
        exp_imag = self._experiment_data["Z_imag"] 
        
        # Residual vectors. original
        real_res = z_real - exp_real
        imag_res = z_imag - exp_imag

        
        w = self._weight_function(v)
        
        return np.concatenate([real_res*w, imag_res*w]) #consider treating as 2 separate weights?

    def _residual_bode(self, v: dict) -> np.ndarray:
        """
        Similar approach: create magnitude & phase residual vectors, then concatenate.
        """
        #print("bode")
    
        freq_array = self._experiment_data["freq"]
        
        z = self._model_circuit.run_model(v, freq_array)
        z_real, z_imag =z.real, z.imag
        
        z_abs = np.sqrt(z_real**2 + z_imag**2)
        z_phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        exp_abs = np.sqrt(exp_real**2 + exp_imag**2)
        exp_phase_deg = np.degrees(np.arctan2(exp_imag, exp_real))
        
        res_abs = np.log10(z_abs) - np.log10(exp_abs)
        res_phase = np.log10(np.abs(z_phase_deg) + 1e-10) - np.log10(np.abs(exp_phase_deg) + 1e-10)
        #print(res_abs,res_phase)
        
        w = self._weight_function(v)
        
        return np.concatenate([res_abs*w, res_phase*w])

    def _weight_function(self, v):
        """
        Assigns dynamic weights to errors based on certain parameters.
        - Parameters like 'Rh', 'Rm', 'Rl' are crucial and should be weighted.
        - Uses exponential functions similar to ZarcPy.
        """
        weight = 1
        weight *= 1 + 3 * np.exp(-15 * v["Ph"])  # Prioritize high-frequency behavior
        weight *= 1 + 3 * np.exp(-15 * v["Pm"])  # Mid-frequency effects
        weight *= 1 + 3 * np.exp(-15 * v["Pl"])  # Low-frequency components
        weight *= 1 + 3 * np.exp(-15 * v["Pef"])  # Modified Zarc components
        
        return weight
        
    def _compute_gaussian_prior(self, x_guessing, x0, lower_bounds, upper_bounds, prior_weight, gaussian_fraction=5):
        # Compute sigmas (scaled standard deviations)

        sigmas = np.array([
            (ub - lb) * gaussian_fraction for lb, ub in zip(lower_bounds, upper_bounds)
        ], dtype=float)
        
        # Compute prior residual
        prior_residual = prior_weight * ((x_guessing - x0) / sigmas)
        
        return prior_residual
    
    def _valid_guess(self, v_dict):
        """Test validity criteria Fh > Fm > Fl"""
        
        return (v_dict["Fh"] >= v_dict["Fm"] and v_dict["Fm"] >= v_dict["Fl"])

    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
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
        
        x = []
        for k in keys:
            if k.startswith('P'):
                # Linear scaling
                x.append(v[k] * 10.0)
            else:
                # Logarithmic scaling
                if v[k] <= 0:
                    raise ValueError(f"Parameter {k} must be > 0; got {v[k]}.")
                x.append(np.log10(v[k]))
        return x
    
    def _descale_x_to_v(self, keys, x):
        "Receives a list of keys and a list fo values. Returns a de-scaled dictionary"
        v = {}
        for i, k in enumerate(keys):
            if k.startswith('P'):
                v[k] = x[i] / 10.0
            else:
                v[k] = 10.0 ** (x[i])
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



