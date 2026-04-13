from setuptools import setup, find_packages
import re


classifiers = [
    "Development Status :: 3 - Alpha",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Science/Research",
]


keywords = [
    'FISH', 'Probe design',
]


URL = "https://github.com/UFISH-Team/U-Probe"


def get_version():
    with open("uprobe/__init__.py") as f:
        for line in f.readlines():
            m = re.match(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", line)
            if m:
                return m.group(1)
        raise IOError("Version information can not found.")


def get_long_description():
    return f"See {URL}"


def get_requirements_from_file(filename):
    requirements = []
    with open(filename) as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0:
                continue
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements


def get_install_requires():
    reqs = get_requirements_from_file('requirements.txt')
    return reqs


packages_for_dev = get_requirements_from_file("requirements-dev.txt")
requires_dev = packages_for_dev


setup(
    name='uprobe',
    author='Qian Zhang, Weize Xu',
    author_email='jshn2022@163.com, ',
    version=get_version(),
    license='MIT',
    description='Web server for U-Probe',
    long_description=get_long_description(),
    keywords=keywords,
    url=URL,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    install_requires=get_install_requires(),
    extras_require={
        'dev': requires_dev,
    },
    python_requires='>=3.8, <4',
    entry_points={
        'console_scripts': [
            'uprobe = uprobe.core.cli:main',
            'u-probe = uprobe.core.cli:main',
        ],
    },
)
