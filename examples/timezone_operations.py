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



## Working with Time Zones
### Retrieving Time Zone Information

# Get the list of country codes
dtly.TimeZoner.CountryCodes
# Output: ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX'.....]


# Get the list of country names
dtly.TimeZoner.CountryNames
# Output: ['Afghanistan', 'Aland Islands', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica'.....]


# Get the list of time zones
dtly.TimeZoner.Zones
# Output: ['Africa/Abidjan', 'Africa/Accra', 'Africa/Addis_Ababa', 'Africa/Algiers', 'Africa/Asmara', 'Africa/Bamako', 'Africa/Bangui'.....] 


# Get time zones by country
dtly.TimeZoner.ZonesByCountry
# Output: {'CI': ['Africa/Abidjan'], 'GH': ['Africa/Accra'], 'ET': ['Africa/Addis_Ababa'].....]}


# Get time zones by DST observance
dtly.TimeZoner.ObservesDST
# Output: {'observes_dst': ['Africa/Casablanca', 'Africa/Ceuta', 'Africa/El_Aaiun'.....]}


# Get time zones by offset
dtly.TimeZoner.Offsets
# Output: {'+00:00': ['Africa/Abidjan', 'Africa/Accra', 'Africa/Bamako'.....], '+03:00': ['Africa/Addis_Ababa', 'Africa/Asmara'.....], '-09:00': ['America/Adak', 'Pacific/Gambier'.....], '-08:00': ['America/Anchorage'.....]}


### Time Zone Operations

# Retrieve detailed information for a specific time zone
dtly.TimeZoner.FilterZoneDetail('America/Denver')
# Output: {'countryCode': 'US', 'countryName': 'United States', 'Offset': '-06:00', 'UTC offset (STD)': '-07:00', 'UTC offset (DST)': '-06:00', 'Abbreviation (STD)': 'MST', 'Abbreviation (DST)': 'MDT'}


# Get the current time for a specific time zone
dtly.TimeZoner.CurrentTimebyZone('Australia/Adelaide')
# Output: '2024-07-02T04:32:05.642329+09:30'


# Convert time from one time zone to another
from_zone = 'Africa/Ceuta'
to_zone = 'America/Anchorage'
dtly.TimeZoner.ConvertTimeZone(from_zone, to_zone, year=2024, month=5, day=22, hour=12, minute=13, second=22)
# Output: [{'countryCode': 'ES', 'countryName': 'Spain', 'zoneName': 'Africa/Ceuta', 'gmtOffset': 7200, 'timestamp': 1719865256}, {'countryCode': 'US', 'countryName': 'United States', 'zoneName': 'America/Anchorage', 'gmtOffset': -28800, 'timestamp': 1719829256}]

