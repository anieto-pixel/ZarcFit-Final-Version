import os
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QFileDialog, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, Qt


class ErrorWindow:
    """
    Provides a static method to display critical error messages in a dialog box.
    """

    @staticmethod
    def show_error_message(message, title="Error"):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()


class FileWriter:
    """
    Handles writing text content to files in a safe manner.
    """

    @staticmethod
    def write_to_file(file_path, content):
        """
        Appends 'content' to the file at 'file_path'.
        If 'file_path' is invalid or the write fails, an error is shown.
        """
        if not file_path:
            ErrorWindow.show_error_message("No file selected for writing.")
            return

        try:
            with open(file_path, "a") as f:  # Append mode
                f.write(f"{content}\n")
        except Exception as e:
            ErrorWindow.show_error_message(f"Could not write to file: {e}")


class FileSelector:
    """
    Handles file creation, selection, and validation.
    """

    @staticmethod
    def create_new_file(desired_type, set_file_callback, set_message_callback):
        """
        Prompts the user to create a new file of 'desired_type'.
        If the file already exists, notifies the user.
        Otherwise, creates a blank file and calls 'set_file_callback' with its path.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            f"Create New {desired_type} File",
            os.getcwd(),
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            # Ensure it has the correct extension
            if not file_path.lower().endswith(desired_type):
                file_path += desired_type

            # Create the file if it doesn't exist yet
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', newline='') as f:
                        pass  # Just create an empty file
                    set_file_callback(file_path)
                except IOError as e:
                    ErrorWindow.show_error_message(f"Failed to create file: {str(e)}")
            else:
                set_message_callback("File already exists")
        else:
            set_message_callback("No file selected")

    @staticmethod
    def open_file_dialog(search_parameters, validate_callback, set_file_callback, set_message_callback):
        """
        Opens a dialog to select an existing file. If 'validate_callback' passes,
        calls 'set_file_callback' to update the application state. Otherwise shows an error.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select File",
            os.getcwd(),
            search_parameters
        )

        if file_path:
            try:
                if validate_callback(file_path):
                    set_file_callback(file_path)
            except ValueError as e:
                ErrorWindow.show_error_message(str(e))
        else:
            set_message_callback("No file selected")

    @staticmethod
    def validate(file_path, desired_type):
        """
        Ensures the file ends with the specified extension.
        Raises ValueError if it does not.
        """
        if not file_path.lower().endswith(desired_type):
            raise ValueError(f"The selected file must end with '{desired_type}'")
        return True


class WidgetOutputFile(QWidget):
    """
    A widget for creating or selecting a .csv output file and writing data to it.
    Renamed from 'OutputFileWidget' to 'WidgetOutputFile'.
    """
    
    output_file_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._desired_type = ".csv"
        self._search_parameters = "CSV Files (*.csv);;All Files (*)"
        self._output_file = None
        self._output_header = None

        # Create UI elements
        self._newfile_button = QPushButton("New File")
        self._newfile_button.clicked.connect(self._handle_create_new_file)

        self._select_button = QPushButton("Select .csv File")
        self._select_button.clicked.connect(self._handle_open_file_dialog)

        self._file_label = QLabel("No output file selected")
        self._file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Build layout
        self._initialize_ui()

    def _initialize_ui(self):
        """
        Places buttons and label into a horizontal layout.
        """
        layout = QHBoxLayout()
        self._newfile_button.setFixedSize(100, 30)
        layout.addWidget(self._newfile_button)
        layout.addWidget(self._select_button)
        layout.addWidget(self._file_label)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(1)
        self.setLayout(layout)

    def _handle_create_new_file(self):
        """
        Invokes 'FileSelector.create_new_file' to create or overwrite a CSV file.
        """
        FileSelector.create_new_file(
            self._desired_type,
            self._set_output_file,
            self._set_file_message
        )

    def _handle_open_file_dialog(self):
        """
        Invokes 'FileSelector.open_file_dialog' to select an existing CSV file.
        """
        FileSelector.open_file_dialog(
            self._search_parameters,
            lambda path: FileSelector.validate(path, self._desired_type),
            self._set_output_file,
            self._set_file_message
        )

    def _set_output_file(self, file_path):
        """
        Updates the widget's label and internal state with the chosen file path.
        """
        self._output_file = file_path
        self._file_label.setText(os.path.basename(file_path))
        
        self.output_file_selected.emit(self._output_file)

    def _set_file_message(self, message):
        """
        Sets a text message on the widget's label (e.g., "File already exists").
        """
        self._file_label.setText(message)

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_output_file(self):
        """
        Returns the path of the currently selected output file, or None if none.
        """
        return self._output_file
    
    def setup_current_file(self, new_imput_file):
        self._set_output_file(new_imput_file)

    def write_to_file(self, content, header=None):
        """
        Writes iterable 'content' to the selected output file. If none is selected, shows an error.
        """ 
        if self._output_file:
            if(self._output_header==None and header != None):
                self._output_header=header
                try:
                    with open(self._output_file, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(header)  # 'content' must be an iterable (e.g., list)
                except Exception as e:
                    ErrorWindow.show_error_message(f"Could not write to file: {e}")

            #FileWriter.write_to_file(self._output_file, content)
            try:
                with open(self._output_file, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(content)  # 'content' must be an iterable (e.g., list)
            except Exception as e:
                ErrorWindow.show_error_message(f"Could not write to file: {e}")
        else:
            ErrorWindow.show_error_message(
                "No output file selected. Please select or create a file first."
            )


# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import numpy as np
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    
    app = QApplication(sys.argv)

    # Create an instance of WidgetOutputFile
    widget = WidgetOutputFile()
    widget.setWindowTitle("WidgetOutputFile - Comprehensive Manual Test")

    # Optional: Add a button or two to test writing in real time
    write_test_button = QPushButton("Write Something")
    
    # A helper function to demonstrate writing
    def write_some_content():
        widget.write_to_file("Hello from the test_widget_output_file!")
        
        modeled_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }
        
        widget.write_to_file(modeled_data['freq'], modeled_data.keys())
    
    write_test_button.clicked.connect(write_some_content)

    # Layout for the test window
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)
    layout.addWidget(write_test_button)
    container.setLayout(layout)
    container.show()


    # ----- STEP 1: Attempt writing with no file selected (should show error) -----
    QTimer.singleShot(1000, lambda: widget.write_to_file("Attempting to write with no file selected..."))

    # (The rest of the steps require manual interaction.)



    sys.exit(app.exec_())