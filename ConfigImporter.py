import os
import configparser
from SubclassesSliderWithTicks import EPowerSliderWithTicks, DoubleSliderWithTicks

class ConfigImporter:
    
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        
        self.config_file = config_file
        self.slider_configurations = {}
        self.slider_default_values = []
        self.input_file_widget_config = {}
        self._read_config_file()

    def _read_config_file(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        # Read slider configurations
        sliders = {}
        for key, value in config["SliderConfigurations"].items():
            slider_type, min_value, max_value, color = value.split(",")
            sliders[key] = (self._safe_import(slider_type), float(min_value), float(max_value), color)
        self.slider_configurations = sliders

        # Read default values
        defaults_str = config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val) for val in defaults_str.split(",")]

        # Read InputFileWidget configurations
        input_file_widget = {}
        for key, value in config["InputFileWidget"].items():
            input_file_widget[key] = value
        self.input_file_widget_config = input_file_widget
        

    @staticmethod
    def _safe_import(class_name):
        """
        Safely imports and instantiates a class from a string.
        Args:
        class_name (str): Name of the class to import.
        
        Returns:
        type: Class reference.
        """
        classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return classes.get(class_name)


"""TEST"""
def test_config_importer():
    # Define the path to the configuration file (adjust as necessary)
    config_file = "test_config.ini"

    # Create a sample configuration file for testing
    with open(config_file, "w") as file:
        file.write("""[SliderConfigurations]
slider1 = EPowerSliderWithTicks,0.0,100.0,red
slider2 = DoubleSliderWithTicks,10.0,200.0,blue

[SliderDefaultValues]
defaults = 50.0,20.0

[InputFileWidget]
SUPPORTED_FILE_EXTENSION = .z
SKIP_ROWS = 128
FREQ_COLUMN = 0
Z_REAL_COLUMN = 4
Z_IMAG_COLUMN = 5
        """)

    try:
        # Initialize the ConfigImporter with the test config
        importer = ConfigImporter(config_file)

        # Print the slider configurations
        print("Slider Configurations:")
        for key, value in importer.slider_configurations.items():
            print(f"{key}: {value}")

        # Print the default values
        print("\nSlider Default Values:")
        print(importer.slider_default_values)

        # Print the InputFileWidget configuration
        print("\nInputFileWidget Config:")
        for key, value in importer.input_file_widget_config.items():
            print(f"{key}: {value}")
        print(importer.input_file_widget_config.keys())

        # Indicate the test passed
        print("\nTest passed: ConfigImporter loaded the configuration correctly.")
    
    except Exception as e:
        # Print the error if something goes wrong
        print(f"Test failed: {e}")

    finally:
        # Clean up by removing the test configuration file
        if os.path.exists(config_file):
            os.remove(config_file)

# Run the test
if __name__ == "__main__":
    test_config_importer()