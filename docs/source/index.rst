.. rst-class:: homepage-hero

Universal & Agentic Probe Design Tool
=======================================

.. image:: https://img.shields.io/github/license/UFISH-Team/U-Probe
   :target: https://github.com/UFISH-Team/U-Probe/blob/main/LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/python-3.8+-blue
   :target: https://www.python.org/downloads/
   :alt: Python Version

**U-Probe** is a comprehensive, automated, and highly customizable Python-based framework for designing nucleic acid probes. It provides an end-to-end workflow tailored for various molecular biology applications, including *in situ* hybridization (e.g., FISH) and targeted sequencing.

By integrating advanced sequence analysis, thermodynamic evaluation, and off-target filtering, U-Probe ensures the generation of highly specific and efficient probe sets.

-------------------
Why Choose U-Probe?
-------------------

.. grid:: 1 2 2 2
    :gutter: 3

    .. grid-item-card:: 🚀 End-to-End Automation
        :class-card: border-2

        Seamlessly transition from target gene selection to final probe generation without manual intervention.

    .. grid-item-card:: ⚙️ Highly Customizable
        :class-card: border-2

        Define complex probe structures, target regions, and filtering criteria using intuitive YAML configurations.

    .. grid-item-card:: 🔬 Advanced Filtering
        :class-card: border-2

        Evaluate GC content, melting temperature (Tm), secondary structure (MFE), and genome-wide off-target potential.

    .. grid-item-card:: 💻 Flexible Interfaces
        :class-card: border-2

        Access U-Probe via an interactive Web UI, a robust Command-Line Interface (CLI), or a programmatic Python API.

-----------
Quick Start
-----------

Install U-Probe via pip:

.. code-block:: bash

   pip install uprobe

Launch the interactive Web UI to design probes visually:

.. code-block:: bash

   # Start in development mode (default)
   uprobe server --host 127.0.0.1 --port 8000

   # Start in production mode
   uprobe server --env production --host 0.0.0.0 --port 8000 --workers 4

Or execute a complete automated workflow via CLI:

.. code-block:: bash

   uprobe run -p protocol.yaml -g genomes.yaml -o ./results --threads 10

----------------------
Documentation Contents
----------------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   cli
   python_api
   workflow
   examples

.. toctree::
   :maxdepth: 1
   :caption: Reference
   :hidden:

   config_reference
   troubleshooting
   faq

.. toctree::
   :maxdepth: 1
   :caption: Development
   :hidden:

   contributing

.. grid:: 1 2 2 2
    :gutter: 3

    .. grid-item-card:: 📚 Getting Started
        :link: installation
        :link-type: doc

        Installation instructions, quickstart guide, and configuration basics.

    .. grid-item-card:: 🛠️ User Guide
        :link: cli
        :link-type: doc

        Detailed tutorials for CLI, Python API, and common design workflows.

    .. grid-item-card:: 📖 Configuration Reference
        :link: config_reference
        :link-type: doc

        Comprehensive documentation of U-Probe's YAML configuration parameters.

    .. grid-item-card:: 💡 Contributing
        :link: contributing
        :link-type: doc

        Guidelines for contributing to the U-Probe open-source project.

--------
Citation
--------

If you use U-Probe in your research, please cite:

.. code-block:: bibtex

    @software{uprobe2025,
      title={U-Probe: Universal Probe Design Tool},
      author={Zhang, Qian and Xu, Weize and Cai, Huaiyuan},
      year={2025},
      url={https://github.com/UFISH-Team/U-Probe},
      version={1.0.0}
    }
