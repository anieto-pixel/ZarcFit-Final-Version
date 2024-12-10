# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 11:50:00 2024

@author: agarcian
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
     
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

        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.next_button)

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

if __name__ == "__main__":
    app = QApplication([])

    widget = InputFileWidget()
    widget.show()
    app.exec_()


