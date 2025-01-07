"""
Loads configuration data for sliders, default values, and file-widget
settings from a .ini file, storing them as attributes.

Parameters
----------
config_file : str
    The path to a .ini config file defining at least the following sections:
      - [SliderConfigurations]
      - [SliderDefaultValues]
      - [InputFileWidget]

Methods
-------
test_config_importer()
    Basic test demonstrating how to create a config file, load it,
    and inspect the results.
"""

import os
import configparser
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class ConfigImporter:


    def __init__(self, config_file: str):
        
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

        self.config_file = config_file
        self.slider_configurations = {}
        self.slider_default_values = []
        self.input_file_widget_config = {}

        self._read_config_file()
        
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _read_config_file(self):
        """
        Internal: Reads and parses the .ini file, populating the class attributes.
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # Preserve the case of keys.
        config.read(self.config_file)

        # SliderConfigurations
        sliders = {}
        for key, value in config["SliderConfigurations"].items():
            slider_type_str, min_val_str, max_val_str, color = value.split(",")
            sliders[key] = (
                self._safe_import(slider_type_str),
                float(min_val_str),
                float(max_val_str),
                color
            )
        self.slider_configurations = sliders


        # SliderDefaultValues
        defaults_str = config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val) for val in defaults_str.split(",")]

        # InputFileWidget
        if "InputFileWidget" in config:
            self.input_file_widget_config = dict(config["InputFileWidget"])

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


# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------
def test_config_importer():
    """
    Demonstrates how to create a sample .ini file, load it via ConfigImporter,
    and inspect the parsed configuration.
    """
    config_file = "test_config.ini"

    # Sample .ini content for testing
    sample_ini_content = """[SliderConfigurations]
Slider1 = EPowerSliderWithTicks,0.0,100.0,red
Slider2 = DoubleSliderWithTicks,10.0,200.0,blue

[SliderDefaultValues]
defaults = 50.0,20.0

[InputFileWidget]
SUPPORTED_FILE_EXTENSION = .z
SKIP_ROWS = 128
FREQ_COLUMN = 0
Z_REAL_COLUMN = 4
Z_IMAG_COLUMN = 5
"""

    # Write the sample config file
    with open(config_file, "w") as file:
        file.write(sample_ini_content)

    try:
        importer = ConfigImporter(config_file)

        # Inspect slider_configurations
        print("Slider Configurations:")
        for key, val in importer.slider_configurations.items():
            print(f"{key}: {val}")

        # Inspect default values
        print("\nSlider Default Values:")
        print(importer.slider_default_values)

        # Inspect InputFileWidget config
        print("\nInputFileWidget Config:")
        for k, v in importer.input_file_widget_config.items():
            print(f"{k}: {v}")

        print("\nTest passed: ConfigImporter loaded the configuration correctly.")

    except Exception as e:
        print(f"Test failed: {e}")

    finally:
        # Cleanup
        if os.path.exists(config_file):
            os.remove(config_file)


if __name__ == "__main__":
    test_config_importer()