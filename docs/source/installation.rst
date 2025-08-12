Installation Guide
==================

U-Probe can be installed in multiple ways depending on your needs. This guide covers all installation methods from basic pip installation to creating standalone executables.

Requirements
------------

Before installing U-Probe, ensure you have:

- **Python 3.9+** (Python 3.11 recommended)
- **Operating System**: Linux, macOS, or Windows
- **Memory**: At least 4GB RAM (8GB+ recommended for large genomes)
- **Storage**: Sufficient space for genome files and indices

System Dependencies
~~~~~~~~~~~~~~~~~~~

U-Probe requires several bioinformatics tools to be installed on your system:

**Required Tools:**

- `Bowtie2 <http://bowtie-bio.sourceforge.net/bowtie2/index.shtml>`_ - For sequence alignment
- `BLAST+ <https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=Download>`_ - For sequence similarity searches

**Installing on Ubuntu/Debian:**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install bowtie2 ncbi-blast+

**Installing on macOS:**

.. code-block:: bash

   brew install bowtie2 blast

**Installing on Windows:**

Download and install the tools manually from their respective websites, or use Windows Subsystem for Linux (WSL).

Installation Methods
--------------------

Method 1: Install from PyPI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to install U-Probe is using pip:

.. code-block:: bash

   pip install uprobe

This installs U-Probe and its Python dependencies. After installation, you can use the ``uprobe`` command directly.

Method 2: Install from Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the latest development version or to contribute to U-Probe:

.. code-block:: bash

   git clone https://github.com/UFISH-Team/U-Probe.git
   cd u-probe
   pip install .

Method 3: Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you plan to modify U-Probe or contribute to development:

.. code-block:: bash

   git clone https://github.com/UFISH-Team/U-Probe.git
   cd u-probe
   pip install -e .

This creates an editable installation where changes to the source code are immediately reflected.

Method 4: Conda Environment (Recommended for Bioinformatics)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a complete bioinformatics environment:

.. code-block:: bash

   git clone https://github.com/UFISH-Team/U-Probe.git
   cd u-probe
   conda env create -f environments.yaml
   conda activate uprobe
   pip install .

Verifying Installation
----------------------

After installation, verify U-Probe is working correctly:

.. code-block:: bash

   # Check version
   uprobe version

   # View help
   uprobe --help

   # Test with a simple command
   uprobe validate-targets --help

You should see the U-Probe version and help information without errors.

Creating Standalone Executables
--------------------------------

For deployment on systems without Python, you can create standalone executables:

Prerequisites
~~~~~~~~~~~~~

.. code-block:: bash

   pip install pyinstaller

Build Process
~~~~~~~~~~~~~

.. code-block:: bash

   # Basic build
   pyinstaller --onefile --name uprobe \
     --hidden-import uprobe \
     --hidden-import uprobe.api \
     --hidden-import uprobe.cli \
     --hidden-import click \
     --collect-all uprobe \
     uprobe/__main__.py

   # The executable will be created in dist/uprobe

Advanced Build with Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a build script for reproducible builds:

.. code-block:: bash

   #!/bin/bash
   echo "Building U-Probe standalone executable..."
   
   # Install dependencies
   pip install -r requirements.txt
   pip install pyinstaller
   
   # Clean previous builds
   rm -rf build dist uprobe.spec
   
   # Build executable
   pyinstaller --onefile --name uprobe \
     --hidden-import uprobe \
     --hidden-import uprobe.api \
     --hidden-import uprobe.cli \
     --hidden-import click \
     --collect-all uprobe \
     uprobe/__main__.py
   
   echo "✅ Build complete! Executable available in dist/uprobe"
   echo "File size: $(du -h dist/uprobe | cut -f1)"

Save this as ``build.sh``, make it executable (``chmod +x build.sh``), and run it.

Docker Installation
-------------------

For containerized deployment:

.. code-block:: dockerfile

   FROM python:3.11-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       bowtie2 \
       ncbi-blast+ \
       && rm -rf /var/lib/apt/lists/*

   # Install U-Probe
   COPY . /app
   WORKDIR /app
   RUN pip install .

   # Set entrypoint
   ENTRYPOINT ["uprobe"]

Build and run:

.. code-block:: bash

   docker build -t uprobe .
   docker run -v $(pwd)/data:/data uprobe --help

Troubleshooting Installation
----------------------------

Common Issues
~~~~~~~~~~~~~

**Import Error: No module named 'uprobe'**

Solution: Ensure you're in the correct environment and U-Probe is properly installed:

.. code-block:: bash

   pip list | grep uprobe
   python -c "import uprobe; print(uprobe.__version__)"

**Command not found: uprobe**

Solution: Check if the installation directory is in your PATH:

.. code-block:: bash

   # Find where uprobe is installed
   which uprobe
   
   # If not found, try with python -m
   python -m uprobe --help

**Missing system dependencies**

Solution: Install Bowtie2 and BLAST+ as described in the System Dependencies section.

**Permission denied errors**

Solution: Use ``--user`` flag for pip or use a virtual environment:

.. code-block:: bash

   pip install --user uprobe

Virtual Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~~~

Using virtualenv:

.. code-block:: bash

   python -m venv uprobe_env
   source uprobe_env/bin/activate  # On Windows: uprobe_env\Scripts\activate
   pip install uprobe

Using conda:

.. code-block:: bash

   conda create -n uprobe python=3.8
   conda activate uprobe
   pip install uprobe

Next Steps
----------

After successful installation:

1. Read the :doc:`quickstart` guide for your first probe design
2. Review the :doc:`configuration` guide to understand config files
3. Explore the :doc:`cli` reference for all available commands

.. note::
   If you encounter any issues during installation, please check our :doc:`troubleshooting` guide or open an issue on `GitHub <https://github.com/UFISH-Team/U-Probe/issues>`_.
