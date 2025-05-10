<p align="center">
  <img src="https://raw.githubusercontent.com/cedricmoorejr/dately/main/dately/assets/py_dately_logo.png" alt="Dately Logo" width="700"/>
</p>


---

<div align="center">

# 📅 **dately** 📅

> **Comprehensive Date, Time **& Natural-Language** Handling in Python**

</div>


`dately` is an end-to-end date-and-time toolkit that now pairs its high-precision formatting utilities with a **mini natural-language-processing (NLP) engine**.  Whether you feed it an ISO-8601 timestamp, a plain month/day string, or a phrase like&nbsp;“second Tuesday of next quarter”, dately can turn it into an exact `datetime` object or `(start, end)` range.


[![Downloads](https://static.pepy.tech/badge/dately)](https://pepy.tech/project/dately)
[![Downloads](https://static.pepy.tech/badge/dately/month)](https://pepy.tech/project/dately)
[![Downloads](https://static.pepy.tech/badge/dately/week)](https://pepy.tech/project/dately)
[![Python](https://img.shields.io/pypi/pyversions/dately)](https://pypi.org/project/dately/)
[![PyPI](https://img.shields.io/pypi/v/dately)](https://pypi.org/project/dately/)
[![NLP Ready](https://img.shields.io/badge/NLP-enabled-brightgreen)]()
[![Powered by DOYDL Technologies](https://img.shields.io/badge/Powered%20by-DOYDL%20Technologies-blue)](https://doydl.com)
---

#### Table of Contents
1. [Why Choose dately?](#why-choose-dately)
2. [Key Features](#key-features)
3. [Solving Windows Date Formatting Issues](#solving-windows-date-formatting-issues)
4. [Usage Examples](#usage-examples)
      
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
To keep this README focused, all full-length usage examples are now available in the [`examples/`](https://github.com/cedricmoorejr/dately/tree/main/examples) folder.

You can explore them here:

- [Date Conversion & Formatting](examples/convert_dates.py)
- [Replacing Date Parts](examples/replace_datestring.py)
- [Time Zone Operations](examples/timezone_operations.py)
- [Natural Language Parsing (NLP)](examples/nlp_parsing.py)

Each file contains runnable code with expected outputs.
