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

safari_versions = {
  "26": [
    "26_6",
    "26_5",
    "26_4",
    "26_3",
    "26_2",
    "26_1"
  ],
  "18": [
    "18_6",
    "18_5",
    "18_4",
    "18_3",
    "18_2",
    "18_1",
    "18_0_1"
  ],
  "17": [
    "17_6",
    "17_5",
    "17_4",
    "17_3",
    "17_2",
    "17_1"
  ],
  "16": [
    "16_6",
    "16_5",
    "16_4",
    "16_3",
    "16_2",
    "16_1"
  ],
  "15": [
    "15_6",
    "15_5",
    "15_4",
    "15_2"
  ],
  "14": [
    "14_1"
  ]
}
