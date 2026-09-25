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

import threading
import re
from urllib.parse import urljoin, urlparse
from collections import deque

from ._vendor.agent_profile import RandomUserAgent
from ._utils import is_leap_year, hundred_thousandths_place



class UserAgentRandomizer:
    """Return a realistic desktop user agent without recent duplicates."""

    _NO_REPEAT = 5
    _lock = threading.Lock()
    _recent = deque(maxlen=_NO_REPEAT)
    _generator = RandomUserAgent()

    @classmethod
    def get(cls) -> str:
        """Return a random User-Agent, avoiding recent repeats."""
        with cls._lock:
            agent = cls._generator.generate()
            while agent in cls._recent:
                agent = cls._generator.generate()
            cls._recent.append(agent)
            return agent

def is_valid_url(string):
    url_pattern = re.compile(
        r'^(https?|ftp):\/\/'  # protocol
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # port
        r'(?:\/?|[\/?]\S+)$', re.IGNORECASE)  # resource path

    # Use the pattern to check if the string matches a URL
    return re.match(url_pattern, string) is not None

def absolute_url(base_url, relative_path):
    """
    Constructs an absolute URL by combining a base URL with a relative URL.

    Args:
    - base_url (str): The base URL (e.g., "http://example.com").
    - relative_path (str): The relative URL to be joined with the base URL.

    Returns:
    - str: The absolute URL.
    """
    return urljoin(base_url, relative_path)

def find_os_in_user_agent(user_agent):
    os_dict = {
        "Windows": "Windows",
        "Macintosh": "macOS",
        "Linux": "Linux",
        "CrOS": "Chrome OS"}
    for key in os_dict:
        if key in user_agent:
            return os_dict[key]
    return None

def findhost(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme and parsed_url.netloc:
        return parsed_url.netloc
    elif not parsed_url.netloc and not parsed_url.scheme:
        return url
    else:
        parsed_url = urlparse('//'+url)
        return parsed_url.netloc




def __dir__():
    return [
        'is_leap_year',
        'hundred_thousandths_place',
        'UserAgentRandomizer',
        'find_os_in_user_agent',
        'findhost',
        ]

__all__ = [
    'is_leap_year',
    'hundred_thousandths_place',
    'UserAgentRandomizer',
    'find_os_in_user_agent',
    'findhost',
    ]




UserAgentRandomizer.get()
