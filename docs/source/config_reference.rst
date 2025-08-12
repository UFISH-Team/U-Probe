Configuration Reference
=======================

This page provides a complete reference for all configuration options in U-Probe's YAML files.

Genomes Configuration (genomes.yaml)
------------------------------------

Required Fields
~~~~~~~~~~~~~~~

.. option:: fasta

   **Type:** string
   
   **Description:** Path to the genome FASTA file containing reference sequences.
   
   **Example:**
   
   .. code-block:: yaml
   
      fasta: "/data/genomes/hg38/hg38.fa"

.. option:: gtf

   **Type:** string
   
   **Description:** Path to the gene annotation GTF file for target validation and coordinate extraction.
   
   **Example:**
   
   .. code-block:: yaml
   
      gtf: "/data/genomes/hg38/gencode.v38.annotation.gtf"

.. option:: align_index

   **Type:** list of strings
   
   **Description:** List of aligners for which to build indices.
   
   **Valid values:** ``bowtie2``, ``blast``
   
   **Example:**
   
   .. code-block:: yaml
   
      align_index:
        - bowtie2
        - blast

Optional Fields
~~~~~~~~~~~~~~~

.. option:: description

   **Type:** string
   
   **Description:** Human-readable description of the genome.
   
   **Example:**
   
   .. code-block:: yaml
   
      description: "Human genome build 38 (GRCh38)"

.. option:: species

   **Type:** string
   
   **Description:** Scientific species name.
   
   **Example:**
   
   .. code-block:: yaml
   
      species: "Homo sapiens"

.. option:: out

   **Type:** string
   
   **Description:** Output directory for genome indices. Defaults to FASTA file directory.
   
   **Example:**
   
   .. code-block:: yaml
   
      out: "/data/genomes/hg38/indices"

.. option:: jellyfish

   **Type:** boolean
   
   **Description:** Whether to build Jellyfish k-mer database for k-mer counting attributes.
   
   **Default:** false
   
   **Example:**
   
   .. code-block:: yaml
   
      jellyfish: true

Protocol Configuration (protocol.yaml)
--------------------------------------

Core Settings
~~~~~~~~~~~~~

.. option:: name

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Unique name for the experiment, used in output filenames.
   
   **Example:**
   
   .. code-block:: yaml
   
      name: "FISH_Experiment_v1"

.. option:: genome

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Name of the genome to use (must match a key in genomes.yaml).
   
   **Example:**
   
   .. code-block:: yaml
   
      genome: "human_hg38"

.. option:: targets

   **Type:** list of strings
   
   **Required:** Yes
   
   **Description:** List of target gene names or identifiers. Must exist in the GTF file.
   
   **Example:**
   
   .. code-block:: yaml
   
      targets:
        - "GAPDH"
        - "ACTB"
        - "ENSG00000141510"

