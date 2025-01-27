# -*- coding: utf-8 -*-
# manual_model.py

import numpy as np
import scipy.optimize as opt
import logging
import inspect
from PyQt5.QtCore import QObject, pyqtSignal

class ModelManual(QObject):
    """
    This class replicates the circuit calculation by evaluating
    formulas from config.ini (compiled by ConfigImporter).
    Now it also calculates 'secondary variables' that used to be in Main.
    It is hardcoded because my boss made me do it :) .
    """

    model_manual_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self):
        """
        :param config_importer: an instance of ConfigImporter
        """
        super().__init__()

        # We'll store frequencies and results in these arrays
        self._experiment_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
#            "Z_real": np.zeros(5),
#            "Z_imag": np.zeros(5),
        }

        # We'll keep a copy of the secondary variables from the last run
        self._q = {}
        self._v_second = {}

    def initialize_expdata(self, file_data: dict):
        self._experiment_data= file_data

    def run_model_manual(self,v):
        z_real, z_imag = self._run_model(v)
        
        # Emit the new impedance data    
        self.model_manual_updated.emit(
            self._experiment_data["freq"],
            z_real, 
            z_imag
        )

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

    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
    
    def _fit_model(self, cost_func, v_initial_guess):
        """
        Single private helper that removes code duplication.  
        It calls the provided cost_func, e.g. _cost_function_cole or _cost_function_bode.
        """
        # 1) Choose a fixed ordering for the parameters.
        param_names = list(v_initial_guess.keys())
    
        # 2) Convert the dict to a NumPy array using that order.
        x0 = np.array([v_initial_guess[k] for k in param_names], dtype=float)
    
        # 3) Define a small wrapper for SciPy that reconstructs the dict, then calls cost_func.
        def cost_wrapper(x_array):
            v_dict = {k: x_array[i] for i, k in enumerate(param_names)}
            return cost_func(v_dict)
    
        # 4) Call scipy.optimize.minimize on the wrapper.
        result = opt.minimize(
            cost_wrapper,
            x0=x0,
            method='Nelder-Mead',
        )
    
        if not result.success:
            print("Optimization failed:", result.message)
            raise RuntimeError("Optimization did not converge.")
    
        # 5) Reconstruct a dict for the best-fit parameters:
        best_fit_array = result.x
        best_fit_dict = {k: best_fit_array[i] for i, k in enumerate(param_names)}
    
        # Finally, run the model with these best-fit params 
        # so that _modeled_data is updated and signals are emitted.
        self.run_model_manual(best_fit_dict)
    
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

    def _run_model(self, v):
        """
        The main model used in cost functions.
        """
        self._calculate_secondary_variables(v)
        v2 = self._v_second

        zr_list = []
        zi_list = []

        for freq in self._experiment_data["freq"]:
            # Inductor
            zinf = self._inductor(freq, v["Linf"])

            # Parallel system
            z_line_h = v2["pRh"] + self._cpe(freq, v2["pQh"], v["Ph"], v["Ph"])
            z_line_m = v2["pRm"] + self._cpe(freq, v2["pQm"], v["Pm"], v["Pm"])
            z_line_l = v2["pRl"] + self._cpe(freq, v2["pQl"], v["Pl"], v["Pl"])

            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, v2["R0"])
            zparallel = self._parallel(z_line_h, z_rock)

            z_cpee = self._cpe(freq, v["Qe"], v["Pef"], v["Pei"])
            zarce = self._parallel(z_cpee, v["Re"])

            z_total = zinf + zparallel + zarce
            zr_list.append(z_total.real)
            zi_list.append(z_total.imag)

        return np.array(zr_list), np.array(zi_list)
        
    def _cost_function_cole(self, v):
        """
        EIS cost function with separate comparisons for real and imaginary parts.
        """
        z_real, z_imag = self._run_model(v)
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]

        diff_real = (z_real - exp_real) ** 2
        diff_imag = (z_imag - exp_imag) ** 2

        return np.sum(diff_real + diff_imag)
    
    def _cost_function_bode(self, v):
        """
        Bode cost function that compares magnitude and phase.
        """
        z_real, z_imag = self._run_model(v)
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
        return (2 * np.pi * freq) * linf *1j
        
    def _q_from_f0(self, r , f0, p):
        return 1.0 / (r * (2.0 * np.pi * f0)**p)
        
    def _cpe(self, freq , q, pf, pi):
        phase_factor = (1j)**pi
        omega_exp = (2.0 * np.pi * freq)**pf
        return 1.0 / (q * phase_factor * omega_exp)
        
    def _parallel(self,z_1, z_2):
        denominator= (1/z_1) + (1/z_2)
        return 1/denominator

# -----------------------------------------------------------------------
#  TEST FOR UPDATED ModelManual
# -----------------------------------------------------------------------
def test_model_manual():
    """
    Manual test function to verify the ModelManual class works.
    Run this in a standalone Python session or integrate into your test suite.
    """
    model = ModelManual()

    # Example experimental data (synthetic)
    test_freq = np.array([1, 10, 100, 1000, 10000], dtype=float)
    test_Zr = np.array([50, 40, 30, 20, 10], dtype=float)
    test_Zi = np.array([0, -10, -20, -30, -40], dtype=float)
    file_data = {
        "freq": test_freq,
        "Z_real": test_Zr,
        "Z_imag": test_Zi,
    }
    model.initialize_expdata(file_data)

    # Example initial guess
    v_init = {
        "Rinf": 10.0,
        "Linf": 1e-6,
        "Rh": 100.0,
        "Fh": 1000.0,
        "Ph": 0.8,
        "Rm": 100.0,
        "Fm": 1000.0,
        "Pm": 0.8,
        "Rl": 100.0,
        "Fl": 1000.0,
        "Pl": 0.8,
        "Re": 50.0,
        "Qe": 1e-5,
        "Pef": 0.8,
        "Pei": 0.8,
    }

    # Fit using the Cole cost function
    best_fit_cole = model.fit_model_cole(v_init)
    print("Best-fit parameters (Cole):")
    for k, val in best_fit_cole.items():
        print(f"  {k}: {val}")

    z_real_fit_cole = model._modeled_data["Z_real"]
    z_imag_fit_cole = model._modeled_data["Z_imag"]
    print("Final model fit (Z_real) [Cole]:", z_real_fit_cole)
    print("Final model fit (Z_imag) [Cole]:", z_imag_fit_cole)

    # Fit using the Bode cost function
    best_fit_bode = model.fit_model_bode(v_init)
    print("\nBest-fit parameters (Bode):")
    for k, val in best_fit_bode.items():
        print(f"  {k}: {val}")

    z_real_fit_bode = model._modeled_data["Z_real"]
    z_imag_fit_bode = model._modeled_data["Z_imag"]
    print("Final model fit (Z_real) [Bode]:", z_real_fit_bode)
    print("Final model fit (Z_imag) [Bode]:", z_imag_fit_bode)

    print("\nDone with manual test.")

# -----------------------------------------------------------------------
#  If you want to run this test immediately when script is invoked:
# -----------------------------------------------------------------------
if __name__ == "__main__":
    test_model_manual()