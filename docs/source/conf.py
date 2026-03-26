# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import datetime
import os
import subprocess

project = 'gnssr4water'
copyright = str(datetime.now().year)+', Roelof Rietbroek'
author = 'Roelof Rietbroek'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['nbsphinx', 'sphinxcontrib.apidoc', 'sphinx.ext.autodoc','sphinx.ext.napoleon', 'sphinx.ext.todo', 'breathe']


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store','**.ipynb_checkpoints']


#figure out the actual installation directory
import gnssr4water
apidoc_module_dir=os.path.dirname(gnssr4water.__file__)

apidoc_output_dir = 'references'
apidoc_separate_modules = True
apidoc_module_first=True
apidoc_toc_file=False

napoleon_numpy_docstring = True

## breathe stuff
read_the_docs_build = os.environ.get('READTHEDOCS', None) == 'True'

if read_the_docs_build:
    #run doxygen on the gnssir code
    subprocess.call(f'cd {apidoc_module_dir}../gnssir/docs; doxygen', shell=True)

breathe_projects = {"gnssir": apidoc_module_dir+"/../gnssir/docs/doxyxml"}
breathe_default_project = "gnssir"




# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme='pydata_sphinx_theme'
html_static_path = ['_static']

html_favicon = '_static/favicon.ico'

html_theme_options = {
    "use_edit_page_button": False,
    "icon_links": [
        {
            # Label for this link
            "name": "GitHub",
            # URL where the link will redirect
            "url": "https://github.com/ITC-Water-Resources/gnssr4water",  # required
            # Icon class (if "type": "fontawesome"), or path to local image (if "type": "local")
            "icon": "fa-brands fa-github",
            # The type of image to be used (see below for details)
            "type": "fontawesome",
        }
   ],
   "logo": {
        "alt_text": "gnssrwater - Home",
        "image_light": "_static/gnssr4water_logo_wtxt_lightmode.png",
        "image_dark": "_static/gnssr4water_logo_wtxt_darkmode.png",
    }
}
