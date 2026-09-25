#! python3.8
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

"""Refresh the checked-in browser version tables."""

import json
import os
import tempfile
from pathlib import Path

from .version_sources.apple import AppleVersions
from .version_sources.chrome import ChromeVersions
from .version_sources.edge import EdgeVersions


OUT_DIR = Path(__file__).resolve().parent / "browser_versions"
HISTORICAL_MAJOR_COUNT = 60


def _validate(name, data):
    if not isinstance(data, dict) or not data or "error" in data:
        raise RuntimeError(f"{name} version refresh failed: {data}")
    if any(not isinstance(values, list) or not values for values in data.values()):
        raise RuntimeError(f"{name} version refresh returned an empty version group.")


def save_py(filename, variable_name, data):
    """Atomically write an importable version table with the required shebang."""
    destination = OUT_DIR / filename
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(OUT_DIR), prefix=f".{filename}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write("#! python3.8\n")
            file.write(f"{variable_name} = ")
            json.dump(data, file, indent=2)
            file.write("\n")
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    print(f"Updated {filename}")


def main():
    tables = {
        "Chrome": (
            "chrome.py",
            "chrome_versions",
            ChromeVersions(n=HISTORICAL_MAJOR_COUNT).get_versions(),
        ),
        "Edge": (
            "edge.py",
            "edge_versions",
            EdgeVersions(n=HISTORICAL_MAJOR_COUNT).get_versions(),
        ),
        "Safari": (
            "safari.py",
            "safari_versions",
            AppleVersions(n=HISTORICAL_MAJOR_COUNT).safari_versions(),
        ),
    }

    for name, (_, _, data) in tables.items():
        _validate(name, data)
    for _, (filename, variable_name, data) in tables.items():
        save_py(filename, variable_name, data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
