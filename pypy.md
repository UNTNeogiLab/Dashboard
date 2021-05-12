Ok you like the speedups of numba and you want the program to be even faster.
Or maybe you're me. Here are the implementation notes for installing pypy for this program:  
1. Pipenv  
you need to run `pipenv --rm` then  `pipenv --python /usr/bin/pypy3` to install pypy3
2. Dependencies  
    You need several dependencies that won't work.  
   1. [llvmlite](https://github.com/numba/llvmlite/issues/525)  
    `LLVM_CONFIG=/path/to/llvm-config CXXFLAGS=-fPIC pip3 install llvmlite`
   2. numba and netcdf4  
    I don't know how to do these 
            
Therefore current pypy status is BROKEN   