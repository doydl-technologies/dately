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

import numpy as np
import pandas as pd
from copy import deepcopy
from datetime import datetime as dt, timedelta as td, date as d

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._log import logger   	
from ._datetime_scan import DateTimeScan
from ._temporal_scan import parse_temporal    
from ._timeutils import (
    strTime, validate_date, make_datetime_string, replace_time_by_position,
    remove_marker, exist_meridiem, validate_timezone,
    datetime_offset, _stripTimeIndicator
)
from .mold.pyd.cdatetime.UniversalDateFormatter import (
    zero_handling_date_formats, has_leading_zero,
    date_format_leading_zero, replace_non_padded_with_padded
)
from .mold.pyd.cdatetime.iso8601T import isISOT as is_iso_date
from .mold.pyd.cdatetime.iso8601Z import replaceZ
from .mold.pyd.clean_str import *
from .mold.pyd.Compiled import (
    datetime_regex as datetime_pattern_search,
    anytime_regex,
    timemeridiem_regex,
    timeboundary_regex,
    time_only_regex,
    iana_timezone_identifier_regex,
    timezone_offset_regex,
    timezone_abbreviation_regex,
    full_timezone_name_regex
)



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

# Debug mode toggle
DEBUG_MODE = False

def _apply_to_data(data, func, vectorize_excluded=None, *func_args, **func_kwargs):
    """
    A single helper to apply `func` to `data`, where `data` can be
    str, list, np.ndarray, or pd.Series.
    """
    # (Optional) default for vectorize_excluded
    if vectorize_excluded is None:
        vectorize_excluded = []

    # 1) STRING
    if isinstance(data, str):
        return func(data, *func_args, **func_kwargs)

    # 2) LIST
    elif isinstance(data, list):
        return [func(item, *func_args, **func_kwargs) for item in data]

    # 3) NUMPY ARRAY
    elif isinstance(data, np.ndarray):
        # We create a vectorized version of `func`.
        vec_func = np.vectorize(
            lambda x: func(x, *func_args, **func_kwargs),
            excluded=vectorize_excluded,
            otypes=[object]
        )
        return vec_func(data)

    # 4) PANDAS SERIES
    elif isinstance(data, pd.Series):
        # Convert to str:
        data = data.astype(str)
        return data.apply(lambda x: func(x, *func_args, **func_kwargs))

    # 5) If none match, raise
    else:
        raise ValueError(
            "Unsupported data type. Must be str, list, np.ndarray, or pd.Series."
        )

#────────────────────────────────────────────────────────────────────────────
# HELPER: if user provides a detected_format, use it; otherwise detect
#────────────────────────────────────────────────────────────────────────────
def _get_detected_format(date_string):
    """
    Returns the detected format for the date string.
    (This helper always calls DateTimeScan.search() internally.)
    """
    return DateTimeScan.search(date_string)

#────────────────────────────────────────────────────────────────────────────
# HELPER: CHECK IF DATETIME OBJECT
#────────────────────────────────────────────────────────────────────────────
def _is_datetime(dt_input):
    """
    Checks if the input `dt_input` is a datetime object or an iterable of datetime objects.

    Parameters:
        dt_input (any): The object to check.

    Returns:
        bool: True if `dt_input` is a datetime object or an iterable of datetime objects, False otherwise.
    """
    # Check for single datetime or date objects
    if isinstance(dt_input, (dt, d)):
        return True

    # Check if `dt_input` is a scalar (not iterable)
    if np.isscalar(dt_input):
        return False

    # Check if it's a list or tuple and contains only datetime-like objects
    if isinstance(dt_input, (list, tuple)):
        return all(isinstance(x, (dt, d)) for x in dt_input)

    # Check if it's a Pandas Series
    if isinstance(dt_input, pd.Series):
        if dt_input.ndim == 1 and (pd.api.types.is_datetime64_any_dtype(dt_input) or 
                                   (pd.api.types.is_object_dtype(dt_input) and dt_input.apply(lambda x: isinstance(x, (dt, d))).all())):
            return True

    # Check if it's a NumPy array
    if isinstance(dt_input, np.ndarray):
        if dt_input.ndim == 1 and (np.issubdtype(dt_input.dtype, np.datetime64) or 
                                   (np.issubdtype(dt_input.dtype, np.object_) and np.all([isinstance(x, (dt, d)) for x in dt_input]))):
            return True

    return False

