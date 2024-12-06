import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 

import pyqtgraph as pg

import os
import numpy as np

#my own classes
from SliderWithTicks import SliderWithTicks

#########################################################################       
#############################################################################        
#Graphs Stuff
#############################################################################        
################################################################
class GraphCalculator(QObject):
    """
    Handles the computation for the graph based on sliders.
    """
    # Declare the signal at the class level
    data_changed = pyqtSignal()
    
    def __init__(self, sliders_widget):
        super().__init__()  # Initialize QObject
        self.sliders_widget = sliders_widget

    def compute_graph_data(self):
        """
        Computes the x and y values for the graph.
        Returns: (x, y) tuple
        """
        suma = sum(slider.get_value() for slider in self.sliders_widget.list_of_sliders)
        x = np.linspace(-100, 100, 1000)
        a = 1  # Quadratic coefficient
        y = a * (x - suma) ** 2  # Quadratic function
        return x, y
    
    def update_graph(self):
        """
        Emits a signal when graph data changes.
        """
        self.data_changed.emit()


class GraphWidget(pg.PlotWidget):
    """
    Displays the graph based on computed data from GraphCalculator.
    """
    def __init__(self, calculator):
        super().__init__()
        self.calculator = calculator
        self.setTitle("Quadratic Equation: y = ax^2 + bx + c")
        self.setLabel('left', 'y')
        self.setLabel('bottom', 'x')

        # Connect calculator's data_changed signal to refresh_graph
        self.calculator.data_changed.connect(self.refresh_graph)
        
        # Initial graph display
        self.refresh_graph()

    def refresh_graph(self):
        """
        Updates the graph display with the latest computed data.
        """
        x, y = self.calculator.compute_graph_data()
        self.clear()  # Clear previous plot
        self.plot(x, y)
  
########################################################################
#################################################################################
#Gidget types
#################################################################################
################################################################
#Sliders
################################

#NSlidersWidget####################################################################

"""
Class for pack of n vertical sliders
"""
class NSlidersWidget(QWidget):
    def __init__(self, n, min_value, max_value, colour):
        super().__init__()
        
        #creates list of n wrapped sliders
        self.list_of_sliders=[]
        for x in range(n):
            slider=SliderWithTicks(min_value, max_value, colour)
            self.list_of_sliders.append(slider)
        

        """
        To delete
        # Creates the label for the added value of the slidersand conects lthe sliders to the value
        """
        self.value_label_total = QLabel(f"Total: {self.calculate_total()}")
        for slider in self.list_of_sliders:
            slider.valueChanged().connect(self.update_labels)
        
        
        #Layouts
        main_layout=QHBoxLayout()
        for s in self.list_of_sliders:
            main_layout.addWidget(s)
        #main_layout.addWidget(self.value_label_total)
        
        main_layout.setContentsMargins(20, 40, 20, 20)  # Add top, left, right, and bottom margins
            
        self.setLayout(main_layout)
        
    """
    To delete. Calculates the sum of all slider values.
    """
    def calculate_total(self):
        return sum(slider.get_value() for slider in self.list_of_sliders)


    def update_labels(self):
        """
        Updates the total value label to reflect the current slider values.
        """
        total = self.calculate_total()
        self.value_label_total.setText(f"Total: {total}")              

#######################################
#Files
######################################
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
        file, _ = QFileDialog.getSaveFileName(parent, "Create New CSV File", os.getcwd(), "CSV Files (*.csv);;All Files (*)")
        
        if file:  # If a file path is selected
            # Ensure the file has a .csv extension
            if not file.lower().endswith(".csv"):
                file += ".csv"

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
        file, _ = QFileDialog.getOpenFileName(parent, "Select Output File", os.getcwd(), "CSV Files (*.csv);;All Files (*)")
    
        if file:  # If a file is selected
            # Validate the file
            try:
                if FileSelector.validate(file):  # Pass the selected file, not self.output_file
                    parent.file_label.setText(file)
                    parent.output_file = file  # Store the selected file path
    
            except ValueError as e:
                # Use the ErrorWindow class to show an error message if the file is invalid
                ErrorWindow.show_error_message(str(e))
        else:
            parent.file_label.setText("No file selected")

    @staticmethod
    def validate(file_path):
        if not file_path.lower().endswith(".csv"):
            raise ValueError("The selected file is not a valid CSV file.")
        return True


