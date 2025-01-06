# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 15:42:43 2025

@author: agarcian
"""

import numpy as np
import configparser
import scipy.optimize as opt

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton

# Updated imports (class name changes)
from WidgetSliders import WidgetSliders
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ConfigImporter import ConfigImporter
from ModelManual import Model

class ModelCalculator(Model):
    

    def __init__(self, variables_keys, variables_default_values, experiment_data):
        
        super().__init__(variables_keys, variables_default_values)
        
        self._experiment_data=[]
        
        
        self._calculate_all_variables()
        self.reset_experiment_values(experiment_data)
        
        
    
    
    def _calculate_all_variables(self):
        linf = self._variables_dictionary["linf"]
        rinf = self._variables_dictionary["rinf"]
        rh = self._variables_dictionary["rh"]
        fh = self._variables_dictionary["fh"]
        ph = self._variables_dictionary["ph"]
        rm = self._variables_dictionary["rm"]
        fm = self._variables_dictionary["fm"]
        pm = self._variables_dictionary["pm"]
        rl = self._variables_dictionary["rl"]
        fl = self._variables_dictionary["fl"]
        pl = self._variables_dictionary["pl"]
        re = self._variables_dictionary["re"]
        qe = self._variables_dictionary["qe"]
        pe_f = self._variables_dictionary["pe_f"]
        pe_i = self._variables_dictionary["pe_i"]
        
        qh = 1/(rh*(2*np.pi*fh)**ph)
        qm = 1/(rm*(2*np.pi*fm)**pm) #### Calculating Qs from given resonant frequencies
        ql = 1/(rl*(2*np.pi*fl)**pl)
        
        r0 = rinf + rh + rm + rl    ### Randy's series to parallel parameter conversions
        rh_p = rinf/rh*(rinf+rh)
        qh_p = qh*(rh/(rinf+rh))**2
        rm_p = (rinf+rh)/rm*(rinf+rh+rm)
        qm_p = qm*(rm/(rinf+rh+rm))**2
        rl_p = (rinf+rh+rm)/rl*(rinf+rh+rm+rl)
        ql_p = ql*(rl/(rinf+rh+rm+rl))**2
        
        self._variables_dictionary["r0"]=r0
        self._variables_dictionary["rh_p"]=rh_p
        self._variables_dictionary["qh_p"]=qh_p
        self._variables_dictionary["rm_p"]=rm_p
        self._variables_dictionary["qm_p"]=qm_p
        self._variables_dictionary["rl_p"]=rl_p
        self._variables_dictionary["ql_p"]=ql_p
        
        
        #[R0p,RHp,QHp,RMp,QMp,RLp,QLp,pCh,pCm,pCl]
    
    def _model(self,freq):
        
        # 0.0 an inductor
        z_0 = self._inductor(freq, l_key='linf')
        
        #the rock (z_1)
        # 1.0 a resistence
        z_10 = self._variables_dictionary["r0"]
        
        # 1.1 a m cpe and a resistence in series
        cpe_m=self._cpe_q(freq, q_key='qm_p', p_i_key='pm', p_f_key='pm')
        p_rm = self._variables_dictionary["rm_p"]
        
        z_11=p_rm + cpe_m
        
        # 1.2 a l cpe and a resistence in series
        cpe_l=self._cpe_q(freq, q_key='ql_p', p_i_key='pl', p_f_key='pl')
        p_rl = self._variables_dictionary["rl_p"]
        
        z_12=p_rl + cpe_l
        
        #the resistor parallel to the medium circuit
        #both parallel to the low circuit
        z_r_cpem=self._parallel_circuit(z_10,z_11)
        z_1=self._parallel_circuit(z_r_cpem,z_12)
        
        # 2.0 a cpe and a resistor in series
        cpe_h=self._cpe_q(freq, q_key='qh_p', p_i_key='ph', p_f_key='ph')
        p_rh = self._variables_dictionary["rh_p"]
        
        z_20=p_rh + cpe_h
        
        #2.1 in parallel to the rock(z_1)
        z_2=self._parallel_circuit(z_1,z_20)
        
        # 3. a modified CPE-R 
        cpe_e=self._cpe_q(freq, q_key='qe', p_i_key='pe_i', p_f_key='pe_f')
        resistor_e=self._variables_dictionary['re']
        
        z_3=self._parallel_circuit(cpe_e,resistor_e)
        
        #Total: z_0, z_2 and z_3 in series
        z_total_complex = z_0 + z_2 + z_3
        
        return z_total_complex

    def _fit_model(self):
        """
        Fits the model to the experimental data using the Nelder-Mead simplex algorithm.
        Mimics the functionality of a 'fit_curve' approach.
        """

        # Parameter names and initial guesses
        param_names = list(self._variables_dictionary.keys())
        initial_guess = [self._variables_dictionary[name] for name in param_names]

        # Objective function for sum of squared real & imaginary residuals
        def objective_function(params):
            # Update variables with guess
            for i, name in enumerate(param_names):
                self._variables_dictionary[name] = params[i]
            
            # Re-run the model with updated params
            self._run_model()
            
            # Compare with experiment data
            diff_real = self._experiment_data["Z_real"] - self._modeled_data["Z_real"]
            diff_imag = self._experiment_data["Z_imag"] - self._modeled_data["Z_imag"]
            
            return np.sum(diff_real**2) + np.sum(diff_imag**2)

        # Perform the minimization
        result = opt.minimize(objective_function, initial_guess, method='Nelder-Mead', options={'maxiter': 700})

        # Update the dictionary with the best fit values
        for i, name in enumerate(param_names):
            self._variables_dictionary[name] = result.x[i]

        # Return the updated dictionary or you could just keep it stored
        return self._variables_dictionary

    def reset_experiment_values(self, experiment_data):
        """
        A simple method to reset or load experimental values.
        Expects a dictionary with keys 'freq', 'z_real', 'z_imag'.
        """
        self._experiment_data=experiment_data
        self._modeled_data['freq'] = self._experiment_data['freq']
        self._reset_values(self._variables_default_values)


 # -----------------------------------------------------------------------
 #  TEST
 # -----------------------------------------------------------------------

import numpy as np
import scipy.optimize as opt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt

class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Fit Test")
        self.setGeometry(100, 100, 1200, 600)

        # Hardcoded experimental data
        synthetic_data = {
            'freq': np.array([1.00000000e+00, 1.12332403e+00, 1.26185688e+00, 1.41747416e+00, 1.59228279e+00,
                              1.78864953e+00, 2.00923300e+00, 2.25701972e+00, 2.53536449e+00, 2.84803587e+00,
                              3.19926714e+00, 3.59381366e+00, 4.03701726e+00, 4.53487851e+00, 5.09413801e+00,
                              5.72236766e+00, 6.42807312e+00, 7.22080902e+00, 8.11130831e+00, 9.11162756e+00,
                              1.02353102e+01, 1.14975700e+01, 1.29154967e+01, 1.45082878e+01, 1.62975083e+01,
                              1.83073828e+01, 2.05651231e+01, 2.31012970e+01, 2.59502421e+01, 2.91505306e+01,
                              3.27454916e+01, 3.67837977e+01, 4.13201240e+01, 4.64158883e+01, 5.21400829e+01,
                              5.85702082e+01, 6.57933225e+01, 7.39072203e+01, 8.30217568e+01, 9.32603347e+01,
                              1.04761575e+02, 1.17681195e+02, 1.32194115e+02, 1.48496826e+02, 1.66810054e+02,
                              1.87381742e+02, 2.10490414e+02, 2.36448941e+02, 2.65608778e+02, 2.98364724e+02,
                              3.35160265e+02, 3.76493581e+02, 4.22924287e+02, 4.75081016e+02, 5.33669923e+02,
                              5.99484250e+02, 6.73415066e+02, 7.56463328e+02, 8.49753436e+02, 9.54548457e+02,
                              1.07226722e+03, 1.20450354e+03, 1.35304777e+03, 1.51991108e+03, 1.70735265e+03,
                              1.91791026e+03, 2.15443469e+03, 2.42012826e+03, 2.71858824e+03, 3.05385551e+03,
                              3.43046929e+03, 3.85352859e+03, 4.32876128e+03, 4.86260158e+03, 5.46227722e+03,
                              6.13590727e+03, 6.89261210e+03, 7.74263683e+03, 8.69749003e+03, 9.77009957e+03,
                              1.09749877e+04, 1.23284674e+04, 1.38488637e+04, 1.55567614e+04, 1.74752840e+04,
                              1.96304065e+04, 2.20513074e+04, 2.47707636e+04, 2.78255940e+04, 3.12571585e+04,
                              3.51119173e+04, 3.94420606e+04, 4.43062146e+04, 4.97702356e+04, 5.59081018e+04,
                              6.28029144e+04, 7.05480231e+04, 7.92482898e+04, 8.90215085e+04, 1.00000000e+05]),
            'Z_real': np.array([67.87503748, 67.86300211, 67.84980166, 67.83532276, 67.819441, 67.80201983,
                                67.78290946, 67.76194552, 67.73894772, 67.71371836, 67.68604069, 67.6556772,
                                67.62236769, 67.58582729, 67.54574429, 67.50177787, 67.45355564, 67.40067114,
                                67.34268117, 67.27910302, 67.20941167, 67.13303687, 67.04936027, 66.95771247,
                                66.8573701, 66.74755295, 66.6274211, 66.49607204, 66.35253775, 66.19578166,
                                66.02469534, 65.83809483, 65.63471635, 65.41321127, 65.17214016, 64.90996568,
                                64.62504439, 64.31561751, 63.97980089, 63.61557473, 63.22077403, 62.79308073,
                                62.33001946, 61.82895889, 61.28712137, 60.70160416, 60.0694161, 59.38753393,
                                58.65298287, 57.86294518, 57.0148995, 56.10679041, 55.13722321, 54.10567263,
                                53.01268632, 51.8600577, 50.65093803, 49.38985985, 48.08265245, 46.73624673,
                                45.35838666, 43.95728333, 42.5412581, 41.11842143, 39.69642212, 38.28228387,
                                36.88232713, 35.50216036, 34.14671725, 32.82031707, 31.52672951, 30.26923215,
                                29.05065545, 27.87341462, 26.73953084, 25.65064553, 24.60803098, 23.61260034,
                                22.66491842, 21.76521471, 20.91339862, 20.10907747, 19.35157707, 18.63996494,
                                17.97307618, 17.34954168, 16.76781838, 16.22622076, 15.7229528, 15.25613939,
                                14.82385637, 14.42415817, 14.05510256, 13.71477215, 13.40129234, 13.11284578,
                                12.84768366, 12.60413392, 12.38060686, 12.1755985]),
            'Z_imag': np.array([-0.08312716, -0.09084011, -0.09926442, -0.10846431, -0.11850948, -0.12947551,
                                -0.14144429, -0.15450444, -0.16875178, -0.18428975, -0.20122989, -0.21969232,
                                -0.23980615, -0.26170996, -0.28555218, -0.31149154, -0.33969737, -0.37034998,
                                -0.40364089, -0.43977309, -0.47896121, -0.52143169, -0.56742292, -0.61718532,
                                -0.67098158, -0.72908683, -0.79178903, -0.85938951, -0.93220364, -1.01056185,
                                -1.09481079, -1.18531472, -1.28245691, -1.38664085, -1.49829094, -1.61785212,
                                -1.74578781, -1.88257539, -2.02869817, -2.18463294, -2.35083182, -2.52769735,
                                -2.71554978, -2.91458561, -3.12482694, -3.34606161, -3.57777512, -3.81907656,
                                -4.06862244, -4.32454503, -4.584394, -4.84510339, -5.10299748, -5.35384999,
                                -5.59300748, -5.81558186, -6.01670508, -6.19182594, -6.33701511, -6.44923644,
                                -6.52654278, -6.56816601, -6.5744901, -6.54691873, -6.48766728, -6.39951844,
                                -6.28558006, -6.14907466, -5.99317698, -5.82090366, -5.63504965, -5.43816108,
                                -5.2325331, -5.02022219, -4.80306556, -4.58270225, -4.36059342, -4.13804023,
                                -3.91619923, -3.69609483, -3.47862909, -3.26458866, -3.05464906, -2.84937638,
                                -2.64922697, -2.4545457, -2.26556361, -2.0823957, -1.90503953, -1.73337502,
                                -1.56716558, -1.40606048, -1.24959809, -1.09720957, -0.94822248, -0.80186382,
                                -0.65726203, -0.51344759, -0.36935188, -0.22380406])
        }

        # Define keys and default values for the model
        variables_keys = [
            'linf', 'rinf', 'rh', 'fh', 'ph', 'rm', 'fm', 'pm', 'rl', 'fl', 'pl', 're', 'qe', 'pe_f', 'pe_i'
        ]
        variables_default_values = [
            1e-6, 10, 5, 1e3, 0.9, 2, 1e4, 0.8, 1, 1e2, 0.7, 50, 1e-5, 0.8, 0.2
        ]

        # Create an instance of ModelCalculator
        self.model_calculator = ModelCalculator(variables_keys, variables_default_values,synthetic_data)

        # Main layout
        main_layout = QHBoxLayout(self)

        layout_1 = QVBoxLayout()
        # Add "Fit Curve" button
        self.fit_button = QPushButton("Fit Curve")
        self.fit_button.clicked.connect(self.run_fit_test)

        layout_1.addWidget(self.fit_button)

        # Add a label for clarity
        self.label_modeled_data = QLabel("Modeled Data vs Experimental Data")
        self.label_modeled_data.setAlignment(Qt.AlignCenter)
        layout_1.addWidget(self.label_modeled_data)

        # Impedance table: freq, Z_real (Model), Z_imag (Model), Z_real (Exp), Z_imag (Exp)
        self.table_imp = QTableWidget(len(synthetic_data['freq']), 5)
        self.table_imp.setHorizontalHeaderLabels([
            "Frequency", "Z_real (Model)", "Z_imag (Model)", "Z_real (Exp)", "Z_imag (Exp)"
        ])
        self.update_impedance_table(synthetic_data)
        layout_1.addWidget(self.table_imp)

        layout_2 = QVBoxLayout()
        # Add a label for variable data
        self.label_variable_data = QLabel("Model Parameters")
        self.label_variable_data.setAlignment(Qt.AlignCenter)
        layout_2.addWidget(self.label_variable_data)

        # Variables table
        self.table_vars = QTableWidget(len(variables_keys), 2)
        self.table_vars.setHorizontalHeaderLabels(["Variable", "Value"])
        for i, key in enumerate(variables_keys):
            self.table_vars.setItem(i, 0, QTableWidgetItem(key))
            self.table_vars.setItem(i, 1, QTableWidgetItem(str(variables_default_values[i])))
        layout_2.addWidget(self.table_vars)

        main_layout.addLayout(layout_1)
        main_layout.addLayout(layout_2)

    def update_impedance_table(self, data):
        modeled_z_real = self.model_calculator._modeled_data['Z_real']
        modeled_z_imag = self.model_calculator._modeled_data['Z_imag']
        num_rows = len(data['freq'])

        # Update the table row count to match the available data
        self.table_imp.setRowCount(num_rows)

        for i in range(num_rows):
            freq = data['freq'][i]
            self.table_imp.setItem(i, 0, QTableWidgetItem(f"{freq:.2f}"))

            # Check if modeled data exists for the index
            if i < len(modeled_z_real):
                self.table_imp.setItem(i, 1, QTableWidgetItem(f"{modeled_z_real[i]:.6f}"))
                self.table_imp.setItem(i, 2, QTableWidgetItem(f"{modeled_z_imag[i]:.6f}"))
            else:
                self.table_imp.setItem(i, 1, QTableWidgetItem("-"))
                self.table_imp.setItem(i, 2, QTableWidgetItem("-"))

            self.table_imp.setItem(i, 3, QTableWidgetItem(f"{data['Z_real'][i]:.6f}"))
            self.table_imp.setItem(i, 4, QTableWidgetItem(f"{data['Z_imag'][i]:.6f}"))

    def run_fit_test(self):
        print("Starting the fit process...")
        self.model_calculator._fit_model()
        print("Fitting process completed.")

        # Update the variables table
        for i, key in enumerate(self.model_calculator._variables_keys):
            value = self.model_calculator._variables_dictionary[key]
            self.table_vars.setItem(i, 1, QTableWidgetItem(str(value)))

        # Update the impedance table with the new modeled data
        self.update_impedance_table(self.model_calculator._experiment_data)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    test_widget = TestWidget()
    test_widget.show()
    sys.exit(app.exec_())