#────────────────────────────────────────────────────────────────────────────
# HELPER: NON-ISO REPLACE TIMESTRING
#────────────────────────────────────────────────────────────────────────────
def _repl_timestring(datetime_strings, hour=None, minute=None, second=None, microsecond=None, tzinfo=None, time_indicator=None):
    """
    Handles non-ISO datetime strings. Applies changes to hour, minute, second, microsecond, tzinfo, 
    and optionally inserts an AM/PM indicator if not already present.
    """
    def process(dt_str):
        # 1) If there's no recognized time, we add a default time
        dt_str = make_datetime_string(dt_str)

        # 2) Replace each component if needed
        if hour is not None:
            dt_str = replace_time_by_position(dt_str, 'hour', hour)
        if minute is not None:
            dt_str = replace_time_by_position(dt_str, 'minute', minute)
        if second is not None:
            dt_str = replace_time_by_position(dt_str, 'second', second)
        if microsecond is not None:
            dt_str = replace_time_by_position(dt_str, 'microsecond', microsecond)
        if tzinfo is not None:
            dt_str = replace_time_by_position(dt_str, 'tzinfo', tzinfo)

        # 3) Handle time indicator (AM/PM) if set
        if time_indicator == '':
            # remove any existing AM/PM
            return remove_marker(_stripTimeIndicator(dt_str))
        elif time_indicator is not None and time_indicator.upper() in ["AM", "PM"]:
            # Insert AM or PM if not present
            timematch = anytime_regex.search(dt_str)
            if timematch:
                time_fragment_str = timematch.group()
                if not exist_meridiem(time_fragment_str):
                    dt_str = (dt_str[:timematch.end()]
                              + f' {time_indicator.upper()}'
                              + dt_str[timematch.end():])

        # 4) Validate the resulting timezone usage
        valid, msg = validate_timezone(dt_str)
        if not valid:
            raise ValueError(f"Invalid time string: {msg}")
        return remove_marker(dt_str)

    return _apply_to_data(datetime_strings, process)

#────────────────────────────────────────────────────────────────────────────
# HELPER: ISO REPLACE TIMESTRING
#────────────────────────────────────────────────────────────────────────────
def _repl_iso_timestring(datetime_strings, hour=None, minute=None, second=None, microsecond=None, tzinfo=None):
    """
    Handles ISO8601-like strings using dt.fromisoformat, adjusting hour, minute, second, microsecond, 
    tzinfo, then returning the new ISO8601 string.
    """
    def process(dt_str, hour=None, minute=None, second=None, microsecond=None, tzinfo=None):
        dt_str = replaceZ(dt_str)
        dt_obj = dt.fromisoformat(dt_str)

        if isinstance(tzinfo, (int, float)):
            tzinfo = datetime_offset(tzinfo)

        new_dt = dt_obj.replace(
            hour=hour if hour is not None else dt_obj.hour,
            minute=minute if minute is not None else dt_obj.minute,
            second=second if second is not None else dt_obj.second,
            microsecond=microsecond if microsecond is not None else dt_obj.microsecond,
            tzinfo=tzinfo if tzinfo is not None else dt_obj.tzinfo
        )
        return new_dt.isoformat()

    return _apply_to_data(datetime_strings, process)





