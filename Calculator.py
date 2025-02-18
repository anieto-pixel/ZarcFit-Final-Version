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

    special_freq: np.ndarray = None  # The 3 special frequencies
    special_z_real: np.ndarray = None
    special_z_imag: np.ndarray = None

    timedomain_freq: np.ndarray = None  # Elements used for the time domain plot
    timedomain_time: np.ndarray = None
    timedomain_volt: np.ndarray = None


class ModelCircuitParent(object):
    """
    Parent class for circuit models.
    """

    def __init__(self, negative_rinf=False, q=None, v_second=None):
        super().__init__()

        # Avoid mutable default arguments; properly assign attributes.
        if q is None:
            q = {}
        if v_second is None:
            v_second = {}

        # Attributes
        self.negative_rinf = negative_rinf
        self.q = q
        self.v_second = v_second

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
        z = self.run_rock(v, freq_array)
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        zinf = [self._inductor(freq, v_l["Linf"]) + v_l["Rinf"] for freq in freq_array]
        z_cpee = [self._cpe(freq, v_l["Qe"], v_l["Pef"], v_l["Pei"]) for freq in freq_array]
        zarce = [self._parallel(z_cpee[i], v_l["Re"]) for i in range(len(freq_array))]

        return np.array([zinf[i] + z[i] + zarce[i] for i in range(len(freq_array))])


class ModelCircuitParallel(ModelCircuitParent):
    """
    Circuit model where elements are in parallel.
    """

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
        z = self.run_rock(v, freq_array)
        v_l = v.copy()

        if self.negative_rinf:
            v_l['Rinf'] = -v_l['Rinf']
        self._calculate_secondary_variables(v_l)

        zinf = [self._inductor(f, v_l["Linf"]) for f in freq_array]
        z_cpee = [self._cpe(f, v_l["Qe"], v_l["Pef"], v_l["Pei"]) for f in freq_array]
        zarce = [self._parallel(z_cpee[i], v_l["Re"]) for i in range(len(freq_array))]

        return np.array([zinf[i] + z[i] + zarce[i] for i in range(len(freq_array))])


