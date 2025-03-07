# This file is part of the shxarray software which is licensed
# under the Apache License version 2.0 (see the LICENSE file in the main repository)
# Copyright Roelof Rietbroek (r.rietbroek@utwente.nl), 2023
#




from setuptools import setup,Extension
from setuptools_scm import get_version
from Cython.Build import cythonize
import Cython.Compiler.Options
import os 
import numpy as np
import sys



debug=True
usegzip=True
uselz4=False

extra_args=[]
if debug:
    extra_args.append("-g")
    extra_args.append("-O0")

if usegzip:
    extra_args.append("-DUSE_GZIP")
    extra_args.append("-lz")

if uselz4:
    extra_args.append("-DUSE_LZ4")



#don't necessarily cythonize on the fly
if "USE_CYTHON" in os.environ:
    useCython=True
    ext=".pyx"
    Cython.Compiler.Options.annotate = True
else:
    useCython=False
    ext=".c"

def listexts():
    nm="gnssrlib_wrap"
    exts=[]
    srcd="src/gnssrlib"
    sources=[f"{srcd}/{nm+ext}"]
    for csrc in ["nmea.c","stream.c","gnssrlib.c"]:
        sources.append(f"{srcd}/src/{csrc}")
    
    if uselz4:
        for csrc in ["lz4stream.c","lz4static/lz4file.c","lz4static/lz4.c","lz4static/lz4hc.c","lz4static/xxhash.c","lz4static/lz4frame.c"]:
            sources.append(f"{srcd}/src/{csrc}")

    exts.append(Extension(f"gnssr4water.gnssrlib",sources,include_dirs=[np.get_include(),"."], define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],extra_compile_args=extra_args,extra_link_args=extra_args))
    return exts

extensions=listexts()


if useCython:
    #additionally cythonize pyx files before building
    extensions=cythonize(extensions,language_level=3,annotate=True,gdb_debug=debug)

setup(
    version = get_version(root='.', relative_to=__file__),
    ext_modules=extensions
    )
