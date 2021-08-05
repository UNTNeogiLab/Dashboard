## Instruments documentation

This repository will include several instruments_[instrument] files  
The files are dynamically loaded and the gui.py renders a GUI and runs the expirement  
I am implementing the support for generic expirements with different dimensions  
You must specify several things in your class:

1. dimensions: array, the primary dimensions which you will write your dataset around
2. coords: dictionary of dictionary with each coordinate  
   1."name" - the name of the coordinate, string  
   2."unit" - unit, string  
   3."dimension" - the associated dimension, string  
   4."values" - array of values for the coordinate  
   5."function" - function to call for each increment of the coordinate, or "none"
3. cap_coords - coordinates to capture along, array
4. loop_coords - coordinates to loop around, array

You can also specify several optional variables

5. datasets - dasets to write to, array. Default is ["ds1"]
6. live - render a live view. Default is true
7. gather - allow user to gather data. Default is true
8. filename - default filename, recommended to use param
### Memory

The program will store the data then write to file every change of the first dimension

## GUI rendering

1. The GUI will display the non hidden parameters in the middle
2. It will call widgets() for an optional third panel
3. graph() will optional render a graph that is continually refreshed

## Gathering data:

Your program must have a function `get_frame()` which accepts an array of all current loop cords.  
EX: looping over x,y from 0,0 will give you [0,0] for the first frame It needs to return a dictionary with the keys
being the datasets and the values being data 