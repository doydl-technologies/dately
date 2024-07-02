import threading

def import_specific_parts():
    global TimeZoner
    from .timezone import TimeZoner

thread = threading.Thread(target=import_specific_parts)
thread.start()

import datetime
import numpy as np
import pandas as pd
from copy import deepcopy

from .mold.pyd.cdatetime.whichformat import *
from .utils import *
from .timeutils import *
from .mold.pyd.cdatetime.UniversalDateFormatter import *
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
thread.join()



class DatelyDate:
    """
    A versatile date and datetime utility class for extracting, detecting, converting, and replacing components of date strings.
    
    This class provides methods to handle various date and datetime formats, allowing for extraction of specific components,
    detection and adjustment of date formats, conversion of dates with optional formatting and temporal adjustments, 
    and replacement of specific components within datetime strings. It supports operations on individual strings as well as
    collections of date strings in lists, numpy arrays, and pandas Series.

    Methods
    -------
    extract_datetime_component(date_strings, component, ret_format=False):
        Extract specific date components from a single date string or a collection of date strings using precompiled regex patterns.

    detect_date_format(date_strings):
        Detect and adjust the date format based on the components of a single date string or a collection of date strings.

    convert_date(dates, to_format=None, delta=0, dict_keys=None, dict_inplace=False):
        Convert single or multiple date strings or datetime objects into a specified format or datetime objects, with optional date modification.

    replace_timestring(datetime_strings, *args, **kwargs):
        Modify various time components within a single datetime string or a collection of datetime strings, supporting both ISO and non-ISO formatted strings.

    replace_datestring(date_strings, year=None, month=None, day=None):
        Replace specific components in a date string or a collection of date strings with new values.

    sequence(start_date, end_date, to_format='%b %-d, %Y'):
        Generate a sequence of formatted dates between two dates.

    """

    def __dir__(self):
        original_dir = super().__dir__()
        return [item for item in original_dir if not item.startswith('_DatelyDate__')]
    
    def extract_datetime_component(self, date_strings, component, ret_format=False):
        """
        Extract specific date components from a single date string or a collection of date strings using precompiled regex patterns.
        
        This function parses a date string to extract specified components, ensuring accurate extraction
        of year, month, day, hour, minute, and second components, which are critical for consistent date
        formatting across different platforms.

        Parameters:
            date_strings (str): The date string to parse.
            component (str): The component to extract. Valid components include:
                'year', 'month', 'day', 'hour24', 'hour12', 'minutes', 'seconds'.

        Returns:
            str or None: The extracted component as a string, or None if no match is found.

        Components:
            - 'year': Year component of the date.
            - 'month': Month component of the date.
            - 'day': Day component of the date.
            - 'weekday': Weekday component of the date.
            - 'hour24': Hour component in 24-hour format.
            - 'hour12': Hour component in 12-hour format.
            - 'minute': Minute component of the time.
            - 'second': Second component of the time.
            - 'microsecond': Microsecond component of the time.
        """
        def process(date_string, component, ret_format=False):
            try:
                detected_format = DateFormatFinder().search(date_string)
                pattern = datetime_pattern_search(detected_format)
                match = pattern.match(date_string)
                if match and component in match.groupdict():
                    value = match.group(component)
                    if component == 'hour12' and 'am_pm' in match.groupdict():
                        am_pm = match.group('am_pm')
                        if am_pm == 'PM' and value != '12':
                            value = str(int(value) + 12)
                        elif am_pm == 'AM' and value == '12':
                            value = '00'
                    if ret_format:
                        return (detected_format, value)
                    return value
            except ValueError:
                return None
            return None

        if isinstance(date_strings, str):
            return process(date_strings, component, ret_format)
        elif isinstance(date_strings, list):
            return [process(date_string, component, ret_format) for date_string in date_strings]
        elif isinstance(date_strings, np.ndarray):
            vectorized_func = np.vectorize(process, otypes=[np.object])
            return vectorized_func(date_strings, component, ret_format)
        elif isinstance(date_strings, pd.Series):
            date_strings = date_strings.astype(str)
            return date_strings.apply(process, args=(component, ret_format))
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")
    
    def detect_date_format(self, date_strings):
        """
        Detect and adjust the date format based on the components of a single date string or a collection of date strings.
        This function analyzes each date string to identify its format and makes adjustments to handle leading zeros in the date components.
        It ensures consistent date formatting across different platforms by replacing zero-padded specifiers with their non-zero-padded
        counterparts where applicable.

        Parameters:
            date_strings (str, list, np.ndarray, pd.Series): The date string or collection of date strings to analyze.

        Returns:
            str, list, np.ndarray, pd.Series: Depending on the input type, returns either a single format or a collection of formats with detected and possibly adjusted date format strings.

        Raises:
            ValueError: If no matching format is found for any of the given date strings.
        """
        def process(date_string):
            detected_format = DateFormatFinder().search(date_string)
            try:
                for comp_key, comp_details in zero_handling_date_formats().items():
                    component_value = self.extract_datetime_component(date_string, comp_key)

                    if has_leading_zero(component_value) is False:
                        detected_format = detected_format.replace(comp_details['zero_padded']['format'], comp_details['no_leading_zero']['format'])
                return detected_format
            except (ValueError, TypeError):
                raise ValueError("No matching format found for the given date string.")

        if isinstance(date_strings, str):
            return process(date_strings)
        elif isinstance(date_strings, list):
            return [process(date_string) for date_string in date_strings]
        elif isinstance(date_strings, np.ndarray):
            vectorized_detect = np.vectorize(process, otypes=[np.object])
            return vectorized_detect(date_strings)
        elif isinstance(date_strings, pd.Series):
            date_strings = date_strings.astype(str)
            return date_strings.apply(process)
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")
    
    def convert_date(self, dates, to_format=None, delta=0, dict_keys=None, dict_inplace=False):
        """
        This function serves as a versatile converter for date and datetime inputs. It supports converting single or 
        multiple date strings or datetime objects into a specified format or datetime objects, with the option to modify
        the date by a given delta of days. Additionally, it handles dictionaries containing date information by applying
        conversions recursively to specified keys.

        This function is particularly useful in data preprocessing where dates might come in various formats and need
        standardization or adjustment based on a temporal delta for further analysis or storage.

        Parameters:
            dates (str, list, np.ndarray, pd.Series, datetime.datetime, dict): The input date(s) which can be a single date string,
                a datetime object, a collection (list, array, series) of date strings or datetime objects, or a dictionary containing
                date strings or datetime objects nested under specified keys.
            to_format (str, optional): The desired output format of the date(s) as a string according to datetime.strftime conventions.
                If None, the function will return datetime objects instead of formatted strings.
            delta (int, default=0): An integer representing the number of days to add or subtract from the input date(s). Positive
                values move the date forward, while negative values move it backwards.
            dict_keys (list, optional): When the 'dates' parameter is a dictionary, this list specifies which keys contain the
                date information to be converted. This parameter is mandatory if 'dates' is a dictionary.
            dict_inplace (bool, default=False): Determines whether the dictionary is modified in place. If True, the dictionary is
                modified directly and the function returns None. If False, the function modifies a copy of the dictionary and returns it.

        Returns:
            The function returns the converted date(s) either as formatted strings (if 'to_format' is specified) or as datetime
                objects. If the input is a dictionary and 'dict_inplace' is False, it returns a new dictionary with the dates converted.
                If 'dict_inplace' is True, the input dictionary is modified directly and the function returns None.

        Raises:
            ValueError: If 'dates' is a dictionary and 'dict_keys' is not provided, or if any input date string format is unrecognized
                or incorrect, making it impossible to parse the date.
        """
        def process(date, to_format, delta):
            if isinstance(date, (datetime.datetime, datetime.date)):
                parsed_date = date + datetime.timedelta(days=int(delta))
            else:
                input_format = self.detect_date_format(date)
                try:
                    parsed_date = datetime.datetime.strptime(date, input_format) + datetime.timedelta(days=int(delta))
                except ValueError:
                    input_format = replace_non_padded_with_padded(input_format)
                    parsed_date = datetime.datetime.strptime(date, input_format) + datetime.timedelta(days=int(delta))

            if to_format and isinstance(parsed_date, datetime.datetime):
                return date_format_leading_zero(parsed_date, to_format)
            else:
                return parsed_date

        def recursive_convert(data, keys):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in keys:
                        if isinstance(value, list):
                            data[key] = [process(item, to_format, delta) if not isinstance(item, (dict, list)) else recursive_convert(item, keys) for item in value]
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

        elif isinstance(dates, (list, np.ndarray, pd.Series)):
            if isinstance(dates, list):
                return [process(date, to_format, delta) for date in dates]
            elif isinstance(dates, np.ndarray):
                vectorized_process = np.vectorize(process, excluded=['to_format', 'delta'], otypes=[np.object])
                return vectorized_process(dates, to_format=to_format, delta=delta)
            elif isinstance(dates, pd.Series):
                return dates.apply(process, to_format=to_format, delta=delta)
        else:
            return process(dates, to_format, delta)

    def _repl_timestring(self, datetime_strings, hour=None, minute=None, second=None, microsecond=None, tzinfo=None, time_indicator=None):
        def process(datetime_string):
            datetime_string = make_datetime_string(datetime_string)
            if hour is not None:
                datetime_string = replace_time_by_position(datetime_string, 'hour', hour)
            if minute is not None:
                datetime_string = replace_time_by_position(datetime_string, 'minute', minute)
            if second is not None:
                datetime_string = replace_time_by_position(datetime_string, 'second', second)
            if microsecond is not None:
                datetime_string = replace_time_by_position(datetime_string, 'microsecond', microsecond)
            if tzinfo is not None:
                datetime_string = replace_time_by_position(datetime_string, 'tzinfo', tzinfo)
            if time_indicator == '':
                return remove_marker(stripTimeIndicator(datetime_string))

            if time_indicator is not None and time_indicator.upper() in ["AM", "PM"]:
                timepattern = anytime_regex
                timematch = timepattern.search(datetime_string)
                if timematch:
                    time_fragment_str = timematch.group()
                    if not exist_meridiem(time_fragment_str):
                        datetime_string = datetime_string[:timematch.end()] + f' {time_indicator.upper()}' + datetime_string[timematch.end():]
            result = validate_timezone(datetime_string)
            if result[0] is False:
                raise ValueError
            return remove_marker(datetime_string)

        if isinstance(datetime_strings, str):
            return process(datetime_strings)
        elif isinstance(datetime_strings, list):
            return [process(dt_string) for dt_string in datetime_strings]
        elif isinstance(datetime_strings, np.ndarray):
            vectorized_func = np.vectorize(process, otypes=[np.object])
            return vectorized_func(datetime_strings)
        elif isinstance(datetime_strings, pd.Series):
            datetime_strings = datetime_strings.astype(str)
            return datetime_strings.apply(process)
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")

    def __repl_iso_timestring(self, datetime_strings, hour=None, minute=None, second=None, microsecond=None, tzinfo=None):
        def process(datetime_string, hour=None, minute=None, second=None, microsecond=None, tzinfo=None):
            datetime_string = replaceZ(datetime_string)
            dt = datetime.datetime.fromisoformat(datetime_string)

            if isinstance(tzinfo, (int, float)):
                tzinfo = datetime_offset(tzinfo)

            new_dt = dt.replace(
                hour=hour if hour is not None else dt.hour,
                minute=minute if minute is not None else dt.minute,
                second=second if second is not None else dt.second,
                microsecond=microsecond if microsecond is not None else dt.microsecond,
                tzinfo=tzinfo if tzinfo is not None else dt.tzinfo
            )
            return new_dt.isoformat()

        if isinstance(datetime_strings, str):
            return process(datetime_strings, hour, minute, second, microsecond, tzinfo)
        elif isinstance(datetime_strings, list):
            return [process(dt_string, hour, minute, second, microsecond, tzinfo) for dt_string in datetime_strings]
        elif isinstance(datetime_strings, np.ndarray):
            vectorized_func = np.vectorize(process, otypes=[np.object], excluded=['hour', 'minute', 'second', 'microsecond', 'tzinfo'])
            return vectorized_func(datetime_strings, hour=hour, minute=minute, second=second, microsecond=microsecond, tzinfo=tzinfo)
        elif isinstance(datetime_strings, pd.Series):
            datetime_strings = datetime_strings.astype(str)
            return datetime_strings.apply(lambda dt_string: process(dt_string, hour, minute, second, microsecond, tzinfo))
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")

    def replace_timestring(self, datetime_strings, *args, **kwargs):
        """
        Modifies various time components within a single datetime string or a collection of datetime strings,
        supporting both ISO and non-ISO formatted strings. This function is adaptable to handle updates to time
        components including hours, minutes, seconds, microseconds, and time zones. It can also add a time indicator 
        (AM/PM) for non-ISO formats.

        This utility is particularly useful in data processing workflows where datetime strings require uniform
        time components across datasets, or adjustments to individual components are necessary for standardization,
        time zone corrections, or formatting for further analysis or display.

        Parameters:
            datetime_strings (str, list, np.ndarray, pd.Series): The datetime string or collection of datetime 
                strings to be modified. This allows the function to integrate seamlessly into various data handling
                contexts, whether the data is a single datetime string, a list from typical Python data manipulations,
                a numpy array from numerical Python operations, or a pandas Series from dataframe manipulations.
            hour (str or int, optional): New hour value, formatted as a string (0-23) or an integer. 
                Optional; if not provided, the hour is not modified.
            minute (str or int, optional): New minute value, formatted as a string (0-59) or an integer. 
                Optional; if not provided, the minute is not modified.
            second (str or int, optional): New second value, formatted as a string (0-59) or an integer. 
                Optional; if not provided, the second is not modified.
            microsecond (str or int, optional): New microsecond value, formatted as a string or an integer.
                Optional; if not provided, the microsecond is not modified.
            tzinfo (str, timezone, int, or float, optional): New timezone information, formatted as a string 
                (e.g., "+0200", "UTC"), a timezone object (e.g., from pytz), or an offset in hours (int or float).
                Optional; if not provided, the timezone is not modified.
            time_indicator (str, optional): Time indicator to add to the datetime string, "AM" or "PM" only.
                Optional; if not provided, no time indicator is added.

        Returns:
            str, list, np.ndarray, pd.Series: Depending on the input type, returns either a single modified datetime 
            string or a collection of modified datetime strings. This allows for easy integration of the function's 
            output back into the data processing pipeline, maintaining the original data structure for seamless 
            further processing.

        Raises:
            ValueError: If the input data type is not supported, or if the datetime string is not in the expected
            format, or if the tzinfo is invalid, raises an error to ensure that the function usage is clear and safe 
            within expected data types.
        """
    def replace_timestring(self, datetime_strings, *args, **kwargs):
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'time_indicator'}

        if isinstance(datetime_strings, str):
            if is_iso_date(datetime_strings):
                return self.__repl_iso_timestring(datetime_strings, *args, **filtered_kwargs)
            else:
                return self._repl_timestring(datetime_strings, *args, **kwargs)
        elif isinstance(datetime_strings, list):
            return [
                self.__repl_iso_timestring(dt_string, *args, **filtered_kwargs) if is_iso_date(dt_string)
                else self._repl_timestring(dt_string, *args, **kwargs)
                for dt_string in datetime_strings
            ]
        elif isinstance(datetime_strings, np.ndarray):
            vectorized_iso_func = np.vectorize(
                lambda dt_string: self.__repl_iso_timestring(dt_string, *args, **filtered_kwargs) if is_iso_date(dt_string)
                else self._repl_timestring(dt_string, *args, **kwargs),
                otypes=[np.object]
            )
            return vectorized_iso_func(datetime_strings)
        elif isinstance(datetime_strings, pd.Series):
            return datetime_strings.apply(
                lambda dt_string: self.__repl_iso_timestring(dt_string, *args, **filtered_kwargs) if is_iso_date(dt_string)
                else self._repl_timestring(dt_string, *args, **kwargs)
            )
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")

    def replace_datestring(self, date_strings, year=None, month=None, day=None):
        """
        Replace specific components in a date string or a collection of date strings with new values.

        This function parses a date string to identify existing components and replaces them with
        new values provided as arguments. It reconstructs the date string with the new values.

        Parameters:
            date_strings (str, list, np.ndarray, pd.Series): The date string or collection to modify.
            year (str or int or None): The new year value to replace the existing year.
            month (str or int or None): The new month value to replace the existing month.
            day (str or int or None): The new day value to replace the existing day.

        Returns:
            str, list, np.ndarray, pd.Series: The modified date string or collection with the new values.
        """
        def process(date_string):
            time_match = None
            result = strTime(date_string)

            if result:
                time_match = result['full_time_details']['full_time_string']
                fulltime_start = result['full_time_details']['start']

                datestr = date_string[:fulltime_start]
                date_string = cleanstr(datestr)

            components = {
                "year": (year, None),
                "month": (month, None),
                "day": (day, None)
            }

            detected_format = DateFormatFinder().search(date_string)
            pattern = datetime_pattern_search(detected_format)
            match = pattern.match(date_string)
            if match:
                for key in components.keys():
                    if key in match.groupdict():
                        components[key] = (components[key][0], match.span(key))

            for key, (new_value, span) in sorted(components.items(), key=lambda item: item[1][1] if item[1][1] else (0, 0), reverse=True):
                if new_value is not None and span:
                    start, end = span
                    date_string = date_string[:start] + str(new_value) + date_string[end:]
            if time_match:
                date_string += f' {time_match}'

            if validate_date(date_string, date_format=detected_format) is False:
                raise ValueError

            return date_string

        if isinstance(date_strings, str):
            return process(date_strings)
        elif isinstance(date_strings, list):
            return [process(date_string) for date_string in date_strings]
        elif isinstance(date_strings, np.ndarray):
            vectorized_func = np.vectorize(process, otypes=[np.object])
            return vectorized_func(date_strings)
        elif isinstance(date_strings, pd.Series):
            date_strings = date_strings.astype(str)
            return date_strings.apply(process)
        else:
            raise ValueError("Unsupported data type. The input must be a scalar (str), list, numpy.ndarray, or pandas.Series.")

    def _is_datetime(self, dt):
        """
        Checks if the dt is a datetime object or an iterable of datetime objects.
        
        Parameters:
            dt (any): The date to check.        

        Returns:
        bool: True if dt is a datetime object or an iterable of datetime objects, False otherwise.
        """
        if isinstance(dt, (datetime.datetime, datetime.date)):
            return True
        if np.isscalar(dt):
            return False
        if isinstance(dt, (list, tuple)):
            if all(isinstance(x, (datetime.datetime, datetime.date)) for x in dt):
                return True
        if isinstance(dt, pd.Series):
            if dt.ndim == 1 and (pd.api.types._is_datetime64_any_dtype(dt) or pd.api.types.is_object_dtype(dt) and all(isinstance(x, (datetime.datetime, datetime.date)) for x in dt)):
                return True
        if isinstance(dt, np.ndarray):
            if dt.ndim == 1 and (np.issubdtype(dt.dtype, np.datetime64) or np.issubdtype(dt.dtype, np.object_) and all(isinstance(x, (datetime.datetime, datetime.date)) for x in dt)):
                return True
        return False

    def sequence(self, start_date, end_date, to_format=None):
        """
        Generate a sequence of formatted dates between two dates.

        Parameters:
            start_date (any): The start date of the sequence, which can be a datetime object or convertible to one.
            end_date (any): The end date of the sequence, which can be a datetime object or convertible to one.
            to_format (str, optional): The format string to use for formatting the dates.
                Defaults to None.

        Returns:
            list of str: List of formatted date strings from start to end date inclusive.
        """
        # Check if the start_date and end_date are valid datetime objects
        if not self._is_datetime(start_date):
            start_date = self.convert_date(start_date, to_format=to_format)
        
        if not self._is_datetime(end_date):
            end_date = self.convert_date(end_date, to_format=to_format)
        
        # Calculate the number of days between the start and end dates
        delta = end_date - start_date
        
        # Generate the list of dates and format them
        date_list = [self.convert_date(start_date + datetime.timedelta(days=i), to_format=to_format) for i in range(delta.days + 1)]
        
        return date_list


# Instance
dt = DatelyDate()


# Define public interface
__all__ = [
    "dt",
    "TimeZoner"
]
