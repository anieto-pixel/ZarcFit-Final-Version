import inspect
import logging
from dataclasses import dataclass

import numpy as np
import scipy.optimize as opt
import scipy.signal as sig
from scipy.interpolate import interp1d
from scipy.optimize import Bounds

from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal

# Bounds are scaled. Need to add padding for 0 values, handle Qei,
# and implement a way of making Rinf negative.


@dataclass
class CalculationResult:
    """
    Container for main and special impedance data.
    """
    main_freq: np.ndarray = None  # The frequency array used for the main curve
    main_z_real: np.ndarray = None
    main_z_imag: np.ndarray = None
    
    rock_z_real: np.ndarray = None
    rock_z_imag: np.ndarray = None

    special_freq: np.ndarray = None  # The 3 special frequencies
    special_z_real: np.ndarray = None
    special_z_imag: np.ndarray = None

    timedomain_freq: np.ndarray = None  # Elements used for the time domain plot
    timedomain_time: np.ndarray = None
    timedomain_volt: np.ndarray = None


###############################################################################
# Circuit Models
###############################################################################
class ModelCircuitParent(object):
    """
    Parent class for circuit models.
    """
    def __init__(self, negative_rinf=False, q=None, v_second=None, v_others=None):
        super().__init__()
        # Avoid mutable default arguments; properly assign attributes.
        if q is None:
            q = {}
        if v_second is None:
            v_second = {}
        # Attributes
        self.name=""
        
        self.negative_rinf = negative_rinf
        self.q = q
        self.v_second = v_second
        self.v_others=v_others

    # ------------------------------------------
    # Public Methods
    # ------------------------------------------
    def init_parameters(self):
        """Return the current state of the model's attributes."""
        return self.negative_rinf, self.q, self.v_second

    def run_model(self, v: dict, freq_array: np.ndarray):
        """
        Model of an electric circuit that uses the received values v as variables
        and returns the impedance array of the circuit.
        """
        return np.array([])

    def run_rock(self, v: dict, freq_array: np.ndarray):
        """Placeholder method for a variant of the circuit model."""
        return np.array([])

    # ------------------------------------------
    # Private Methods
    # ------------------------------------------
    def _calculate_secondary_variables(self, v):
        """
        Compute 'series' and 'parallel' secondary variables.

        Returns a dict of newly calculated secondary variables.
        """
        Qh = self._q_from_f0(v["Rh"], v["Fh"], v["Ph"])
        Qm = self._q_from_f0(v["Rm"], v["Fm"], v["Pm"])
        Ql = self._q_from_f0(v["Rl"], v["Fl"], v["Pl"])

        self.q["Qh"] = Qh
        self.q["Qm"] = Qm
        self.q["Ql"] = Ql

        self.v_second["R0"] = v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]
        self.v_second["pRh"] = v["Rinf"] * (v["Rinf"] + v["Rh"]) / v["Rh"]
        self.v_second["pQh"] = Qh * (v["Rh"] / (v["Rinf"] + v["Rh"])) ** 2
        self.v_second["pRm"] = (v["Rinf"] + v["Rh"]) * (v["Rinf"] + v["Rh"] + v["Rm"]) / v["Rm"]
        self.v_second["pQm"] = Qm * (v["Rm"] / (v["Rinf"] + v["Rh"] + v["Rm"])) ** 2
        self.v_second["pRl"] = (v["Rinf"] + v["Rh"] + v["Rm"]) * (v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"]) / v["Rl"]
        self.v_second["pQl"] = Ql * (v["Rl"] / (v["Rinf"] + v["Rh"] + v["Rm"] + v["Rl"])) ** 2
        
        self.v_second["Ch"]= 1/(2*np.pi*v["Fh"]*v["Rh"] )
        self.v_second["pCh"]=1/(2*np.pi*v["Fh"]*self.v_second["pRh"] )
        self.v_second["Cm"]=1/(2*np.pi*v["Fm"]*v["Rm"] )
        self.v_second["pCm"]=1/(2*np.pi*v["Fm"]*self.v_second["pRm"] )
        self.v_second["Cl"]=1/(2*np.pi*v["Fl"]*v["Rl"] )
        self.v_second["pCl"] =1/(2*np.pi*v["Fl"]*self.v_second["pRl"] )
        
    def _inductor(self, freq, linf):
        """
        Return the impedance of an inductor at a given frequency and inductance.
        """
        if linf == 0:
            raise ValueError("Inductance (linf) cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency cannot be negative.")
        result = (2 * np.pi * freq) * linf * 1j
        return result

    def _q_from_f0(self, r, f0, p):
        """
        Return the Q of a CPE given the f0.
        """
        if r == 0:
            raise ValueError("Resistance r cannot be zero.")
        if f0 <= 0:
            raise ValueError("Resonant frequency f0 must be positive.")
        result = 1.0 / (r * (2.0 * np.pi * f0) ** p)
        return result

    def _cpe(self, freq, q, pf, pi):
        """
        Return the impedance of a CPE for a given frequency.
        """
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
        """
        Return the impedance of two components in parallel.
        """
        if z_1 == 0 or z_2 == 0:
            raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")
        denominator = (1 / z_1) + (1 / z_2)
        result = 1 / denominator
        return result


class ModelCircuitSeries(ModelCircuitParent):
    """
    Circuit model where elements are in series.
    """
    
    def __init__(self, negative_rinf=False, q=None, v_second=None, v_others=None):
        super().__init__(negative_rinf, q, v_second, v_others)
        self.name = "Series Circuit"

    def run_rock(self, v: dict, freq_array: np.ndarray):
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        z = []

        for freq in freq_array:
            z_cpeh = self._cpe(freq, self.q["Qh"], v_l["Ph"], v_l["Ph"])
            zarch = self._parallel(z_cpeh, v_l["Rh"])

            z_cpem = self._cpe(freq, self.q["Qm"], v_l["Pm"], v_l["Pm"])
            zarcm = self._parallel(z_cpem, v_l["Rm"])

            z_cpel = self._cpe(freq, self.q["Ql"], v_l["Pl"], v_l["Pl"])
            zarcl = self._parallel(z_cpel, v_l["Rl"])

            z_total = zarch + zarcm + zarcl
            z.append(z_total)

        return np.array(z)

    def run_model(self, v: dict, freq_array: np.ndarray):
        z_rock = self.run_rock(v, freq_array)
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        zinf = [self._inductor(freq, v_l["Linf"]) + v_l["Rinf"] for freq in freq_array]
        z_cpee = [self._cpe(freq, v_l["Qe"], v_l["Pef"], v_l["Pei"]) for freq in freq_array]
        zarce = [self._parallel(z_cpee[i], v_l["Re"]) for i in range(len(freq_array))]

        return np.array([zinf[i] + z_rock[i] + zarce[i] for i in range(len(freq_array))]), np.array(z_rock)
    

class ModelCircuitParallel(ModelCircuitParent):
    """
    Circuit model where elements are in parallel.
    """
    def __init__(self, negative_rinf=False, q=None, v_second=None, v_others=None):
        super().__init__(negative_rinf, q, v_second, v_others)
        self.name = "Parallel Circuit"

    def run_rock(self, v: dict, freq_array: np.ndarray):
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        v2 = self.v_second

        z = []

        for f in freq_array:
            z_line_h = v2["pRh"] + self._cpe(f, v2["pQh"], v_l["Ph"], v_l["Ph"])
            z_line_m = v2["pRm"] + self._cpe(f, v2["pQm"], v_l["Pm"], v_l["Pm"])
            z_line_l = v2["pRl"] + self._cpe(f, v2["pQl"], v_l["Pl"], v_l["Pl"])

            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, v2["R0"])
            zparallel = self._parallel(z_line_h, z_rock)

            z.append(zparallel)

        return np.array(z)

    def run_model(self, v: dict, freq_array: np.ndarray):
        z_rock = self.run_rock(v, freq_array)
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        zinf = [self._inductor(f, v_l["Linf"]) for f in freq_array]
        z_cpee = [self._cpe(f, v_l["Qe"], v_l["Pef"], v_l["Pei"]) for f in freq_array]
        zarce = [self._parallel(z_cpee[i], v_l["Re"]) for i in range(len(freq_array))]

        return np.array([zinf[i] + z_rock[i] + zarce[i] for i in range(len(freq_array))]), np.array(z_rock)


