import os
import sys

# Point Sphinx at the src layout so autodoc can import pudu
sys.path.insert(0, os.path.abspath('../src'))

# ---------------------------------------------------------------------------
# Project info
# ---------------------------------------------------------------------------
project = 'PUDU'
copyright = '2024, Gonzalo Vidal, Oscar Rodriguez'
author = 'Gonzalo Vidal, Oscar Rodriguez'
release = '1.0.0b9'

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Pull docstrings from source
    'sphinx.ext.napoleon',     # Support Google-style docstrings (Args:, Returns:, etc.)
    'sphinx.ext.viewcode',     # Add [source] links next to every API entry
    'sphinx.ext.intersphinx',  # Cross-reference Python standard library docs
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# ---------------------------------------------------------------------------
# autodoc settings
# ---------------------------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': False,   # Hide members with no docstring
    'show-inheritance': True,
    'member-order': 'bysource',  # Preserve definition order, not alphabetical
}
autodoc_typehints = 'description'  # Show type hints in the parameter descriptions

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True   # Include __init__ docstring in class page
napoleon_use_param = True
napoleon_use_rtype = True

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 3,
    'titles_only': False,
}

html_static_path = ['_static']

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
