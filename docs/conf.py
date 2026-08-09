"""Sphinx configuration for richpool's docs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import richpool  # noqa: E402

project = "richpool"
copyright = "2026, Sahil Jhawar"
author = "Sahil Jhawar"
version = richpool.__version__
release = richpool.__version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_exec_code",
    "sphinx_copybutton",
    "matplotlib.sphinxext.plot_directive",
]

root_doc = "index"
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "inherited-members": True,
    "show-inheritance": True,
}
autosummary_generate = True
napoleon_numpy_docstring = True
napoleon_google_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

plot_formats = ["png"]
plot_html_show_source_link = False
plot_html_show_formats = False

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_title = "richpool"

html_theme_options = {
    "github_url": "https://github.com/sahiljhawar/richpool",
    "use_edit_page_button": False,
    "navigation_with_keys": True,
    "show_toc_level": 2,
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
}

html_context = {
    "github_user": "sahiljhawar",
    "github_repo": "richpool",
    "github_version": "main",
    "doc_path": "docs",
}
