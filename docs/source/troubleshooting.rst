===============
Troubleshooting
===============

This guide addresses common issues encountered when using U-Probe.

Installation Issues
-------------------

Command not found: uprobe
~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Cause**: The Python scripts directory is not in your system's PATH.
* **Solution**: Ensure you are in the correct virtual environment (``conda activate uprobe`` or ``source venv/bin/activate``). Alternatively, run it as a Python module: ``python -m uprobe``.

Missing dependencies errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Cause**: External tools like Bowtie2 or BLAST+ are not installed.
* **Solution**: Install them via your package manager (e.g., ``sudo apt install bowtie2 ncbi-blast+`` or ``brew install bowtie2 blast``).

--------------------
Configuration Issues
--------------------

Target validation failed
~~~~~~~~~~~~~~~~~~~~~~~~

* **Cause**: The gene names in your ``protocol.yaml`` do not match the GTF annotation file.
* **Solution**: Verify the exact gene names or IDs in your GTF file:

  .. code-block:: bash

     grep -i "GAPDH" /path/to/annotation.gtf

Invalid YAML syntax
~~~~~~~~~~~~~~~~~~~~

* **Cause**: Incorrect indentation or unquoted special characters in YAML.
* **Solution**: Ensure consistent spacing (2 spaces per level) and quote expressions like ``expr: "rc(target_region)"``.

--------------
Runtime Issues
--------------

All probes filtered out
~~~~~~~~~~~~~~~~~~~~~~~

* **Cause**: Post-processing filters are too strict.
* **Solution**: Run U-Probe with the ``--raw`` flag to output unfiltered data. Inspect the ``_raw.csv`` file to understand the distribution of attributes (e.g., GC content, Tm) and adjust your filters accordingly.

Slow execution / Memory issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Cause**: Large genomes, many targets, or computationally expensive attributes (like ``kmer_count`` or ``fold_score``).
* **Solution**: 
  1. Increase threads: ``uprobe run -t 16``.
  2. Temporarily disable expensive attributes during the initial design phase.
  3. Use ``exon`` extraction instead of ``gene`` to reduce sequence length.

------------------
Reporting an Issue
------------------

If you cannot resolve the issue, please open a bug report on our `GitHub Issues <https://github.com/UFISH-Team/U-Probe/issues>`_ page. Include:

1. Your U-Probe version (``uprobe --version``).
2. The exact command run and the full error traceback.
3. A minimal version of your ``protocol.yaml`` and ``genomes.yaml``.
