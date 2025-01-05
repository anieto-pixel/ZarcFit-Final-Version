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

    def __init__(self, config_file: str):
        """
        Loads configuration from the specified .ini file and initializes
        the UI for folder selection and file navigation.
        
        Parameters
        ----------
        config_file : str
            The path to a .ini file. Must contain an 'InputFileWidget' section
            with keys like 'supported_file_extension', 'skip_rows', etc.
        """
        super().__init__()

        # Load and parse configuration
        self.config = ConfigImporter(config_file)
        cfg_section = self.config.input_file_widget_config

        # Extract required fields from config
        self.supported_file_extension = cfg_section.get('supported_file_extension')
        self.skip_rows = int(cfg_section.get('skip_rows'))
        self.freq_column = int(cfg_section.get('freq_column'))
        self.z_real_column = int(cfg_section.get('z_real_column'))
        self.z_imag_column = int(cfg_section.get('z_imag_column'))

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
            # Only include files whose names end with the extension (case-insensitive)
            self._files = [
                f for f in os.listdir(self._folder_path)
                if f.lower().endswith(self.supported_file_extension)
            ]
            if self._files:
                self._current_index = 0
                self._update_file_display()
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(len(self._files) > 1)
            else:
                self.file_label.setText(
                    f"No {self.supported_file_extension} files found in the selected folder."
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

            # Adjust buttons based on position
            self.previous_button.setEnabled(self._current_index > 0)
            self.next_button.setEnabled(self._current_index < len(self._files) - 1)

            # Build full path and extract the file's content
            file_path = os.path.join(self._folder_path, current_file)
            self._extract_content(file_path)

    def _show_previous_file(self):
        """
        Moves to the previous file in the list, if possible.
        """
        if self._current_index > 0:
            self._current_index -= 1
            self._update_file_display()

    def _show_next_file(self):
        """
        Moves to the next file in the list, if possible.
        """
        if self._current_index < len(self._files) - 1:
            self._current_index += 1
            self._update_file_display()

    def _extract_content(self, file_path: str):
        """
        Carefully reads the file at file_path. Uses skip_rows, freq_column,
        z_real_column, and z_imag_column to parse the data. Emits a signal
        with the arrays or empty arrays on error.
        """
        try:
            df = pd.read_csv(
                file_path,
                sep='\t',
                skiprows=self.skip_rows,
                header=None
            )

            # Ensure columns exist
            if max(self.freq_column, self.z_real_column, self.z_imag_column) >= len(df.columns):
                raise ValueError("File does not contain the required columns.")

            freq = df[self.freq_column].to_numpy()
            z_real = df[self.z_real_column].to_numpy()
            z_imag = df[self.z_imag_column].to_numpy()

            self.file_data_updated.emit(freq, z_real, z_imag)
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            self.file_data_updated.emit(np.array([]), np.array([]), np.array([]))

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_folder_path(self) -> str:
        """
        Returns
        -------
        str :
            The currently selected folder path, or None if none selected.
        """
        return self._folder_path

    def get_current_file_path(self) -> str:
        """
        Returns
        -------
        str :
            The absolute path of the currently displayed file, or None if invalid.
        """
        if 0 <= self._current_index < len(self._files):
            return os.path.join(self._folder_path, self._files[self._current_index])
        return None

    def get_current_file_name(self) -> str:
        """
        Returns
        -------
        str :
            The name of the currently displayed file, or None if invalid.
        """
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None


# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------
def test_input_file_widget():
    """
    Basic test that creates a temporary .ini file, verifies that
    WidgetInputFile loads config fields, and shows the UI.
    """
    import os
    config_file = "test_config.ini"

    # Create sample config
    with open(config_file, "w") as file:
        file.write("""
[SliderConfigurations]
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
        app = QApplication([])
        widget = WidgetInputFile(config_file)

        # Verify config
        assert widget.supported_file_extension == ".z", "SUPPORTED_FILE_EXTENSION mismatch."
        assert widget.skip_rows == 128, "SKIP_ROWS mismatch."
        assert widget.freq_column == 0, "FREQ_COLUMN mismatch."
        assert widget.z_real_column == 4, "Z_REAL_COLUMN mismatch."
        assert widget.z_imag_column == 5, "Z_IMAG_COLUMN mismatch."

        print("Configuration values loaded successfully!")
        widget.show()
        app.exec_()
        print("\nTest passed: WidgetInputFile loaded configuration correctly.")

    except Exception as e:
        print(f"Test failed: {e}")

    finally:
        if os.path.exists(config_file):
            os.remove(config_file)


if __name__ == "__main__":
    test_input_file_widget()

    # Optionally, run the widget using a known config.ini
    # app = QApplication([])
    # widget = WidgetInputFile("config.ini")
    # widget.show()
    # app.exec_()