#────────────────────────────────────────────────────────────────────────────
# 1) EXTRACT DATETIME COMPONENT
#────────────────────────────────────────────────────────────────────────────
def extract_datetime_component(date_strings, component, ret_format=False):
    """
    Extract a specific component from a single date string or a collection of date strings.

    This function parses a date string to extract specified components, ensuring accurate extraction
    of year, month, day, hour, minute, and second components, which are critical for consistent date
    formatting across different platforms.

    Parameters:
    ──────────────────────────    
    - date_strings (*str | list | np.ndarray | pd.Series*):  
      A single date string or a collection of date strings to extract components from.
      
    - component (*str*):  
      The component to extract. Options include:
      - `'year'` – Year component
      - `'month'` – Month component
      - `'day'` – Day component
      - `'weekday'` – Weekday component
      - `'hour24'` – Hour in 24-hour format
      - `'hour12'` – Hour in 12-hour format
      - `'minute'` – Minute component
      - `'second'` – Second component
      - `'microsecond'` – Microsecond component

    - ret_format (*bool, optional*):  
      If `True`, returns a tuple (`format`, `value`).

    Returns:
    ──────────────────────────    
    - (*str | None*):  
      - The extracted component as a string.  
      - Returns `None` if no match is found.

    Raises:
    ──────────────────────────    
    - ValueError:  
      If the input format is not recognized.
    """
    def process(date_string, comp, ret_fmt):
        try:
            used_format = _get_detected_format(date_string)
            pattern = datetime_pattern_search(used_format)
            match = pattern.match(date_string)
            if match and comp in match.groupdict():
                value = match.group(comp)
                if comp == 'hour12' and 'am_pm' in match.groupdict():
                    am_pm = match.group('am_pm')
                    if am_pm == 'PM' and value != '12':
                        value = str(int(value) + 12)
                    elif am_pm == 'AM' and value == '12':
                        value = '00'
                if ret_fmt:
                    return (used_format, value)
                return value
        except ValueError:
            return None
        return None

    return _apply_to_data(
        data=date_strings,
        func=process,
        # The next arguments become *func_args or **func_kwargs
        comp=component,
        ret_fmt=ret_format
    )


#────────────────────────────────────────────────────────────────────────────
# 2) DETECT DATE FORMAT
#────────────────────────────────────────────────────────────────────────────
def detect_date_format(date_strings):
    """
    Detect and adjust the date format for a given date string or a collection of date strings.

    This function detects and adjusts the date format based on the components of a single date string or a collection of date strings.
    It analyzes each date string to identify its format and makes adjustments to handle leading zeros in the date components.
    It ensures consistent date formatting across different platforms by replacing zero-padded specifiers with their non-zero-padded
    counterparts where applicable.    

    Parameters:
    ──────────────────────────    
    - date_strings (*str | list | np.ndarray | pd.Series*):  
      A single date string or a collection of date strings.

    - detected_format (*str, optional*):  
      If you already know the format, pass it to skip automatic detection.

    Returns:
    ──────────────────────────    
    - (*str | list*):  
      - The detected or adjusted format string.
      - Returns a list if multiple date strings are provided.

    Raises:
    ──────────────────────────    
    - ValueError:  
      If no valid format is found for the given date string.
    """
    def process(date_string):
        fmt = _get_detected_format(date_string)
        try:
            for comp_key, comp_details in zero_handling_date_formats().items():
                component_value = extract_datetime_component(date_string, comp_key)
                if has_leading_zero(component_value) is False:
                    fmt = fmt.replace(comp_details['zero_padded']['format'],
                                      comp_details['no_leading_zero']['format'])
            return fmt
        except (ValueError, TypeError):
            raise ValueError("No matching format found for the given date string.")

    return _apply_to_data(date_strings, process)


