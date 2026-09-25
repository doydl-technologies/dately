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

import requests
import re
from collections import defaultdict

# ──────────────────────────────────────────
# MICROSOFT EDGE
# ──────────────────────────────────────────
class EdgeVersions:
    RELNOTES_URL = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel"
    ARCHIVE_URL = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-archive-stable-channel"

    def __init__(self, input_version= None, n= 2):
        """
        :param input_version: target Edge version (e.g. "137.0.3296.68");
                              if None, get_versions() will fetch latest Stable for comparison.
        :param n: number of previous majors to include
        """
        self.input_version = input_version
        self.n = n

    def _fetch_html(self, url):
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text

    def _extract_versions(self, html):
        # Extract version info using regex (includes date if wanted)
        pattern = r"Version\s+(\d+\.\d+\.\d+\.\d+):"
        matches = re.findall(pattern, html)
        return matches

    def _get_all_versions(self):
        # Fetch both release notes and archive, combine, de-duplicate and sort
        html_current = self._fetch_html(self.RELNOTES_URL)
        html_archive = self._fetch_html(self.ARCHIVE_URL)
        versions = self._extract_versions(html_current) + self._extract_versions(html_archive)
        # Remove duplicates while keeping order (most recent first)
        seen = set()
        all_versions = []
        for v in versions:
            if v not in seen:
                all_versions.append(v)
                seen.add(v)
        # Sort versions in descending order
        all_versions.sort(key=lambda v: [int(x) for x in v.split('.')], reverse=True)
        return all_versions

    def _extract_versions_with_dates(self, html):
        pattern = r"Version\s+(\d+\.\d+\.\d+\.\d+):\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        matches = re.findall(pattern, html)
        return matches  # List of (version, date) tuples

    def _get_all_versions_with_dates(self):
        html_current = self._fetch_html(self.RELNOTES_URL)
        html_archive = self._fetch_html(self.ARCHIVE_URL)
        versions = self._extract_versions_with_dates(html_current) + self._extract_versions_with_dates(html_archive)
        # Remove duplicates by version, keep the first (most recent) date
        seen = {}
        for v, date in versions:
            if v not in seen:
                seen[v] = date
        # Sort by version descending
        all_versions = sorted(seen.items(), key=lambda x: [int(p) for p in x[0].split('.')], reverse=True)
        return all_versions

    def get_all_versions_by_major_with_dates(self):
        """
        Returns all versions as {major: [(version, date), ...]}
        """
        versions_with_dates = self._get_all_versions_with_dates()
        by_major = defaultdict(list)
        for version, date in versions_with_dates:
            major = version.split('.')[0]
            by_major[major].append((version, date))
        # Sort majors descending
        sorted_majors = sorted(by_major.keys(), key=int, reverse=True)
        return {major: by_major[major] for major in sorted_majors}

    def get_stable_version(self):
        """
        Return the latest Stable channel version string.
        """
        all_versions = self._get_all_versions()
        if not all_versions:
            raise RuntimeError("No Edge versions found on release notes pages.")
        return all_versions[0]  # The latest is first

    def get_versions(self):
        """
        Returns dict mapping major version → list of full versions for that major
        and the preceding n majors.
        """
        try:
            versions = self._get_all_versions()
        except requests.RequestException as error:
            return {"error": f"Failed to fetch Edge Stable releases: {error}"}
        if not versions:
            return {"error": "No Edge versions found."}

        # 2) Ensure we have an input_version
        if not self.input_version:
            self.input_version = versions[0]

        # 3) Parse major
        try:
            input_major = int(self.input_version.split('.')[0])
        except ValueError:
            return {"error": f"Invalid version format: {self.input_version}"}

        # 4) Organize all versions by major
        by_major = defaultdict(list)
        for v in versions:
            major = v.split('.')[0]
            by_major[major].append(v)

        majors = sorted({int(m) for m in by_major.keys()}, reverse=True)
        # 5) Find the closest major <= requested
        recent_major = next((m for m in majors if m <= input_major), None)
        if recent_major is None:
            return {"error": "No matching major found"}

        idx = majors.index(recent_major)
        selected_majors = majors[idx:idx + self.n + 1]

        result = {}
        for m in selected_majors:
            ms = str(m)
            result[ms] = by_major[ms]

        return result

    def get_all_versions_by_major(self):
        """
        Returns all versions as {major: [versions...]} with all available majors.
        """
        versions = self._get_all_versions()
        by_major = defaultdict(list)
        for v in versions:
            major = v.split('.')[0]
            by_major[major].append(v)
        # Sort the dictionary by descending major version
        sorted_majors = sorted(by_major.keys(), key=int, reverse=True)
        return {major: by_major[major] for major in sorted_majors}
