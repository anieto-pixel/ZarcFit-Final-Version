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
        self.series_secondary_variables = {}
        self.parallel_model_secondary_variables = {}

        # NEW: additional expressions
        self.model_secondary_formulas = {}
        self.model_terciary_formulas = {}

        # Compiled Lambdas
        self.compiled_expressions = {}          # from SeriesSecondaryVariables
        self.dependent_compiled_expressions = {}# from ParallelModelSecondaryVariables
        self.compiled_model_secondary = {}       # from ModelSecondaryFormulas
        self.compiled_model_terciary = {}        # from ModelTerciaryFormulas

        self.model_final_formula = None          # single lambda from [ModelFormula]

        # A list of primary slider symbols
        self.symbols_list = []

        self._read_config_file()

        
####################
# Public Methods
###################
    
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

    ####################
    # Private Methods
    ###################

    # MM not sure I like this design. Is it worth it to make a method for
    # optional variables so things look cleaner?

    def _read_config_file(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_file)

        self._extract_mandatory_parameters()
        self._extract_optional_parameters()
        self._compile_secondary_expressions()     # Series + Parallel
        self._compile_model_sections()            # ModelSecondaryFormulas + ModelTerciaryFormulas
        self._compile_final_formula()             # [ModelFormula]
        


    def _extract_mandatory_parameters(self):
        required_sections = [
            "SliderConfigurations",
            "SliderDefaultValues",
            "InputFileWidget",
            "SeriesSecondaryVariables",
            "ParallelModelSecondaryVariables",
            "ModelSecondaryFormulas",
            "ModelTerciaryFormulas",
            "ModelFormula"
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing '{section}' section in the config file.")

        # Sliders
        self._extract_sliders_configurations()

        # Defaults
        defaults_str = self.config["SliderDefaultValues"]["defaults"]
        self.slider_default_values = [float(val.strip()) for val in defaults_str.split(",")]

        # InputFileWidget
        self.input_file_widget_config = {
            key.strip(): value.strip() 
            for key, value in self.config["InputFileWidget"].items()
        }

        # Series & Parallel expressions
        self.series_secondary_variables = {
            k.strip(): v.strip() 
            for k, v in self.config["SeriesSecondaryVariables"].items()
        }
        self.parallel_model_secondary_variables = {
            k.strip(): v.strip()
            for k, v in self.config["ParallelModelSecondaryVariables"].items()
        }

        # Additional model sections
        self.model_secondary_formulas = {
            k.strip(): v.strip()
            for k, v in self.config["ModelSecondaryFormulas"].items()
        }
        self.model_terciary_formulas = {
            k.strip(): v.strip()
            for k, v in self.config["ModelTerciaryFormulas"].items()
        }



    def _compile_secondary_expressions(self):
        """
        Compiles the expressions from Series and Parallel sections
        into lambdas. 
        (Same logic as your original approach)
        """
        # 1) Primary slider symbols
        primary_vars = list(self.slider_configurations.keys())
        primary_symbols = symbols(primary_vars)
        self.symbols_list = list(primary_symbols)

        # 2) Series expressions
        self._compile_expressions(
            self.series_secondary_variables,
            self.compiled_expressions,  # store here
            self.symbols_list
        )

        # 3) Parallel expressions need extended vars
        extended_vars = primary_vars + list(self.series_secondary_variables.keys())
        extended_symbols = symbols(extended_vars)

        self._compile_expressions(
            self.parallel_model_secondary_variables,
            self.dependent_compiled_expressions,  # store here
            extended_symbols
        )

    def _compile_model_sections(self):
        """
        Compiles the formulas in [ModelSecondaryFormulas] and [ModelTerciaryFormulas].
        Both might need the full extended set of symbols: 
        primary slider vars + series + parallel vars + freq.
        """
        primary_vars = list(self.slider_configurations.keys())
        series_vars  = list(self.series_secondary_variables.keys())
        parallel_vars= list(self.parallel_model_secondary_variables.keys())

        # We also need `freq` in these expressions
        all_vars = primary_vars + series_vars + parallel_vars + ["freq"]
        all_symbols = symbols(all_vars)

        # 1) Compile [ModelSecondaryFormulas]
        self._compile_expressions(
            self.model_secondary_formulas,
            self.compiled_model_secondary,  # store here
            all_symbols
        )

        # 2) Compile [ModelTerciaryFormulas]
        #    They might refer to the variables from [ModelSecondaryFormulas] as well.
        extended_vars2 = all_vars + list(self.model_secondary_formulas.keys())
        extended_symbols2 = symbols(extended_vars2)

        self._compile_expressions(
            self.model_terciary_formulas,
            self.compiled_model_terciary,  # store here
            extended_symbols2
        )

    def _compile_final_formula(self):
        """
        Compiles the single formula from [ModelFormula].
        For example: formula = Z0 + (Zh*Zrock)/(Zh+Zrock) + ...
        """
        section = "ModelFormula"
        if section not in self.config:
            raise ValueError("Missing [ModelFormula] section.")
        formula_str = self.config[section].get("formula", "").strip()
        if not formula_str:
            raise ValueError("No 'formula' key under [ModelFormula].")

        # Gather all possible symbols
        primary_vars    = list(self.slider_configurations.keys())
        series_vars     = list(self.series_secondary_variables.keys())
        parallel_vars   = list(self.parallel_model_secondary_variables.keys())
        secondary_vars  = list(self.model_secondary_formulas.keys())
        terciary_vars   = list(self.model_terciary_formulas.keys())

        all_vars = primary_vars + series_vars + parallel_vars + secondary_vars + terciary_vars + ["freq"]
        all_symbols = symbols(all_vars)

        try:
            expr = sympify(formula_str)
            # Check undefined
            missing = expr.free_symbols - set(all_symbols)
            if missing:
                raise ValueError(f"Undefined symbols in [ModelFormula]: {missing}")

            # Lambdify
            self.model_final_formula = lambdify(all_symbols, expr, "numpy")
            logging.info("[ModelFormula] compiled successfully.")
        except SympifyError as e:
            raise ValueError(f"Error parsing [ModelFormula]: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error: {e}")




    #Aux for _extratc_mandatory_parameters
    def _extract_sliders_configurations(self):
        sliders = {}
        for key, value in self.config["SliderConfigurations"].items():
            parts = value.split(",")
            if len(parts) != 4:
                raise ValueError(f"Invalid slider configuration for '{key}'. Expected 4 comma-separated values.")
            slider_type_str, min_val_str, max_val_str, color = parts
            slider_class = self._safe_import(slider_type_str.strip())
            if slider_class is None:
                raise ValueError(f"Unrecognized slider type '{slider_type_str}' for slider '{key}'.")
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str.strip()),
                float(max_val_str.strip()),
                color.strip(),
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
           

    def _compile_secondary_expressions(self):
        """
        Compiles SymPy expressions for secondary variables to speed up evaluations.
        Processes independent (series) and dependent (parallel) variables based on configuration sections.
        """
        try:
            # Define symbols for primary slider variables
            primary_vars = list(self.slider_configurations.keys())
            primary_symbols = symbols(primary_vars)
            self.symbols_list = list(primary_symbols)
        except Exception as e:
            raise ValueError(f"Error initializing symbols: {e}")

        # Compile SeriesSecondaryVariables (Independent)
        self._compile_expressions(
            self.series_secondary_variables,
            self.compiled_expressions,
            self.symbols_list
        )

        # Prepare symbols for ParallelModelSecondaryVariables (Dependent)
        # Include both primary slider symbols and series secondary variable symbols
        extended_vars = primary_vars + list(self.series_secondary_variables.keys())
        extended_symbols = symbols(extended_vars)

        self._compile_expressions(
            self.parallel_model_secondary_variables,
            self.dependent_compiled_expressions,
            extended_symbols
        )

    #Aux for _compile_secondary_expressions
    def _compile_expressions(self, variable_dict, compiled_dict, symbol_list):
        """
        Compiles SymPy expressions into lambda functions.

        :param variable_dict: Dictionary of variable names to expression strings.
        :param compiled_dict: Dictionary to store compiled lambda functions.
        :param symbol_list: List of SymPy symbols that the expressions can use.
        """
        for variable, expr in variable_dict.items():
            try:
                sympy_expr = sympify(expr)
                # Check for undefined symbols
                expr_symbols = sympy_expr.free_symbols
                defined_symbols = set(symbol_list)
                missing_symbols = expr_symbols - defined_symbols
                if missing_symbols:
                    missing = ", ".join(str(s) for s in missing_symbols)
                    raise ValueError(f"Expression for '{variable}' contains undefined symbols: {missing}")

                # Create a lambda function for the expression
                func = lambdify(symbol_list, sympy_expr, "numpy")

                # Validate the number of arguments
                expected_args = len(symbol_list)
                if func.__code__.co_argcount != expected_args:
                    raise ValueError(
                        f"Function for '{variable}' expects {expected_args} arguments, "
                        f"but got {func.__code__.co_argcount}."
                    )

                compiled_dict[variable] = func

            except SympifyError as e:
                print(f"Error parsing equation for '{variable}': {e}")
                compiled_dict[variable] = None
            except Exception as e:
                print(f"Unexpected error compiling equation for '{variable}': {e}")
                compiled_dict[variable] = None

    def _compile_serial_model(self):
        """
        Compiles the SerialModelFormula expression, dynamically collecting all valid symbols
        from the configuration.
        """
        if "SerialModelFormula" not in self.config:
            raise ValueError("Missing 'SerialModelFormula' section in the config file.")
    
        formula_str = self.config["SerialModelFormula"].get("formula", "").strip()
        if not formula_str:
            raise ValueError("No formula defined under 'SerialModelFormula' section.")
    
        try:
            # Gather all possible symbols from sliders and secondary variables
            primary_vars = list(self.slider_configurations.keys())
            series_vars = list(self.series_secondary_variables.keys())
            parallel_vars = list(self.parallel_model_secondary_variables.keys())
            all_vars = primary_vars + series_vars + parallel_vars + ["freq"]
    
            all_symbols = symbols(all_vars)
    
            # Parse and validate the formula
            sympy_expr = sympify(formula_str)
    
            # Check for undefined symbols
            expr_symbols = sympy_expr.free_symbols
            missing_symbols = expr_symbols - set(all_symbols)
            if missing_symbols:
                missing = ", ".join(str(s) for s in missing_symbols)
                raise ValueError(f"SerialModelFormula contains undefined symbols: {missing}")
    
            # Compile the formula
            self.serial_model_compiled_formula = lambdify(all_symbols, sympy_expr, "numpy")
    
            logging.info("SerialModelFormula compiled successfully.")
    
        except SympifyError as e:
            raise ValueError(f"Error parsing SerialModelFormula: {e}")
    
        except Exception as e:
            raise ValueError(f"Unexpected error compiling SerialModelFormula: {e}")
    



    
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
            raise ValueError(f"Invalid file path. The directory does nto exist.")
        return True

    

#####################################
#Testing
#########################################

# Run the tests
if __name__ == '__main__':
    config_file = "config.ini"
    my_importer= ConfigImporter(config_file)
