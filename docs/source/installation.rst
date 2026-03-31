==================
Installation Guide
==================

U-Probe is designed to be easily installed and integrated into your bioinformatics environment. We recommend using a virtual environment (such as `conda` or `venv`) to manage dependencies.

Requirements
------------

Before installing U-Probe, ensure your system meets the following prerequisites:

* **Python**: Version 3.9 or higher (3.11 recommended)
* **Operating System**: Linux, macOS, or Windows (WSL recommended for Windows)
* **Memory**: Minimum 4GB RAM (8GB+ recommended for large genome processing)

-------------------
System Dependencies
-------------------

U-Probe relies on several external bioinformatics tools for sequence alignment and k-mer analysis. Please ensure these are installed and accessible in your system's ``PATH``.

* **Bowtie2**: For rapid sequence alignment and off-target screening.
* **BLAST+**: For sequence similarity searches.
* **Jellyfish** *(Optional)*: For fast k-mer counting.

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install bowtie2 ncbi-blast+ jellyfish

**macOS (via Homebrew):**

.. code-block:: bash

   brew install bowtie2 blast jellyfish

--------------------
Installation Methods
--------------------

Method 1: Install via pip (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most straightforward method to install U-Probe is via the Python Package Index (PyPI):

.. code-block:: bash

   pip install uprobe

Method 2: Install from Source (Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to use the latest development version or contribute to the project, you can install U-Probe directly from the GitHub repository:

.. code-block:: bash

   git clone https://github.com/UFISH-Team/U-Probe.git
   cd U-Probe
   pip install -e .

Method 3: Conda Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a clean and isolated bioinformatics environment, we provide an ``environments.yaml`` file:

.. code-block:: bash

   git clone https://github.com/UFISH-Team/U-Probe.git
   cd U-Probe
   conda env create -f environments.yaml
   conda activate uprobe
   pip install .

----------------------
Verifying Installation
----------------------

To confirm that U-Probe has been successfully installed, run the following command in your terminal:

.. code-block:: bash

   uprobe --help

You should see the U-Probe command-line interface (CLI) help menu, detailing available commands such as ``run``, ``server``, and ``build-index``.

----------
Next Steps
----------

* Proceed to the :doc:`quickstart` guide to design your first probe.
* Learn how to configure your design parameters in the :doc:`configuration` section.
