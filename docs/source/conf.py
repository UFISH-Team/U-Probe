# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

# -- Project information -----------------------------------------------------
project = "U-Probe"
author = "Qian Zhang"
copyright = "2025-2026, Qian Zhang"

try:
    from uprobe import __version__
    version = __version__
    release = __version__
except ImportError:
    version = "1.0.0"
    release = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_click",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": None,
    ".md": "myst_parser",
}

master_doc = "index"
pygments_style = "default"

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_title = project
html_short_title = project

# Add any paths that contain custom static files (such as style sheets) here
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Logo and Favicon
html_favicon = "_static/logo.svg"

# Furo Theme Options
html_theme_options = {
    "source_repository": "https://github.com/UFISH-Team/U-Probe",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "sidebar_hide_name": True,
    "top_of_page_button": "edit",
    "light_logo": "logo.svg",
    "dark_logo": "logo.svg",
}

htmlhelp_basename = "UProbedoc"

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
}

intersphinx_timeout = 5

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Copy button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
