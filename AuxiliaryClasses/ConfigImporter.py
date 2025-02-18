import os
import configparser
import logging
from sympy import sympify, symbols, lambdify, SympifyError

# Import slider classes. Replace with the actual module if needed.
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class ConfigImporter:
    """
    Class to import and manage configuration settings.

    Reads a configuration file to extract paths, slider settings,
    and various widget parameters.
    """

    def __init__(self, config_file: str):
        """
        Initialize the ConfigImporter with the specified configuration file.

        Args:
            config_file (str): Path to the configuration file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found."
            )

        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # Maintain case sensitivity for keys
        self.config.read(config_file)

        # Paths for input and output files.
        self.input_file = None
        self.output_file = None

        # Widget configuration.
        self.input_file_widget_config = {}

        # Slider configurations and default values.
        self.slider_configurations = {}
        self.slider_default_values = []

        # Secondary variables to display.
        self.secondary_variables_to_display = []

        self._read_config_file()

    def set_input_file(self, new_input_file: str) -> None:
        """
        Set a new input file path and update the configuration file.

        Args:
            new_input_file (str): New input file path.
        """
        if self._validate_path(new_input_file):
            if 'InputFile' not in self.config:
                self.config['InputFile'] = {}
            self.config['InputFile']['path'] = new_input_file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            self.input_file = new_input_file

    def set_output_file(self, new_output_file: str) -> None:
        """
        Set a new output file path and update the configuration file.

        Args:
            new_output_file (str): New output file path.
        """
        if self._validate_path(new_output_file):
            if 'OutputFile' not in self.config:
                self.config['OutputFile'] = {}
            self.config['OutputFile']['path'] = new_output_file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            self.output_file = new_output_file

    def _read_config_file(self) -> None:
        """
        Read the configuration file and extract both mandatory and optional parameters.
        """
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_file)

        self._extract_mandatory_parameters()
        self._extract_optional_parameters()

    def _extract_mandatory_parameters(self) -> None:
        """
        Extract mandatory sections and parameters from the configuration file.

        Raises:
            ValueError: If any required section is missing.
        """
        required_sections = [
            "SliderConfigurations",
            "SliderDefaultValues",
            "VariablesToPrint",
            "WidgetInputFile",
            "SecondaryVariablesToDisplay",
        ]
        for section in required_sections:
            if section not in self.config:
                raise ValueError(
                    f"Missing '{section}' section in the config file."
                )

        # Extract slider configurations.
        self._extract_sliders_configurations()

        # Extract slider default values.
        defaults_str = self.config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [
            float(val.strip()) for val in defaults_str.split(",")
        ]

        # Extract variables to print.
        vars_str = self.config["VariablesToPrint"]["variables"]
        self.variables_to_print = [
            v.strip() for v in vars_str.split(",") if v.strip()
        ]

        # Extract input file widget configuration.
        self.input_file_widget_config = {
            key.strip(): value.strip()
            for key, value in self.config["WidgetInputFile"].items()
        }

        # Extract secondary variables to display.
        secondary_str = self.config["SecondaryVariablesToDisplay"]["variables"]
        self.secondary_variables_to_display = [
            v.strip() for v in secondary_str.split(",") if v.strip()
        ]

    def _extract_sliders_configurations(self) -> None:
        """
        Extract slider configurations from the configuration file.

        Each slider configuration must consist of 5 comma-separated values:
        slider type, min value, max value, color, and tick interval.

        Raises:
            ValueError: If a slider configuration is invalid or the slider type
                        is unrecognized.
        """
        sliders = {}
        for key, value in self.config["SliderConfigurations"].items():
            parts = value.split(",")
            if len(parts) != 5:
                raise ValueError(
                    f"Invalid slider configuration for '{key}'. "
                    "Expected 5 comma-separated values."
                )
            slider_type_str, min_val_str, max_val_str, color, tick_interval_str = parts
            slider_class = self._safe_import(slider_type_str.strip())
            if slider_class is None:
                raise ValueError(
                    f"Unrecognized slider type '{slider_type_str}' for slider '{key}'."
                )
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str.strip()),
                float(max_val_str.strip()),
                color.strip(),
                int(tick_interval_str.strip()),
            )
        self.slider_configurations = sliders

    def _extract_optional_parameters(self) -> None:
        """
        Extract optional parameters such as input and output file paths from the configuration.
        """
        if 'InputFile' in self.config:
            path = self.config['InputFile'].get('path')
            if path and self._validate_path(path):
                self.input_file = path

        if 'OutputFile' in self.config:
            path = self.config['OutputFile'].get('path')
            if path and self._validate_path(path):
                self.output_file = path

    @staticmethod
    def _safe_import(class_name: str):
        """
        Return the slider class corresponding to the given class name.

        Args:
            class_name (str): Name of the slider class.

        Returns:
            The slider class if recognized, otherwise None.
        """
        classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return classes.get(class_name)

    def _validate_path(self, path: str) -> bool:
        """
        Validate the given file path.

        Args:
            path (str): File path to validate.

        Returns:
            bool: True if the path is valid.

        Raises:
            TypeError: If the path is not a string.
            ValueError: If the directory for the path does not exist.
        """
        if not isinstance(path, str):
            raise TypeError("Path must be a string.")

        output_dir = os.path.dirname(path) or '.'
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid file path. The directory does not exist.")
        return True


#####################################
# Testing
#########################################

if __name__ == '__main__':
    config_file = "config.ini"
    my_importer = ConfigImporter(config_file)