#────────────────────────────────────────────────────────────────────────────
# 3) CONVERT DATE
#────────────────────────────────────────────────────────────────────────────
def convert_date(dates, to_format=None, delta=0, dict_keys=None, dict_inplace=False):
    """
    Convert date strings or datetime objects to a specified format or modify them by a time delta.

    This function serves as a versatile converter for date and datetime inputs. It supports converting single or 
    multiple date strings or datetime objects into a specified format or datetime objects, with the option to modify
    the date by a given delta of days. Additionally, it handles dictionaries containing date information by applying
    conversions recursively to specified keys.

    Parameters:
    ──────────────────────────    
    - dates (*str | list | np.ndarray | pd.Series | datetime | dict*):  
      - A single date string, datetime object, or a collection of them.  
      - Can also be a dictionary containing date strings or datetime objects.

    - to_format (*str, optional*):  
      - Desired output format according to `datetime.strftime`.
      - If `None`, returns datetime objects.

    - delta (*int, default=0*):  
      - Number of days to add (`+`) or subtract (`-`).

    - dict_keys (*list, optional*):  
      - When `dates` is a dictionary, specify which keys contain date information.

    - dict_inplace (*bool, default=False*):  
      - If `True`, modifies the dictionary in place and returns `None`.

    Returns:
    ──────────────────────────    
    - (*str | datetime | list | dict*):  
      - Formatted date string(s) or datetime object(s).
      - If input is a dictionary and `dict_inplace=False`, returns a modified dictionary.

    Raises:
    ──────────────────────────    
    - ValueError:  
      - If `dates` is a dictionary but `dict_keys` is not provided.
      - If date format is unrecognized or invalid.
    """
    def process(date, to_format, delta):
        try:        
            if isinstance(date, (dt, d)):
                parsed_date = date + td(days=int(delta))
            else:
                input_format = detect_date_format(date)            
                try:
                    parsed_date = dt.strptime(date, input_format) + td(days=int(delta))
                except ValueError:
                    input_format = replace_non_padded_with_padded(input_format)
                    parsed_date = dt.strptime(date, input_format) + td(days=int(delta))

            if to_format and isinstance(parsed_date, dt):
                return date_format_leading_zero(parsed_date, to_format)
            else:
                return parsed_date
        except Exception as e:
            raise ValueError(f"Error processing date: {date}. {str(e)}") from e
           
    # Handle dictionary inputs separately using recursive conversion.
    def recursive_convert(data, keys):
        if isinstance(data, dict):
            for key, value in data.items():
                if key in keys:
                    if isinstance(value, list):
                        data[key] = [process(item, to_format, delta) if not isinstance(item, (dict, list)) 
                                     else recursive_convert(item, keys) for item in value]
                    else:
                        data[key] = process(value, to_format, delta)
                elif isinstance(value, dict):
                    recursive_convert(value, keys)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            recursive_convert(item, keys)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    data[i] = recursive_convert(item, keys)
        return data

    if isinstance(dates, dict):
        if dict_keys is None:
            raise ValueError("dict_keys must be provided when dates is a dictionary")
        if not dict_inplace:
            dates = deepcopy(dates)
        processed_data = recursive_convert(dates, dict_keys)
        if dict_inplace:
            return
        else:
            return processed_data
    else:
        # For all other types, use the helper to dispatch.
        return _apply_to_data(dates, process, to_format=to_format, delta=delta)


