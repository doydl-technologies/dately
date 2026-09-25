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

chrome_versions = {
  "152": [
    "152.0.0.0"
  ],
  "151": [
    "151.0.0.0"
  ],
  "150": [
    "150.0.0.0"
  ],
  "149": [
    "149.0.0.0"
  ],
  "148": [
    "148.0.0.0"
  ],
  "147": [
    "147.0.0.0"
  ],
  "146": [
    "146.0.0.0"
  ],
  "145": [
    "145.0.0.0"
  ],
  "144": [
    "144.0.0.0"
  ],
  "143": [
    "143.0.0.0"
  ],
  "142": [
    "142.0.0.0"
  ],
  "141": [
    "141.0.0.0"
  ],
  "140": [
    "140.0.0.0"
  ],
  "139": [
    "139.0.0.0"
  ],
  "138": [
    "138.0.0.0"
  ],
  "137": [
    "137.0.0.0"
  ],
  "136": [
    "136.0.0.0"
  ],
  "135": [
    "135.0.0.0"
  ],
  "134": [
    "134.0.0.0"
  ],
  "133": [
    "133.0.0.0"
  ],
  "132": [
    "132.0.0.0"
  ],
  "131": [
    "131.0.0.0"
  ],
  "130": [
    "130.0.0.0"
  ],
  "129": [
    "129.0.0.0"
  ],
  "128": [
    "128.0.0.0"
  ],
  "127": [
    "127.0.0.0"
  ],
  "126": [
    "126.0.0.0"
  ],
  "125": [
    "125.0.0.0"
  ],
  "124": [
    "124.0.0.0"
  ],
  "123": [
    "123.0.0.0"
  ],
  "122": [
    "122.0.0.0"
  ],
  "121": [
    "121.0.0.0"
  ],
  "120": [
    "120.0.0.0"
  ],
  "119": [
    "119.0.0.0"
  ],
  "118": [
    "118.0.0.0"
  ],
  "117": [
    "117.0.0.0"
  ],
  "116": [
    "116.0.0.0"
  ],
  "115": [
    "115.0.0.0"
  ],
  "114": [
    "114.0.0.0"
  ],
  "113": [
    "113.0.0.0"
  ],
  "112": [
    "112.0.0.0"
  ],
  "111": [
    "111.0.0.0"
  ],
  "110": [
    "110.0.0.0"
  ],
  "109": [
    "109.0.0.0"
  ],
  "108": [
    "108.0.0.0"
  ],
  "107": [
    "107.0.0.0"
  ],
  "106": [
    "106.0.0.0"
  ],
  "105": [
    "105.0.0.0"
  ],
  "104": [
    "104.0.0.0"
  ],
  "103": [
    "103.0.0.0"
  ],
  "102": [
    "102.0.0.0"
  ],
  "101": [
    "101.0.0.0"
  ]
}
