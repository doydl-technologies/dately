<p align="center">
  <img src="https://github.com/cedricmoorejr/dately/blob/main/dately/assets/dately_logo.png" alt="Dately Logo" width="500"/>
</p>

# Date Parsing and Component Extraction Module

This module, currently available only for the Windows operating system, provides comprehensive functionalities for date parsing, detection, extraction, and conversion. It efficiently handles both individual dates and large arrays of dates, offering robust support for various input types including date strings, datetime objects, pandas Series, and NumPy arrays. The core functionalities include converting dates to specified formats or datetime objects, as well as parsing, detecting, and extracting date components. Leveraging regular expressions and NumPy, it processes dates with high speed and accuracy, ensuring consistent date handling across different platforms, specifically optimized for Windows environments.

## Key Feature:

A key part of this module is to address inconsistencies in Python's date formatting specifically for the Windows operating system. The module targets the handling of the '-' flag in date format specifiers. While the '-' flag, used to remove leading zeros from formatted output (e.g., turning '01' into '1' for January), works reliably on Unix-like systems, it does not function as intended on Windows. This discrepancy arises from the differing implementations of the underlying C libraries that Python relies on. For example, using a date format like '%Y-%-m-%d' on Windows results in Python not recognizing the specifier, leading to unexpected behaviors.

On Windows, where the feature to omit leading zeros using `%-m` in the `strftime()` and `strptime()` functions is unsupported, attempts to use such formats with inputs like '2024-3-01' can lead to misinterpretations, defaulting to '%Y-%m-%d', which retains the leading zero.

To solve this problem on Windows, this module introduces a workaround using regular expressions. It utilizes a detect function to determine the format string and then examines each date component for leading zeros through an extract_date_component function and a subsequent has_leading_zero check. Depending on the presence of leading zeros, the module adjusts the format string—replacing `%m` with `%-m` where applicable—to emulate the behavior expected from the '-' flag on Unix-like systems.

This method ensures that users on Windows achieve consistent date formatting, effectively compensating for the lack of native support for the '-' flag in date specifiers on this system.