###############################################################################
# ModelManual
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
        self.lower_bounds = {}
        self.upper_bounds = {}
        self.disabled_variables = set()
        self.gaussian_prior = False
        self._model_circuit = ModelCircuitParallel()

    # ------------------------------
    # Public Methods
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

    def set_rinf_negative(self, state: bool) -> None:
        self._model_circuit.negative_rinf = state

    def set_gaussian_prior(self, state: bool) -> None:
        self.gaussian_prior = state

    def set_bounds(self, slider_configurations: dict) -> None:
        """Set the lower and upper bounds for parameters based on slider configurations."""
        for key, config in slider_configurations.items():
            if "Power" in str(config[0]):
                self.lower_bounds[key] = 10 ** config[1]
                self.upper_bounds[key] = 10 ** config[2]
            else:
                self.lower_bounds[key] = config[1]
                self.upper_bounds[key] = config[2]

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
        print("cole")
        return self._fit_model(self._residual_cole, initial_params, prior_weight=9000000)

    def fit_model_bode(self, initial_params: dict) -> dict:
        """Fit the model using the Bode cost function."""
        print("bode")
        return self._fit_model(self._residual_bode, initial_params, prior_weight=500)

    def run_model_manual(self, params: dict) -> CalculationResult:
        """
        Run the model with the given parameters.

        1) Compute main impedance arrays over the experimental frequencies.
        2) Compute special frequencies and their impedance.
        3) Compute the time-domain response.
        4) Pack all results into a CalculationResult and emit a signal.
        """
        freq_array = self._experiment_data["freq"]
        z = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag

        special_freq = self._get_special_freqs(params)
        spec_z = self._model_circuit.run_model(params, special_freq)
        spec_zr, spec_zi = spec_z.real, spec_z.imag

        tdomain_freq, tdomain_time, tdomain_volt = self.run_time_domain(params)

        result = CalculationResult(
            main_freq=freq_array,
            main_z_real=z_real,
            main_z_imag=z_imag,
            special_freq=special_freq,
            special_z_real=spec_zr,
            special_z_imag=spec_zi,
            timedomain_freq=tdomain_freq,
            timedomain_time=tdomain_time,
            timedomain_volt=tdomain_volt
        )

        self.model_manual_result.emit(result)
        return result

    def run_time_domain(self, params: dict, N: int = 2 ** 8, T: int = 4, crit_time: int = 2):
        """
        Calculate time-domain values using a real IFFT.
        """
        dt = crit_time / N
        df = 1.0 / crit_time
        freq_indices = np.arange(1, (N // 2) + 1)
        freqs_uniform = freq_indices * df

        z_total = self._model_circuit.run_rock(params, freqs_uniform)
        volt_time = np.fft.irfft(z_total, n=N)
        t = np.arange(N) * dt
        return freqs_uniform, t, volt_time

    def transform_to_time_domain(self, crit_time: float = 2.0, n_points: int = 1024):
        """
        Transform experimental data to the time domain.
        """
        dt = crit_time / n_points
        df = 1.0 / crit_time
        freq_indices = np.arange(1, (n_points // 2) + 1)
        freqs_uniform = freq_indices * df
        z_interp = self._interpolate_points_for_time_domain(freqs_uniform)
        t, volt_time = self._fourier_transform(n_points, z_interp, dt, df)
        return freqs_uniform, t, volt_time

    def get_latest_secondaries(self) -> dict:
        """Return the most recent dictionary of secondary variables."""
        return dict(self._model_circuit.v_second)

    def get_model_parameters(self) -> dict:
        """Return the combined dictionary of model parameters."""
        return self._model_circuit.q | self._model_circuit.v_second

    # ------------------------------
    # Private Methods
    # ------------------------------

    def _fit_model(self, residual_func, initial_params: dict, prior_weight: float = 0) -> dict:
        """
        Fit the model using a residual function and (optionally) a Gaussian prior
        that penalizes deviation from the initial guess.
        
        This version minimizes overhead by precomputing the locked parameters
        and inlining the conversion of free parameters.
        """
        all_keys = list(initial_params.keys())
        free_keys = [k for k in all_keys if k not in self.disabled_variables]
        # Precompute locked parameters once.
        locked_params = {k: initial_params[k] for k in self.disabled_variables if k in initial_params}
        x0 = self._scale_params(free_keys, initial_params)
        lower_bounds, upper_bounds = self._build_bounds(free_keys)

        def _residual_wrapper(x_guessing: np.ndarray) -> np.ndarray:
            # Inline descaling of free parameters.
            free_params = {}
            for i, k in enumerate(free_keys):
                if k.startswith('P'):
                    free_params[k] = x_guessing[i] / 10.0
                else:
                    free_params[k] = 10 ** x_guessing[i]
            full_params = locked_params.copy()
            full_params.update(free_params)
            try:
                model_residual = residual_func(full_params)
            except ValueError:
                return np.ones(10000) * 1e6
            if self.gaussian_prior:
                if not self._valid_guess(full_params):
                    penalty = np.ones(2 * len(self._experiment_data["freq"])) * 1e6
                    penalty = np.concatenate([penalty, np.ones(len(free_keys)) * 1e6])
                    return penalty
                prior_residual = self._compute_gaussian_prior(
                    x_guessing, x0, lower_bounds, upper_bounds, prior_weight
                )
            else:
                prior_residual = np.array([], dtype=float)
            return np.concatenate([model_residual, prior_residual])

        result = opt.least_squares(
            _residual_wrapper,
            x0=x0,
            bounds=(lower_bounds, upper_bounds),
            method='trf',
            max_nfev=2000
        )
        best_fit_free = self._descale_params(free_keys, result.x)
        best_fit = locked_params.copy()
        best_fit.update(best_fit_free)
        self.model_manual_values.emit(best_fit)
        return best_fit

    def _residual_cole(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Cole model."""
        freq_array = self._experiment_data["freq"]
        z = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        real_res = z_real - exp_real
        imag_res = z_imag - exp_imag
        w = self._weight_function(params)
        return np.concatenate([real_res * w, imag_res * w])

    def _residual_bode(self, params: dict) -> np.ndarray:
        """Return the residual vector for the Bode model."""
        freq_array = self._experiment_data["freq"]
        z = self._model_circuit.run_model(params, freq_array)
        z_real, z_imag = z.real, z.imag
        z_abs = np.sqrt(z_real ** 2 + z_imag ** 2)
        z_phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        exp_real = self._experiment_data["Z_real"]
        exp_imag = self._experiment_data["Z_imag"]
        exp_abs = np.sqrt(exp_real ** 2 + exp_imag ** 2)
        exp_phase_deg = np.degrees(np.arctan2(exp_imag, exp_real))
        res_abs = np.log10(z_abs) - np.log10(exp_abs)
        res_phase = np.log10(np.abs(z_phase_deg) + 1e-10) - np.log10(np.abs(exp_phase_deg) + 1e-10)
        w = self._weight_function(params)
        return np.concatenate([res_abs * w, res_phase * w])

    def _weight_function(self, params: dict) -> float:
        """Assign dynamic weights to errors based on selected parameters."""
        weight = 1
        weight *= 1 + 3 * np.exp(-15 * params["Ph"])
        weight *= 1 + 3 * np.exp(-15 * params["Pm"])
        weight *= 1 + 3 * np.exp(-15 * params["Pl"])
        weight *= 1 + 3 * np.exp(-15 * params["Pef"])
        return weight

    def _build_bounds(self, free_keys: list) -> (np.ndarray, np.ndarray):
        lower_bounds = self._scale_params(free_keys, self.lower_bounds)
        upper_bounds = self._scale_params(free_keys, self.upper_bounds)
        return lower_bounds, upper_bounds

    def _compute_gaussian_prior(
        self, x_guessing: np.ndarray, x0: np.ndarray,
        lower_bounds: np.ndarray, upper_bounds: np.ndarray,
        prior_weight: float, gaussian_fraction: int = 5
    ) -> np.ndarray:
        """
        Compute the Gaussian prior penalty based on scaled standard deviations.
        """
        sigmas = np.array(
            [(ub - lb) * gaussian_fraction for lb, ub in zip(lower_bounds, upper_bounds)],
            dtype=float
        )
        return prior_weight * ((x_guessing - x0) / sigmas)

    def _valid_guess(self, params: dict) -> bool:
        """Test validity criteria: Fh >= Fm >= Fl."""
        return params["Fh"] >= params["Fm"] and params["Fm"] >= params["Fl"]

    def _interpolate_points_for_time_domain(self, freqs_uniform: np.ndarray) -> np.ndarray:
        """
        Interpolate measured impedance data for the time-domain transform.
        """
        freq = self._experiment_data["freq"]
        z_real = self._experiment_data["Z_real"]
        z_imag = self._experiment_data["Z_imag"]
        f_min, f_max = freq[0], freq[-1]

        def clamp_freq(f):  # inline helper
            return np.clip(f, f_min, f_max)

        z_real_interp = np.interp(clamp_freq(freqs_uniform), freq, z_real)
        z_imag_interp = np.interp(clamp_freq(freqs_uniform), freq, z_imag)
        return z_real_interp + 1j * z_imag_interp

    def _fourier_transform(self, n_points: int, z_interp: np.ndarray, dt: float, df: float):
        """
        Build the single-sided array for IRFFT and perform a real IFFT.
        """
        volt_spectrum = np.zeros(n_points // 2 + 1, dtype=complex)
        volt_spectrum[1:] = z_interp
        volt_time = np.fft.irfft(volt_spectrum, n=n_points)
        b, a = sig.butter(2, 0.45, fs=1)
        volt_time = sig.filtfilt(b, a, volt_time)
        t = np.arange(n_points) * dt
        return t, volt_time

    def _get_special_freqs(self, slider_values: dict) -> np.ndarray:
        """
        Return three special frequency points based on slider values.
        """
        f1 = slider_values["Fh"]
        f2 = slider_values["Fm"]
        f3 = slider_values["Fl"]
        return np.array([f1, f2, f3], dtype=float)

    @staticmethod
    def _scale_params(keys: list, params: dict) -> np.ndarray:
        """
        Convert parameter values into a scaled vector.
        """
        scaled = []
        for k in keys:
            if k.startswith('P'):
                scaled.append(params[k] * 10.0)
            else:
                if params[k] <= 0:
                    raise ValueError(f"Parameter {k} must be > 0; got {params[k]}.")
                scaled.append(np.log10(params[k]))
        return np.array(scaled)

    @staticmethod
    def _descale_params(keys: list, x: np.ndarray) -> dict:
        """
        Convert a scaled vector back to a parameter dictionary.
        """
        descale = {}
        for i, k in enumerate(keys):
            if k.startswith('P'):
                descale[k] = x[i] / 10.0
            else:
                descale[k] = 10.0 ** x[i]
        return descale
