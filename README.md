<p align="center">
  <img src="https://raw.githubusercontent.com/cedricmoorejr/dately/main/dately/assets/dately_logo.png" alt="Dately Logo" style="max-width: 100%; height: auto;"/>
</p>


Dately Library: Comprehensive Date and Time Handling in Python

The `dately` module is a comprehensive library designed for advanced date and time manipulation. It offers extensive capabilities to handle various date and time formats, ensuring compatibility across different systems and data structures. The module provides tools for validating, extracting, and transforming date and time information with a focus on performance and accuracy.

#### Why Choose Dately?

- **Windows Optimized**: Specifically addresses inconsistencies in Python's date formatting on the Windows operating system.
- **Comprehensive Functionalities**: Supports date parsing, detection, extraction, and conversion for various input types, including date strings, datetime objects, pandas Series, and NumPy arrays.
- **High Performance**: Leverages both high-level Python and low-level C code (via Cython) for efficient operations.

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

#### Solving Windows Date Formatting Issues

A key aspect of this module is addressing inconsistencies in Python's date formatting on the Windows operating system. The module specifically targets the handling of the hyphen-minus (-) in date format specifiers. This flag, used to remove leading zeros from formatted output (e.g., turning '01' into '1' for January), works reliably on Unix-like systems but does not function as intended on Windows.

To solve this problem on Windows, the `dately` module introduces a workaround using regular expressions. It utilizes a detection function to determine the format string and then examines each date component for leading zeros through an extract_date_component function and a subsequent has_leading_zero check. Depending on the presence of leading zeros, the module adjusts the format string-replacing `%m` with `%-m` where applicable-to emulate the behavior expected from the hyphen-minus on Unix-like systems.

This method ensures that users on Windows achieve consistent date formatting, effectively compensating for the lack of native support for the hyphen-minus in date specifiers on this system.

Overall, `dately` is a powerful utility for anyone needing precise and flexible date and time handling in their applications, making it easier to manage, format, and validate date and time data consistently and efficiently.
