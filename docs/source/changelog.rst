Changelog
=========

All notable changes to U-Probe will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~
- Comprehensive Sphinx documentation with ReadTheDocs support
- Detailed examples for FISH, PCR, and multiplexed probe design
- Complete CLI interface with individual workflow steps
- Advanced filtering and quality control options

Changed
~~~~~~~
- Improved API documentation with detailed docstrings
- Enhanced error handling and user feedback

[1.0.0] - 2024-01-31
--------------------

Added
~~~~~

**Core Functionality**
- Complete probe design workflow from target selection to filtered results
- Support for multiple probe architectures (FISH, PCR, sequencing)
- YAML-based configuration system for flexible probe design
- Python API for programmatic access and pipeline integration

**Target Extraction**
- Extraction from exonic, gene, and genomic coordinate regions
- Configurable sequence length and overlap parameters
- Gene-specific extraction parameter overrides
- Support for multiple genome assemblies

**Probe Construction**
- Template-based probe design with configurable parts
- Expression system for sequence manipulation and barcode integration
- Nested template support for complex probe structures
- Reference system for cross-probe dependencies

**Quality Attributes**
- GC content calculation
- Melting temperature estimation  
- Self-complementarity analysis
- Secondary structure prediction
- Off-target mapping with Bowtie2 and BLAST
- K-mer abundance analysis with Jellyfish integration
- Sequence complexity scoring

**Filtering and Selection**
- Pandas-based filtering with complex boolean conditions
- Multi-attribute sorting (ascending/descending)
- Overlap removal based on genomic coordinates
- Customizable filter thresholds

**Command Line Interface**
- Complete workflow execution with single command
- Individual step execution for fine-grained control
- Comprehensive help system and parameter validation
- Verbose logging and progress tracking

**Python API**
- Object-oriented API design
- Step-by-step workflow control
- DataFrame-based result handling
- Error handling and validation

**External Tool Integration**
- Bowtie2 integration for fast sequence alignment
- BLAST+ support for similarity searches
- Jellyfish integration for k-mer counting
- Automated genome index building

**Output and Results**
- CSV output with all probe sequences and attributes
- Raw data export option for analysis
- Timestamped output files
- Comprehensive result metadata

**Documentation**
- Complete API documentation
- Configuration file reference
- Example configurations for common applications
- Troubleshooting guide

**Testing**
- Comprehensive test suite with pytest
- Example data and configurations
- Continuous integration setup

Security
~~~~~~~~
- Input validation for all configuration parameters
- Safe file handling with path validation
- Protection against code injection in expressions

Fixed
~~~~~
- Initial release - no previous bugs to fix

[0.9.0] - 2024-01-15
--------------------

Added
~~~~~
- Beta release with core probe design functionality
- Basic FISH and PCR probe support
- Command line interface prototype
- Initial documentation

Changed
~~~~~~~
- Refined API based on user feedback
- Improved performance for large target sets

Fixed
~~~~~
- Memory usage optimization
- Error handling improvements

[0.8.0] - 2023-12-01
--------------------

Added
~~~~~
- Alpha release for testing
- Core probe generation algorithms
- Basic quality control metrics
- Initial Python API

[0.1.0] - 2023-10-01
--------------------

Added
~~~~~
- Initial project structure
- Basic sequence manipulation utilities
- Proof-of-concept probe design
- Development environment setup

Development Milestones
----------------------

Future Plans (Roadmap)
~~~~~~~~~~~~~~~~~~~~~~

**Version 1.1.0** (Planned Q2 2024)
- Enhanced secondary structure prediction
- Improved multiplexing capabilities
- Additional quality metrics
- Performance optimizations

**Version 1.2.0** (Planned Q3 2024)
- Web interface for probe design
- Database integration for common targets
- Batch processing improvements
- Extended genome support

**Version 2.0.0** (Planned 2025)
- Machine learning-based probe optimization
- Real-time collaboration features
- Advanced visualization tools
- Cloud deployment options

Breaking Changes
----------------

