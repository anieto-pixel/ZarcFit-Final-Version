# -*- coding: utf-8 -*-
# manual_model.py

import numpy as np
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
        self._modeled_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.zeros(5),
            "Z_imag": np.zeros(5),
        }

        # We'll keep a copy of the secondary variables from the last run
        self._q = {}
        self._v_second = {}

    def initialize_frequencies(self, freq_array: np.ndarray):
        """
        Initializes the frequency array used for model calculations.
        """
        self._modeled_data['freq'] = freq_array
        self._modeled_data['Z_real'] = np.zeros_like(freq_array)
        self._modeled_data['Z_imag'] = np.zeros_like(freq_array)

    def run_model(self, v):
        
        #v is v_sliders, shortene dname for readability
        """
        """
        # 1) Compute or update secondary variables
        self._calculate_secondary_variables(v)

        Zr_list = []
        Zi_list = []

        # Combine the user’s slider dictionary with v_seco
        for freq in self._modeled_data["freq"]:
            zinf = self._inductor(freq, v["Linf"]) + v["Rinf"]
            
            z_cpeh = self._cpe(freq, v["Rh"], self._q["Qh"], v["Ph"], v["Ph"])
            zarch = self._parallel(z_cpeh, v["Rh"])
            
            z_cpem = self._cpe(freq, v["Rm"], self._q["Qm"], v["Pm"], v["Pm"])
            zarcm =  self._parallel(z_cpem, v["Rm"])
            
            z_cpel = self._cpe(freq, v["Rl"], self._q["Ql"], v["Pl"], v["Pl"])
            zarcl = self._parallel(z_cpel, v["Rl"])
            
            z_cpee = self._cpe(freq, v["Re"], v["Qe"], v["Pef"], v["Pei"])
            zarce = self._parallel(z_cpee, v["Re"])

            # Evaluate final formula
            Z_total = zinf + zarch + zarcm + zarcl + zarce

            Zr_list.append(Z_total.real)
            Zi_list.append(Z_total.imag)

        # Update the arrays
        self._modeled_data["Z_real"] = np.array(Zr_list)
        self._modeled_data["Z_imag"] = np.array(Zi_list)

        # Emit the new impedance data
        self.model_manual_updated.emit(
            self._modeled_data["freq"],
            self._modeled_data["Z_real"],
            self._modeled_data["Z_imag"]
        )

    
    def get_latest_secondaries(self):
        """
        Return the most recent dictionary of secondary variables
        that was computed in run_model.
        """
        return dict(self._v_second)

    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
    def _calculate_secondary_variables(self, v):
        """
        Computes 'series' and 'parallel' secondary variables
        Returns a dict of newly calculated secondary variables.
        """
        
        print(v)
        
        Qh = self._q_from_f0( v["Rh"], v["Fh"], v["Ph"])
        Qm = self._q_from_f0( v["Rm"], v["Fm"], v["Pm"])
        Ql = self._q_from_f0( v["Rl"], v["Fl"], v["Pl"])
        
        print(self._q)
        
        self._q["Qh"]=Qh
        self._q["Qm"]=Qm
        self._q["Ql"]=Ql

        self._v_second["R0"] = v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]
        self._v_second["pRh"] = v["Rinf"]*(v["Rinf"] + v["Rh"])/v["Rh"]
        self._v_second["pQh"] = Qh*(v["Rh"]/(v["Rinf"] + v["Rh"]))**2
        self._v_second["pRm"] = (v["Rinf"] + v["Rh"])*(v["Rinf"] + v["Rh"] +v["Rm"])/v["Rm"]
        self._v_second["pQm"] = Qm*(v["Rm"]/(v["Rinf"] + v["Rh"] + v["Rm"]))**2
        self._v_second["pRl"] = (v["Rinf"] + v["Rh"] + v["Rm"])*(v["Rinf"] + v["Rh"] + v["Rm"] +v["Rl"])/v["Rl"]
        self._v_second["pQl"] = Ql*(v["Rl"]/(v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]))**2
        
    # ----------------------------------------------------
    # Circuit Methods
    # ----------------------------------------------------

    def _inductor(self, freq, linf):
        return (2 * np.pi * freq) * linf *1j
        
    def _q_from_f0(self, r , f0, p):
        return 1.0 / (r * (2.0 * np.pi * f0)**p)
        
    def _cpe(self, freq, r , q, pf, pi):
        phase_factor = (1j)**pi
        omega_exp = (2.0 * np.pi * freq)**pf
        return 1.0 / (q * phase_factor * omega_exp)
        
    def _parallel(self,z_1, z_2):
        denominator= (1/z_1) + (1/z_2)
        return 1/denominator

# -----------------------------------------------------------------------
#  TEST FOR UPDATED ModelManual with CustomSliders
# -----------------------------------------------------------------------
