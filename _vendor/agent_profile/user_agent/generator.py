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

"""Generate realistic reduced desktop browser user-agent strings."""

import random

from .browser_versions.chrome import chrome_versions as chrome
from .browser_versions.edge import edge_versions as edge
from .browser_versions.safari import safari_versions as safari


class Normalize:
    """Utilities for manipulating dotted-decimal version strings."""

    def __init__(self, version):
        self.version = str(version).replace("_", ".")

    @staticmethod
    def _split(version_str):
        return version_str.split(".")

    @staticmethod
    def _join(parts):
        return ".".join(parts)

    @staticmethod
    def major(version_str, as_four=False):
        if not version_str or not version_str.strip():
            return ""
        major = Normalize._split(version_str)[0]
        return f"{major}.0.0.0" if as_four else major

    @staticmethod
    def ensure_four(version_str):
        parts = Normalize._split(version_str)
        while len(parts) < 4:
            parts.append("0")
        return Normalize._join(parts[:4])

    @staticmethod
    def strip_trailing_zeros(version_str):
        parts = Normalize._split(version_str)
        while len(parts) > 1 and parts[-1] == "0":
            parts.pop()
        return Normalize._join(parts)

    def as_major(self, as_four=False):
        return self.major(self.version, as_four=as_four)

    def as_four_part(self):
        return self.ensure_four(self.version)

    def compact(self):
        return self.strip_trailing_zeros(self.version)


class RandomUserAgent:
    """Build recent or age-weighted historical desktop user agents."""

    _CHROMIUM_PLATFORMS = {
        "windows": "Windows NT 10.0; Win64; x64",
        "macos": "Macintosh; Intel Mac OS X 10_15_7",
        "linux": "X11; Linux x86_64",
    }
    _SAFARI_PLATFORM = "Macintosh; Intel Mac OS X 10_15_7"
    _CHROMIUM_WEBKIT = "537.36"
    _SAFARI_WEBKIT = "605.1.15"
    _VERSION_PROFILES = ("recent", "historical")
    _EDGE_REDUCTION_MAJOR = 119

    def __init__(
        self,
        chrome_versions=chrome,
        edge_versions=edge,
        safari_versions=safari,
    ):
        self.chrome_versions = self._validate_versions("Chrome", chrome_versions)
        self.edge_versions = self._validate_versions("Edge", edge_versions)
        self.safari_versions = self._validate_versions(
            "Safari", safari_versions, allow_empty=True
        )

    @staticmethod
    def _validate_versions(name, versions, allow_empty=False):
        if allow_empty and not versions:
            return {}
        if not isinstance(versions, dict) or not versions or "error" in versions:
            raise ValueError(f"{name} version data is missing or invalid.")
        if any(not values for values in versions.values()):
            raise ValueError(f"{name} version data contains an empty version group.")
        return versions

    @staticmethod
    def _ordered_groups(versions):
        return sorted(versions.items(), key=lambda item: int(item[0]), reverse=True)

    @classmethod
    def _random_version(cls, versions, version_profile, recent_major_count):
        groups = cls._ordered_groups(versions)
        if version_profile == "recent":
            groups = groups[:recent_major_count]
            _, releases = random.choice(groups)
            return random.choice(releases)

        # Approximate an auto-updating desktop population: 65% current, 20%
        # previous, 10% spread across ranks 2-5, and 5% across older releases.
        if len(groups) == 1:
            return random.choice(groups[0][1])

        weights = []
        old_count = len(groups) - 6
        middle_weight = 2.5 if old_count > 0 else 15.0 / max(len(groups) - 2, 1)
        for rank, _ in enumerate(groups):
            if rank == 0:
                weights.append(65.0)
            elif rank == 1:
                weights.append(20.0)
            elif rank <= 5:
                weights.append(middle_weight)
            else:
                weights.append(5.0 / old_count)
        _, releases = random.choices(groups, weights=weights, k=1)[0]
        return random.choice(releases)

    @staticmethod
    def _reduced_version(version):
        return Normalize(version).as_major(as_four=True)

    def _chromium_platform(self, platform=None):
        if platform is None:
            platform = random.choice(list(self._CHROMIUM_PLATFORMS))
        try:
            return self._CHROMIUM_PLATFORMS[platform.lower()]
        except (AttributeError, KeyError):
            choices = ", ".join(self._CHROMIUM_PLATFORMS)
            raise ValueError(f"Chromium platform must be one of: {choices}.")

    def _generate_chrome(self, platform=None, version_profile="recent"):
        source_version = self._random_version(
            self.chrome_versions, version_profile, recent_major_count=3
        )
        version = self._reduced_version(source_version)
        os_token = self._chromium_platform(platform)
        return (
            f"Mozilla/5.0 ({os_token}) "
            f"AppleWebKit/{self._CHROMIUM_WEBKIT} (KHTML, like Gecko) "
            f"Chrome/{version} Safari/{self._CHROMIUM_WEBKIT}"
        )

    def _generate_edge(self, platform=None, version_profile="recent"):
        source_version = self._random_version(
            self.edge_versions, version_profile, recent_major_count=3
        )
        major = int(Normalize.major(source_version))
        chrome_version = self._reduced_version(source_version)
        edge_version = (
            self._reduced_version(source_version)
            if major >= self._EDGE_REDUCTION_MAJOR
            else Normalize.ensure_four(source_version)
        )
        os_token = self._chromium_platform(platform)
        return (
            f"Mozilla/5.0 ({os_token}) "
            f"AppleWebKit/{self._CHROMIUM_WEBKIT} (KHTML, like Gecko) "
            f"Chrome/{chrome_version} Safari/{self._CHROMIUM_WEBKIT} "
            f"Edg/{edge_version}"
        )

    def _generate_safari(self, version_profile="recent"):
        version = Normalize(
            self._random_version(
                self.safari_versions, version_profile, recent_major_count=2
            )
        ).version
        return (
            f"Mozilla/5.0 ({self._SAFARI_PLATFORM}) "
            f"AppleWebKit/{self._SAFARI_WEBKIT} (KHTML, like Gecko) "
            f"Version/{version} Safari/{self._SAFARI_WEBKIT}"
        )

    def generate(self, browser=None, platform=None, version_profile="recent"):
        """Return one user agent, optionally constrained by family and age profile."""
        if version_profile not in self._VERSION_PROFILES:
            raise ValueError(
                f"Version profile must be one of: {', '.join(self._VERSION_PROFILES)}."
            )
        families = ["chrome", "edge"]
        if self.safari_versions:
            families.append("safari")

        family = browser.lower() if isinstance(browser, str) else random.choice(families)
        if family not in families:
            raise ValueError(f"Browser must be one of: {', '.join(families)}.")
        if family == "safari" and platform not in (None, "macos"):
            raise ValueError("Desktop Safari user agents require the macos platform.")
        if family == "chrome":
            return self._generate_chrome(platform, version_profile)
        if family == "edge":
            return self._generate_edge(platform, version_profile)
        return self._generate_safari(version_profile)
