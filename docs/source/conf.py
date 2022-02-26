# type: ignore
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))
print("docs conf sys path: \n", sys.path)
print("cwd: ", os.path.abspath(os.path.curdir))


# -- Project information -----------------------------------------------------

project = 'anacreonlib'
author = 'Ritik Mishra'

# The full version, including alpha/beta/rc tags
_version_file_path = Path(__file__)/'..'/'..'/'..'/'VERSION'
with open(_version_file_path.resolve(), "r") as f:
    release = f.read()


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.doctest'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Intersphinx configuration allows us to link to other libraries, like the 
# Python standard library
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# Tells sphinx autodoc to use both the class docstring and the __init__ 
# docstring
autoclass_content = "both"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_theme_options = {
    # "body_max_width": 'none'
}
html_show_copyright = False
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']