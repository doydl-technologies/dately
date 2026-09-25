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

### Importing the Module

# Import module
import dately as dtly

# Additional imports for examples
import pandas as pd
import numpy as np

# Set variables
datestring = "2023-06-21"
datestring_list = [
    '2023-06-21', '2024-06-21', '2024-07-21', '2024-08-20',
    '2024-09-19', '2024-10-19', '2024-11-18', '2024-12-18',
    '2025-01-17', '2025-02-16', '2025-03-18', '2025-04-17'
]
datestring_array = np.array(datestring_list)
datestring_series = pd.Series(datestring_list)


## Natural Language Parsing (NLP)

# dately's NLP engine interprets and resolve **free-text temporal expressions** into real calendar dates. It supports a wide range of grammar structures and handles expressions like:
#
# * `"2nd Monday of next month"`
# * `"last 3 weekends"`
# * `"Q2 2026"`
# * `"5 days ago"`
# * `"middle of this year"`
# * `"next 6 weeks starting from March 15"`
# Behind the scenes, it uses rule-based grammars, temporal math, and context-aware resolution anchored to today's date (or a custom one you provide).



### Basic Usage
# Parse natural phrases into exact dates or date ranges
dtly.parse("first Monday of next month")

# → datetime.date(2024, 6, 3)
dtly.parse("last 5 weekends")
# → [(start_date_1, end_date_1), ..., (start_date_5, end_date_5)]


### Customizing Week Start
# Control which day is considered the start of the week (default = Sunday):
dtly.set_week_start("monday")  # affects “this week”, “last 3 weekends”, etc.

