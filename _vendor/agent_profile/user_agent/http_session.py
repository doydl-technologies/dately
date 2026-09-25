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

"""Requests session that generates a coherent user agent for every request."""

import requests
from requests.structures import CaseInsensitiveDict

from .headers import HeaderProfile


_ROTATING_HEADER_NAMES = (
    "User-Agent",
    "Sec-CH-UA",
    "Sec-CH-UA-Mobile",
    "Sec-CH-UA-Platform",
)


class RotatingUserAgentSession(requests.Session):
    """Generate new user-agent headers for each explicit HTTP request."""

    def __init__(
        self,
        header_profile=None,
        force_distinct=True,
        generation_options=None,
    ):
        super().__init__()
        self.header_profile = header_profile or HeaderProfile()
        self.force_distinct = force_distinct
        self.generation_options = dict(generation_options or {})
        self.request_count = 0
        self.last_user_agent = None

    def request(self, method, url, **kwargs):
        """Apply a newly generated profile, then make and count the request."""
        generated = self.header_profile.random_headers(
            force_distinct=self.force_distinct,
            **self.generation_options,
        )
        headers = CaseInsensitiveDict(kwargs.pop("headers", {}) or {})
        for name in _ROTATING_HEADER_NAMES:
            headers.pop(name, None)
            if name in generated:
                headers[name] = generated[name]
        self.last_user_agent = generated["User-Agent"]
        kwargs["headers"] = headers
        self.request_count += 1
        return super().request(method, url, **kwargs)


__all__ = ["RotatingUserAgentSession"]
