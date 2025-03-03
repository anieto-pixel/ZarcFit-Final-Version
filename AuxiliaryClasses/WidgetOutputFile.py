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
    Handles writing rows of data to CSV files safely.
    """
    @staticmethod
    def write_to_file(file_path, rows, header=None):
        """
        Appends rows to 'file_path' as CSV lines.
        
        If 'header' is provided, it is ignored in this version (for backward compatibility).
        
        :param file_path: Path to the CSV file.
        :param rows: A single row or a list of rows (iterables) to write.
        :param header: (Ignored) Header row.
        """
        if not file_path:
            ErrorWindow.show_error_message("FileWriter.write_to_file :No file selected for writing.")
            return

        try:
            with open(file_path, "a", newline="") as f:
                writer = csv.writer(f)

                # 'header' is currently ignored (kept for backward compatibility)
                if header is not None and False:
                    writer.writerow(header)

                # If rows is a single row, wrap it in a list
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
                    with open(file_path, "w", newline="") as f:
                        pass  # Create empty file.
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
        Opens a dialog to select an existing file.
        If 'validate_callback' passes, calls 'set_file_callback' to update the application state.
        Otherwise, shows an error.
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
        Validates that the file path ends with the desired type.
        """
        if not file_path.lower().endswith(desired_type):
            raise ValueError(f"The selected file must end with '{desired_type}'")
        return True


class WidgetOutputFile(QWidget):
    """
    A widget for creating or selecting a .csv output file and writing data to it.
    The write_to_file() method expects a dictionary and builds a single row from it.
    """

    output_file_selected = pyqtSignal(str)

    def __init__(self, variables_to_print=None, output_file=None):
        super().__init__()

        if variables_to_print is None:
            variables_to_print = []

        self.variables_to_print = variables_to_print  # List of keys to look for.
        self._desired_type = ".csv"
        self._search_parameters = "CSV Files (*.csv);;All Files (*)"
        self._output_file = output_file

        # Create UI elements.
        self._newfile_button = QPushButton("New File")
        self._select_button = QPushButton("Select .csv File")
        self._file_label = QLabel("No output file selected")

        self._initialize_ui()
        self._connect_signals()
        self._set_output_file(output_file)
        
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_output_file(self):
        """Returns the currently selected output file path or None."""
        return self._output_file

    def set_current_file(self, output_file):
        """Sets the widget's file to 'new_input_file' and updates the UI."""
        self._set_output_file(output_file)

    def print_variables_list(self):
        """
        Writes 'variables_to_print' as a single row to the CSV file.
        """
        if not self._output_file:
            ErrorWindow.show_error_message(
                "No output file selected. Please select or create a file first."
            )
            return

        if self.variables_to_print:
            FileWriter.write_to_file(
                file_path=self._output_file,
                rows=self.variables_to_print  # Write as a single row.
            )

    def write_to_file(self, dictionary):
        """
        Expects a dictionary and builds a row by checking each key in
        'variables_to_print'. Missing keys are replaced with empty strings.
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

        row = [dictionary.get(key, "") for key in self.variables_to_print]

        FileWriter.write_to_file(
            file_path=self._output_file,
            rows=row,
            header=None  # Header param is ignored.
        )

    def find_row_in_file(self, head):
        """
        Searches the CSV file for a row whose first column matches 'head'
        and returns it as a dictionary.
        """
        try:
            with open(self._output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in reversed(lines):
                columns = line.strip().split(",")
                if columns and columns[0] == head:
                    dictionary = dict(zip(self.variables_to_print, columns))
                    return dictionary

            return None
        except Exception as e:
            ErrorWindow.show_error_message(
                f"WidgetOutputFile.find_row_in_file :Error reading file: {e}"
            )
            return None
       
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    def _initialize_ui(self):
        """
        Builds and sets the layout for this widget.
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(1)

        # Button sizes and alignment
        self._newfile_button.setFixedSize(100, 30)
        self._file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Add widgets to layout
        layout.addWidget(self._newfile_button)
        layout.addWidget(self._select_button)
        layout.addWidget(self._file_label)

        self.setLayout(layout)
        
    def _connect_signals(self):
        """
        Connects signals from buttons to their handlers.
        """
        self._newfile_button.clicked.connect(self._handle_create_new_file)
        self._select_button.clicked.connect(self._handle_open_file_dialog)

    def _handle_create_new_file(self):
        """
        Handler for creating a new file.
        """
        FileSelector.create_new_file(
            self._desired_type,
            self._set_output_file,
            self._set_file_message
        )
        if self.variables_to_print:
            self.print_variables_list()

    def _handle_open_file_dialog(self):
        """
        Handler for opening an existing file.
        """
        FileSelector.open_file_dialog(
            self._search_parameters,
            lambda path: FileSelector.validate(path, self._desired_type),
            self._set_output_file,
            self._set_file_message
        )

    def _set_output_file(self, file_path):
        """
        Called when the user picks or creates a file.
        Stores the file path and updates the UI.
        """
        if not isinstance(file_path, str):
               return
        
        self._output_file = file_path
        self._file_label.setText(os.path.basename(file_path))
        self.output_file_selected.emit(self._output_file)

        # Immediately write variables if available.
        #Code commented out at Randy's request
        # Enable for automatic writting of headers on open outputfile
        #if self.variables_to_print:
        #    self.print_variables_list()

    def _set_file_message(self, message):
        """
        Updates the label with a given message.
        """
        self._file_label.setText(message)


# -----------------------------------------------------------------------
# Test (Manually Adapted)
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # Hardcoded list of variables to print.
    vars_to_print = ["A", "B", "C", "D", "E"]

    widget = WidgetOutputFile(variables_to_print=vars_to_print)
    widget.setWindowTitle("WidgetOutputFile - Dictionary Test")

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)

    # Button to test writing a dictionary.
    write_test_button = QPushButton("Write Test Dictionary")
    layout.addWidget(write_test_button)
    container.setLayout(layout)
    container.show()

    def on_write_test_button():
        """
        Simulate a dictionary that includes some variables from vars_to_print
        and possibly extra keys not in vars_to_print.
        """
        data_dict = {
            "A": 100,
            "C": 300,
            "Z": 999  # 'Z' is not in vars_to_print.
        }
        widget.write_to_file(data_dict)

    write_test_button.clicked.connect(on_write_test_button)

    # Test writing with no file after 1 second.
    QTimer.singleShot(1000, lambda: widget.write_to_file({"A": 42}))

    sys.exit(app.exec_())