Version 1.0.0
~~~~~~~~~~~~~~
- Configuration format standardized (may require updates to existing configs)
- API method names finalized (some beta methods renamed)
- Output format stabilized (column names may differ from beta)

Migration Guide
---------------

From Beta Versions (0.x.x) to 1.0.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Configuration Files:**

Old format:
.. code-block:: yaml

   probe_config:
     target_binding: "rc(target[0:25])"

New format:
.. code-block:: yaml

   probes:
     main_probe:
       template: "{binding}"
       parts:
         binding:
           expr: "rc(target_region[0:25])"

**API Changes:**

Old API:
.. code-block:: python

   designer = ProbeDesigner(config)
   probes = designer.design_probes(targets)

New API:
.. code-block:: python

   uprobe = UProbeAPI(protocol_config, genomes_config, output_dir)
   probes = uprobe.run_workflow()

**CLI Changes:**

Old CLI:
.. code-block:: bash

   python -m uprobe design --config config.yaml

New CLI:
.. code-block:: bash

   uprobe run --protocol protocol.yaml --genomes genomes.yaml

Contributors
------------

Version 1.0.0
~~~~~~~~~~~~~~
- **Weize Xu** - Core development and algorithms
- **Huaiyuan Cai** - Quality control and validation
- **Qian Zhang** - CLI and user interface  
- **Yu Chen** - Documentation and testing

Beta Versions
~~~~~~~~~~~~~
- **UFISH Team** - Initial concept and development
- **Community Contributors** - Testing and feedback

Acknowledgments
---------------

We thank the bioinformatics community for valuable feedback during development, and the authors of the following tools that U-Probe integrates:

- **Bowtie2** - Fast sequence alignment
- **BLAST+** - Sequence similarity search
- **Jellyfish** - K-mer counting
- **Primer3** - Primer design algorithms (inspiration)
- **ViennaRNA** - Secondary structure prediction

Special thanks to early adopters who provided testing and feedback during the beta releases.

Statistics
----------

.. list-table:: Release Statistics
   :header-rows: 1
   :widths: 15 15 15 15 15 15 10

   * - Version
     - Release Date
     - Features
     - Bug Fixes
     - Contributors
     - Tests
     - Coverage
   * - 1.0.0
     - 2024-01-31
     - 25+
     - N/A
     - 4
     - 150+
     - 85%+
   * - 0.9.0
     - 2024-01-15
     - 20
     - 5
     - 4
     - 100
     - 75%
   * - 0.8.0
     - 2023-12-01
     - 15
     - 8
     - 3
     - 75
     - 60%
   * - 0.1.0
     - 2023-10-01
     - 5
     - 0
     - 2
     - 25
     - 40%

How to Stay Updated
-------------------

- **GitHub Releases**: Watch the repository for release notifications
- **Documentation**: Check this changelog for latest updates
- **PyPI**: Monitor for new package versions
- **Discussions**: Join GitHub Discussions for development updates

Reporting Issues
----------------

Found a bug or have a suggestion? Please help us improve U-Probe:

1. **Check existing issues** on GitHub
2. **Create a new issue** with detailed information
3. **Include version information**: ``uprobe version``
4. **Provide reproducible examples** when possible

See our :doc:`contributing` guide for more details on how to help improve U-Probe.

Versioning Policy
-----------------

U-Probe follows semantic versioning (SemVer):

- **Major version** (X.0.0): Breaking changes, major new features
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

**Pre-release versions:**
- **Alpha** (X.X.X-alpha.N): Early development, unstable
- **Beta** (X.X.X-beta.N): Feature complete, testing phase
- **Release Candidate** (X.X.X-rc.N): Stable, final testing

**Long-term Support (LTS):**
- Major versions will be supported for at least 2 years
- Critical security fixes for 3 years
- LTS versions will be clearly marked

License
-------

U-Probe is released under the MIT License. See the `LICENSE <https://github.com/UFISH-Team/U-Probe/blob/main/LICENSE>`_ file for details.

This changelog is maintained by the U-Probe development team and community contributors.
