=======================
Contributing to U-Probe
=======================

We welcome contributions to U-Probe! Whether you are reporting bugs, suggesting features, or submitting code, your help is appreciated.

Setting Up Development Environment
----------------------------------

1. **Fork and Clone:**

   .. code-block:: bash

      git clone https://github.com/YOUR-USERNAME/U-Probe.git
      cd U-Probe

2. **Create a Virtual Environment & Install:**

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate
      pip install -e ".[dev]"

3. **Run Tests:**

   .. code-block:: bash

      pytest

------------------
Submitting Changes
------------------

1. Create a new branch (``git checkout -b feature/your-feature``).
2. Make your changes.
3. Ensure your code follows PEP 8. We use ``black`` for formatting and ``isort`` for imports.
4. Write tests for your new functionality.
5. Submit a Pull Request (PR) to the ``main`` branch.

----------------
Reporting Issues
----------------

When reporting bugs on GitHub Issues, please include:

1. U-Probe version (``uprobe --version``).
2. Operating system and Python version.
3. A minimal reproducible example (your YAML configs).
4. The full error traceback.

-----------------------
Documentation Standards
-----------------------

* Use Google-style docstrings for all public functions and classes.
* Include type hints for all parameters and return values.
* If you add a new feature, update the corresponding ``.rst`` files in the ``docs/source/`` directory.

Thank you for helping make U-Probe better!
