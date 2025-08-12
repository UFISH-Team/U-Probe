# U-Probe Documentation

This directory contains the source files for U-Probe's documentation, built with [Sphinx](https://www.sphinx-doc.org/) and hosted on [Read the Docs](https://readthedocs.org/).

## 📖 Online Documentation

The latest documentation is available at: **https://uprobe.readthedocs.io/**

## 🏗️ Building Documentation Locally

### Prerequisites

Install documentation dependencies:

```bash
# From the project root
pip install -e ".[docs]"

# Or install requirements directly
pip install -r docs/requirements.txt
```

### Quick Build

```bash
cd docs/
chmod +x build_docs.sh
./build_docs.sh
```

This will build the HTML documentation and place it in `build/html/`. Open `build/html/index.html` in your browser.

### Manual Build

```bash
cd docs/
sphinx-build -b html source build/html
```

### Clean Build

```bash
./build_docs.sh clean
```

### Build PDF (Optional)

Requires LaTeX installation:

```bash
./build_docs.sh pdf
```

## 📁 Documentation Structure

```
docs/
├── source/                    # Source files
│   ├── conf.py               # Sphinx configuration
│   ├── index.rst             # Main documentation page
│   ├── installation.rst      # Installation guide
│   ├── quickstart.rst        # Quick start tutorial
│   ├── configuration.rst     # Configuration file guide
│   ├── cli.rst              # CLI reference
│   ├── python_api.rst       # Python API guide
│   ├── workflows.rst        # Common workflows
│   ├── examples.rst         # Examples and tutorials
│   ├── api_reference.rst    # Complete API reference
│   ├── config_reference.rst # Configuration reference
│   ├── troubleshooting.rst  # Troubleshooting guide
│   ├── faq.rst              # Frequently asked questions
│   ├── contributing.rst     # Contributing guide
│   ├── changelog.rst        # Version history
│   ├── _static/             # Static files (CSS, images, etc.)
│   └── _templates/          # Custom templates
├── build/                   # Generated documentation
├── requirements.txt         # Documentation dependencies
├── build_docs.sh           # Build script
└── README.md               # This file
```

## ✍️ Contributing to Documentation

### Adding New Pages

1. Create a new `.rst` file in `source/`
2. Add it to the appropriate `toctree` in `index.rst` or related pages
3. Follow the existing style and structure

### Writing Style Guide

- Use clear, concise language
- Include code examples for technical concepts
- Add cross-references using `:doc:` and `:ref:`
- Use appropriate reStructuredText formatting

### reStructuredText Primer

```rst
Page Title
==========

Section
-------

Subsection
~~~~~~~~~~

**Bold text**
*Italic text*
``Code text``

.. code-block:: python

   # Code blocks
   def example():
       return "Hello, World!"

.. note::
   This is a note admonition.

.. warning::
   This is a warning admonition.
```

### Testing Changes

Always test your documentation changes locally:

```bash
./build_docs.sh clean
```

Check for:
- Proper rendering of new content
- Working cross-references
- No build warnings or errors
- Mobile-friendly layout

## 🔧 Configuration

### Sphinx Configuration (`source/conf.py`)

Key settings:
- **Theme**: `sphinx_rtd_theme` for consistent ReadTheDocs appearance
- **Extensions**: Includes autodoc, Napoleon, MyST parser, and more
- **Cross-references**: Links to external documentation (pandas, numpy, etc.)

### ReadTheDocs Configuration (`.readthedocs.yaml`)

- Python 3.11 build environment
- Automatic dependency installation
- PDF and EPUB export enabled
- Integration with GitHub webhooks for automatic updates

## 📚 Documentation Sections

### Getting Started
- **Installation**: Complete setup guide with multiple methods
- **Quick Start**: Step-by-step first probe design
- **Configuration**: Detailed guide to YAML config files

### User Guide
- **CLI**: Complete command-line reference
- **Python API**: Programmatic usage guide
- **Workflows**: Common use cases and best practices
- **Examples**: Real-world examples with full configurations

### Reference
- **API Reference**: Auto-generated from docstrings
- **Configuration Reference**: Complete config file documentation
- **Troubleshooting**: Solutions to common problems
- **FAQ**: Frequently asked questions

### Development
- **Contributing**: How to contribute to the project
- **Changelog**: Version history and release notes

## 🌐 ReadTheDocs Integration

### Automatic Builds

Documentation is automatically built and deployed when:
- Changes are pushed to the main branch
- Pull requests are created (preview builds)
- New tags/releases are created

### Manual Builds

To trigger a manual build:
1. Go to the ReadTheDocs project page
2. Click "Build Version"
3. Select the branch/tag to build

### Preview Builds

Pull requests automatically get preview documentation builds. Look for the ReadTheDocs bot comment with a preview link.

## 🐛 Troubleshooting

### Common Build Issues

**"No module named 'uprobe'"**
```bash
# Install U-Probe in development mode
pip install -e .
```

**"Theme not found"**
```bash
# Install theme
pip install sphinx_rtd_theme
```

**"Extension not found"**
```bash
# Install missing extension
pip install myst-parser sphinx-copybutton
```

### Build Warnings

- **Undefined references**: Check that all `:doc:` and `:ref:` targets exist
- **Missing docstrings**: Add docstrings to functions/classes in the code
- **Orphaned documents**: Ensure all `.rst` files are included in a `toctree`

### Performance Issues

For faster local builds during development:
```bash
# Build only changed files
sphinx-build -b html source build/html

# Or use the built-in auto-build
sphinx-autobuild source build/html
```

## 📞 Getting Help

- **Documentation issues**: Open an issue on GitHub
- **Build problems**: Check the troubleshooting section above
- **Content suggestions**: Use GitHub Discussions
- **Style questions**: Follow existing patterns in the documentation

## 📈 Analytics

ReadTheDocs provides analytics for:
- Page views and popular content
- Search queries
- Geographic distribution
- Referrer information

Access analytics through the ReadTheDocs dashboard.

---

For more information about Sphinx and ReadTheDocs:
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [ReadTheDocs User Guide](https://docs.readthedocs.io/)
- [reStructuredText Guide](https://docutils.sourceforge.io/rst.html)
