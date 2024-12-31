# -*- coding: utf-8 -*- 
"""
Created on Tue Dec 10 11:50:00 2024

@author: agarcian
"""
import os
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt

import configparser


"""
A widget for selecting a folder, navigating supported files, and extracting file content.

Signals:
    - file_contents_updated (np.ndarray, np.ndarray, np.ndarray):
    Emitted with frequencies, real impedances, and imaginary impedances.
"""

class InputFileWidget(QWidget):
    file_contents_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, config_file):
        super().__init__()

        # Read configuration from the provided config file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.supported_file_extension = self.config.get("InputFileWidget", "SUPPORTED_FILE_EXTENSION")
        self.skip_rows = self.config.getint("InputFileWidget", "SKIP_ROWS")
        self.freq_column = self.config.getint("InputFileWidget", "FREQ_COLUMN")
        self.z_real_column = self.config.getint("InputFileWidget", "Z_REAL_COLUMN")
        self.z_imag_column = self.config.getint("InputFileWidget", "Z_IMAG_COLUMN")

        # Private attributes
        self._folder_path = None
        self._files = []
        self._current_index = -1

        # Initialize buttons
        self.select_folder_button = QPushButton("Select Input Folder")
        self.select_folder_button.clicked.connect(self._select_folder)

        self.previous_button = QPushButton("<")
        self.previous_button.clicked.connect(self._show_previous_file)
        self.previous_button.setEnabled(False)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self._show_next_file)
        self.next_button.setEnabled(False)

        # Initialize label
        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)

        # Arrange layout
        self._initialize_ui()

    def _initialize_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._folder_path = folder
            self._load_files()

    def _load_files(self):
        if self._folder_path:
            self._files = [f for f in os.listdir(self._folder_path) if f.lower().endswith(self.supported_file_extension)]
            if self._files:
                self._current_index = 0
                self._update_file_display()
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(len(self._files) > 1)
            else:
                self.file_label.setText(f"No {self.supported_file_extension} files found in the selected folder.")
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(False)

    def _update_file_display(self):
        if 0 <= self._current_index < len(self._files):
            current_file = self._files[self._current_index]
            self.file_label.setText(current_file)
            self.previous_button.setEnabled(self._current_index > 0)
            self.next_button.setEnabled(self._current_index < len(self._files) - 1)
            self._extract_content(os.path.join(self._folder_path, current_file))

    def _show_previous_file(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._update_file_display()

    def _show_next_file(self):
        if self._current_index < len(self._files) - 1:
            self._current_index += 1
            self._update_file_display()

    def _extract_content(self, file_path):
        try:
            df = pd.read_csv(file_path, sep='\t', skiprows=self.skip_rows, header=None)

            if max(self.freq_column, self.z_real_column, self.z_imag_column) >= len(df.columns):
                raise ValueError("File does not contain the required columns.")

            freq = df[self.freq_column].to_numpy()
            Z_real = df[self.z_real_column].to_numpy()
            Z_imag = df[self.z_imag_column].to_numpy()

            self.file_contents_updated.emit(freq, Z_real, Z_imag)

        except Exception as e:
            print(f"Error reading file: {e}")
            self.file_contents_updated.emit(np.array([]), np.array([]), np.array([]))
    """PUBLIC METHODS."""

    def get_folder_path(self):
        """Returns the path of the currently selected folder."""
        
        return self._folder_path

    def get_current_file_path(self):
        """Returns the full path of the currently displayed file."""
        
        if 0 <= self._current_index < len(self._files):
            return os.path.join(self._folder_path, self._files[self._current_index])
        return None
    
    def get_current_file_name(self):
        """Returns the name of the currently displayed file."""
        
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None


if __name__ == "__main__":
    app = QApplication([])

    widget = InputFileWidget("config.ini")
    widget.show()

    app.exec_()