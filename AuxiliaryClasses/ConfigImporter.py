import os
import configparser
from typing import Optional

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

        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # Maintain case sensitivity for keys
        self.config.read(config_file)

        # File paths for input and output.
        self.input_file: Optional[str] = None
        self.output_file: Optional[str] = None

        # Widget configuration.
        self.input_file_widget_config = {}

        # Slider configurations and default values.
        self.slider_configurations = {}
        self.slider_default_values = []
        self.slider_default_disabled = []

        # Secondary variables to display.
        self.secondary_variables_to_display = []
        self.variables_to_print = []

        # Read and process the configuration file.
        self._read_config_file()
        self._check_sliders_length()

    def set_input_file(self, new_input_file: str) -> None:
        """
        Set a new input file path and update the configuration file.
        """
        if self._validate_path(new_input_file):
            self._update_config("InputFile", "path", new_input_file)
            self.input_file = new_input_file

    def set_output_file(self, new_output_file: str) -> None:
        """
        Set a new output file path and update the configuration file.
        """
        if self._validate_path(new_output_file):
            self._update_config("OutputFile", "path", new_output_file)
            self.output_file = new_output_file

    def _update_config(self, section: str, key: str, value: str) -> None:
        """
        Update a specific section and key in the configuration and write it to file.

        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def _read_config_file(self) -> None:
        """
        Read the configuration file and extract both mandatory and optional parameters.
        """
        # Reload config to ensure updates are included.
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_file)

        self._extract_mandatory_parameters()
        self._extract_optional_parameters()

    def _extract_mandatory_parameters(self) -> None:
        """
        Extract mandatory sections and parameters from the configuration file.
        Raises:ValueError: If any required section is missing.
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
                    f"ConfigImporter._extract_mandatory_parameters :Missing '{section}' section in the config file."
                    )

        self._extract_sliders_configurations()

        # Process slider default values.
        defaults_str = self.config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val.strip()) for val in defaults_str.split(",")]

        # Process variables to print.
        vars_str = self.config["VariablesToPrint"]["variables"]
        self.variables_to_print = [v.strip() for v in vars_str.split(",") if v.strip()]

        # Process input file widget configuration.
        self.input_file_widget_config = {
            key.strip(): value.strip() for key, value in self.config["WidgetInputFile"].items()
        }

        # Process secondary variables to display.
        secondary_str = self.config["SecondaryVariablesToDisplay"]["variables"]
        self.secondary_variables_to_display = [v.strip() for v in secondary_str.split(",") if v.strip()]

    def _extract_sliders_configurations(self) -> None:
        """
        Extract slider configurations from the configuration file.
        Each slider configuration must consist of 5 comma-separated values:
        slider type, min value, max value, color, and tick interval.
        Raises:
            ValueError: If a slider configuration is invalid or the slider type is unrecognized.
        """
        sliders = {}
        for key, value in self.config["SliderConfigurations"].items():
            parts = value.split(",")
            if len(parts) != 5:
                raise ValueError(
                    f"Invalid slider configuration for '{key}'. Expected 5 comma-separated values."
                )
            slider_type_str, min_val_str, max_val_str, color, tick_interval_str = [p.strip() for p in parts]
            slider_class = self._safe_import(slider_type_str)
            if slider_class is None:
                raise ValueError(
                    f"ConfigImporter._extract_sliders_configurations :Unrecognized slider type '{slider_type_str}' for slider '{key}'."
                    )
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str),
                float(max_val_str),
                color,
                int(tick_interval_str),
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
                
        if 'SliderDisabled' in self.config:

            defaults_str = self.config["SliderDefaultValues"]["defaults"]
            self.slider_default_disabled = [bool(val.strip()) for val in defaults_str.split(",")]

    @staticmethod
    def _safe_import(class_name: str):
        """
        Return the slider class corresponding to the given class name.
        Returns: The slider class if recognized, otherwise None.
        """
        slider_classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return slider_classes.get(class_name)

    def _validate_path(self, path: str) -> bool:
        """
        Validate the given file path.
        Raises:
            TypeError: If the path is not a string.
            ValueError: If the directory for the path does not exist.
        """
        if not isinstance(path, str):
            raise TypeError("Path must be a string.")

        directory = os.path.dirname(path) or '.'
        if not os.path.isdir(directory):
            raise ValueError("ConfigImporter._validate_path :Invalid file path. The directory does not exist.")
        return True
        """
        Validate the given file path.
        Raises:
            TypeError: If the path is not a string.
            ValueError: If the directory for the path does not exist.
        """
        if not isinstance(path, str):
            raise TypeError("ConfigImporter._validate_path:Path must be a string.")

        output_dir = os.path.dirname(path) or '.'
        if not os.path.isdir(output_dir):
            raise ValueError("ConfigImporter._validate_path:Invalid file path. The directory does not exist.")
        return True

    def _check_sliders_length(self):
        
        len1=len(self.slider_configurations)
        len2=len(self.slider_default_values)
        len3=len(self.slider_default_disabled)
        condition1=len1==len2
        condition2=(len1==len3) or (len3==0)
        
        if not (condition1 and condition2):
            raise ValueError(
                f"ConfigImporter._check_sliders_length: Mismatch detected"
                )
            
    
#####################################
# Testing
#########################################

if __name__ == '__main__':
    #config_file = "config.ini"
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    my_importer = ConfigImporter(config_file)
