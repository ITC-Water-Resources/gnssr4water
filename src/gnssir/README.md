# GNSSRLIB extension

This directory holds Cython wrapper code and c extension code (in src), to speed up computation.

Currently, the lz4 library is included for static linkage as the code depends on lzfile.h which the distribution packager not always install long with the lz4 library. It is expected that this can be removed in the future when the LZ4 File interface becomes more stable.

## Outlook
The idea is that  C code in the src directory may also be used for embedded processing (e.g. Arduino, Zephyr,etc.) 