#────────────────────────────────────────────────────────────────────────────
# 4) REPLACE TIMESTRING
#────────────────────────────────────────────────────────────────────────────
def replace_timestring(datetime_strings, *args, **kwargs):
    """
    Modifies various time components within a single datetime string or a collection of datetime strings,
    supporting both ISO and non-ISO formatted strings. This function is adaptable to handle updates to time
    components including hours, minutes, seconds, microseconds, and time zones. It can also add a time indicator 
    (AM/PM) for non-ISO formats.

    This utility is particularly useful in data processing workflows where datetime strings require uniform
    time components across datasets, or adjustments to individual components are necessary for standardization,
    time zone corrections, or formatting for further analysis or display.

    Parameters:
    ──────────────────────────
    - datetime_strings (*str | list | np.ndarray | pd.Series*):  
      A datetime string or a collection of datetime strings to be modified. Supports various formats:
      - Single string (e.g., `"2024-03-13T14:30:00"`)
      - List (`["2024-03-13T14:30:00", "2025-01-01T00:00:00"]`)
      - NumPy array (`np.array([...])`)
      - Pandas Series (`pd.Series([...])`)  

    - hour (*str | int, optional*):  
      The new hour value (`0-23`). If not provided, the hour remains unchanged.

    - minute (*str | int, optional*):  
      The new minute value (`0-59`). If not provided, the minute remains unchanged.

    - second (*str | int, optional*):  
      The new second value (`0-59`). If not provided, the second remains unchanged.

    - microsecond (*str | int, optional*):  
      The new microsecond value. If not provided, the microsecond remains unchanged.

    - tzinfo (*str | timezone | int | float, optional*):  
      Specifies the new timezone:  
      - As a string (e.g., `"UTC"`, `"+0200"`)  
      - As a timezone object (`pytz.timezone("Europe/London")`)  
      - As an integer/float offset (e.g., `-5`, `5.5`)  
      If not provided, the timezone remains unchanged.

    - time_indicator (*str, optional*):  
      Appends a time indicator to the datetime string (`"AM"` or `"PM"`).  
      Only applicable for non-ISO formatted strings. If not provided, no time indicator is added.

    Returns:
    ──────────────────────────    
    (*str | list | np.ndarray | pd.Series*):  
    - If input is a single string, returns a single modified datetime string.  
    - If input is a list, NumPy array, or Pandas Series, returns a modified collection of datetime strings  
      while preserving the original structure.

    Raises:
    ──────────────────────────    
    - ValueError:  
      - If the input data type is unsupported.  
      - If the datetime string format is invalid.  
      - If an invalid `tzinfo` value is provided.  
      These safeguards ensure proper function usage within expected data types.
    """
    # Filter out time_indicator from kwargs for ISO processing (if needed)        
    filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'time_indicator'}

    def transform(dt_str):
        if is_iso_date(dt_str):
            return _repl_iso_timestring(dt_str, *args, **filtered_kwargs)
        else:
            return _repl_timestring(dt_str, *args, **kwargs)
    return _apply_to_data(datetime_strings, transform)


#────────────────────────────────────────────────────────────────────────────
# 5) REPLACE DATESTRING
#────────────────────────────────────────────────────────────────────────────
def replace_datestring(date_strings, year=None, month=None, day=None):
    """
    Replace specific components (year, month, day) in a date string or a collection of date strings.

    This function parses a date string to identify existing components and replaces them with
    new values provided as arguments. It reconstructs the date string with the new values.
    
    Parameters:
    ──────────────────────────    
    - date_strings (*str | list | np.ndarray | pd.Series*):  
      - The date string(s) to modify.

    - year (*str | int, optional*):  
      - New year value to replace the existing one.

    - month (*str | int, optional*):  
      - New month value to replace the existing one.

    - day (*str | int, optional*):  
      - New day value to replace the existing one.

    Returns:
    ──────────────────────────    
    - (*str | list | np.ndarray | pd.Series*):  
      - The modified date string(s) with the updated values.

    Raises:
    ──────────────────────────    
    - ValueError:  
      - If the resulting date string is invalid after modifications.
    """
    def process(date_string):
        result = strTime(date_string)
        time_match = None
        if result:
            time_match = result['full_time_details']['full_time_string']
            fulltime_start = result['full_time_details']['start']
            datestr = date_string[:fulltime_start]
            date_string = cleanstr(datestr)
        used_format = _get_detected_format(date_string)
        pattern = datetime_pattern_search(used_format)
        match = pattern.match(date_string)
        components = {"year": (year, None), "month": (month, None), "day": (day, None)}
        if match:
            for key in components.keys():
                if key in match.groupdict():
                    components[key] = (components[key][0], match.span(key))
        # Replace components from rightmost (largest index) first:
        for key, (new_value, span) in sorted(components.items(), key=lambda item: item[1][1] if item[1][1] else (0,0), reverse=True):
            if new_value is not None and span:
                start, end = span
                date_string = date_string[:start] + str(new_value) + date_string[end:]
        if time_match:
            date_string += f' {time_match}'
        if not validate_date(date_string, date_format=used_format):
            raise ValueError("Invalid date string after replacement.")
        return date_string

    return _apply_to_data(date_strings, process)
       

