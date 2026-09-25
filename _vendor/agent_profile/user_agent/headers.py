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

"""Build coherent HTTP header profiles around generated user agents."""

import re
import threading

from .generator import RandomUserAgent


class HeaderProfile:
    """Generate a desktop user agent and matching low-entropy client hints."""

    _PLATFORM_PATTERNS = (
        ("Windows", r"Windows NT "),
        ("macOS", r"Mac OS X "),
        ("Linux", r"X11; Linux "),
    )

    def __init__(self, ua_generator=None):
        self.ua_generator = ua_generator or RandomUserAgent()
        self._last_user_agent = None
        self._lock = threading.Lock()

    @staticmethod
    def _extract_browser_info(user_agent):
        edge = re.search(r"\bEdg/(\d+)", user_agent)
        chrome = re.search(r"\bChrome/(\d+)", user_agent)
        if edge and chrome:
            return "Microsoft Edge", edge.group(1), chrome.group(1)
        if chrome:
            return "Google Chrome", chrome.group(1), chrome.group(1)
        return None, None, None

    def _extract_platform(self, user_agent):
        for platform, pattern in self._PLATFORM_PATTERNS:
            if re.search(pattern, user_agent):
                return platform
        return None

    @staticmethod
    def build_sec_ch_ua(brand, brand_major, chromium_major):
        return (
            f'"Not_A Brand";v="99", "Chromium";v="{chromium_major}", '
            f'"{brand}";v="{brand_major}"'
        )

    def headers_for_ua(self, user_agent):
        brand, brand_major, chromium_major = self._extract_browser_info(user_agent)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Chromium sends these low-entropy hints by default. High-entropy hints,
        # such as platform version, require an Accept-CH response and are omitted.
        if brand:
            platform = self._extract_platform(user_agent)
            headers.update(
                {
                    "Sec-CH-UA": self.build_sec_ch_ua(
                        brand, brand_major, chromium_major
                    ),
                    "Sec-CH-UA-Mobile": "?0",
                }
            )
            if platform:
                headers["Sec-CH-UA-Platform"] = f'"{platform}"'
        return headers

    def random_headers(self, force_distinct=False, max_tries=5, **generate_options):
        """Return headers, optionally avoiding the immediately previous UA."""
        with self._lock:
            attempts = max(1, max_tries if force_distinct else 1)
            user_agent = None
            for _ in range(attempts):
                user_agent = self.ua_generator.generate(**generate_options)
                if not force_distinct or user_agent != self._last_user_agent:
                    break
            self._last_user_agent = user_agent
            return self.headers_for_ua(user_agent)


__all__ = ["HeaderProfile"]
