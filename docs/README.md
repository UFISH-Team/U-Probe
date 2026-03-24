# U-Probe Documentation Guide

This directory contains the source files for U-Probe's official documentation, built with [Sphinx](https://www.sphinx-doc.org/) and hosted on [Read the Docs](https://readthedocs.org/).

## 📖 Online Documentation

The latest documentation is available at: **https://uprobe.readthedocs.io/**

## 🏗️ Building Documentation Locally

If you want to preview documentation changes locally, follow these steps:

### 1. Install Dependencies

Run the following command from the project root to install the required dependencies for building the documentation:

```bash
pip install -e ".[docs]"
```

### 2. Quick Build

Navigate to the `docs` directory and run the build script:

```bash
cd docs/
chmod +x build_docs.sh
./build_docs.sh
```

Once the build is complete, open `build/html/index.html` in your browser to view the documentation.

### 3. Clean Build Cache

If you need to rebuild from scratch, you can clean the old build files first:

```bash
./build_docs.sh clean
```

## 📁 Directory Structure

- `source/`: Contains the documentation source files (all `.rst` files and configurations).
  - `conf.py`: The core configuration file for Sphinx.
  - `index.rst`: The main homepage structure of the documentation.
- `build/`: The output directory for the generated HTML documentation (created after building).
- `build_docs.sh`: A shortcut script to simplify the build process.

## ✍️ Contributing to Documentation

We welcome contributions to improve the U-Probe documentation!
1. Modify or add `.rst` files in the `source/` directory.
2. Ensure you run `./build_docs.sh` locally to test your changes.
3. Submit a Pull Request. Read the Docs will automatically generate a preview build.
