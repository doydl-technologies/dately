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

"""Retrieve recent Chrome Stable majors for reduced user-agent strings."""

import requests


class ChromeVersions:
    UA_REDUCTION_MAJOR = 101
    STABLE_URL = (
        "https://googlechromelabs.github.io/chrome-for-testing/"
        "last-known-good-versions.json"
    )

    def __init__(self, input_version=None, n=2):
        self.input_version = input_version
        self.n = n

    @staticmethod
    def _fetch_json(url):
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_stable_version(self):
        data = self._fetch_json(self.STABLE_URL)
        return data["channels"]["Stable"]["version"]

    def get_versions(self):
        """Return the current Stable major and ``n`` preceding reduced majors."""
        try:
            version = self.input_version or self.get_stable_version()
            stable_major = int(str(version).split(".")[0])
        except (KeyError, TypeError, ValueError, requests.RequestException) as error:
            return {"error": f"Failed to determine Chrome Stable: {error}"}

        return {
            str(major): [f"{major}.0.0.0"]
            for major in range(stable_major, stable_major - self.n - 1, -1)
            if major >= self.UA_REDUCTION_MAJOR
        }
