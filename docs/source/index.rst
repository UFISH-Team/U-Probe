🧬 U-Probe: Universal Probe Design Tool
=======================================

.. image:: https://img.shields.io/github/license/UFISH-Team/U-Probe
   :target: https://github.com/UFISH-Team/U-Probe/blob/main/LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/python-3.8+-blue
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://readthedocs.org/projects/uprobe/badge/?version=latest
   :target: https://uprobe.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

**U-Probe** is a powerful and flexible Python-based tool for designing custom DNA or RNA probes for various molecular biology applications, such as *in situ* hybridization and targeted sequencing. It provides a comprehensive workflow from target gene selection to final probe generation, with a focus on automation, customization, and ease of use.

.. note::
   U-Probe is developed by the UFISH Team and is actively maintained. For the latest updates and source code, visit our `GitHub repository <https://github.com/UFISH-Team/U-Probe>`_.

Key Features
------------

✨ **End-to-end workflow**: Automates the entire probe design process, from sequence extraction to final filtering.

⚙️ **Highly customizable**: Use simple YAML configuration files to define target genes, probe structures, and filtering criteria.

🔍 **Advanced filtering**: Filter probes based on a wide range of attributes like GC content, melting temperature (Tm), and off-target potential.

🔌 **Extensible API**: In addition to a command-line interface, U-Probe offers a clean Python API for programmatic access and integration into other bioinformatics pipelines.

🗃️ **Built-in indexing**: Automatically handles the creation of genome indices for alignment tools like Bowtie2 and BLAST.

Quick Start
-----------

Install U-Probe with pip:

.. code-block:: bash

   pip install uprobe

Run a complete probe design workflow:

.. code-block:: bash

   uprobe run --protocol protocol.yaml --genomes genomes.yaml --output results/

For detailed installation instructions and usage examples, see the :doc:`installation` and :doc:`quickstart` guides.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   cli
   python_api
   workflows
   examples

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   api_reference
   config_reference
   troubleshooting
   faq

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   contributing

Getting Started
~~~~~~~~~~~~~~~

New to U-Probe? Start here:

* :doc:`installation` - Install U-Probe on your system
* :doc:`quickstart` - Get up and running in minutes
* :doc:`configuration` - Learn about configuration files

User Guide
~~~~~~~~~~

Learn how to use U-Probe effectively:

* :doc:`cli` - Command-line interface reference
* :doc:`python_api` - Python API guide
* :doc:`workflows` - Common workflows and best practices
* :doc:`examples` - Real-world examples and tutorials

Reference
~~~~~~~~~

Detailed reference documentation:

* :doc:`api_reference` - Complete API documentation
* :doc:`config_reference` - Configuration file reference
* :doc:`troubleshooting` - Common issues and solutions
* :doc:`faq` - Frequently asked questions

Community & Support
-------------------

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card:: 💬 GitHub Discussions
      :link: https://github.com/UFISH-Team/U-Probe/discussions

      Ask questions, share ideas, and get help from the community.

   .. grid-item-card:: 🐛 Bug Reports
      :link: https://github.com/UFISH-Team/U-Probe/issues

      Found a bug? Report it on GitHub Issues.

   .. grid-item-card:: 📖 Documentation
      :link: https://uprobe.readthedocs.io

      You're already here! Browse the complete documentation.

   .. grid-item-card:: 🚀 Contribute
      :link: contributing

      Help make U-Probe better for everyone.

License
-------

U-Probe is released under the MIT License. See the `LICENSE <https://github.com/UFISH-Team/U-Probe/blob/main/LICENSE>`_ file for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
