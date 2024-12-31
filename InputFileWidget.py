# -*- coding: utf-8 -*- 
"""
Created on Tue Dec 10 11:50:00 2024

@author: agarcian
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import numpy as np
import pandas as pd  # Ensure this is imported for reading CSV files


class InputFileWidget(QWidget):
    """
    A widget that allows the user to select a folder, navigate through `.z` files,
    and display the content of the selected file.

    Signals:
        - file_contents_updated (str): Emitted when the content of the currently 
          displayed file is updated. The signal carries the file's contents as a string.
    """

    file_contents_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self):
        """
        Initialize the widget by setting up the UI and preparing internal attributes.
        """
        super().__init__()

        # Private attributes
        self._folder_path = None
        self._z_files = []
        self._current_index = -1

        # Initialize Buttons 
        self.select_folder_button = QPushButton("Select Input Folder")
        self.select_folder_button.clicked.connect(self._select_folder)

        self.previous_button = QPushButton("<")
        self.previous_button.clicked.connect(self._show_previous_file)
        self.previous_button.setEnabled(False)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self._show_next_file)
        self.next_button.setEnabled(False)

        # Creates label
        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)

        # Arrange layout
        self._initialize_ui()

        # Connect the signal to a test slot, when testing is needed
        #self.file_contents_updated.connect(self.test_signal)

    ### Private methods

    def _initialize_ui(self):
        """
        Sets up the layouts for the widget.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)

        self.setLayout(layout)

    def _select_folder(self):
        """
        Opens a dialog for the user to select a folder. If a folder is selected,
        loads all `.z` files from the folder and initializes navigation.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._folder_path = folder
            self._load_z_files()

    def _load_z_files(self):
        """
        Loads all `.z` files from the currently selected folder.
        """
        if self._folder_path:
            self._z_files = [f for f in os.listdir(self._folder_path) if f.lower().endswith(".z")]

            if self._z_files:
                self._current_index = 0
                self._update_file_display()
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(len(self._z_files) > 1)
            else:
                self.file_label.setText("No .z files found in the selected folder.")
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(False)

    def _update_file_display(self):
        """
        Updates the file display label and navigation button states.
        Emits the contents of the currently selected file.
        """
        if 0 <= self._current_index < len(self._z_files):
            current_file = self._z_files[self._current_index]
            self.file_label.setText(f"{current_file}")
            self.previous_button.setEnabled(self._current_index > 0)
            self.next_button.setEnabled(self._current_index < len(self._z_files) - 1)

            # Emit the contents of the file when it's updated
            self._extract_content(os.path.join(self._folder_path, current_file))

    def _show_previous_file(self):
        """
        Moves to the previous file in the list and updates the display.
        """
        if self._current_index > 0:
            self._current_index -= 1
            self._update_file_display()

    def _show_next_file(self):
        """
        Moves to the next file in the list and updates the display.
        """
        if self._current_index < len(self._z_files) - 1:
            self._current_index += 1
            self._update_file_display()

    def _extract_content(self, file_path):

        try:
            # Read the CSV file into a DataFrame, skipping the metadata lines
            # We use the 'skiprows' argument to skip all non-data lines before the actual data
            df = pd.read_csv(file_path, sep='\t', skiprows=range(0, 128), header=None)

            # Extract relevant columns (Freq(Hz), Z'(a), Z''(b))
            freq = df[0].to_numpy()  # Frequency (Hz)
            Z_real = df[4].to_numpy()  # Z'(a)
            Z_imag = df[5].to_numpy()  # Z''(b)

            # Emit the three numpy arrays as separate parameters in the signal
            self.file_contents_updated.emit(freq, Z_real, Z_imag)
        
        except Exception as e:
            print(f"Error reading file: {e}")
            # In case of an error, emit empty arrays
            self.file_contents_updated.emit(np.array([]), np.array([]), np.array([]))

    ### Public Methods

    def get_folder_path(self):
        """
        Returns the path of the folder currently selected by the user.
        """
        return self._folder_path

    def get_current_file_path(self):
        """
        Returns the full path of the currently displayed `.z` file.
        """
        if 0 <= self._current_index < len(self._z_files):
            return os.path.join(self._folder_path, self._z_files[self._current_index])
        return None

    # This is the slot that will receive the signal
    def test_signal(self, freqs, resistances, reactances):
        """
        This method receives the numpy arrays sent from the signal.
        """
        print(f"Received Frequencies: {freqs}")
        print(f"Received Resistances: {resistances}")
        print(f"Received Reactances: {reactances}")


if __name__ == "__main__":
    app = QApplication([])

    widget = InputFileWidget()
    widget.show()

    app.exec_()