import os
from utils.importer import *
files = [file for file in os.listdir('data') if (file.split(".",1)[1] == "hspy" and (file.split(".",1)[0]+".5nc")not in os.listdir("converted"))]
print(files)
for file in files:
    filename = "data/"+file
    output = "converted/"+file.split(".",1)[0]
    read(filename,output)
    print("converted: "+filename+ " to " +output +".5nc")

# TODO UPGRADE