###############################################################################
# Fit_class ?
###############################################################################
class Fit(QObject):
    def __init__(self) -> None:
        pass

###############################################################################
# v/t class
###############################################################################
class TimeDomainBuilder(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.N = 2 ** 8
        self.T = 4
        
        self._integral_variables={}
        
    #   Public Methods
    def get_integral_variables(self):
        return self._integral_variables

    def run_time_domain(self, params: dict, model_circuit: ModelCircuitParent):
        """
        Calculate time-domain values using a real IFFT.
        """ 
        n_freq = (self.N // 2) #+1
        
        dt = self.T / self.N
        df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq / self.T
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        freq_even[0] = 0.001

        z_complex = model_circuit.run_rock(params, freq_even)
        t, volt_down=self._fourier_transform(z_complex, dt)       
        
        self._integration_variables(t, volt_down)
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1]

    def transform_to_time_domain(self,experiment_data):
        """
        Transform experimental data to the time domain.
        """
        n_freq = (self.N // 2) #+1
        
        dt = self.T / self.N
        df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq / self.T
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        freq_even[0] = 0.001
              
        z_interp = self._interpolate_points_for_time_domain(freq_even, experiment_data)
        t, volt_down=self._fourier_transform(z_interp, dt)   
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1]  

    #Private Methods
    def _interpolate_points_for_time_domain(self, freqs_even: np.ndarray, experiment_data) -> np.ndarray:
        """
        Interpolate measured impedance data for the time-domain transform.
        """
        freq   = experiment_data["freq"]
        z_real = experiment_data["Z_real"]
        z_imag = experiment_data["Z_imag"]
    
        # Create interpolation functions that extrapolate outside the measured range.
        interp_real = interp1d(freq, z_real, kind="cubic", fill_value="extrapolate")
        interp_imag = interp1d(freq, z_imag, kind="cubic", fill_value="extrapolate")
    
        # Evaluate the interpolants at the uniformly spaced frequencies.
        z_real_interp = interp_real(freqs_even)
        z_imag_interp = interp_imag(freqs_even)
        
        return z_real_interp + 1j * z_imag_interp

    def _fourier_transform(self, z_complex: np.ndarray, dt: float):
        """
        Build the single-sided array for IRFFT and perform a real IFFT.
        """
        v = np.fft.irfft(z_complex)       #to transform the impedance data from the freq domain to the time domain.
                                        #largest value is 0.28         
        b, a = sig.butter(2, 0.45) 
        z_inversefft = np.fft.irfft(z_complex)       #to transform the impedance data from the freq domain to the time domain.
                   #largest value is 0.28       
        z_inversefft = sig.filtfilt(b, a, z_inversefft)   #Applies filter
        t = np.arange(len(z_inversefft)) * dt  # constructs time based on N and dt
 
        volt_up = np.concatenate(([0], np.cumsum(z_inversefft)[:-1]))
        
        time_to_plot_in_seconds=2
        
        index = np.searchsorted(t, time_to_plot_in_seconds, side="right")
        volt_down = volt_up[index]-volt_up
        
        return t, volt_down

    def _integration_variables(self, t, v_down):
        
        keys=['V(.1ms)',	'V(1ms)', 'V(10)',	'V(100)','V(200)',	'V(400)',	'V(800)',	'V(1.2s)', 'V(1.6s)']
        seconds=[0.0001,	0.001, 0.01,	0.1, 0.2, 0.4, 0.8, 1.2, 1.6]
        
        for key, mili in zip (keys, seconds):
            index = np.searchsorted(t, mili)
            self._integral_variables[key]=v_down[index]
            
###############################################################################
# Calculator
###############################################################################
class Calculator(QObject):
    """
    This class replicates the circuit calculation by evaluating formulas from
    config.ini. It also calculates secondary variables that were previously in Main.
    """
    model_manual_result = pyqtSignal(CalculationResult)
    model_manual_values = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        # Initialize experimental data.
        self._experiment_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.zeros(5),
            "Z_imag": np.zeros(5),
        }
        # Auxiliary class to handle time domain conversion.
        self._model_circuit = ModelCircuitParallel()
        self.time_domain_builder = TimeDomainBuilder()
        
        # Boundaries and disabled variables.
        self.lower_bounds = {}
        self.upper_bounds = {}
        self.disabled_variables = set()
        self.gaussian_prior = False

        # Dictionary for additional fit variables.
        self._fit_variables = {'model': self._model_circuit.name}

    # ------------------------------
    # Public Methods (Interface Unchanged)
    # ------------------------------
    def initialize_expdata(self, file_data: dict) -> None:
        """Set the experimental data from an external dictionary."""
        self._experiment_data = file_data

    def set_disabled_variables(self, key: str, disabled: bool) -> None:
        """Enable or disable a parameter for the fit based on its key."""
        if disabled:
            self.disabled_variables.add(key)
        else:
            self.disabled_variables.discard(key)
            
        print(f"disabled variables{self.disabled_variables}")

    def set_rinf_negative(self, state: bool) -> None:
        """Set negative resistance flag in the circuit model."""
        self._model_circuit.negative_rinf = state

    def set_gaussian_prior(self, state: bool) -> None:
        """Enable or disable the Gaussian prior for model fitting."""
        self.gaussian_prior = state

    def set_bounds(self, slider_configurations: dict) -> None:
        """
        Set the lower and upper bounds for parameters based on slider configurations.
        """
        for key, config in slider_configurations.items():
            if "Power" in str(config[0]):
                self.lower_bounds[key] = 10 ** config[1]
                self.upper_bounds[key] = 10 ** config[2]
            else:
                self.lower_bounds[key] = config[1]
                self.upper_bounds[key] = config[2]

    def get_latest_secondaries(self) -> dict:
        """Return the most recent dictionary of secondary variables."""
        return dict(self._model_circuit.v_second)

    def get_model_parameters(self) -> dict:
        """
        Return the combined dictionary of model parameters, integrating:
          - Circuit model parameters.
          - Time domain integral variables.
          - Additional fit variables.
        """
        integral_vars = self.time_domain_builder.get_integral_variables()
        circuit_params = self._model_circuit.q | self._model_circuit.v_second | self._fit_variables
        return circuit_params | integral_vars

    def switch_circuit_model(self, state: bool) -> None:
        """
        Switch the circuit model:
          - True selects ModelCircuitSeries.
          - False selects ModelCircuitParallel.
        """
        neg_rinf, old_q, old_vsec = self._model_circuit.init_parameters()
        if state:
            self._model_circuit = ModelCircuitSeries(
                negative_rinf=neg_rinf,
                q=dict(old_q),
                v_second=dict(old_vsec)
            )
        else:
            self._model_circuit = ModelCircuitParallel(
                negative_rinf=neg_rinf,
                q=dict(old_q),
                v_second=dict(old_vsec)
            )

    def fit_model_cole(self, initial_params: dict) -> dict:
        """Fit the model using the Cole cost function."""
        prior_weight = 10 ** 6
        return self._fit_model(self._residual_cole, initial_params, prior_weight)

    def fit_model_bode(self, initial_params: dict) -> dict:
        """Fit the model using the Bode cost function."""
        prior_weight = 400
        return self._fit_model(self._residual_bode, initial_params, prior_weight)

    def run_model_manual(self, params: dict) -> CalculationResult:
        """
        Run the model with the given parameters.

        1) Compute main impedance arrays over the experimental frequencies.
        2) Compute special frequencies and their impedance.
        3) Compute the time-domain response.
        4) Pack all results into a CalculationResult and emit a signal.
        """
        freq_array = self._experiment_data["freq"]
        z, rock_z = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        rock_z_real, rock_z_imag = rock_z.real, rock_z.imag

        special_freq = self._get_special_freqs(params)
        spec_z, _ = self._model_circuit.run_model(params, special_freq)
        spec_zr, spec_zi = spec_z.real, spec_z.imag
        # Adjust the special impedance marker.
        spec_zi[len(spec_z) - 1] = 0

        t_freq, t_time, t_volt = self.run_time_domain(params)

        result = CalculationResult(
            main_freq=freq_array,
            main_z_real=z_real,
            main_z_imag=z_imag,
            rock_z_real=rock_z_real,
            rock_z_imag=rock_z_imag,
            special_freq=special_freq,
            special_z_real=spec_zr,
            special_z_imag=spec_zi,
            timedomain_freq=t_freq,
            timedomain_time=t_time,
            timedomain_volt=t_volt
        )
        
        self.model_manual_result.emit(result)
        self._update_fit_variables(z_real, z_imag, params)
        return result

    def run_time_domain(self, params: dict):
        """
        Calculate time-domain values using a real IFFT.
        """
        return self.time_domain_builder.run_time_domain(params, self._model_circuit)

    def transform_to_time_domain(self):
        """
        Transform experimental data to time domain.
        """
        return self.time_domain_builder.transform_to_time_domain(self._experiment_data)

    # ------------------------------
    # Private Methods
    # ------------------------------

    # ---------- Fitting Methods ----------
    def _fit_model(self, residual_func, initial_params: dict, prior_weight: float = 0) -> dict:
        """
        Fit the model using a provided residual function and (optionally) a Gaussian prior
        that penalizes deviation from the initial guess.
        """
        all_keys = list(initial_params.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
        locked_params = {k: initial_params[k] for k in self.disabled_variables if k in initial_params}
        x0 = self._scale_params(free_keys, initial_params)
        lower_bounds_scaled, upper_bounds_scaled = self._build_bounds(free_keys)
    
        def _residual_wrapper(x_free: np.ndarray) -> np.ndarray:
            free_params = self._descale_params(free_keys, x_free)
            full_params = {**locked_params, **free_params}
    
            try:
                model_residual = residual_func(full_params)
            except ValueError:
                # Return a large penalty if the model evaluation fails.
                return np.ones(10000) * 1e6
    
            if self.gaussian_prior:
                prior_res = self._compute_gaussian_prior(x_free, x0, lower_bounds_scaled, upper_bounds_scaled, prior_weight)
                invalid_penalty = self._compute_invalid_guess_penalty(full_params, prior_weight)
                model_residual = np.concatenate([model_residual, prior_res, invalid_penalty])
            
            return model_residual

        result = opt.least_squares(
            _residual_wrapper,
            x0=x0,
            bounds=(lower_bounds_scaled, upper_bounds_scaled),
            method='trf',
            max_nfev=2000
        )
        best_fit_free = self._descale_params(free_keys, result.x)
        best_fit = {**locked_params, **best_fit_free}
        self.model_manual_values.emit(best_fit)
        return best_fit

    def _residual_cole(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Cole model."""
        freq_array = self._experiment_data["freq"]
        z, _ = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        weight = self._weight_function(params)
        return np.concatenate([(z_real - exp_real) * weight, (z_imag - exp_imag) * weight])

    def _residual_bode(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Bode model."""
        freq_array = self._experiment_data["freq"]
        z, _ = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        z_abs = np.hypot(z_real, z_imag)
        z_phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        exp_abs = np.hypot(exp_real, exp_imag)
        exp_phase_deg = np.degrees(np.arctan2(exp_imag, exp_real))
        res_abs = np.log10(z_abs) - np.log10(exp_abs)
        res_phase = np.log10(np.abs(z_phase_deg) + 1e-10) - np.log10(np.abs(exp_phase_deg) + 1e-10)
        weight = self._weight_function(params)
        return np.concatenate([res_abs * weight, res_phase * weight])

    def _weight_function(self, params: dict) -> float:
        """
        Assign dynamic weights to errors based on selected parameters.
        """
        weight = 1
        for key in ["Ph", "Pm", "Pl", "Pef"]:
            weight *= 1 + 3 * np.exp(-15 * params[key])
        return weight

    def _build_bounds(self, free_keys: list) -> (np.ndarray, np.ndarray):
        """
        Build scaled lower and upper bounds arrays for free parameters.
        """
        lower_scaled = self._scale_params(free_keys, self.lower_bounds)
        upper_scaled = self._scale_params(free_keys, self.upper_bounds)
        return lower_scaled, upper_scaled

    def _compute_invalid_guess_penalty(self, params: dict, prior_weight: float) -> np.ndarray:
        """
        Returns the penalty array if the guess is invalid, otherwise zeros.
        """
        arbitrary_scaling =1e4
        deviation = self._invalid_guess(params)
        return deviation * arbitrary_scaling * prior_weight

    def _compute_gaussian_prior(
        self, x_guess: np.ndarray, x0: np.ndarray,
        lower_bounds: np.ndarray, upper_bounds: np.ndarray,
        prior_weight: float, gaussian_fraction: int = 5
    ) -> np.ndarray:
        """
        Calculate the Gaussian prior penalty for each parameter.
        """
        sigmas = (upper_bounds - lower_bounds) * gaussian_fraction
        return prior_weight * ((x_guess - x0) / sigmas)

    def _invalid_guess(self, params: dict) -> np.ndarray:
        """
        Test validity criteria: Fh >= Fm >= Fl.
        Returns positive deviations if invalid, zeros otherwise.
        """
        return np.array([
            max(0.0, params["Fm"] - params["Fh"]),
            max(0.0, params["Fl"] - params["Fm"])
        ])

    # ---------- Special Frequencies and Other Values of Interest ----------
    def _get_special_freqs(self, slider_values: dict) -> np.ndarray:
        """
        Return special frequency points based on slider values.
        """
        return np.array([
            slider_values["Fh"],
            slider_values["Fm"],
            slider_values["Fl"],
            0.1
        ], dtype=float)
    
    def _update_fit_variables(self, z_real, z_imag, params: dict) -> None:
        """
        Update internal fit variables such as mismatch and resistance at 0.1Hz.
        """
        exp_complex = self._experiment_data["Z_real"] + 1j * self._experiment_data["Z_imag"]
        calc_complex = z_real + 1j * z_imag
        mismatch = np.sum(np.abs(exp_complex - calc_complex) ** 2)
        self._fit_variables['mismatch'] = mismatch
        
        # Compute resistance at 0.1Hz.
        z_1Hz = self._model_circuit.run_model(params, [0.1])[0]
        self._fit_variables['Res.1Hz'] = abs(z_1Hz.real)
        
        freq_array = self._experiment_data["freq"]
        self._fit_variables['Fhigh'] = freq_array[0]
        self._fit_variables['Flow'] = freq_array[-1]

    # ---------- Parameter Scaling ----------
    @staticmethod
    def _scale_params(keys: list, params: dict) -> np.ndarray:
        """
        Convert parameter values into a scaled vector for optimization.
        """
        scaled = []
        for key in keys:
            value = params[key]
            if key.startswith('P'):
                scaled.append(value * 10.0)
            else:
                if value <= 0:
                    raise ValueError(f"Parameter {key} must be > 0; got {value}.")
                scaled.append(np.log10(value))
        return np.array(scaled)

    @staticmethod
    def _descale_params(keys: list, x: np.ndarray) -> dict:
        """
        Convert a scaled vector back to the original parameter dictionary.
        """
        descale = {}
        for i, key in enumerate(keys):
            if key.startswith('P'):
                descale[key] = x[i] / 10.0
            else:
                descale[key] = 10 ** x[i]
        return descale

    
######################################################################################

import unittest
import numpy as np
from PyQt5.QtWidgets import QApplication
import sys
from scipy.optimize import least_squares

# Ensure a QApplication exists (required for QObject-based classes)
if QApplication.instance() is None:
    app = QApplication(sys.argv)

# Dummy model circuit that returns ones so that the logarithms are finite.
class DummyModelCircuit:
    def __init__(self):
        self.v_second = {}
        self.q = {}
        self.name = "DummyCircuit"
    
    def run_model(self, params, freq_array):
        # Return an array of ones (complex ones) so that |z|=1.
        z = np.ones(len(freq_array), dtype=complex)
        return z, z
    
    def run_rock(self, params, freq_array):
        return self.run_model(params, freq_array)
    
    def init_parameters(self):
        # Return default parameters.
        return False, {}, {}

class TestCalculatorFitFunctions(unittest.TestCase):
    def setUp(self):
        # Create a Calculator instance.
        self.calc = Calculator()
        # Replace the circuit model with our dummy model.
        self.calc._model_circuit = DummyModelCircuit()
        
        # Set experimental data to ones (avoiding zeros so log10 is defined).
        exp_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.ones(5),
            "Z_imag": np.ones(5)
        }
        self.calc.initialize_expdata(exp_data)
        
        # Set dummy lower and upper bounds for the fit parameters.
        self.calc.lower_bounds = {
            "Fh": 1, "Fm": 1, "Fl": 1, "Ph": 0.1, "Pm": 0.1, "Pl": 0.1, "Pef": 0.1,
            "Rinf": 1, "Rh": 1, "Rm": 1, "Rl": 1, "Linf": 0.0001, "Qe": 1e-5, "Pei": 0.1, "Re": 1
        }
        self.calc.upper_bounds = {
            "Fh": 1000, "Fm": 1000, "Fl": 1000, "Ph": 10, "Pm": 10, "Pl": 10, "Pef": 10,
            "Rinf": 1000, "Rh": 1000, "Rm": 1000, "Rl": 1000, "Linf": 0.01, "Qe": 1e-2, "Pei": 10, "Re": 100
        }
        
        # Define dummy initial parameters (all > 0).
        self.dummy_params = {
            "Fh": 100,
            "Fm": 50,
            "Fl": 10,
            "Ph": 1,
            "Pm": 1,
            "Pl": 1,
            "Pef": 1,
            "Rinf": 100,
            "Rh": 50,
            "Rm": 30,
            "Rl": 20,
            "Linf": 0.001,
            "Qe": 1e-3,
            "Pei": 1,
            "Re": 10
        }
        
        # Ensure no disabled variables and Gaussian prior is off.
        self.calc.disabled_variables = set()
        self.calc.gaussian_prior = False

    def test_fit_model_cole(self):
        """Test that the Cole fitting function runs and returns a dict with expected keys."""
        result = self.calc.fit_model_cole(self.dummy_params)
        self.assertIsInstance(result, dict)
        for key in self.dummy_params.keys():
            self.assertIn(key, result)

    def test_fit_model_bode(self):
        """Test that the Bode fitting function runs and returns a dict with expected keys."""
        result = self.calc.fit_model_bode(self.dummy_params)
        self.assertIsInstance(result, dict)
        for key in self.dummy_params.keys():
            self.assertIn(key, result)

    def test_get_model_parameters(self):
        """Test that get_model_parameters returns a combined dictionary including fit variables."""
        _ = self.calc.run_model_manual(self.dummy_params)
        params = self.calc.get_model_parameters()
        self.assertIsInstance(params, dict)
        self.assertIn("model", params)
        self.assertIn("mismatch", params)

if __name__ == '__main__':
    unittest.main()

