# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# `dately` is a precision-first library for parsing, interpreting, and normalizing time expressions
# across both structured data and natural language. Built for developers and data teams working in
# time-sensitive domains, it delivers deterministic behavior, high-performance parsing, and
# transparent reasoning around temporal meaning.
#
# Designed for integration into NLP pipelines, ETL processes, scheduling engines, and cross-platform
# applications, `dately` supports everything from ISO formats and user-generated timestamps to
# phrases like “next Friday” or “Q2 2025.” Its symbolic parser bridges the gap between language and
# logic, enabling interpretable, testable, and production-grade handling of ambiguous or implicit
# time references.
#
# Features include format inference, batch-safe transformations, timezone normalization, and a
# modular architecture for composable workflows. Whether you're resolving date strings in a chatbot
# or aligning logs across systems, `dately` brings clarity, consistency, and control to temporal data.
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




### Replacing Datestring
# Replacing year in a single date string
print(dtly.replace_datestring(datestring, year=2021))
# Output: '2021-06-21'
# Replacing month in a single date string
print(dtly.replace_datestring(datestring, month="5"))
# Output: '2023-5-21'
# Replacing day in a list of date strings
print(dtly.replace_datestring(datestring_list, day=6))
# Output: ['2023-06-6', '2024-06-6', '2024-07-6', '2024-08-6', '2024-09-6', '2024-10-6', '2024-11-6', '2024-12-6', '2025-01-6', '2025-02-6', '2025-03-6', '2025-04-6']
# Replacing day in a Pandas Series of date strings
print(dtly.replace_datestring(datestring_series, day="02"))
# Output:
# 0     2023-06-02
# 1     2024-06-02
# 2     2024-07-02
# 3     2024-08-02
# 4     2024-09-02
# 5     2024-10-02
# 6     2024-11-02
# 7     2024-12-02
# 8     2025-01-02
# 9     2025-02-02
# 10    2025-03-02
# 11    2025-04-02
# dtype: object


### Replacing Datetimestring
# Replacing time components in a single date string
print(dtly.replace_timestring(datestring))
# Output: '2023-06-21 15:17:47.50691'
print(dtly.replace_timestring(datestring, hour=13))
# Output: '2023-06-21 13:17:47.56700'
print(dtly.replace_timestring(datestring, hour="02"))
# Output: '2023-06-21 02:17:47.63773'
print(dtly.replace_timestring(datestring, hour="02", minute=11))
# Output: '2023-06-21 02:11:47.69779'
print(dtly.replace_timestring(datestring, hour="02", minute=10, second=44))
# Output: '2023-06-21 02:10:44.75777'
print(dtly.replace_timestring(datestring, hour="02", minute=10, second=44, microsecond=1))
# Output: '2023-06-21 02:10:44.00001'
print(dtly.replace_timestring(datestring, hour="02", minute=10, second=44, microsecond=1, time_indicator="AM"))
# Output: '2023-06-21 02:10:44.00001 AM'
# Replacing time components in an ISO date string
iso_datestring = "2023-06-21T12:30:00Z"
print(dtly.replace_timestring(iso_datestring, hour=2, minute=10, second=44, microsecond=1))
# Output: '2023-06-21T02:10:44.000001+00:00'
print(dtly.replace_timestring(iso_datestring, hour=2, minute=10, second=44, microsecond=1, tzinfo=3))
# Output: '2023-06-21T02:10:44.000001+03:00'

