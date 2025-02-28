# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 11:50:00 2024

A widget for selecting a folder of input files and extracting data from them.

Renamed from 'InputFileWidget' to 'WidgetInputFile' to match updated class naming conventions.
"""

import os
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QHBoxLayout, QFileDialog, QInputDialog, QFileDialog, QMenu, QAction
)
from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from ConfigImporter import ConfigImporter
from CustomListSliders import ListSlider



#this is a file type
class NewZFile:
    """
    Handles writing rows of data to CSV files safely.
    """
    
    name='New .Z'
    
    caracteristics={
        'supported_file_extension': '.z', 
        'skip_rows': '128', 
        'freq_column': '0', 
        'z_real_column': '4', 
        'z_imag_column': '5'
    }
    
    
class OldZFile:
    """
    Handles writing rows of data to CSV files safely.
    """
    name='Old .Z'
    
    caracteristics={
        'supported_file_extension': '.jpg', 
        'skip_rows': '128', 
        'freq_column': '0', 
        'z_real_column': '4', 
        'z_imag_column': '5'
    }


class FileTypesRegistry:
    
    def __init__(self):
        
        self._registry = {
        NewZFile.name: NewZFile,
        OldZFile.name: OldZFile,
    }

    def get_file_type(self, file_type_name):
        
        file_cls = self._registry.get(file_type_name)
        if file_cls is None:
            raise ValueError(f"Unknown file type: {file_type_name}")
        return file_cls()
    
    def get_default_file_type(self):
        default_key = list(self._registry.keys())[0]
        return self.get_file_type(default_key)
    
    def get_available_file_types(self):
        """
        Returns a list of all registered file type names.
        """
        return list(self._registry.keys())


class WidgetInputFile(QWidget):
    """
    A widget for browsing supported files in a directory, reading them in,
    and emitting arrays of frequency, real Z, and imaginary Z via a signal.
    """

    file_data_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, config_parameters, current_file=None, filetype_name=None):

        super().__init__()
        
        self.registry = FileTypesRegistry()
        
        self._file_type = None
        
        if filetype_name is None:
            self._file_type =self.registry.get_default_file_type()
        else: 
            self._file_type = self.registry.get_file_type(filetype_name)

        self.config_p = self._file_type.caracteristics
        #self.config_p = config_parameters




        # Internal state
        self._folder_path = None
        self._files = []
        self._current_index = -1
        
        # Declare UI elements
        self.select_folder_button = QPushButton("Select Input Folder")
        self.select_file_type_button = QPushButton("Select File Type")
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.file_label = QLabel("No file selected")
        self._slider = ListSlider()
        
        self._slider.valueChanged.connect(self._slider_update_handler)
        # Build the UI layout
        self._initialize_ui() 
        self._validate_parameters()
  
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_folder_path(self) -> str:
        """
        Returns the currently selected folder path.
        """
        return self._folder_path

    def get_current_file_path(self) -> str:
        """
        Returns the absolute path of the currently displayed file.
        """
        if 0 <= self._current_index < len(self._files):
            return os.path.join(self._folder_path, self._files[self._current_index])
        return None

    def get_current_file_name(self) -> str:
        """
        Returns the name of the currently displayed file.
        """
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None
  
    def get_file_type_name(self):
        return self._file_type.name
    
    def setup_current_file(self, current_file):
        """
        Sets up the current file by verifying its existence, loading the files
        in its directory, and updating the current index if found.
        
        Parameters
        ----------
        current_file : str, optional
            The full path to a .z file to be initially selected, by default None.
        """
        if current_file and os.path.isfile(current_file):
            folder_path = os.path.dirname(current_file)
            self._folder_path = folder_path
            self._load_files()
            
            file_name = os.path.basename(current_file)
            if file_name in self._files:
                self._current_index = self._files.index(file_name)
                self._update_file_display()
                self._update_navigation_buttons()
                
            else:
                print(f"File '{file_name}' was not found in the folder '{self._folder_path}'.")
        
        elif current_file:
            folder_path = os.path.dirname(current_file)
            
            if os.path.isdir(folder_path):
                self._folder_path = folder_path
                self._load_files()
                print(f"File '{os.path.basename(current_file)}' was not found in the folder '{self._folder_path}'.")
            else:
                print(f"Path '{current_file}' was not found.")
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    # UI Methods
    def _initialize_ui(self):
        """
        Creates and lays out all UI elements, and connects signals.
        """
        # Button actions
        self.select_folder_button.clicked.connect(self._select_folder_handler)
        self.select_file_type_button.clicked.connect(self._select_file_type_handler)
        self.previous_button.clicked.connect(self._show_previous_file)
        self.next_button.clicked.connect(self._show_next_file)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        # Slider setup
        self._slider.setMinimumWidth(600)
        self._slider.valueChanged.connect(self._slider_update_handler)
        
        # File label
        self.file_label.setAlignment(Qt.AlignCenter)
        
        # Main layout
        layout = QHBoxLayout()
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.select_file_type_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)
        layout.addWidget(self._slider)
        self.setLayout(layout)
        
    # Configuration
    def _validate_parameters(self):
        """
        Validates that all required configuration parameters are present.
        Raises a ValueError if any are missing.
        """
        needed_parameters = [
            'supported_file_extension',
            'skip_rows',
            'freq_column',
            'z_real_column',
            'z_imag_column'
        ]
        missing_params = [param for param in needed_parameters if param not in self.config_p]
        if missing_params:
            missing = ', '.join(missing_params)
            raise ValueError(f"WidgetInputFile._validate_parameters: Configuration must include parameters: {missing}")
        else:
            self.config_p=self._cast_config_parameters(self.config_p)
    
    def _cast_config_parameters(self, config_parameters):
        
        try:
            return {
                'supported_file_extension': config_parameters['supported_file_extension'].lower(),
                'skip_rows': int(config_parameters['skip_rows']),
                'freq_column': int(config_parameters['freq_column']),
                'z_real_column': int(config_parameters['z_real_column']),
                'z_imag_column': int(config_parameters['z_imag_column'])
            }
        except (KeyError, ValueError) as e:
            raise ValueError(f"WidgetInputFile._cast_config_parameters:Invalid configuration parameters: {e}")

    #  File/Folder Methods       
    def _select_folder_handler(self):
        """
        Opens a directory selection dialog, then triggers file loading
        if a valid path is chosen.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._folder_path = folder
            self._load_files()

    def _load_files(self):
        """
        Scans the selected folder for files matching the supported extension,
        resets the current file index, and updates the UI.
        """
        if self._folder_path:
            supported_ext = self.config_p["supported_file_extension"]
            self._files = [
                f for f in os.listdir(self._folder_path)
                if f.lower().endswith(supported_ext)
            ]
            if self._files:
                self._current_index = 0
                self._update_file_display()
                self._update_navigation_buttons()
            else:
                self.file_label.setText(
                    f'No {self.config_p["supported_file_extension"]} files found in the selected folder.'
                )
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(False)
            self._slider.set_list(self._files)

    def _update_file_display(self):
        """
        Updates the UI to show the current file name, and calls
        _extract_content to read the file's data.
        """
        if 0 <= self._current_index < len(self._files):
            current_file = self._files[self._current_index]
            self.file_label.setText(current_file)
            
            #Set the slider
            self._slider.setValue(self._current_index)

            # Build full path and extract the file's content
            file_path = os.path.join(self._folder_path, current_file)
            self._extract_content(file_path)

    def _update_navigation_buttons(self):
        """
        Enables or disables navigation buttons based on the current index.
        """
        self.previous_button.setEnabled(self._current_index > 0)
        self.next_button.setEnabled(self._current_index < len(self._files) - 1)  
    
    #File Type Methods
    def _select_file_type_handler(self):

        file_types = self.registry.get_available_file_types()
        
        # Create a popup menu
        menu = QMenu(self)
        
        # Add one QAction per file type
        for ft in file_types:
            action = QAction(ft, self)
            
            # Connect the action's "triggered" signal
            # Use a lambda to capture ft in the callback
            action.triggered.connect(lambda checked, ft_name=ft: self._on_file_type_selected(ft_name))
            menu.addAction(action)
        
        # Position the menu so it drops down from the button
        # We'll map to global coords and just offset below the button
        button_pos = self.select_file_type_button.mapToGlobal(QPoint(0, self.select_file_type_button.height()))
        menu.exec_(button_pos)

    def _on_file_type_selected(self, selected_type):
        """
        Internal slot called when a file type is chosen from the popup menu.
        """
        self._file_type = self.registry.get_file_type(selected_type)
        self.config_p = self._file_type.caracteristics
        self._validate_parameters()
        
        # If a folder is already selected, reload the files so the new extension
        if self._folder_path:
            self._load_files()
                
    
    # Private Navigation Methods  
    def _show_previous_file(self):
        """
        Moves to the previous file in the list, if possible.
        """
        if self._current_index > 0:
            self._current_index -= 1
            self._update_file_display()
            self._update_navigation_buttons()
            
            self._slider.down()

    def _show_next_file(self):
        """
        Moves to the next file in the list, if possible.
        """
        if self._current_index < len(self._files) - 1:
            self._current_index += 1
            self._update_file_display()
            self._update_navigation_buttons()
            
            self._slider.up()
    
    def _slider_update_handler(self, index):
        self._current_index=index
        self._update_file_display()
        self._update_navigation_buttons()

    # Content methods
    def _extract_content(self, file_path: str):
        #print("_extract_content")
        """
        Reads the file at file_path using the specified configuration,
        and emits a signal with the extracted data.
        
        Parameters
        ----------
        file_path : str
            The absolute path to the file to be read.
        """
        try:
            df = pd.read_csv(
                file_path,
                sep='\t',
                skiprows=self.config_p["skip_rows"],
                header=None
            )

            # Ensure columns exist
            freq_col = self.config_p["freq_column"]
            z_real_col = self.config_p["z_real_column"]
            z_imag_col = self.config_p["z_imag_column"]
            max_col = max(freq_col, z_real_col, z_imag_col)
            
            if max_col >= len(df.columns):
                raise ValueError("File does not contain the required columns.")

            freq = df[freq_col].to_numpy()
            z_real = df[z_real_col].to_numpy()
            z_imag = df[z_imag_col].to_numpy()

            self.file_data_updated.emit(freq, z_real, z_imag)
            
            #print("emitted signal")
        
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            self.file_data_updated.emit(np.array([]), np.array([]), np.array([]))

# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------

import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
)
from PyQt5.QtCore import Qt


class TestWindow(QWidget):
    def __init__(self, config_parameters):
        
        super().__init__()
        self.setWindowTitle("Test for WidgetInputFile")

        # 1) Create the WidgetInputFile instance
        self.widget_input_file = WidgetInputFile(config_parameters)

        # 2) Connect its signal to see incoming data in console
        self.widget_input_file.file_data_updated.connect(self.handle_file_data_updated)

        # 3) Build a layout: the widget + some test buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.widget_input_file)

        # Buttons to test the public methods
        button_layout = QHBoxLayout()

        btn_folder_path = QPushButton("Get Folder Path")
        btn_folder_path.clicked.connect(self.show_folder_path)
        button_layout.addWidget(btn_folder_path)

        btn_current_file_path = QPushButton("Get Current File Path")
        btn_current_file_path.clicked.connect(self.show_current_file_path)
        button_layout.addWidget(btn_current_file_path)

        btn_current_file_name = QPushButton("Get Current File Name")
        btn_current_file_name.clicked.connect(self.show_current_file_name)
        button_layout.addWidget(btn_current_file_name)

        # Optional: a button to demonstrate setup_current_file
        btn_setup_file = QPushButton("Setup Current File")
        btn_setup_file.clicked.connect(self.test_setup_current_file)
        button_layout.addWidget(btn_setup_file)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    # -----------------------------------------------------------------------
    #  Button Handlers
    # -----------------------------------------------------------------------
    def show_folder_path(self):
        print("Folder path:", self.widget_input_file.get_folder_path())

    def show_current_file_path(self):
        print("Current file path:", self.widget_input_file.get_current_file_path())

    def show_current_file_name(self):
        print("Current file name:", self.widget_input_file.get_current_file_name())

    def test_setup_current_file(self):
        """
        Example usage:
        Suppose we have some file like 'C:/data/test.z'.
        If it exists, WidgetInputFile will load that folder and set that file.
        """
        dummy_file = "C:/path/to/your/test.z"
        self.widget_input_file.setup_current_file(dummy_file)

    # -----------------------------------------------------------------------
    #  Slot for file_data_updated
    # -----------------------------------------------------------------------
    def handle_file_data_updated(self, freq, z_real, z_imag):
        print("Received file_data_updated signal:")
        print("  freq:", freq)
        print("  z_real:", z_real)
        print("  z_imag:", z_imag)


if __name__ == "__main__":

    # Sample config dict. Normally you might read these from a ConfigImporter or JSON
    config = {
        'supported_file_extension': '.z',
        'skip_rows': 1,
        'freq_column': 0,
        'z_real_column': 1,
        'z_imag_column': 2
    }

    app = QApplication(sys.argv)

    test_window = TestWindow(config)
    test_window.resize(800, 100)
    test_window.show()

    sys.exit(app.exec_())