class OutputFileWidget(QWidget):
    """
    Class for selecting files and displaying the selected file.
    """
    def __init__(self):
        super().__init__()

        self.output_file = None

        # Create button for selecting a file
        self.select_button = QPushButton("Select .csv File")
        # Connect button's clicked signal to open_file_dialog without invoking it immediately
        self.select_button.clicked.connect(lambda: FileSelector.open_file_dialog(self))

        # Create button for creating a file
        self.newfile_button = QPushButton("New .csv File")
        self.newfile_button.clicked.connect(lambda: FileSelector.create_new_file(self))

        #####################
        ## Appearance stuff
        #################

        # Label to display the selected file
        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Horizontal layout for button and label
        file_names_layout = QHBoxLayout()
        file_names_layout.addWidget(self.select_button)
        file_names_layout.addWidget(self.file_label)
        file_names_layout.addWidget(self.newfile_button)
        file_names_layout.setContentsMargins(5, 5, 5, 5)
        file_names_layout.setSpacing(10)

        # Set the layout of the widget
        self.setLayout(file_names_layout)



class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        ##################
        # Files
        ####################
        self.patatito = "pattito"  # Variable to write to file

        self.output_file_widget = OutputFileWidget()

        ##################
        # Sliders
        ####################
        # Slider widgets
        frequency = l_inf = NSlidersWidget(1, 0, 100, "orange")
        l_inf = NSlidersWidget(1, 0, 100, "black")
        r_inf = NSlidersWidget(1, 0, 100, "black")
        r_h = NSlidersWidget(3, 0, 100, "red")
        r_m = NSlidersWidget(3, 0, 100, "green")
        r_l = NSlidersWidget(3, 0, 100, "blue")
        r_extra = NSlidersWidget(4, 0, 100, "black")

        # Horizontal layout for sliders
        self.list_of_sliders = [frequency, l_inf, r_inf,
                                r_h, r_m, r_l, r_extra]
        sliders_layout = QHBoxLayout()
        for s in self.list_of_sliders:
            sliders_layout.addWidget(s)

        ##################
        # Graphs
        #################### 
        # Calculators
        self.calculator = GraphCalculator(r_extra)
        for slider in r_extra.list_of_sliders:
            slider.valueChanged().connect(self.calculator.update_graph)

        self.big_graph = GraphWidget(self.calculator)
        self.small_graph = GraphWidget(self.calculator)
        # Horizontal layout for graphs:
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.big_graph)
        graph_layout.addWidget(self.small_graph)

        ##################
        # Save Button
        ####################
        self.save_button = QPushButton("Save patatito")
        self.save_button.clicked.connect(self.save_to_file)

        ##################
        # Main Layout
        ####################
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.output_file_widget)
        main_layout.addLayout(graph_layout)
        main_layout.addLayout(sliders_layout)
        main_layout.addWidget(self.save_button)  # Add the save button

        self.setLayout(main_layout)

    def save_to_file(self):
        """
        Save the 'patatito' variable to the selected output file using FileWriter.
        """
        output_file = self.output_file_widget.output_file
        if output_file:
            FileWriter.write_to_file(output_file, self.patatito)  # Use FileWriter to handle the file writing
            self.show_successful_write_feedback()  # Show the feedback for successful writing
        else:
            ErrorWindow.show_error_message("No output file selected.")

    def show_successful_write_feedback(self):
        """
        Briefly changes the background color of the save button to a subdued green to indicate success.
        """
        # Set button background to a subdued green color
        original_color = self.save_button.styleSheet()  # Store the original style
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        
        # Reset the button's background after 200 milliseconds
        QTimer.singleShot(200, lambda: self.save_button.setStyleSheet(original_color))



    
# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWidget()
    
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    