Target Extraction (extracts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: extracts.target_region

   **Type:** object
   
   **Required:** Yes
   
   **Description:** Configuration for extracting target sequences from the genome.

.. option:: extracts.target_region.source

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Source regions for extraction.
   
   **Valid values:**
   
   - ``exon`` - Extract from exonic regions only
   - ``gene`` - Extract from entire gene regions (including introns)
   - ``genome`` - Extract from specified genomic coordinates
   
   **Example:**
   
   .. code-block:: yaml
   
      extracts:
        target_region:
          source: "exon"

.. option:: extracts.target_region.length

   **Type:** integer
   
   **Required:** Yes
   
   **Description:** Length of each target region in base pairs.
   
   **Example:**
   
   .. code-block:: yaml
   
      extracts:
        target_region:
          length: 120

.. option:: extracts.target_region.overlap

   **Type:** integer
   
   **Required:** Yes
   
   **Description:** Overlap between adjacent extracts in base pairs.
   
   **Example:**
   
   .. code-block:: yaml
   
      extracts:
        target_region:
          overlap: 20

.. option:: extracts.target_region.coordinates

   **Type:** list of strings
   
   **Required:** Only when source is "genome"
   
   **Description:** Specific genomic coordinates to extract (format: "chr:start-end").
   
   **Example:**
   
   .. code-block:: yaml
   
      extracts:
        target_region:
          source: "genome"
          coordinates:
            - "chr1:1000000-1001000"
            - "chr2:2000000-2001000"

.. option:: extracts.target_region.gene_specific

   **Type:** object
   
   **Required:** No
   
   **Description:** Gene-specific extraction parameters that override defaults.
   
   **Example:**
   
   .. code-block:: yaml
   
      extracts:
        target_region:
          source: "exon"
          length: 120
          gene_specific:
            GAPDH:
              length: 150
              overlap: 30
            TP53:
              source: "gene"

Probe Design (probes)
~~~~~~~~~~~~~~~~~~~~~

.. option:: probes

   **Type:** object
   
   **Required:** Yes
   
   **Description:** Defines probe structures and composition. Keys are probe names.

.. option:: probes.[probe_name].template

   **Type:** string
   
   **Required:** Yes (unless using expr)
   
   **Description:** Template string defining probe structure using part names in braces.
   
   **Example:**
   
   .. code-block:: yaml
   
      probes:
        main_probe:
          template: "{part1}{spacer}{part2}"

.. option:: probes.[probe_name].expr

   **Type:** string
   
   **Required:** Yes (unless using template)
   
   **Description:** Direct expression for simple probes without parts.
   
   **Example:**
   
   .. code-block:: yaml
   
      probes:
        simple_probe:
          expr: "rc(target_region[0:25])"

.. option:: probes.[probe_name].parts

   **Type:** object
   
   **Required:** When using template
   
   **Description:** Definitions for each part referenced in the template.

.. option:: probes.[probe_name].parts.[part_name].expr

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Expression defining how to generate this part.
   
   **Available expressions:**
   
   - ``target_region[start:end]`` - Slice of target sequence
   - ``rc(sequence)`` - Reverse complement
   - ``encoding[gene_name]['key']`` - Barcode lookup
   - ``random_seq(length)`` - Random sequence
   - ``probe_name[start:end]`` - Reference other probes
   - ``'LITERAL'`` - Fixed sequence (in quotes)

.. option:: probes.[probe_name].parts.[part_name].length

   **Type:** integer
   
   **Required:** For some expressions
   
   **Description:** Required length for this part (used with slicing expressions).

.. option:: probes.[probe_name].parts.[part_name].template

   **Type:** string
   
   **Required:** No
   
   **Description:** Nested template for complex parts.

Nested Parts Example:

.. code-block:: yaml

   probes:
     complex_probe:
       template: "{binding_region}{barcode_region}"
       parts:
         binding_region:
           length: 25
           expr: "rc(target_region[0:25])"
         barcode_region:
           template: "{bc1}GGG{bc2}"
           parts:
             bc1:
               expr: "encoding[gene_name]['BC1']"
             bc2:
               expr: "encoding[gene_name]['BC2']"

Encoding System (encoding)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: encoding

   **Type:** object
   
   **Required:** When using encoding expressions
   
   **Description:** Maps gene names to barcode sequences or other identifiers.

.. option:: encoding.[gene_name]

   **Type:** object
   
   **Description:** Barcode/identifier mappings for a specific gene.

.. option:: encoding.[gene_name].[key]

   **Type:** string
   
   **Description:** Sequence associated with this key for this gene.

**Example:**

.. code-block:: yaml

   encoding:
     GAPDH:
       BC1: "ACGTACGTACGT"
       BC2: "TGCATGCATGCA"
       fluorophore: "AAAATTTTCCCCGGGG"
     ACTB:
       BC1: "CGATCGATCGAT"
       BC2: "ATCGATCGATCG"
       fluorophore: "TTTTAAAACCCCGGGG"

Quality Attributes (attributes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: attributes

   **Type:** object
   
   **Required:** No
   
   **Description:** Defines quality metrics to calculate for probes.

.. option:: attributes.[attribute_name].target

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Target sequence to analyze (probe name, part name, or "target_region").

.. option:: attributes.[attribute_name].type

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Type of attribute to calculate.
   
   **Available types:**
   
   - ``gc_content`` - GC content (0.0 to 1.0)
   - ``annealing_temperature`` - Melting temperature (°C)
   - ``self_match`` - Self-complementarity score
   - ``fold_score`` - Secondary structure propensity
   - ``n_mapped_genes`` - Off-target mapping count
   - ``kmer_count`` - K-mer abundance
   - ``length`` - Sequence length
   - ``complexity_score`` - Sequence complexity

**Basic Attribute Example:**

.. code-block:: yaml

   attributes:
     probe_gc:
       target: main_probe
       type: gc_content
     probe_tm:
       target: main_probe
       type: annealing_temperature

Alignment-Based Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: attributes.[attribute_name].aligner

   **Type:** string
   
   **Required:** For alignment-based attributes
   
   **Description:** Aligner to use for mapping analysis.
   
   **Valid values:** ``bowtie2``, ``blast``

.. option:: attributes.[attribute_name].min_mapq

   **Type:** integer
   
   **Description:** Minimum mapping quality (for bowtie2).
   
   **Default:** 30

.. option:: attributes.[attribute_name].e_value

   **Type:** float
   
   **Description:** E-value threshold (for BLAST).
   
   **Default:** 0.001

**Example:**

.. code-block:: yaml

   attributes:
     off_targets:
       target: main_probe
       type: n_mapped_genes
       aligner: bowtie2
       min_mapq: 30

K-mer Attributes
~~~~~~~~~~~~~~~~

.. option:: attributes.[attribute_name].kmer_length

   **Type:** integer
   
   **Required:** For kmer_count type
   
   **Description:** Length of k-mers to count.

.. option:: attributes.[attribute_name].kmer_threshold

   **Type:** integer
   
   **Description:** Abundance threshold for counting.

.. option:: attributes.[attribute_name].kmer_file

   **Type:** string
   
   **Description:** Jellyfish database file to use.

**Example:**

.. code-block:: yaml

   attributes:
     repetitive_kmers:
       target: main_probe
       type: kmer_count
       kmer_length: 12
       kmer_threshold: 100
       kmer_file: "genome.jf"

Post-Processing (post_process)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: post_process

   **Type:** object
   
   **Required:** No
   
   **Description:** Defines filtering, sorting, and overlap removal.

Filtering (post_process.filters)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: post_process.filters

   **Type:** object
   
   **Description:** Filter criteria for probe quality control.

.. option:: post_process.filters.[filter_name].condition

   **Type:** string
   
   **Required:** Yes
   
   **Description:** Boolean condition using attribute names and pandas syntax.
   
   **Operators:** ``>=``, ``<=``, ``>``, ``<``, ``==``, ``!=``, ``&`` (and), ``|`` (or)
   
   **Functions:** ``abs()``, mathematical functions

**Examples:**

.. code-block:: yaml

   post_process:
     filters:
       # Simple range filter
       gc_content:
         condition: "gc_content >= 0.4 & gc_content <= 0.6"
       
       # Threshold filter
       off_targets:
         condition: "off_targets <= 5"
       
       # Complex condition
       quality_filter:
         condition: "(gc_content >= 0.45 & melting_temp >= 55) | self_match < 0.8"
       
       # Using functions
       tm_similarity:
         condition: "abs(fwd_tm - rev_tm) <= 3"

Sorting (post_process.sorts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: post_process.sorts.is_ascending

   **Type:** list of strings
   
   **Description:** Attributes to sort in ascending order (low to high).

.. option:: post_process.sorts.is_descending

   **Type:** list of strings
   
   **Description:** Attributes to sort in descending order (high to low).

**Example:**

.. code-block:: yaml

   post_process:
     sorts:
       is_ascending:
         - "off_targets"
         - "self_match"
       is_descending:
         - "melting_temp"
         - "gc_content"

Overlap Removal (post_process.remove_overlap)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: post_process.remove_overlap.location_interval

   **Type:** integer
   
   **Description:** Minimum distance in base pairs between selected probes.

**Example:**

.. code-block:: yaml

   post_process:
     remove_overlap:
       location_interval: 25

Expression Reference
--------------------

Target Region Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Expression
     - Description
   * - ``target_region``
     - Entire target sequence
   * - ``target_region[0:20]``
     - First 20 bases
   * - ``target_region[-20:]``
     - Last 20 bases
   * - ``target_region[10:30]``
     - Bases 10-29 (20 bases)

Sequence Manipulation
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Expression
     - Description
   * - ``rc(sequence)``
     - Reverse complement
   * - ``random_seq(length)``
     - Random DNA sequence
   * - ``'ACGTACGT'``
     - Fixed literal sequence

Barcode Access
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Expression
     - Description
   * - ``encoding[gene_name]['BC1']``
     - Barcode for current gene
   * - ``encoding['GAPDH']['BC1']``
     - Barcode for specific gene

Probe References
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Expression
     - Description
   * - ``probe_1``
     - Entire probe_1 sequence
   * - ``probe_1[0:10]``
     - First 10 bases of probe_1
   * - ``probe_1:part1``
     - Specific part of probe_1

Context Variables
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``gene_name``
     - Current gene name
   * - ``gene_id``
     - Current gene ID
   * - ``target_region``
     - Current target sequence

Validation and Error Handling
------------------------------

Configuration validation occurs at multiple stages:

1. **Syntax validation** - YAML structure and required fields
2. **Reference validation** - Genome files exist, targets found in GTF
3. **Expression validation** - Probe expressions are valid
4. **Runtime validation** - Attribute calculations succeed

Common Validation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Error Type
     - Solution
   * - "Genome not found"
     - Check genome name matches genomes.yaml key
   * - "Target not found in GTF"
     - Verify gene names/IDs exist in annotation
   * - "Invalid expression"
     - Check probe expression syntax
   * - "Attribute calculation failed"
     - Verify required indices and files exist
   * - "No probes after filtering"
     - Relax filter conditions

Best Practices
--------------

Organization
~~~~~~~~~~~~

.. code-block:: yaml

   # Use descriptive names
   name: "FISH_Neuronal_Markers_v2.1"
   
   # Group related targets
   targets:
     # Housekeeping genes
     - "GAPDH"
     - "ACTB"
     # Neuronal markers  
     - "MAP2"
     - "NEUN"

Documentation
~~~~~~~~~~~~~

.. code-block:: yaml

   # Document design rationale
   name: "Optimized_FISH_Design"
   # Design notes:
   # - 25bp binding region for high specificity
   # - 6bp poly-T spacer to reduce steric hindrance  
   # - Strict GC content for uniform hybridization
   
   probes:
     fish_probe:
       template: "{binding}TTTTTT{fluorophore}"

Validation
~~~~~~~~~~

.. code-block:: yaml

   # Start with relaxed filters for testing
   post_process:
     filters:
       gc_content:
         condition: "gc_content >= 0.3 & gc_content <= 0.7"
   
   # Then tighten based on results
   # gc_content:
   #   condition: "gc_content >= 0.45 & gc_content <= 0.55"

Next Steps
----------

- Try the :doc:`examples` with different configurations
- Learn about :doc:`workflows` for your application
- Check :doc:`troubleshooting` for common issues
- Explore the :doc:`python_api` for programmatic access
