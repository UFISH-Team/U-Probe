=======================
Configuration Reference
=======================

This page provides a comprehensive reference for all parameters available in U-Probe's YAML configuration files.

Genomes Configuration (genomes.yaml)
------------------------------------

The ``genomes.yaml`` file defines the reference genome paths and indexing options.

.. option:: fasta

   **Type:** string

   **Required:** Yes

   Path to the genome FASTA file.

.. option:: gtf

   **Type:** string

   **Required:** Yes

   Path to the gene annotation GTF file.

.. option:: align_index

   **Type:** list of strings

   **Required:** Yes

   Aligners to build indices for. Valid options: ``bowtie2``, ``blast``.

.. option:: jellyfish

   **Type:** boolean

   **Default:** false

   Whether to build a Jellyfish k-mer database for fast specificity screening.

Protocol Configuration (protocol.yaml)
--------------------------------------

The ``protocol.yaml`` file defines the probe design logic.

Core Settings
~~~~~~~~~~~~~

.. option:: name

   **Type:** string

   Unique identifier for the experiment. Used in output filenames.

.. option:: genome

   **Type:** string

   Name of the genome to use (must match a key in ``genomes.yaml``).

.. option:: targets

   **Type:** list of strings

   List of target gene names or IDs. Must exist in the GTF file.

Target Extraction (extracts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: extracts.target_region.source

   **Type:** string

   Source regions for extraction. Valid values: ``exon``, ``gene``, ``genome``.

.. option:: extracts.target_region.length

   **Type:** integer

   Length of each extracted target region in base pairs.

.. option:: extracts.target_region.overlap

   **Type:** integer

   Overlap between adjacent extracts (stride = length - overlap).

Probe Design (probes)
~~~~~~~~~~~~~~~~~~~~~

.. option:: probes.[probe_name].template

   **Type:** string

   Template string defining probe structure using part names in braces (e.g., ``"{part1}{part2}"``).

.. option:: probes.[probe_name].parts.[part_name].expr

   **Type:** string

   Expression defining how to generate this part.

   *Available functions:* ``rc(sequence)``, ``target_region[start:end]``, ``encoding[target]['key']``.

Quality Attributes (attributes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: attributes.[attribute_name].type

   **Type:** string

   Type of attribute to calculate.

   *Available types:* 

   - ``gc_content``: GC ratio (0.0 to 1.0)
   - ``annealing_temperature``: Melting temperature (°C) via Primer3
   - ``self_match``: Self-complementarity score
   - ``fold_score``: Minimum Free Energy (MFE) via ViennaRNA
   - ``n_mapped_genes``: Off-target mapping count (requires ``aligner: bowtie2``)
   - ``kmer_count``: K-mer abundance (requires ``jellyfish: true``)

Post-Processing (post_process)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: post_process.filters.[filter_name].condition

   **Type:** string

   Boolean condition using attribute names and pandas syntax (e.g., ``"gc_content >= 0.4 & melting_temp > 37"``).

.. option:: post_process.sorts.is_ascending

   **Type:** list of strings

   Attributes to sort in ascending order (low to high).

.. option:: post_process.sorts.is_descending

   **Type:** list of strings

   Attributes to sort in descending order (high to low).

.. option:: remove_overlap.location_interval

   **Type:** integer

   Minimum distance in base pairs between selected probes on the target sequence. Set to 0 to ensure no physical overlap.