#────────────────────────────────────────────────────────────────────────────
# 6) SEQUENCE
#────────────────────────────────────────────────────────────────────────────
def sequence(start_date, end_date, to_format=None):
    """
    Generate a sequence of formatted dates between two given dates.

    Parameters:
    ──────────────────────────    
    - start_date (*str | datetime*):  
      - The start date of the sequence.

    - end_date (*str | datetime*):  
      - The end date of the sequence.

    - to_format (*str, optional*):  
      - Desired format for the generated dates.

    Returns:
    ──────────────────────────    
    - (*list of str*):  
      - A list of formatted date strings from `start_date` to `end_date`, inclusive.

    Raises:
    ──────────────────────────    
    - ValueError:  
      - If the input dates are not valid datetime objects or convertible to one.
    """
    # Check if the start_date and end_date are valid datetime objects
    if not _is_datetime(start_date):
        start_date = convert_date(start_date, to_format=to_format)
    
    if not _is_datetime(end_date):
        end_date = convert_date(end_date, to_format=to_format)
    
    # Calculate the number of days between the start and end dates
    delta = end_date - start_date
    
    # Generate the list of dates and format them
    date_list = [convert_date(start_date + td(days=i), to_format=to_format) for i in range(delta.days + 1)]
    
    return date_list


#────────────────────────────────────────────────────────────────────────────
# 7) PARSE
#────────────────────────────────────────────────────────────────────────────
def parse(input_str):
    """
    Parse a natural language or formatted date string into a datetime object or range.

    This function acts as a unified entry point for interpreting both natural-language
    temporal expressions (e.g., "first Monday of next month") and structured date strings
    (e.g., "2024-04-01"). It first attempts to interpret the input using `parse_temporal`,
    which supports relative and fuzzy date phrases. If that fails or the result signals
    a plain date string, it falls back to `convert_date`.

    Parameters:
    ──────────────────────────
    - input_str (str):
        A natural-language expression or a formatted date string.

    Returns:
    ──────────────────────────
    - datetime.date
    - or (start_date, end_date) tuple
    - or None if the input is invalid or unrecognized.    
    """
    try:
        temporal_result = parse_temporal(input_str, skip_validation=False, parse=True, clean_tokens=True)
        if isinstance(temporal_result, tuple) and temporal_result[0] == "datetime":
            result = convert_date(temporal_result[1])
        else:
            result = temporal_result or convert_date(input_str)

        # Fix year if parser defaulted to 1900
        current_year = dt.today().year
        if isinstance(result, dt) and result.year == 1900:
            result = result.replace(year=current_year)
        elif isinstance(result, tuple):
            result = tuple(
                r.replace(year=current_year) if isinstance(r, dt) and r.year == 1900 else r
                for r in result
            )
        return result   

    except Exception as e:
        msg = (
            f"[dately:parse] NLP parsing failed for input: '{input_str}'.\n"
            f"{type(e).__name__}: {e}"
        )
        if DEBUG_MODE:
            print(msg)
        else:
            logger.warning(msg)
        logger.warning("To help improve NLP parsing, please report this issue:\n"
                        "→ https://github.com/cedricmoorejr/dately/issues/new?title=NLP%20parse%20error")
        # Fallback to deterministic parser
        try:
            return convert_date(input_str)
        except Exception:
            return None


# Define public interface.
__all__ = [
    "extract_datetime_component",
    "detect_date_format",
    "convert_date",
    "replace_timestring",
    "replace_datestring",
    "sequence",
    "parse",    
]
