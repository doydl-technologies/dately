# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# The `dately` module is a deterministic engine for parsing, resolving, and normalizing
# temporal expressions across both natural and symbolic language contexts — built for NLP
# workflows, cross-platform date handling, and fine-grained temporal reasoning.
#
# Designed with formal grammatical rigor, `dately` interprets phrases like “first five days of next month,”
# “Q3 of last year,” and “April 3” — handling cardinal/ordinal resolution, anchored structures, and
# ambiguous or implicit references with linguistic sensitivity.
#
# The engine combines structured tokenization, symbolic transformation, and rule-based semantic
# composition to support precision across tasks such as entity recognition, information extraction,
# and temporal normalization in noisy or informal text.
#
# It guarantees invertibility, transparency, and cross-platform consistency, resolving platform-specific
# formatting differences (e.g. Windows vs. Unix) while maintaining NLP-grade flexibility for English-language
# temporal constructions.
#
# Whether embedded in intelligent agents, ETL pipelines, or legal/medical NLP systems, `dately` brings
# clarity and structure to temporal meaning — bridging symbolic logic with real-world language.
#
# Copyright (c) 2024 by doydl technologies. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import re
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup
from setuptools.command.build_py import build_py as _build_py


ROOT = Path(__file__).resolve().parent
VERSION_MATCH = re.search(
    r'^__version__\s*=\s*["\']([^"\']+)["\']',
    (ROOT / "_version.py").read_text(encoding="utf-8"),
    re.MULTILINE,
)
if VERSION_MATCH is None:
    raise RuntimeError("Unable to determine the dately version from _version.py.")
VERSION = VERSION_MATCH.group(1)


subpackages = find_packages(str(ROOT), exclude=("tests", "tests.*"))
include_dir = "mold/include"


class BuildPy(_build_py):
    """Keep the repository's build script out of the flat-layout package."""

    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [module for module in modules if not (package == "dately" and module[1] == "setup")]


def extension(name, *sources):
    """Create an extension from authoritative Cython and C helper sources."""
    return Extension(
        name,
        sources=[f"mold/src/{source}" for source in sources],
        include_dirs=[include_dir],
        define_macros=[("CYTHON_USE_PYLONG_INTERNALS", "0")],
    )


extensions = [
    extension("dately.mold.pyd.clean_str", "../pyx/clean_str.pyx", "clean_str_impl.c"),
    extension("dately.mold.pyd.Compiled", "../pyx/Compiled.pyx"),
    extension("dately.mold.pyd.time_zones", "../pyx/time_zones.pyx", "time_zones_impl.c"),
    extension("dately.mold.pyd.cdatetime.iso8601T", "../pyx/iso8601T.pyx", "iso8601T_impl.c"),
    extension("dately.mold.pyd.cdatetime.iso8601Z", "../pyx/iso8601Z.pyx", "iso8601Z_impl.c"),
    extension("dately.mold.pyd.cdatetime.UniversalDateFormatter", "../pyx/UniversalDateFormatter.pyx"),
    extension("dately.mold.pyd.cdatetime.whichformat", "../pyx/whichformat.pyx"),
]

extensions = cythonize(extensions, compiler_directives={"language_level": "3"})

setup(
    name="dately",
    version=VERSION,
    description="Deterministic date, time, timezone, holiday, and temporal-language processing.",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/cedricmoorejr/dately",
    project_urls={
        "Documentation": "https://github.com/cedricmoorejr/dately#readme",
        "Issues": "https://github.com/cedricmoorejr/dately/issues",
        "Source": "https://github.com/cedricmoorejr/dately",
    },
    author="cedricmoorejunior",
    license="MIT",
    packages=["dately"] + [f"dately.{package}" for package in subpackages],
    package_dir={"dately": "."},
    package_data={
        "dately": [
            "files/country_variants.json",
            "files/holiday.json",
            "files/timezone_data.json",
            "_vendor/agent_profile/user_agent/*.md",
        ]
    },
    ext_modules=extensions,
    cmdclass={"build_py": BuildPy},
    include_package_data=False,
    install_requires=[
        "importlib-resources; python_version < '3.9'",
        "numbr",
        "numpy",
        "pandas",
        "pytz",
        "requests",
        "requests-cache",
    ],
    python_requires=">=3.8,<3.15",
    platforms=["Windows"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    zip_safe=False,
)
