<p align="center">
  <img src="https://raw.githubusercontent.com/cedricmoorejr/dately/main/dately/assets/py_dately_logo.png" alt="Dately Logo" width="700"/>
</p>

### dately: Comprehensive Date, Time **& Natural-Language** Handling in Python

[![Downloads](https://static.pepy.tech/badge/dately)](https://pepy.tech/project/dately)
[![Downloads](https://static.pepy.tech/badge/dately/month)](https://pepy.tech/project/dately)
[![Downloads](https://static.pepy.tech/badge/dately/week)](https://pepy.tech/project/dately)

`dately` is an end-to-end date-and-time toolkit that now pairs its high-precision formatting utilities with a **mini natural-language-processing (NLP) engine**.  Whether you feed it an ISO-8601 timestamp, a plain month/day string, or a phrase like&nbsp;“second Tuesday of next quarter”, dately can turn it into an exact `datetime` object or `(start, end)` range.

#### Table of Contents
1. [Why Choose dately?](#why-choose-dately)
2. [Key Features](#key-features)
3. [Solving Windows Date Formatting Issues](#solving-windows-date-formatting-issues)
4. [Usage Examples - Working with Date Strings](#usage-examples---working-with-date-strings)
    - [Importing the Module](#importing-the-module)
    - [Extracting Datetime Components](#extracting-datetime-components)
    - [Detecting Datetime Formats](#detecting-datetime-formats)
    - [Converting Dates](#converting-dates)
    - [Converting Dates in Dictionaries](#converting-dates-in-dictionaries)
    - [Replacing Datestring](#replacing-datestring)
    - [Replacing Datetimestring](#replacing-datetimestring)
5. [Working with Time Zones](#working-with-time-zones)
    - [Retrieving Time Zone Information](#retrieving-time-zone-information)
    - [Time Zone Operations](#time-zone-operations)
6. [Natural Language Parsing (NLP)](#natural-language-parsing-nlp)
    - [Overview](#overview)
    - [Basic Usage](#basic-usage)
    - [Phrase Examples](#phrase-examples)
    - [Customizing Week Start](#customizing-week-start)
      
#### Why Choose dately?
- **Windows Optimized** – fixes `%‐m`/#zero-suppression inconsistencies on Windows.
- **NLP Inside** – understands expressions such as “last 5 weekends”, “Q4 2026”, “3 days ago starting from April 10”.
- **Comprehensive API** – parsing, detection, extraction and conversion for raw strings, `datetime` objects, pandas Series, NumPy arrays **and** free-text phrases.
- **High Performance** – Python + Cython hot-paths for heavy string/date workloads.

#### Key Features
1. **Date and Time Format Detection**:
   - Automatically detect various date and time formats from strings, ensuring seamless parsing and conversion.
   - Supports a wide range of date formats, including standard and unique custom formats.
2. **Timezone Management**:
   - Provides detailed information for specific time zones.
   - Converts time from one time zone to another.
   - Retrieves the current time for specific time zones.
   - Categorizes time zones by country, offset, and daylight saving time observance.
3. **String Manipulation and Validation**:
   - Extract specific components (year, month, day, hour, minute, second, timezone) from datetime strings.
   - Validate and replace parts of datetime strings to ensure accuracy and consistency.
   - Strip time and timezone information from datetime strings when needed.
4. **Performance Optimizations**:
   - Utilizes Cython to enhance performance for computationally intensive tasks.
   - Interfaces with underlying C code to perform high-speed string operations and date validations.
5. **Natural-Language Parsing**  *(new!)*  
   - _Relative phrases_ `"next 2 Fridays" → [date, date]`  
   - _Range phrases_ `"first half of last year"`  
   - _Anchored clauses_ `"start of Q3 2024"`  
   - _Token normalisation_ (cardinal ↔︎ ordinal words, plural handling, etc.)  
   - Rule-based NLP pipeline: tokenisation → normalisation → pattern matching → date algebra.

#### Solving Windows Date Formatting Issues
A key aspect of this module is addressing inconsistencies in Python's date formatting on the Windows operating system. The module specifically targets the handling of the hyphen-minus (-) in date format specifiers. This flag, used to remove leading zeros from formatted output (e.g., turning '01' into '1' for January), works reliably on Unix-like systems but does not function as intended on Windows.

To solve this problem on Windows, the `dately` module introduces a workaround using regular expressions. It utilizes a detection function to determine the format string and then examines each date component for leading zeros through an extract_date_component function and a subsequent has_leading_zero check. Depending on the presence of leading zeros, the module adjusts the format string-replacing `%m` with `%-m` where applicable-to emulate the behavior expected from the hyphen-minus on Unix-like systems.

This method ensures that users on Windows achieve consistent date formatting, effectively compensating for the lack of native support for the hyphen-minus in date specifiers on this system.

Overall, `dately` is a powerful utility for anyone needing precise and flexible date and time handling in their applications, making it easier to manage, format, and validate date and time data consistently and efficiently.


## Usage Examples - Working with Date Strings
### Importing the Module
```python
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
```

---
### Extracting Datetime Components
#### Single Date String
```python
print(dtly.dt.extract_datetime_component(datestring, "year"))
# Output: '2023'
print(dtly.dt.extract_datetime_component(datestring, "day"))
# Output: '21'
print(dtly.dt.extract_datetime_component(datestring, "month"))
# Output: '06'
```

#### List of Date Strings
```python
print(dtly.dt.extract_datetime_component(datestring_list, "year"))
# Output: ['2023', '2024', '2024', '2024', '2024', '2024', '2024', '2024', '2025', '2025', '2025', '2025']
print(dtly.dt.extract_datetime_component(datestring_list, "day"))
# Output: ['21', '21', '21', '20', '19', '19', '18', '18', '17', '16', '18', '17']
print(dtly.dt.extract_datetime_component(datestring_list, "month"))
# Output: ['06', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04']
```

#### NumPy Array of Date Strings
```python
print(dtly.dt.extract_datetime_component(datestring_array, "year"))
# Output: array(['2023', '2024', '2024', '2024', '2024', '2024', '2024', '2024', '2025', '2025', '2025', '2025'], dtype=object)
print(dtly.dt.extract_datetime_component(datestring_array, "day"))
# Output: array(['21', '21', '21', '20', '19', '19', '18', '18', '17', '16', '18', '17'], dtype=object)
print(dtly.dt.extract_datetime_component(datestring_array, "month"))
# Output: array(['06', '06', '07', '08', '09', '10', '11', '12', '01', '02', '03', '04'], dtype=object)
```

#### Pandas Series of Date Strings
```python
print(dtly.dt.extract_datetime_component(datestring_series, "year"))
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
print(dtly.dt.extract_datetime_component(datestring_series, "day"))
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
print(dtly.dt.extract_datetime_component(datestring_series, "month"))
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
```


---
### Detecting Datetime Formats
#### Single Date String
```python
print(dtly.dt.detect_date_format(datestring))
# Output: '%Y-%m-%d'
```
#### List of Date Strings
```python
print(dtly.dt.detect_date_format(datestring_list))
# Output: ['%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d']
```
#### NumPy Array of Date Strings
```python
print(dtly.dt.detect_date_format(datestring_array))
# Output: array(['%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m-%d'], dtype=object)
```
#### Pandas Series of Date Strings
```python
print(dtly.dt.detect_date_format(datestring_series))
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
```
---
### Converting Dates
```python
# Converting a single date string
print(dtly.dt.convert_date(datestring, to_format='%m.%Y/%d %I:%M %p', delta=1))
# Output: '06.2023/22 12:00 AM'
# Converting a list of date strings
print(dtly.dt.convert_date(datestring_list, to_format='%Y/%m/%d %I:%M:%S %p'))
# Output: ['2023/06/21 12:00:00 AM', '2024/06/21 12:00:00 AM', '2024/07/21 12:00:00 AM', '2024/08/20 12:00:00 AM', '2024/09/19 12:00:00 AM', '2024/10/19 12:00:00 AM', '2024/11/18 12:00:00 AM', '2024/12/18 12:00:00 AM', '2025/01/17 12:00:00 AM', '2025/02/16 12:00:00 AM', '2025/03/18 12:00:00 AM', '2025/04/17 12:00:00 AM']
# Converting a NumPy array of date strings
print(dtly.dt.convert_date(datestring_array, to_format='%y/%m-%d %H:%M'))
# Output: array(['23/06-21 00:00', '24/06-21 00:00', '24/07-21 00:00', '24/08-20 00:00', '24/09-19 00:00', '24/10-19 00:00', '24/11-18 00:00', '24/12-18 00:00', '25/01-17 00:00', '25/02-16 00:00', '25/03-18 00:00', '25/04-17 00:00'], dtype=object)
# Converting a Pandas Series of date strings
print(dtly.dt.convert_date(datestring_series, to_format='%Y.%m.%d'))
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
```
---
### Converting Dates in Dictionaries
```python
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
converted_dict = dtly.dt.convert_date(sample_dict, to_format='%Y/%m', dict_keys=["meeting_date", "date", "session_dates"])
print(converted_dict)
# Output:
# {'event': {'name': 'Annual Conference', 'dates': {'start_date': '2024-01-15', 'end_date': '2024-01-20'}, 'registration': {'open_date': '2023-11-01', 'close_date': '2023-12-30'}}, 'meetings': [{'title': 'Planning Meeting', 'meeting_date': '2023/10'}, {'title': 'Review Meeting', 'meeting_date': '2023/10'}], 'webinars': [{'topic': 'Introduction to the Event', 'session_dates': ['2023/11', '2023/11']}], 'workshops': {'sessions': [{'session_name': 'Workshop 1', 'date': '2024/01'}, {'session_name': 'Workshop 2', 'date': '2024/01'}]}}
```
---
### Replacing Datestring
```python
# Replacing year in a single date string
print(dtly.dt.replace_datestring(datestring, year=2021))
# Output: '2021-06-21'
# Replacing month in a single date string
print(dtly.dt.replace_datestring(datestring, month="5"))
# Output: '2023-5-21'
# Replacing day in a list of date strings
print(dtly.dt.replace_datestring(datestring_list, day=6))
# Output: ['2023-06-6', '2024-06-6', '2024-07-6', '2024-08-6', '2024-09-6', '2024-10-6', '2024-11-6', '2024-12-6', '2025-01-6', '2025-02-6', '2025-03-6', '2025-04-6']
# Replacing day in a Pandas Series of date strings
print(dtly.dt.replace_datestring(datestring_series, day="02"))
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
```
---
### Replacing Datetimestring
```python
# Replacing time components in a single date string
print(dtly.dt.replace_timestring(datestring))
# Output: '2023-06-21 15:17:47.50691'
print(dtly.dt.replace_timestring(datestring, hour=13))
# Output: '2023-06-21 13:17:47.56700'
print(dtly.dt.replace_timestring(datestring, hour="02"))
# Output: '2023-06-21 02:17:47.63773'
print(dtly.dt.replace_timestring(datestring, hour="02", minute=11))
# Output: '2023-06-21 02:11:47.69779'
print(dtly.dt.replace_timestring(datestring, hour="02", minute=10, second=44))
# Output: '2023-06-21 02:10:44.75777'
print(dtly.dt.replace_timestring(datestring, hour="02", minute=10, second=44, microsecond=1))
# Output: '2023-06-21 02:10:44.00001'
print(dtly.dt.replace_timestring(datestring, hour="02", minute=10, second=44, microsecond=1, time_indicator="AM"))
# Output: '2023-06-21 02:10:44.00001 AM'
# Replacing time components in an ISO date string
iso_datestring = "2023-06-21T12:30:00Z"
print(dtly.dt.replace_timestring(iso_datestring, hour=2, minute=10, second=44, microsecond=1))
# Output: '2023-06-21T02:10:44.000001+00:00'
print(dtly.dt.replace_timestring(iso_datestring, hour=2, minute=10, second=44, microsecond=1, tzinfo=3))
# Output: '2023-06-21T02:10:44.000001+03:00'
```

## Working with Time Zones
### Retrieving Time Zone Information
```python
# Get the list of country codes
dtly.TimeZoner.CountryCodes
# Output: ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX'.....]
```
```python
# Get the list of country names
dtly.TimeZoner.CountryNames
# Output: ['Afghanistan', 'Aland Islands', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica'.....]
```
```python
# Get the list of time zones
dtly.TimeZoner.Zones
# Output: ['Africa/Abidjan', 'Africa/Accra', 'Africa/Addis_Ababa', 'Africa/Algiers', 'Africa/Asmara', 'Africa/Bamako', 'Africa/Bangui'.....] 
```
```python
# Get time zones by country
dtly.TimeZoner.ZonesByCountry
# Output: {'CI': ['Africa/Abidjan'], 'GH': ['Africa/Accra'], 'ET': ['Africa/Addis_Ababa'].....]}
```
```python
# Get time zones by DST observance
dtly.TimeZoner.ObservesDST
# Output: {'observes_dst': ['Africa/Casablanca', 'Africa/Ceuta', 'Africa/El_Aaiun'.....]}
```
```python
# Get time zones by offset
dtly.TimeZoner.Offsets
# Output: {'+00:00': ['Africa/Abidjan', 'Africa/Accra', 'Africa/Bamako'.....], '+03:00': ['Africa/Addis_Ababa', 'Africa/Asmara'.....], '-09:00': ['America/Adak', 'Pacific/Gambier'.....], '-08:00': ['America/Anchorage'.....]}
```
---
### Time Zone Operations
```python
# Retrieve detailed information for a specific time zone
dtly.TimeZoner.FilterZoneDetail('America/Denver')
# Output: {'countryCode': 'US', 'countryName': 'United States', 'Offset': '-06:00', 'UTC offset (STD)': '-07:00', 'UTC offset (DST)': '-06:00', 'Abbreviation (STD)': 'MST', 'Abbreviation (DST)': 'MDT'}
```
```python
# Get the current time for a specific time zone
dtly.TimeZoner.CurrentTimebyZone('Australia/Adelaide')
# Output: '2024-07-02T04:32:05.642329+09:30'
```
```python
# Convert time from one time zone to another
from_zone = 'Africa/Ceuta'
to_zone = 'America/Anchorage'
dtly.TimeZoner.ConvertTimeZone(from_zone, to_zone, year=2024, month=5, day=22, hour=12, minute=13, second=22)
# Output: [{'countryCode': 'ES', 'countryName': 'Spain', 'zoneName': 'Africa/Ceuta', 'gmtOffset': 7200, 'timestamp': 1719865256}, {'countryCode': 'US', 'countryName': 'United States', 'zoneName': 'America/Anchorage', 'gmtOffset': -28800, 'timestamp': 1719829256}]
```

## Natural Language Parsing (NLP)

### Overview

dately's new NLP engine allows you to interpret and resolve **free-text temporal expressions** into real calendar dates. It supports a wide range of grammar structures and handles expressions like:

* `"2nd Monday of next month"`
* `"last 3 weekends"`
* `"Q2 2026"`
* `"5 days ago"`
* `"middle of this year"`
* `"next 6 weeks starting from March 15"`

Behind the scenes, it uses rule-based grammars, temporal math, and context-aware resolution anchored to today's date (or a custom one you provide).

---

### Basic Usage

```python
import dately as dtly 

# Parse natural phrases into exact dates or date ranges
dtly.parse("first Monday of next month")

# → datetime.date(2024, 6, 3)
dtly.parse("last 5 weekends")
# → [(start_date_1, end_date_1), ..., (start_date_5, end_date_5)]
```

---

### Phrase Examples

| Expression                       | Output                       |
| -------------------------------- | ---------------------------- |
| `"3 days ago"`                   | `datetime.date(2024, 4, 29)` |
| `"start of next quarter"`        | `(2024-07-01, 2024-09-30)`   |
| `"next 2 Fridays"`               | `[date1, date2]`             |
| `"middle of last year"`          | `datetime.date(2023, 7, 1)`  |
| `"start of the 2nd week of May"` | `(2024-05-06, 2024-05-12)`   |


---

### Customizing Week Start

Control which day is considered the start of the week (default = Sunday):

```python
import dately as dtly 

dtly.set_week_start("monday")  # affects “this week”, “last 3 weekends”, etc.
```



