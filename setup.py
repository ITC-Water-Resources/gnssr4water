# setup.py  
# This file is part of gnssr4water.
# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2022
# Author Lubin Roineau (lubin.roineau@ensg.eu), 2022
import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="gnssr4water",
    author="Roelof Rietbroek",
    author_email="r.rietbroek@utwente.nl",
    version="1.0",
    description="Python library to help perform gnss reflectometry for water applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ITC-Water-Resources/gnssr4water",
    packages=find_packages("."),
    package_dir={"":"."},
    install_requires=['numpy','math','pandas','shapely','matplotlib','astropy','os','geopandas','unlzw3','pathlib','GDAL','Shapely','io','cartopy','urllib'],
    classifiers=["Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
        "Development Status :: Beta"]
    
)
