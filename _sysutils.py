# -*- coding: utf-8 -*-

import time
import json
import sys
from pathlib import Path
# import pkg_resources as pkg_res
try:
    from importlib.resources import open_text
except ImportError:
    from importlib_resources import open_text


#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import requests

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._log import logger      
from ._version import *
from ._mskutils import Shift



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

class VersionChecker:
    @staticmethod
    def check_version_sufficiency(minimum_required_version='3.9'):
        """
        Checks if the current version is at least the minimum required version.

        Args:
            minimum_required_version (str): The minimum version required.

        Returns:
            bool: True if the current version is equal to or greater than the minimum required version, False otherwise.
        """
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        parts_current = list(map(int, current_version.split('.')))
        parts_minimum = list(map(int, minimum_required_version.split('.')))

        # Normalize the length of version lists by padding with zeros
        max_length = max(len(parts_current), len(parts_minimum))
        parts_current.extend([0] * (max_length - len(parts_current)))
        parts_minimum.extend([0] * (max_length - len(parts_minimum)))

        return parts_current >= parts_minimum

class UnixTime:
    @staticmethod
    def Timestamp(year=None, month=None, day=None, hour=None, minute=None, second=None, weekday=None, yearday=None, isdst=-1):
        """
        Initializes the UnixTime with specific time components or defaults to current time values.

        Parameters:
        year (int): The year (e.g., 2021). Default is the current year if not provided or invalid.
        month (int): The month (1-12). Default is the current month if not provided or invalid.
        day (int): The day of the month (1-31). Default is the current day if not provided or invalid.
        hour (int): The hour (0-23). Default is the current hour if not provided or invalid.
        minute (int): The minute (0-59). Default is the current minute if not provided or invalid.
        second (int): The second (0-59). Default is the current second if not provided or invalid.
        weekday (int): The day of the week (0-6, Monday is 0). Default is 0.
        yearday (int): The day of the year (1-366). Default is 0.
        isdst (int): Daylight Saving Time flag. Use -1 for automatic DST detection. Default is -1.
        """
        current_time = time.localtime()
        
        year = UnixTime.validate_input(year, current_time.tm_year)
        month = UnixTime.validate_input(month, current_time.tm_mon)
        day = UnixTime.validate_input(day, current_time.tm_mday)
        hour = UnixTime.validate_input(hour, current_time.tm_hour)
        minute = UnixTime.validate_input(minute, current_time.tm_min)
        second = UnixTime.validate_input(second, current_time.tm_sec)
        weekday = UnixTime.validate_input(weekday, 0)
        yearday = UnixTime.validate_input(yearday, 0)
        isdst = UnixTime.validate_input(isdst, -1)
        time_tuple = (year, month, day, hour, minute, second, weekday, yearday, isdst)
        return int(time.mktime(time_tuple))

    @staticmethod
    def Date(unix_timestamp):
        """
        Converts a Unix timestamp to a human-readable date.

        Parameters:
        unix_timestamp (int): The Unix timestamp to convert.

        Returns:
        str: The human-readable date in the format 'YYYY-MM-DD HH:MM:SS'.
        """
        time_struct = time.localtime(unix_timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

    @staticmethod
    def validate_input(value, default):
        """
        Validates the input to ensure it is an integer or defaults if None or invalid.
        """
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default



def _load_json(bundled_pkg, filename, remote_url):
    """
    bundled_pkg  – import-path where the built-in file lives (e.g. 'dately.files')
    filename     – 'holiday.json'
    remote_url   – fallback URL
    """
    _CACHE_DIR = Path.home() / ".dately"
    _MAX_AGE   = 3600 * 24 * 7          # 7 days
    
    # Bundled file
    try:
        # with pkg_res.open_text(bundled_pkg, filename) as f:
        with open_text(bundled_pkg, filename) as f:        
            logger.debug("Loaded bundled %s", filename)
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    # ~/.dately cache
    cache_file = _CACHE_DIR / filename
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < _MAX_AGE:
            with cache_file.open() as f:
                logger.debug("Loaded cached %s (age %.0fs)", filename, age)
                return json.load(f)

    # Remote download
    logger.info("Fetching %s from GitHub …", filename)
    resp = requests.get(remote_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Persist cache
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Could not write cache for %s: %s", filename, e)

    return data


class DataImport:
    @staticmethod
    def load_holiday_urls():
        data = _load_json(
            "dately.files",
            "holiday.json",
            f"https://raw.githubusercontent.com/cedricmoorejr/dately/v{__version__}/files/holiday.json",
        )
        for item in data:
            if "Link" in item:
                item["Link"] = Shift.format.chr(item["Link"], "format")
        return data

    @staticmethod
    def load_country_variants():
        return _load_json(
            "dately.files",
            "country_variants.json",
            f"https://raw.githubusercontent.com/cedricmoorejr/dately/v{__version__}/files/country_variants.json",
        )

    @staticmethod
    def load_timezone_data():
        data = _load_json(
            "dately.files",
            "timezone_data.json",
            f"https://raw.githubusercontent.com/cedricmoorejr/dately/v{__version__}/files/timezone_data.json",
        )
        try:
            if VersionChecker.check_version_sufficiency():
                from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
                for entry in data:
                    try:
                        entry["timezone_object"] = ZoneInfo(entry["zoneName"])
                    except ZoneInfoNotFoundError:
                        logger.warning(f"Unknown timezone: {entry['zoneName']}")
                        entry["timezone_object"] = None
            else:
                import pytz
                for entry in data:
                    try:
                        entry["timezone_object"] = pytz.timezone(entry["zoneName"])
                    except pytz.UnknownTimeZoneError:
                        logger.warning(f"Unknown timezone: {entry['zoneName']}")
                        entry["timezone_object"] = None
        except Exception as e:
            logger.error(f"Error processing timezone data: {e}")
        return data



# Define public interface
__all__ = ['UnixTime', 'DataImport']
