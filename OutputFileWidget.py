from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os

"""
Created on Fri Dec  6 13:07:51 2024

@author: agarcian
"""

class ErrorWindow:
    @staticmethod
    def show_error_message(message, title="Error"):
        """
        Displays an error message in a dialog box.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()


class FileWriter:
    """
    Helper class responsible for writing data to a file.
    """
    @staticmethod
    def write_to_file(file_path, content):
        """
        Writes the provided content to the given file.
        """
        try:
            with open(file_path, "a") as f:  # Open file in append mode
                f.write(f"{content}\n")
        except Exception as e:
            ErrorWindow.show_error_message(f"Could not write to file: {e}")


class FileSelector:
    """
    Class responsible for handling file selection and validation.
    """
    @staticmethod
    def create_new_file(desired_type, set_file_callback, set_message_callback):
        """
        Opens a dialog for creating a new CSV file and creates the file if it doesn't exist.
        """
        file, _ = QFileDialog.getSaveFileName(None, f"Create New {desired_type} File",
                                              os.getcwd(), "CSV Files (*.csv);;All Files (*)")

        if file:
            if not file.lower().endswith(desired_type):
                file += desired_type

            if not os.path.exists(file):
                try:
                    with open(file, 'w', newline='') as f:
                        pass  # Creating an empty CSV file
                    set_file_callback(file)
                except IOError as e:
                    ErrorWindow.show_error_message(f"Failed to create file: {str(e)}")
            else:
                set_message_callback("File already exists")
        else:
            set_message_callback("No file selected")

    @staticmethod
    def open_file_dialog(search_parameters, validate_callback, set_file_callback, set_message_callback):
        """
        Opens a dialog for selecting a file and updates the label with the selected file's path.
        """
        file, _ = QFileDialog.getOpenFileName(None, "Select File", os.getcwd(), search_parameters)

        if file:
            try:
                if validate_callback(file):
                    set_file_callback(file)
            except ValueError as e:
                ErrorWindow.show_error_message(str(e))
        else:
            set_message_callback("No file selected")

    @staticmethod
    def validate(file_path, desired_type):
        if not file_path.lower().endswith(desired_type):
            raise ValueError("The selected file is of an invalid type.")
        return True


class OutputFileWidget(QWidget):
    """
    Class for selecting files and displaying the selected file.
    """
    def __init__(self):
        super().__init__()

        #Atributes
        self.__desired_type = ".csv"
        self.__search_parameters = "CSV Files (*.csv);;All Files (*)"
        self.__output_file = None

        #Create and connect buttons
        self.__newfile_button = QPushButton("New File")
        self.__newfile_button.clicked.connect(self.__handle_create_new_file)

        self.__select_button = QPushButton("Select .csv File")
        self.__select_button.clicked.connect(self.__handle_open_file_dialog)

        #Create label
        self.__file_label = QLabel("No output file selected")
        self.__file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)


        self._initialize_ui()
        
    def _initialize_ui(self):
        
        output_layout = QHBoxLayout()
        self.__newfile_button.setFixedSize(100, 30)
        output_layout.addWidget(self.__newfile_button)
        output_layout.addWidget(self.__select_button)
        output_layout.addWidget(self.__file_label)

        output_layout.setContentsMargins(5, 5, 5, 5)
        output_layout.setSpacing(1)
        self.setLayout(output_layout)

    def __handle_create_new_file(self):
        FileSelector.create_new_file(
            self.__desired_type,
            self.__set_file_label,
            self.__set_file_message
        )

    def __handle_open_file_dialog(self):
        FileSelector.open_file_dialog(
            self.__search_parameters,
            lambda file: FileSelector.validate(file, self.__desired_type),
            self.__set_file_label,
            self.__set_file_message
        )

    def __set_file_label(self, file_path):
        self.__output_file = file_path
        self.__file_label.setText(os.path.basename(file_path))

    def __set_file_message(self, message):
        self.__file_label.setText(message)

    def get_output_file(self):
        """Public getter for the selected output file path."""
        return self.__output_file
    
    def write_to_file(self, content):
        """Public method to write content in output file."""
        FileWriter.write_to_file(self.__output_file, content)


# To run the test in a standalone application
if __name__ == "__main__":
    app = QApplication([])

    widget = OutputFileWidget()
    widget.show()
    app.exec_()