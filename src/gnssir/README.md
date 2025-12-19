# GNSSIR C Library aimed at embedded platforms adding GNSS interferometry and Transmissiometry functionality

R. Rietbroek, 2025

The repository is co-developed as a subtree of [gnssr4water](https://github.com/ITC-Water-Resources/gnssr4water/tree/main).
Besides the code for building the libgnssir librarry the directory holds Cython wrapper code to build a c extension ofr gnssr4water 

Currently, the lz4 library is included for static linkage as the code depends on lzfile.h which the distribution packager not always install long with the lz4 library. It is expected that this can be removed in the future when the LZ4 File interface becomes more stable.

## Outlook
The idea is that  C code in the src directory will also be used for embedded projects (e.g. Arduino, Zephyr, esp-32's, etc.) 
