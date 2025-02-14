import os
import configparser
import logging
from sympy import sympify, symbols, lambdify, SympifyError

# Assuming these classes are defined in your CustomSliders module.
# Replace the following import statement with the actual import if necessary.
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class ConfigImporter:

    def __init__(self, config_file: str):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # Maintain case sensitivity for keys
        self.config.read(config_file)

        # Paths
        self.input_file = None
        self.output_file = None

        # Widget config
        self.input_file_widget_config = {}

        # Slider info
        self.slider_configurations = {}
        self.slider_default_values = []

        # Secondary vars
        self.secondary_variables_to_display = []

        self._read_config_file()

    #------------------------------
    # Public Methods
    #--------------------------------
        
    def set_input_file(self, new_input_file: str):
        if self._validate_path(new_input_file):
            # Update the config and write back to file
            if 'InputFile' not in self.config:
                self.config['InputFile'] = {}
            
            self.config['InputFile']['path'] = new_input_file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

            # Update the instance attribute
            self.input_file = new_input_file

    def set_output_file(self, new_output_file: str):
        if self._validate_path(new_output_file):
            # Update the config and write back to file
            if 'OutputFile' not in self.config:
                self.config['OutputFile'] = {}
            
            self.config['OutputFile']['path'] = new_output_file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

            # Update the instance attribute
            self.output_file = new_output_file

    #--------------------------
    # Private Methods
    #--------------------------

    def _read_config_file(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_file)

        self._extract_mandatory_parameters()
        self._extract_optional_parameters()
        
    def _extract_mandatory_parameters(self):
        required_sections = [
            "SliderConfigurations",
            "SliderDefaultValues",
            "VariablesToPrint",
            "InputFileWidget",
            "SecondaryVariablesToDisplay",
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing '{section}' section in the config file.")

        # Sliders
        self._extract_sliders_configurations()

        # Defaults
        defaults_str = self.config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val.strip()) for val in defaults_str.split(",")]

        # Print Variables
        vars_str = self.config["VariablesToPrint"]["variables"]
        # Convert to a list, stripping whitespace
        self.variables_to_print = [v.strip() for v in vars_str.split(",") if v.strip()]

        # InputFileWidget
        self.input_file_widget_config = {
            key.strip(): value.strip() 
            for key, value in self.config["InputFileWidget"].items()
        }

        secondary_str = self.config["SecondaryVariablesToDisplay"]["variables"]
        self.secondary_variables_to_display = [v.strip() for v in secondary_str.split(",") if v.strip()]

    def _extract_sliders_configurations(self):
        
        sliders = {}
        for key, value in self.config["SliderConfigurations"].items():
            parts = value.split(",")
            # *** Updated Line: Expect 5 parts now ***
            if len(parts) != 5:
                raise ValueError(f"Invalid slider configuration for '{key}'. Expected 5 comma-separated values.")
            # *** Extract the fifth parameter: number_of_tick_intervals ***
            slider_type_str, min_val_str, max_val_str, color, tick_interval_str = parts
            slider_class = self._safe_import(slider_type_str.strip())
            if slider_class is None:
                raise ValueError(f"Unrecognized slider type '{slider_type_str}' for slider '{key}'.")
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str.strip()),
                float(max_val_str.strip()),
                color.strip(),
                int(tick_interval_str.strip()),  # *** Store the fifth parameter as int ***
            )
        self.slider_configurations = sliders

    def _extract_optional_parameters(self):
        # Corrected the syntax to check for section and key
        
        if 'InputFile' in self.config:
            path = self.config['InputFile'].get('path')  # Use .get() to handle missing 'path'
            if path and self._validate_path(path):  # Ensure path is not None before validation
                self.input_file = path
             
        if 'OutputFile' in self.config:
            path = self.config['OutputFile'].get('path')
            if path and self._validate_path(path):
                self.output_file = path
               


    #################
    # General Helper Methods
    ###############
    
    @staticmethod
    def _safe_import(class_name: str):
        """
        Returns the slider class reference matching the given class_name.
        If the name is unrecognized, returns None.
        """
        classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return classes.get(class_name)
    
    def _validate_path(self, path):
        if not isinstance(path, str):
            raise TypeError("Path must be a string.")

        output_dir = os.path.dirname(path) or '.'
        if not os.path.isdir(output_dir):
            raise ValueError(f"Invalid file path. The directory does not exist.")
        return True

#####################################
#Testing
#########################################

# Run the tests
if __name__ == '__main__':
    config_file = "config.ini"
    my_importer= ConfigImporter(config_file)
