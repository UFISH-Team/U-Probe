Contributing to U-Probe
=======================

We welcome contributions to U-Probe! This guide explains how to contribute to the project, whether you're reporting bugs, suggesting features, or contributing code.

Getting Started
---------------

Ways to Contribute
~~~~~~~~~~~~~~~~~~

- **Report bugs** and issues
- **Suggest new features** or improvements
- **Improve documentation**
- **Write tests** for existing functionality
- **Submit code** for bug fixes or new features
- **Share examples** and use cases
- **Help other users** in discussions

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   .. code-block:: bash

      git clone https://github.com/YOUR-USERNAME/U-Probe.git
      cd u-probe

3. **Set up development environment**:

   .. code-block:: bash

      # Create virtual environment
      python -m venv uprobe_dev
      source uprobe_dev/bin/activate  # On Windows: uprobe_dev\Scripts\activate
      
      # Install in development mode
      pip install -e ".[dev]"

4. **Install pre-commit hooks** (optional but recommended):

   .. code-block:: bash

      pip install pre-commit
      pre-commit install

5. **Run tests** to ensure everything works:

   .. code-block:: bash

      pytest

Reporting Issues
----------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, please include:

1. **U-Probe version**: ``uprobe version``
2. **Operating system** and Python version
3. **Complete error message** and traceback
4. **Minimal example** to reproduce the issue
5. **Expected vs actual behavior**
6. **Configuration files** (anonymized if needed)

Use our bug report template:

.. code-block:: text

   **Bug Description**
   A clear description of the bug.

   **To Reproduce**
   Steps to reproduce the behavior:
   1. Create config file '...'
   2. Run command '...'
   3. See error

   **Expected Behavior**
   What you expected to happen.

   **Environment**
   - U-Probe version: [e.g. 1.0.0]
   - OS: [e.g. Ubuntu 20.04]
   - Python version: [e.g. 3.11.0]

   **Additional Context**
   Any other relevant information.

Feature Requests
~~~~~~~~~~~~~~~~

For feature requests, describe:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought of
4. **Implementation ideas**: If you have technical suggestions

Submitting Changes
------------------

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Create a branch** for your changes:

   .. code-block:: bash

      git checkout -b feature/your-feature-name
      # or
      git checkout -b fix/issue-number

2. **Make your changes** following our coding standards
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Commit changes** with descriptive messages:

   .. code-block:: bash

      git add .
      git commit -m "Add feature X to solve problem Y"

6. **Push to your fork**:

   .. code-block:: bash

      git push origin feature/your-feature-name

7. **Create a Pull Request** on GitHub

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

**Before submitting:**

- Run tests: ``pytest``
- Check code formatting: ``black --check .``
- Verify imports: ``isort --check-only .``
- Test documentation builds: ``make html`` (in docs/ directory)

**Pull request description should include:**

- Clear description of changes
- Reference to related issues (e.g., "Fixes #123")
- Type of change (bug fix, feature, documentation, etc.)
- Testing performed
- Breaking changes (if any)

Pull Request Template:

.. code-block:: text

   ## Description
   Brief description of changes.

   ## Type of Change
   - [ ] Bug fix (non-breaking change that fixes an issue)
   - [ ] New feature (non-breaking change that adds functionality)
   - [ ] Breaking change (fix or feature that breaks existing functionality)
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added tests for new functionality
   - [ ] Manual testing performed

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Changes described in commit messages

Code Standards
--------------

Style Guidelines
~~~~~~~~~~~~~~~~

We follow Python community standards:

- **PEP 8** for code style
- **Black** for code formatting
- **isort** for import sorting
- **Type hints** for new code
- **Docstrings** for all public functions/classes

**Code formatting:**

.. code-block:: bash

   # Format code
   black .
   isort .
   
   # Check formatting
   black --check .
   isort --check-only .

**Example function:**

.. code-block:: python

   def calculate_gc_content(sequence: str) -> float:
       """
       Calculate GC content of a DNA sequence.
       
       Args:
           sequence: DNA sequence string containing only ATCG characters
           
       Returns:
           GC content as a float between 0.0 and 1.0
           
       Raises:
           ValueError: If sequence contains invalid characters
           
       Examples:
           >>> calculate_gc_content("ATCG")
           0.5
           >>> calculate_gc_content("AAAA")
           0.0
       """
       if not sequence:
           return 0.0
           
       valid_chars = set('ATCG')
       if not set(sequence.upper()).issubset(valid_chars):
           raise ValueError("Sequence contains invalid characters")
           
       gc_count = sequence.upper().count('G') + sequence.upper().count('C')
       return gc_count / len(sequence)

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~~

- **Docstrings**: Use Google/NumPy style
- **Type hints**: Include for all parameters and returns
- **Examples**: Provide usage examples in docstrings
- **README updates**: Update if adding new features
- **Sphinx docs**: Update relevant .rst files

**Docstring example:**

.. code-block:: python

   class ProbeDesigner:
       """
       Design probes for molecular biology applications.
       
       This class provides methods for designing various types of molecular
       probes including FISH probes, PCR primers, and sequencing adapters.
       
       Attributes:
           config: Configuration dictionary for probe design
           genome: Genome information and file paths
           
       Examples:
           >>> designer = ProbeDesigner(config, genome)
           >>> probes = designer.design_fish_probes(targets)
           >>> len(probes)
           42
       """

Testing Guidelines
~~~~~~~~~~~~~~~~~~

All new code should include tests:

