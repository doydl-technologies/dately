from setuptools import setup, find_packages
import sys

# Check if the system is Windows
if sys.platform != 'win32':
    raise RuntimeError("This package is only compatible with Windows.")


setup(
    name="dately",
    version="1.0.0",
    author="Cedric Moore Jr.",
    author_email="cedric@doydl.tech",
    description="A library for manipulating datetime strings.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cedricmoorejr/dately",
    project_urls={
        "Source Code": "https://github.com/cedricmoorejr/dately",
    },
    packages=find_packages(),
    package_data={
        'dately': [
            'mold/pyd/*.pyd',
            'mold/pyd/cdatetime/*.pyd'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.8',
    install_requires=[
        "numpy",
        "pandas",
        "pytz",
        "requests",
    ],
    license="MIT",
)
