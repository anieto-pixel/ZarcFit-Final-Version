from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import numpy as np
from SubclassesSliderWithTicks import EPowerSliderWithTicks, DoubleSliderWithTicks

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
        }

        self._set_default_values()

    def _calculate_Zarc(self, frec, r, fo, p):
        omega = 2 * np.pi * frec
        omega_h = 2 * np.pi * fo
        Q = 1 / (omega_h ** p)  # CPE scaling constant approximation

        Z_cpe_mag = 1 / (Q * omega ** p)
        Z_cpe_real = Z_cpe_mag * np.cos(-np.pi * p / 2)
        Z_cpe_imag = Z_cpe_mag * np.sin(-np.pi * p / 2)

        Z_real = 1 / (1 / r + 1 / Z_cpe_real)
        Z_imag = 1 / (1 / Z_cpe_imag)

        return Z_real, Z_imag

    def _run_model(self):
        zarc_h_real = []
        zarc_h_imag = []

        for freq in self._manual_data['freq']:
            z_real, z_imag = self._calculate_Zarc(
                freq,
                self._variables_dictionary['rh'],
                self._variables_dictionary['fh'],
                self._variables_dictionary['ph']
            )
            zarc_h_real.append(z_real)
            zarc_h_imag.append(z_imag)

        self._manual_data['Z_real'] = np.array(zarc_h_real)
        self._manual_data['Z_imag'] = np.array(zarc_h_imag)

        self.manual_model_updated.emit(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag']
        )

    def _set_default_values(self):
        for key, default_value in zip(self._variables_keys, self._variables_default_values):
            self._variables_dictionary[key] = default_value

    def update_variable(self, key, new_value):
        if key in self._variables_dictionary:
            self._variables_dictionary[key] = new_value
            self._run_model()
        else:
            raise KeyError(f"Variable '{key}' not found in the model.")

class ManualMethodDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Model Demo")
        self.setGeometry(100, 100, 800, 600)

        self.manual_model = ManualModel(['rh', 'fh', 'ph'], [10**6, 0, 0.8])
        self.manual_model.manual_model_updated.connect(self.update_display)

        self.slider1 = EPowerSliderWithTicks(0, 10, 'red')
        self.slider2 = EPowerSliderWithTicks(0, 10, 'red')
        self.slider3 = DoubleSliderWithTicks(0.0, 1.0, 'red')

        self.slider1.value_changed().connect(lambda value: self.manual_model.update_variable('rh', 10 ** value))
        self.slider2.value_changed().connect(lambda value: self.manual_model.update_variable('fh', 10 ** value))
        self.slider3.value_changed().connect(lambda value: self.manual_model.update_variable('ph', value))

        # Horizontal layout for sliders
        sliders_layout = QHBoxLayout()
        sliders_layout.addWidget(QLabel("Resistance (rh)"))
        sliders_layout.addWidget(self.slider1)
        sliders_layout.addWidget(QLabel("Frequency (fh)"))
        sliders_layout.addWidget(self.slider2)
        sliders_layout.addWidget(QLabel("Phase (ph)"))
        sliders_layout.addWidget(self.slider3)

        # Vertical layout for labels
        labels_layout = QVBoxLayout()
        self.rh_label = QLabel(f"Resistance (rh): {self.manual_model._variables_dictionary['rh']}")
        self.fh_label = QLabel(f"Frequency (fh): {self.manual_model._variables_dictionary['fh']}")
        self.ph_label = QLabel(f"Phase (ph): {self.manual_model._variables_dictionary['ph']}")

        labels_layout.addWidget(self.rh_label)
        labels_layout.addWidget(self.fh_label)
        labels_layout.addWidget(self.ph_label)

        # The result label
        self.result_label = QLabel("Results will appear here.")
        labels_layout.addWidget(self.result_label)

        # Main layout combining both sliders and labels
        main_layout = QHBoxLayout()
        main_layout.addLayout(sliders_layout)
        main_layout.addLayout(labels_layout)

        self.setLayout(main_layout)

    def update_display(self, freq, z_real, z_imag):
        # Update the display for the Z values
        result_text = f"Frequency: {freq}\nZ_real: {z_real}\nZ_imag: {z_imag}"
        self.result_label.setText(result_text)

        # Update the labels for the current values of the variables
        self.rh_label.setText(f"Resistance (rh): {self.manual_model._variables_dictionary['rh']}")
        self.fh_label.setText(f"Frequency (fh): {self.manual_model._variables_dictionary['fh']}")
        self.ph_label.setText(f"Phase (ph): {self.manual_model._variables_dictionary['ph']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = ManualMethodDemo()
    demo.show()
    sys.exit(app.exec_())
