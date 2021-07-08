##Instruments documentation 
This repository will include several instruments_[instrument] files  
The files are dynamically loaded and the gui.py renders a GUI and runs the expirement  
I am implementing the support for generic expirements with different dimensions  
You must specify several things in your program:

1. dimensions: array, the primary dimensions which you will write your dataset around  
2. coords: dictionary of dictionary with each coordinate  
    1."name" - the name of the coordinate, string  
    2."unit" - unit, string  
    3."dimension" - the associated dimension, string  
    4."values" - array of values for the coordinate  
    5."function" - function to call for each increment of the coordinate, or "none"
3. cap_coords - coordinates to capture along, array
4. loop_coords - coordinates to loop around, array 
###Memory 
The program will store the data then write to file every change of the first dimension
