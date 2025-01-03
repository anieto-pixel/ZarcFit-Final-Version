# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 09:28:03 2024

@author: agarcian
"""

import sys
from PyQt5.QtWidgets import *

#my own classes
from SubclassesSliderWithTicks import *
from OutputFileWidget import OutputFileWidget

class ButtonsWidgetRow(QWidget):
    def __init__(self):
        super().__init__()
    
        #save buttons(eventually buttons, or sets of themed buttons, will have their class)
        self.f1_button = QPushButton("F1")
        self.f2_button = QPushButton("F2")
        self.f3_button = QPushButton("F3")
        self.save_button = QPushButton("Save plot")
        self.f5_button = QPushButton("F5")
        self.f6_button = QPushButton("F6")
        self.f7_button = QPushButton("F7")
        self.f8_button = QPushButton("F8")
        self.f9_button = QPushButton("F9")
        
        self.list_of_buttons=[self.f1_button, self.f2_button, self.f3_button,
                         self.save_button,self.f5_button,self.f6_button,
                         self.f7_button,self.f8_button,self.f9_button,
                         ]
        buttons_column_layout= QVBoxLayout()
        for b in self.list_of_buttons:
            buttons_column_layout.addWidget(b)
            
            
        #buttons_column_layout.setSpacing(5) 

        # Set the layout of the widget
        self.setLayout(buttons_column_layout)
        self.setMaximumWidth(150)
        self.setMinimumSize(90,35*len(self.list_of_buttons))# width, hight
        
        
if __name__ == "__main__":

    # Manual test method
    def test_buttons_widget_row():
        app = QApplication(sys.argv)
        
        # Create and show the ButtonsWidgetRow
        widget = ButtonsWidgetRow()
        
        min_size = widget.save_button.minimumSize()  # Returns a QSize object
        min_width, min_height = min_size.width(), min_size.height()
        print(f"Minimum size: {min_width}px x {min_height}px")
        
        
        widget.setWindowTitle("Test ButtonsWidgetRow")
        widget.show()
        
        # Run the application event loop
        sys.exit(app.exec_())

    # Run the test
    test_buttons_widget_row()