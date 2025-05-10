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



### Extracting Datetime Components
#### Single Date String
print(dtly.extract_datetime_component(datestring, "year"))
# Output: '2023'
print(dtly.extract_datetime_component(datestring, "day"))
# Output: '21'
print(dtly.extract_datetime_component(datestring, "month"))
# Output: '06'


#### List of Date Strings
print(dtly.extract_datetime_component(datestring_list, "year"))
# Output: ['2023', '2024', '2024', '2024', '2024', '2024', '2024', '2024', '2025', '2025', '2025', '2025']
print(dtly.extract_datetime_component(datestring_list, "day"))
# Output: ['21', '21', '21', '20', '19', '19', '18', '18', '17', '16', '18', '17']
print(dtly.extract_datetime_component(datestring_list, "month"))
# Output: ['06', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04']


#### NumPy Array of Date Strings
print(dtly.extract_datetime_component(datestring_array, "year"))
# Output: array(['2023', '2024', '2024', '2024', '2024', '2024', '2024', '2024', '2025', '2025', '2025', '2025'], dtype=object)
print(dtly.extract_datetime_component(datestring_array, "day"))
# Output: array(['21', '21', '21', '20', '19', '19', '18', '18', '17', '16', '18', '17'], dtype=object)
print(dtly.extract_datetime_component(datestring_array, "month"))
# Output: array(['06', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04'], dtype=object)


#### Pandas Series of Date Strings
print(dtly.extract_datetime_component(datestring_series, "year"))
# Output:
# 0     2023
# 1     2024
# 2     2024
# 3     2024
# 4     2024
# 5     2024
# 6     2024
# 7     2024
# 8     2025
# 9     2025
# 10    2025
# 11    2025
# dtype: object
print(dtly.extract_datetime_component(datestring_series, "day"))
# Output:
# 0     21
# 1     21
# 2     21
# 3     20
# 4     19
# 5     19
# 6     18
# 7     18
# 8     17
# 9     16
# 10    18
# 11    17
# dtype: object
print(dtly.extract_datetime_component(datestring_series, "month"))
# Output:
# 0     06
# 1     06
# 2     07
# 3     08
# 4     09
# 5     10
# 6     11
# 7     12
# 8     01
# 9     02
# 10    03
# 11    04
# dtype: object




### Detecting Datetime Formats
#### Single Date String
print(dtly.detect_date_format(datestring))
# Output: '%Y-%m-%d'

#### List of Date Strings
print(dtly.detect_date_format(datestring_list))
# Output: ['%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d']

#### NumPy Array of Date Strings
print(dtly.detect_date_format(datestring_array))
# Output: array(['%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d'], dtype=object)

#### Pandas Series of Date Strings
print(dtly.detect_date_format(datestring_series))
# Output:
# 0     %Y-%m-%d
# 1     %Y-%m-%d
# 2     %Y-%m-%d
# 3     %Y-%m-%d
# 4     %Y-%m-%d
# 5     %Y-%m-%d
# 6     %Y-%m-%d
# 7     %Y-%m-%d
# 8     %Y-%m-%d
# 9     %Y-%m-%d
# 10    %Y-%m-%d
# 11    %Y-%m-%d
# dtype: object


### Converting Dates
# Converting a single date string
print(dtly.convert_date(datestring, to_format='%m.%Y/%d %I:%M %p', delta=1))
# Output: '06.2023/22 12:00 AM'
# Converting a list of date strings
print(dtly.convert_date(datestring_list, to_format='%Y/%m/%d %I:%M:%S %p'))
# Output: ['2023/06/21 12:00:00 AM', '2024/06/21 12:00:00 AM', '2024/07/21 12:00:00 AM', '2024/08/20 12:00:00 AM', '2024/09/19 12:00:00 AM', '2024/10/19 12:00:00 AM', '2024/11/18 12:00:00 AM', '2024/12/18 12:00:00 AM', '2025/01/17 12:00:00 AM', '2025/02/16 12:00:00 AM', '2025/03/18 12:00:00 AM', '2025/04/17 12:00:00 AM']
# Converting a NumPy array of date strings
print(dtly.convert_date(datestring_array, to_format='%y/%m-%d %H:%M'))
# Output: array(['23/06-21 00:00', '24/06-21 00:00', '24/07-21 00:00', '24/08-20 00:00', '24/09-19 00:00', '24/10-19 00:00', '24/11-18 00:00', '24/12-18 00:00', '25/01-17 00:00', '25/02-16 00:00', '25/03-18 00:00', '25/04-17 00:00'], dtype=object)
# Converting a Pandas Series of date strings
print(dtly.convert_date(datestring_series, to_format='%Y.%m.%d'))
# Output:
# 0     2023.06.21
# 1     2024.06.21
# 2     2024.07.21
# 3     2024.08.20
# 4     2024.09.19
# 5     2024.10.19
# 6     2024.11.18
# 7     2024.12.18
# 8     2025.01.17
# 9     2025.02.16
# 10    2025.03.18
# 11    2025.04.17
# dtype: object


### Converting Dates in Dictionaries
# Sample dictionary with dates
sample_dict = {
    "event": {
        "name": "Annual Conference",
        "dates": {
            "start_date": "2024-01-15",
            "end_date": "2024-01-20"
        },
        "registration": {
            "open_date": "2023-11-01",
            "close_date": "2023-12-30"
        }
    },
    "meetings": [
        {
            "title": "Planning Meeting",
            "meeting_date": "2023-10-01"
        },
        {
            "title": "Review Meeting",
            "meeting_date": "2023-10-15"
        }
    ],
    "webinars": [
        {
            "topic": "Introduction to the Event",
            "session_dates": [
                "2023-11-10",
                "2023-11-17"
            ]
        }
    ],
    "workshops": {
        "sessions": [
            {
                "session_name": "Workshop 1",
                "date": "01/01/2024"
            },
            {
                "session_name": "Workshop 2",
                "date": "2024-01-18"
            }
        ]
    }
}
# Converting dates in a dictionary
converted_dict = dtly.convert_date(sample_dict, to_format='%Y/%m', dict_keys=["meeting_date", "date", "session_dates"])
print(converted_dict)
# Output:
# {'event': {'name': 'Annual Conference', 'dates': {'start_date': '2024-01-15', 'end_date': '2024-01-20'}, 'registration': {'open_date': '2023-11-01', 'close_date': '2023-12-30'}}, 'meetings': [{'title': 'Planning Meeting', 'meeting_date': '2023/10'}, {'title': 'Review Meeting', 'meeting_date': '2023/10'}], 'webinars': [{'topic': 'Introduction to the Event', 'session_dates': ['2023/11', '2023/11']}], 'workshops': {'sessions': [{'session_name': 'Workshop 1', 'date': '2024/01'}, {'session_name': 'Workshop 2', 'date': '2024/01'}]}}


