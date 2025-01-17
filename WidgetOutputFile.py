import os
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QFileDialog, QHBoxLayout, QMessageBox, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal

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
    Handles writing rows of data to CSV files in a safe manner.
    """
    @staticmethod
    def write_to_file(file_path, rows, header=None):
        """
        Appends rows to 'file_path' as CSV lines.
        If 'header' is given, writes that first (in append mode).
        
        :param file_path: path to the CSV file
        :param rows: a single row or a list of rows (iterables) to write
        :param header: (ignored in this version, but kept for backward compatibility)
        """
        if not file_path:
            ErrorWindow.show_error_message("No file selected for writing.")
            return

        try:
            with open(file_path, "a", newline='') as f:
                writer = csv.writer(f)

                # If 'header' is present, we are ignoring it
                # but you could remove or adapt this if truly unnecessary:
                if header is not None and False:  # 'False' ensures it's never used
                    writer.writerow(header)

                # If 'rows' is a single row, wrap it in a list
                if isinstance(rows[0], (int, float, str)):
                    writer.writerow(rows)
                else:
                    for row in rows:
                        writer.writerow(row)

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
            if not file_path.lower().endswith(desired_type):
                file_path += desired_type

            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', newline='') as f:
                        pass  # create empty file
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
        if not file_path.lower().endswith(desired_type):
            raise ValueError(f"The selected file must end with '{desired_type}'")
        return True

class WidgetOutputFile(QWidget):
    """
    A widget for creating or selecting a .csv output file and writing data to it.
    Now write_to_file(...) expects a dictionary and builds a single row from it.
    """

    output_file_selected = pyqtSignal(str)

    def __init__(self, variables_to_print=[]):
        super().__init__()

        self.variables_to_print = variables_to_print  # list of keys to look for
        self._desired_type = ".csv"
        self._search_parameters = "CSV Files (*.csv);;All Files (*)"
        self._output_file = None

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
        layout = QHBoxLayout()
        self._newfile_button.setFixedSize(100, 30)
        layout.addWidget(self._newfile_button)
        layout.addWidget(self._select_button)
        layout.addWidget(self._file_label)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(1)
        self.setLayout(layout)

    def _handle_create_new_file(self):
        FileSelector.create_new_file(
            self._desired_type,
            self._set_output_file,
            self._set_file_message
        )

    def _handle_open_file_dialog(self):
        FileSelector.open_file_dialog(
            self._search_parameters,
            lambda path: FileSelector.validate(path, self._desired_type),
            self._set_output_file,
            self._set_file_message
        )

    def _set_output_file(self, file_path):
        """
        Called whenever user picks or creates a file.
        We store file_path and immediately print the variables in one row.
        """
        self._output_file = file_path
        self._file_label.setText(os.path.basename(file_path))

        self.output_file_selected.emit(self._output_file)

        # Print the single row of variables if available
        if self.variables_to_print:
            self.print_variables_list()

    def _set_file_message(self, message):
        self._file_label.setText(message)

    # -----------------------------------------------------------------------
    #  Public methods
    # -----------------------------------------------------------------------
    def get_output_file(self):
        return self._output_file

    def setup_current_file(self, new_input_file):
        self._set_output_file(new_input_file)

    def print_variables_list(self):
        """
        Writes 'variables_to_print' in a single row to the CSV file.
        Called whenever a new file is created or selected.
        """
        if not self._output_file:
            ErrorWindow.show_error_message(
                "No output file selected. Please select or create a file first."
            )
            return

        if self.variables_to_print:
            FileWriter.write_to_file(
                file_path=self._output_file,
                rows=self.variables_to_print  # single row
            )

    def write_to_file(self, dictionary):
        """
        Expects a dictionary. 
        We build a single row by checking each key in 'variables_to_print' (in order):
          - If the key is in 'content', we append the value
          - Otherwise, we append an empty string

        Then we pass that row to FileWriter.write_to_file(...) 
        to be appended as one line in the CSV.
        """
        if not self._output_file:
            ErrorWindow.show_error_message(
                "No output file selected. Please select or create a file first."
            )
            return

        if not isinstance(dictionary, dict):
            ErrorWindow.show_error_message(
                "write_to_file requires a dictionary. Received something else."
            )
            return

        row = []
        for key in self.variables_to_print:
            # If key is present, use its value; else an empty string
            value = dictionary.get(key, "")
            row.append(value)

        # Now pass this single row to FileWriter
        FileWriter.write_to_file(
            file_path=self._output_file,
            rows=row,
            header=None  # ignoring header now
        )


# -----------------------------------------------------------------------
#  TEST (Manually adapted)
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # In a real app, you'd do something like:
    # config_importer = ConfigImporter("config.ini")
    # vars_to_print = config_importer.variables_to_print
    # But here, we'll hardcode a simple list of variables:
    vars_to_print = ["A", "B", "C", "D", "E"]

    widget = WidgetOutputFile(variables_to_print=vars_to_print)
    widget.setWindowTitle("WidgetOutputFile - Dictionary Test")

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)

    # A button to test writing a dictionary
    write_test_button = QPushButton("Write Test Dictionary")
    layout.addWidget(write_test_button)
    container.setLayout(layout)
    container.show()

    def on_write_test_button():
        """
        We'll simulate a dictionary that:
         - includes some variables from vars_to_print (A, C),
         - excludes others (B, D, E),
         - and possibly has extra keys not in vars_to_print (e.g. 'Z').
        """
        data_dict = {
            "A": 100,
            "C": 300,
            "Z": 999  # not in vars_to_print
        }
        # This will produce a row: [100, "", 300, "", ""] for A, B, C, D, E
        widget.write_to_file(data_dict)

    write_test_button.clicked.connect(on_write_test_button)

    # Attempt writing with no file to see the error after 1s
    # This dictionary only has "A" => the row would be [42, "", "", "", ""]
    QTimer.singleShot(1000, lambda: widget.write_to_file({"A": 42}))

    sys.exit(app.exec_())
