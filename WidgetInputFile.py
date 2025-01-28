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
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from ConfigImporter import ConfigImporter


class WidgetInputFile(QWidget):
    """
    A widget for browsing supported files in a directory, reading them in,
    and emitting arrays of frequency, real Z, and imaginary Z via a signal.
    """

    file_data_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, config_parameters, current_file=None):

        super().__init__()
        
        self.config_p = config_parameters

        # Internal state
        self._folder_path = None
        self._files = []
        self._current_index = -1

        # UI elements
        self.select_folder_button = QPushButton("Select Input Folder")
        self.select_folder_button.clicked.connect(self._select_folder)

        self.previous_button = QPushButton("<")
        self.previous_button.clicked.connect(self._show_previous_file)
        self.previous_button.setEnabled(False)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self._show_next_file)
        self.next_button.setEnabled(False)

        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)

        # Build the UI layout
        self._initialize_ui() 
        self._validate_parameters()

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
            raise ValueError(f"Invalid configuration parameters: {e}")

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
            raise ValueError(f"Configuration must include parameters: {missing}")
        else:
            self.config_p=self._cast_config_parameters(self.config_p)

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

    def _initialize_ui(self):
        """
        Adds all buttons and the file label into a horizontal layout,
        then sets this widget's layout.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

    def _select_folder(self):
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

    def _update_file_display(self):
        """
        Updates the UI to show the current file name, and calls
        _extract_content to read the file's data.
        """
        if 0 <= self._current_index < len(self._files):
            current_file = self._files[self._current_index]
            self.file_label.setText(current_file)

            # Build full path and extract the file's content
            file_path = os.path.join(self._folder_path, current_file)
            self._extract_content(file_path)

    def _update_navigation_buttons(self):
        """
        Enables or disables navigation buttons based on the current index.
        """
        self.previous_button.setEnabled(self._current_index > 0)
        self.next_button.setEnabled(self._current_index < len(self._files) - 1)

    def _show_previous_file(self):
        """
        Moves to the previous file in the list, if possible.
        """
        if self._current_index > 0:
            self._current_index -= 1
            self._update_file_display()
            self._update_navigation_buttons()

    def _show_next_file(self):
        """
        Moves to the next file in the list, if possible.
        """
        if self._current_index < len(self._files) - 1:
            self._current_index += 1
            self._update_file_display()
            self._update_navigation_buttons()

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
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_folder_path(self) -> str:
        """
        Returns the currently selected folder path.
        
        Returns
        -------
        str
            The currently selected folder path, or None if none selected.
        """
        return self._folder_path

    def get_current_file_path(self) -> str:
        """
        Returns the absolute path of the currently displayed file.
        
        Returns
        -------
        str
            The absolute path of the currently displayed file, or None if invalid.
        """
        if 0 <= self._current_index < len(self._files):
            return os.path.join(self._folder_path, self._files[self._current_index])
        return None

    def get_current_file_name(self) -> str:
        """
        Returns the name of the currently displayed file.
        
        Returns
        -------
        str
            The name of the currently displayed file, or None if invalid.
        """
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None


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