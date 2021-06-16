import matlab.engine
eng = matlab.engine.start_matlab()
x = 4.0
eng.workspace['y'] = x
a = eng.eval('sqrt(y)')
print(a)
'''
Some sample matlab code taken from their website
Placeholder for actual code
Currently demonstrates matlab engine functionality
'''