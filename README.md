# ScanningMWIRCamera
Python based software for controlling and displaying output of the MWIR scanning camera built for my undergraduate Engineering Part IIB Project.

It interfaces with a Melles Griot Nanostep Master Control Unit to control sensor position using NI-VISA via pyvisa.

A Velleman P8055 board is used to provide an ADC input. A 32bit C++ program which implements the provided DLL for controlling the board is used and this is called by the Python code.

The main user interface is a GUI built using PyQt5 which should provide all required features.
