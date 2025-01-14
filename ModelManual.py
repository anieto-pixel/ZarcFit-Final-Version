# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

ModelManual is a widget that calculates combined impedance from:
  - R + jωL (resistor + inductor in series)
  - Zarc circuits (H, M, L)
  - An optional 'modified Zarc' (E) circuit

Emits a signal (model_manual_updated) whenever it recalculates,
passing the new Z_real and Z_imag arrays.
"""

import numpy as np
import configparser
import logging

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal


class ModelManual(QObject):

    # This signal now carries three np.ndarrays (freq, Z_real, Z_imag)
    model_manual_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self):
        super().__init__()
        
        # Example data; in practice, you'll replace these with your own.
        self._modeled_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

    # -----------------------------------------------------------------------
    #  Public Interface
    # -----------------------------------------------------------------------
    def initialize_frequencies(self, key, np_array):
        """
        Replaces 'freq' in self._modeled_data, resets default values, and re-runs the model.
        """
        if key not in self._modeled_data:
            logging.error(f"Key '{key}' not found in modeled data.")
            return
        self._modeled_data[key] = np_array
        # If needed, you could also reset Z_real, Z_imag here or run_model again

    def run_model(self, v):
        """
        Recalculate impedance using the given parameter dictionary `v`.
        """
        modeling_z_real = []
        modeling_z_imag = []

        # 1) FIX: iterate over the array of frequencies
        for freq in self._modeled_data['freq']:
            z = self._circuit(freq, v)
            modeling_z_real.append(z.real)
            modeling_z_imag.append(z.imag)

        # Update the stored results
        self._modeled_data['Z_real'] = np.array(modeling_z_real)
        self._modeled_data['Z_imag'] = np.array(modeling_z_imag)

        # Emit updated signal
        self.model_manual_updated.emit(
            self._modeled_data['freq'],
            self._modeled_data['Z_real'],
            self._modeled_data['Z_imag']
        )

    # -----------------------------------------------------------------------
    #  Private helpers
    # -----------------------------------------------------------------------
    def _inductor(self, freq, ind):
        """
        Impedance of an inductor: Z = jωL = j(2πfL)
        """
        return 1j * (2 * np.pi * freq) * ind

    def _cpe_q(self, freq, q, p_i, p_f):
        """
        Constant phase element: Z = 1 / (Q * (j^p_i) * (ω^p_f))
        """
        phase_factor = (1j)**p_i
        omega_exp    = (2.0 * np.pi * freq)**p_f
        return 1.0 / (q * phase_factor * omega_exp)

    def _parallel_circuit(self, z_1, z_2):
        """
        Two impedances in parallel: Z = (Z1*Z2)/(Z1+Z2)
        """
        return (z_1 * z_2) / (z_1 + z_2) if (z_1 + z_2) != 0 else 0

    def _circuit(self, freq, v):
        """
        Builds the total impedance of the circuit, using parameters in `v`.
        """

        # 0) Inductor in series
        z_0 = self._inductor(freq, v['Linf'])

        # 1) A parallel set
        #    1.0 resistor + CPE in series
        cpe_h = self._cpe_q(freq, v['pQh'], v['Ph'], v['Ph'])
        z_h  = cpe_h + v['pRh']

        # 1.1 The rock: three branches in parallel
        #     1.1.0 resistor + cpe_l in series
        cpe_l  = self._cpe_q(freq, v['pQl'], v['Pl'], v['Pl'])
        z_l  = cpe_l + v['pRl']   # FIX: use cpe_l

        #     1.1.1 resistor + cpe_m in series
        cpe_m  = self._cpe_q(freq, v['pQm'], v['Pm'], v['Pm'])
        z_m  = cpe_m + v['pRm']   # FIX: use cpe_m

        # 1.1.2 combine z_110 and z_111 in parallel
        z_m_l = self._parallel_circuit(z_m, z_l)

        # combine that result in parallel with R0
        z_rock = self._parallel_circuit(v['R0'], z_m_l)

        # 1) final parallel among z_10 and z_11
        z_1 = self._parallel_circuit(z_h, z_rock)

        # 2) A "modified Zarc" in parallel with a resistor
        cpe_e = self._cpe_q(freq, v['Qe'], v['Pe_i'], v['Pe_f'])
        z_2   = self._parallel_circuit(cpe_e, v['Re'])

        # total impedance = everything in series
        z_total = z_0 + z_1 + z_2

        return z_total


#---------------------------------------------------------
#   TEST
#---------------------------------------------------------

import numpy as np
import sys

def test_model_changes():
    """
    Quick test to confirm that adjusting the 'L' parameters (pQl, Pl, pRl)
    changes the computed Z values in ModelManual.
    """

    model = ModelManual()

    # We'll define a dictionary `v` with *all* parameters used in `_circuit()`.
    # (Adjust the numbers to your needs.)
    v_initial = {
        "Linf": 1e-6,   # Inductor
        "pQh": 1e-4,    # High-frequency CPE magnitude
        "Ph": 0.8,      # High-frequency CPE exponent
        "pRh": 10.0,    # High-frequency resistor

        "pQl": 1e-5,    # Low-frequency CPE magnitude
        "Pl": 0.7,      # Low-frequency CPE exponent
        "pRl": 50.0,    # Low-frequency resistor

        "pQm": 1e-5,    # Mid-frequency CPE magnitude
        "Pm": 0.9,      # Mid-frequency CPE exponent
        "pRm": 15.0,    # Mid-frequency resistor

        "R0": 1.0,      # Another resistor in parallel

        "Qe": 1e-4,     # "Modified Zarc" CPE magnitude
        "Pe_i": 0.8,    # CPE exponent (phase factor)
        "Pe_f": 0.8,    # CPE exponent for omega
        "Re": 25.0,     # Resistor in parallel with the "modified Zarc"
    }

    # Run model the first time
    model.run_model(v_initial)
    freq_baseline = model._modeled_data["freq"].copy()
    Zr_baseline   = model._modeled_data["Z_real"].copy()
    Zi_baseline   = model._modeled_data["Z_imag"].copy()

    # Print baseline for reference
    print("=== Baseline (original) ===")
    for f, zr, zi in zip(freq_baseline, Zr_baseline, Zi_baseline):
        print(f"freq={f:6g} Hz -> Zr={zr:8.3f}, Zi={zi:8.3f}")

    # Now let's modify just the "L" branch significantly
    v_changed = dict(v_initial)  # copy
    v_changed["pQl"] = 1e-3   # increase by 100x
    v_changed["Pl"]  = 0.5    # change exponent
    v_changed["pRl"] = 500.0  # 10x bigger resistor

    # Run again
    model.run_model(v_changed)
    freq_new = model._modeled_data["freq"].copy()
    Zr_new   = model._modeled_data["Z_real"].copy()
    Zi_new   = model._modeled_data["Z_imag"].copy()

    # Print new results for comparison
    print("\n=== Changed L-branch parameters ===")
    for f, zr, zi in zip(freq_new, Zr_new, Zi_new):
        print(f"freq={f:6g} Hz -> Zr={zr:8.3f}, Zi={zi:8.3f}")

    # Check differences
    same_real = np.allclose(Zr_baseline, Zr_new, atol=1e-12, rtol=1e-3)
    same_imag = np.allclose(Zi_baseline, Zi_new, atol=1e-12, rtol=1e-3)

    if same_real and same_imag:
        print("\n[WARNING] Changing pQl, Pl, and pRl produced almost NO change!")
        print("Check if your parameter changes are large enough or if there's a bug.")
    else:
        print("\n[OK] Changing pQl, Pl, and pRl produced different results, as expected.")

if __name__ == "__main__":
    # If you run this script directly, it will do the test:
    test_model_changes()
    sys.exit(0)