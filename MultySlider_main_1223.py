import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 
import pyqtgraph as pg
import numpy as np

#################################################################################
#Gidget types
#################################################################################

"""
Class contains a QWidget with a graduated slider with range min_value, max_value, and colour
"""
class SliderWithTicks(QWidget,):
    def __init__(self,min_value, max_value, colour):
        super().__init__()

        # Set up the slider
        self.s = QSlider(Qt.Vertical, self)
        self.s.setRange(min_value, max_value)  # Min and Max values
        self.s.setTickPosition(QSlider.TicksBothSides)  # Display ticks on both sides
        self.s.setTickInterval(round((max_value-min_value)/10))  # Set interval for ticks
        
        #customize slider appeareance
        self.s.setStyleSheet(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }}
        """)

        # Set up the label
        self.value_label = QLabel(f"Slider: {self.s.value()}", self)

        # Layout for slider and label
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.s)
        self.layout.addWidget(self.value_label)
        self.setLayout(self.layout)

        # Connect slider to label update
        self.s.valueChanged.connect(self.update_label)
        
        
    def get_value(self):
        """
        Returns the current value of the slider.
        """
        return self.s.value()
    
    def valueChanged(self):
        """
        Exposes the slider's valueChanged signal for external use.
        """
        return self.s.valueChanged

    def update_label(self):
        """
        Update the label when slider value changes.
        """
        self.value_label.setText(f"Slider: {self.s.value()}")
    
    def paintEvent(self, event):
        """
        Custom painting for drawing tick labels.
        """
        super().paintEvent(event)
    
        # Create a painter object to draw on the widget
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 6))  # Set font for tick labels
        painter.setPen(QColor(0, 0, 0))  # Set text color to black
    
        # Get slider range
        min_value = self.s.minimum()
        max_value = self.s.maximum()
    
        # Get tick interval
        tick_interval = self.s.tickInterval()
    
        # Get the height of the slider widget
        height = self.s.height()
    
        # Add top offset to account for padding
        top_offset = 5  # Adjust this value based on observed misalignment
        bottom_offset = 5  # Adjust this as well if needed
    
        # Calculate effective height, excluding offsets
        effective_height = height - top_offset - bottom_offset
    
        # Iterate over the range and draw numbers
        for i in range(min_value, max_value + 1, tick_interval):
            # Adjust the vertical position to account for offsets
            tick_pos = (
                height - bottom_offset - (effective_height * (i - min_value)) // (max_value - min_value)
            )
    
            # Draw the number as text next to the tick mark
            text_rect = QRect(30, tick_pos, 50, 20)  # Position text to the right
            painter.drawText(text_rect, Qt.AlignCenter, str(i))
            
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
        
#############################################################################        
#Graphs Stuff
#############################################################################        

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
                


###########################
#Main
#####################################

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        ##################
        #filers
        ####################
        # Create some example file names for display
        file_names = ["file1.txt", "file2.csv", "file3.png"]
        # Horizontal layout for file names
        file_names_layout = QHBoxLayout()
        for file_name in file_names:
            file_label = QLabel(file_name)
            file_names_layout.addWidget(file_label)
            
        ##################
        #sliders
        ####################
        #slider wedgets
        l_inf=NSlidersWidget(1,0,100, "black")
        r_inf=NSlidersWidget(1,0,100, "black")
        r_h=NSlidersWidget(3,0,100, "red")
        r_m=NSlidersWidget(3,0,100, "green")
        r_l=NSlidersWidget(3,0,100, "blue")
        r_extra =NSlidersWidget(4,0,100, "black")
        
        #Horizontal layout for sliders
        self.list_of_sliders=[l_inf, r_inf,
                         r_h, r_m, r_l, r_extra
                         ]        
        sliders_layout=QHBoxLayout()
        for s in self.list_of_sliders:
            sliders_layout.addWidget(s)
        
        ##################
        #graphs
        #################### 
        
        #Calculators
        self.calculator = GraphCalculator(r_extra)
        for slider in r_extra.list_of_sliders:
            slider.valueChanged().connect(self.calculator.update_graph)

        self.big_graph=GraphWidget(self.calculator)
        self.small_graph=GraphWidget(self.calculator)
        #Horizontal layout for graphs:
        graph_layout=QHBoxLayout()
        graph_layout.addWidget(self.big_graph)
        graph_layout.addWidget(self.small_graph)
        
        
        ##################
        #main layout
        ####################
        main_layout=QVBoxLayout()
        main_layout.addLayout(file_names_layout)
        main_layout.addLayout(graph_layout)
        main_layout.addLayout(sliders_layout)
 
        self.setLayout(main_layout)


    
# Main code to start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWidget()
    
    
    window.setWindowTitle("Slider with Ticks and Labels")
    window.setGeometry(100, 100, 800, 900)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
    
