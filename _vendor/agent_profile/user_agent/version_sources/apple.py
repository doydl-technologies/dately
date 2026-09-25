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

"""Retrieve released Safari versions from Apple documentation."""

import re

import requests


class AppleVersions:
    FROZEN_MACOS_UA_MAJOR = 14
    SAFARI_NOTES = (
        "https://developer.apple.com/tutorials/data/documentation/"
        "safari-release-notes.json"
    )
    _IDENT_END = re.compile(r"release-notes$")
    _VERSION_PATTERN = re.compile(
        r"safari(?:-[\w-]+)?-(\d+_\d+(?:_\d+)?)", re.IGNORECASE
    )

    def __init__(self, n=1):
        self.n = n

    def safari_versions(self):
        response = requests.get(
            self.SAFARI_NOTES,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        identifiers = [
            identifier
            for section in data.get("topicSections", [])
            for identifier in section.get("identifiers", [])
            if self._IDENT_END.search(identifier)
        ]
        versions = sorted(
            {
                match.group(1)
                for identifier in identifiers
                for match in (self._VERSION_PATTERN.search(identifier),)
                if match
            },
            key=lambda version: [int(part) for part in version.split("_")],
            reverse=True,
        )
        if not versions:
            raise RuntimeError("No Safari release versions were found.")

        grouped = {}
        for version in versions:
            major = version.split("_")[0]
            if int(major) >= self.FROZEN_MACOS_UA_MAJOR:
                grouped.setdefault(major, []).append(version)
        keep = sorted(grouped, key=int, reverse=True)[: self.n + 1]
        return {major: grouped[major] for major in keep}