.. code-block:: python

   import pytest
   from uprobe.utils import calculate_gc_content

   class TestGCContent:
       """Test GC content calculation."""
       
       def test_gc_content_basic(self):
           """Test basic GC content calculation."""
           assert calculate_gc_content("ATCG") == 0.5
           assert calculate_gc_content("AAAA") == 0.0
           assert calculate_gc_content("GGCC") == 1.0
       
       def test_gc_content_empty(self):
           """Test GC content with empty string."""
           assert calculate_gc_content("") == 0.0
       
       def test_gc_content_invalid_chars(self):
           """Test GC content with invalid characters."""
           with pytest.raises(ValueError, match="invalid characters"):
               calculate_gc_content("ATCGN")
       
       @pytest.mark.parametrize("sequence,expected", [
           ("AT", 0.0),
           ("GC", 1.0),
           ("ATGC", 0.5),
           ("ATGCGC", 0.667),
       ])
       def test_gc_content_parametrized(self, sequence, expected):
           """Test GC content with multiple inputs."""
           assert abs(calculate_gc_content(sequence) - expected) < 0.001

Run specific tests:

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run specific test file
   pytest tests/test_utils.py
   
   # Run with coverage
   pytest --cov=uprobe

Types of Contributions
----------------------

Bug Fixes
~~~~~~~~~~

Small bug fixes are always welcome:

1. Create issue describing the bug (if one doesn't exist)
2. Fix the bug with minimal changes
3. Add test case that would have caught the bug
4. Submit pull request referencing the issue

New Features
~~~~~~~~~~~~

For larger features:

1. **Open an issue** to discuss the feature first
2. **Get feedback** from maintainers and community
3. **Break down** large features into smaller PRs
4. **Include comprehensive tests** and documentation
5. **Consider backward compatibility**

Documentation
~~~~~~~~~~~~~

Documentation improvements are highly valued:

- Fix typos and grammar
- Add missing examples
- Improve clarity of explanations
- Add new tutorials or guides
- Update API documentation

**Building docs locally:**

.. code-block:: bash

   cd docs/
   make html
   # Open build/html/index.html in browser

Examples and Tutorials
~~~~~~~~~~~~~~~~~~~~~~

Share your U-Probe applications:

- Create example configurations
- Write tutorials for specific use cases
- Document best practices
- Share integration examples

Add to ``examples/`` directory or documentation.

Testing
~~~~~~~

Help improve test coverage:

- Write tests for untested code
- Add edge case tests
- Create integration tests
- Performance benchmarking

Community Guidelines
--------------------

Code of Conduct
~~~~~~~~~~~~~~~

We follow the Contributor Covenant:

- **Be respectful** and inclusive
- **Welcome newcomers** and help them learn
- **Accept constructive criticism** gracefully
- **Focus on what's best** for the community
- **Show empathy** towards other contributors

Communication
~~~~~~~~~~~~~

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **Pull Requests**: Code reviews and technical discussion
- **Email**: Maintainer contact for sensitive issues

Be patient and understanding - contributors volunteer their time.

Review Process
--------------

What Happens After Submitting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Automated checks** run (tests, linting, etc.)
2. **Maintainer review** for appropriateness and quality
3. **Community feedback** on larger changes
4. **Iterative improvements** based on feedback
5. **Final approval** and merge

Review Criteria
~~~~~~~~~~~~~~~

We look for:

- **Correct functionality**: Does it work as intended?
- **Code quality**: Is it readable and maintainable?
- **Test coverage**: Are changes adequately tested?
- **Documentation**: Is it documented appropriately?
- **Compatibility**: Does it break existing functionality?
- **Performance**: Does it significantly impact performance?

Getting Your PR Merged
~~~~~~~~~~~~~~~~~~~~~~~

To speed up the review process:

- **Keep PRs focused**: One feature/fix per PR
- **Write clear descriptions**: Explain what and why
- **Respond to feedback**: Address reviewer comments promptly
- **Keep PRs updated**: Rebase on main branch if needed
- **Be patient**: Reviews take time, especially for complex changes

Development Setup Details
-------------------------

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   u-probe/
   ├── uprobe/              # Main package
   │   ├── __init__.py
   │   ├── api.py           # Main API class
   │   ├── cli.py           # Command line interface
   │   ├── attributes/      # Attribute calculation
   │   ├── gen/             # Probe generation
   │   ├── process/         # Post-processing
   │   └── tools/           # External tool integration
   ├── tests/               # Test files
   ├── docs/                # Documentation
   ├── examples/            # Example configurations
   ├── requirements*.txt    # Dependencies
   └── setup.py            # Package configuration

Running Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev]"
   
   # Run tests with coverage
   pytest --cov=uprobe --cov-report=html
   
   # Check code quality
   black --check .
   isort --check-only .
   flake8 uprobe/
   
   # Build documentation
   cd docs/
   make html

Debugging
~~~~~~~~~

For debugging issues:

.. code-block:: bash

   # Run with verbose logging
   uprobe --verbose run -p protocol.yaml -g genomes.yaml
   
   # Run single test with debugging
   pytest -xvs tests/test_specific.py::test_function
   
   # Use pdb for interactive debugging
   python -m pdb -c continue uprobe_script.py

Release Process
---------------

For maintainers, the release process involves:

1. Update version in ``uprobe/__init__.py``
2. Update ``CHANGELOG.md``
3. Create release branch
4. Test thoroughly
5. Create GitHub release
6. Build and upload to PyPI

Regular contributors may be invited to help with releases.

Recognition
-----------

Contributors are recognized through:

- **GitHub contributors page**
- **Release notes** acknowledgments
- **Documentation credits**
- **Potential co-authorship** on papers using U-Probe

Questions?
----------

If you have questions about contributing:

- Check existing GitHub discussions
- Open a new discussion with the "Contributing" label  
- Review this guide thoroughly
- Look at existing PRs for examples

Thank you for contributing to U-Probe! 🧬
