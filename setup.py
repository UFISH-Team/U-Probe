from setuptools import setup, find_packages
import re
import os


classifiers = [
    "Development Status :: 3 - Alpha",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
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
            m = re.match("__version__ = '([^']+)'", line)
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


posix_requires = [
    "pysam"
]


def get_install_requires():
    reqs = get_requirements_from_file('requirements.txt')
    # Add posix_requires if the OS is posix(Linux, MacOS, etc.)
    if os.name == 'posix':
        reqs += posix_requires
    return reqs


packages_for_dev = get_requirements_from_file("requirements-dev.txt")
packages_for_docs = get_requirements_from_file("requirements-doc.txt")
requires_dev = packages_for_dev + packages_for_docs


setup(
    name='uprobe',
    author='Weize Xu, Huaiyuan Cai, Qian Zhang, Yu Chen',
    author_email='vet.xwz@gmail.com',
    version=get_version(),
    license='MIT',
    description='Universal oligo probe design tools.',
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
    python_requires='>=3.9, <4',
    entry_points={
        'console_scripts': [
            'uprobe = uprobe.__main__:main',
        ],
    },
)
