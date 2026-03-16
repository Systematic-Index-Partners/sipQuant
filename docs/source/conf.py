import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'sipQuant'
copyright = '2026, SIP Global — Systematic Index Partners'
author = 'SIP Global — Systematic Index Partners'
release = '1.0.0'
version = '1.0'

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': 4,
    'titles_only': False,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}
