__**ZarcFit: Impedance Analysis of Rock Samples**__

A user-friendly tool for researchers to analyze and fit experimental impedance data of rock samples using theoretical electronic circuit models.

This is a Python reworking and update of the original ZarcFit program, which was developed in LabView by Dr. Enkin in 2014. The program remains under development to meet his specifications.

**Features**

-Implements two theoretical circuit models to represent rock sample impedance.
-Provides graphical visualization of experimental vs. modeled data.
-Supports interactive parameter adjustments through color-coded sliders.
-Uses a configuration file (config.ini) for easy parameter tuning.
-Written in Python, offering improved flexibility and maintainability over the original LabView version.

**Usage**

Understanding the Models

The theoretical foundation of the models can be found in the attached image (circuit_models.jpg), which displays the circuit representations used.
The green line in the graphs represents the experimental impedance data.
The blue curve represents the modeled impedance data.
Adjusting Parameters

The color-coded sliders allow tuning of impedance parameters:
Red, Green, and Blue sliders represent high, medium, and low-frequency Zarcs.
Black sliders adjust external circuit components such as electrode effects.
Configuration & Customization

The config.ini file enables quick access to adjustable parameters without modifying the code.
The hardcoded circuit models, as per Dr. Enkin’s request, are implemented in Calculator.py and are designed for easy readability.

**Running Program:**

Execute python Main.py

**Structure:**
ZarcFit/
|-- AuxiliaryClasses/       # All helper modules (imported in Main.py)

|   |-- ConfigImporter.py   # Handles configuration settings

|   |-- Calculator.py       # Implements circuit model calculations

|   |-- WidgetGraphs.py     # Graph visualization (Impedance, Bode, etc.)

|   |-- WidgetSliders.py    # UI sliders for parameter adjustments

|   |-- WidgetInputFile.py  # File input handling

|   |-- WidgetOutputFile.py # CSV output management

|   |-- ...

|-- Main.py                 # Main execution script

|-- config.ini              # Configuration file for adjustable parameters

|-- README.md               # This documentation file





