==========================
Frequently Asked Questions
==========================

General Questions
-----------------

What is U-Probe?
~~~~~~~~~~~~~~~~~
U-Probe is a comprehensive, automated framework for designing DNA/RNA probes for various molecular biology applications, including FISH, PCR, and targeted sequencing.

What makes U-Probe different from other tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **End-to-End Automation**: From target selection to final probe generation.
* **DAG Architecture**: Supports highly complex, modular probe structures.
* **Configuration-Driven**: YAML-based setup ensures reproducibility.
* **Flexible Interfaces**: Offers a Web UI, a CLI, and a Python API.

----------------------
Installation and Setup
----------------------

Do I need to install external tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Yes. U-Probe requires **Bowtie2** (for sequence alignment) and **BLAST+** (for similarity searches). **Jellyfish** is optional but recommended for k-mer counting.

Can I use U-Probe on Windows?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Yes, but we strongly recommend using Windows Subsystem for Linux (WSL) to ensure seamless compatibility with external bioinformatics tools like Bowtie2.

-------------
Configuration
-------------

How do I find the correct gene names?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gene names in your ``protocol.yaml`` must exactly match the ``gene_name`` or ``gene_id`` attributes in your provided GTF annotation file.

What's the difference between "exon", "gene", and "genome" extraction?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **exon**: Extracts only from annotated exonic regions (spliced sequences). Ideal for RNA FISH.
* **gene**: Extracts from the entire gene region, including introns.
* **genome**: Extracts from specific genomic coordinates (e.g., ``chr1:1000-2000``).

------------
Probe Design
------------

Why are all my probes being filtered out?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This usually happens if your filters are too strict. Try running the pipeline with the ``--raw`` flag to inspect the unfiltered data distribution, then adjust your ``gc_content`` or ``melting_temp`` thresholds accordingly.

How can I speed up probe design?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Increase the number of threads (``-t 16``).
2. Remove computationally expensive attributes (like ``fold_score`` or ``kmer_count``) during the initial design phase.
3. Use ``exon`` extraction instead of ``gene`` to reduce the search space.

-----------------
Getting More Help
-----------------

If your question isn't answered here, please visit our `GitHub Discussions <https://github.com/UFISH-Team/U-Probe/discussions>`_ or open an issue on our repository.
