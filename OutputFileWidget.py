# -*- coding: utf-8 -*-

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
        
        Parameters:
        - message: The error message to display.
        - title: The title of the message box (default is "Error").
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

        Parameters:
        - file_path: The path to the file where the content should be written.
        - content: The content to be written to the file.
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
    def create_new_file(parent):
        """
        Opens a dialog for creating a new CSV file and creates the file if it doesn't exist.
        """
        # Open a Save File dialog to create a new file
        file, _ = QFileDialog.getSaveFileName(parent, f"Create New {parent.desired_type} File", os.getcwd(), "CSV Files (*.csv);;All Files (*)")
        
        if file:  # If a file path is selected
            # Ensure the file has a .csv extension
            if not file.lower().endswith(parent.desired_type):
                file += parent.desired_type

            # Create the file if it doesn't exist
            if not os.path.exists(file):
                try:
                    with open(file, 'w', newline='') as f:
                        pass  # Creating an empty CSV file
                    parent.file_label.setText(file)
                    parent.output_file = file  # Set the file path to the parent widget
                except IOError as e:
                    # Handle error during file creation
                    ErrorWindow.show_error_message(f"Failed to create file: {str(e)}")
            else:
                parent.file_label.setText("File already exists")
        else:
            parent.file_label.setText("No file selected")
    
    @staticmethod
    def open_file_dialog(parent):
        """
        Opens a dialog for selecting a file and updates the label with the selected file's path.
        """
        # Open a file selection dialog
        file, _ = QFileDialog.getOpenFileName(parent, "Select File", os.getcwd(), parent.search_parameters)
    
        if file:  # If a file is selected
            # Validate the file
            try:
                if FileSelector.validate(file, parent.desired_type):  # Pass the selected file, not self.output_file
                    parent.file_label.setText(file)
                    parent.output_file = file  # Store the selected file path
    
            except ValueError as e:
                # Use the ErrorWindow class to show an error message if the file is invalid
                ErrorWindow.show_error_message(str(e))
        else:
            parent.file_label.setText("No file selected")

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

        self.desired_type=".csv"
        self.search_parameters= "CSV Files (*.csv);;All Files (*)"
        self.output_file = None
        
        # Create button for creating a file
        self.newfile_button = QPushButton("New File")
        self.newfile_button.clicked.connect(lambda: FileSelector.create_new_file(self))

        # Create button for selecting a file
        self.select_button = QPushButton("Select .csv File")
        # Connect button's clicked signal to open_file_dialog without invoking it immediately
        self.select_button.clicked.connect(lambda: FileSelector.open_file_dialog(self))

        # Label to display the selected file
        self.file_label = QLabel("No output file selected")
        self.file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        #####################
        ## Appearance stuff
        #################
        
        # Horizontal layout for buttons and labels
        output_layout = QHBoxLayout()
        
        # Set the newfile_button to be smaller
        self.newfile_button.setFixedSize(100, 30)  # Adjust size as needed
        output_layout.addWidget(self.newfile_button)
        #output_layout.addStretch(3)  # Add stretch to take 3/4 of the space
        
        output_layout.addWidget(self.select_button)
        output_layout.addWidget(self.file_label)
        
        output_layout.setContentsMargins(5, 5, 5, 5)
        output_layout.setSpacing(1)

        # Set the layout of the widget
        self.setLayout(output_layout)
        
        
##################################################
##################################################
#Input files
##################################################
##################################################

        
class InputFileWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.folder_path = None
        self.z_files = []
        self.current_index = -1

        self.select_folder_button = QPushButton("Select Input Folder")
        self.select_folder_button.clicked.connect(self.select_folder)

        self.previous_button = QPushButton("<")
        self.previous_button.clicked.connect(self.show_previous_file)
        self.previous_button.setEnabled(False)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.show_next_file)
        self.next_button.setEnabled(False)

        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout()
       # button_layout = QHBoxLayout()

       # button_layout.addWidget(self.previous_button)
       # button_layout.addWidget(self.next_button)

        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)
        #layout.addLayout(button_layout)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.load_z_files()

    def load_z_files(self):
        if self.folder_path:
            self.z_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".z")]
            if self.z_files:
                self.current_index = 0
                self.update_file_display()
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(len(self.z_files) > 1)
            else:
                self.file_label.setText("No .z files found in the selected folder.")
                self.previous_button.setEnabled(False)
                self.next_button.setEnabled(False)

    def update_file_display(self):
        if 0 <= self.current_index < len(self.z_files):
            current_file = self.z_files[self.current_index]
            self.file_label.setText(f"{current_file}")
            self.previous_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.z_files) - 1)

    def show_previous_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_file_display()

    def show_next_file(self):
        if self.current_index < len(self.z_files) - 1:
            self.current_index += 1
            self.update_file_display()







# To run the test in a standalone application
if __name__ == "__main__":
    app = QApplication([])

    layout = QHBoxLayout()
    widget_1 = InputFileWidget()
    widget_2 = OutputFileWidget()

    layout.addWidget(widget_1)  # Add widget_1 to the left
    layout.addStretch()         # Add a stretchable space to push the next widget to the right
    layout.addWidget(widget_2)  # Add widget_2 to the right

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()
    app.exec_()