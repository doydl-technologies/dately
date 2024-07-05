import os
import json
import tempfile
import shutil
import requests
import time
import random
import re
import pandas as pd
import sys

from .mskutils import *
from .sysutils import *


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
       
       
       
class TZLoader:
    @staticmethod
    def load_iana_zones():
        current_dir = os.path.dirname(__file__)
        json_file_path = os.path.join(current_dir, 'sources', 'iana_zones.json')
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        iana_zones_df = pd.DataFrame(data)
        return iana_zones_df

    @staticmethod
    def load_timezone_data():
        """
        Load timezone data from a JSON file and recreate the timezone objects depending on the Python version.
        """
        current_dir = os.path.dirname(__file__)
        json_file_path = os.path.join(current_dir, 'sources', 'timezone_data.json')
        
        with open(json_file_path, 'r') as file:
            loaded_data = json.load(file)
        if VersionChecker.check_version_sufficiency():
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
            for entry in loaded_data:
                try:
                    entry['timezone_object'] = ZoneInfo(entry['zoneName'])
                except ZoneInfoNotFoundError:
                    print(f"Unknown timezone: {entry['zoneName']}")
                    entry['timezone_object'] = None
        else:
            import pytz
            for entry in loaded_data:
                try:
                    entry['timezone_object'] = pytz.timezone(entry['zoneName'])
                except pytz.UnknownTimeZoneError:
                    print(f"Unknown timezone: {entry['zoneName']}")
                    entry['timezone_object'] = None
        return loaded_data

def get_timezone_data():
    return TZLoader.load_timezone_data()
       



class NoAPIKeysError(Exception):
    """Exception raised when no API keys are available."""
    pass

class Request:
    def __init__(self, base_url='aHR0cDovL2FwaS50aW1lem9uZWRiLmNvbS92Mi4xL2xpc3QtdGltZS16b25lP2tleT0=', use_api_key=True, default_key_type="FullVersion"):
        """ Initialize the API utility with the given base URL. """
        self.base_url = Shift.format.chr(base_url, "format")
        self.use_api_key = use_api_key
        self.api_keys = {}
        self.last_key = None
        self.last_request_time = 0
        self.rate_limit_limit = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.default_key_type = default_key_type
        self.current_key_type = default_key_type

        if self.use_api_key:
            self.initialize()
            
    def initialize(self):
        """Initialize the API utility by fetching API keys if not already present."""
        if not self.api_keys:
            self.fetch_api_keys()

    def fetch_api_keys(self):
        """Fetch API keys from the specified URL and store them in the api_keys dictionary."""
        # url_unformatted = 'aHR0cHM6Ly90aW1lem9uemVkYXRhLm5ldGxpZnkuYXBwL2RhdGEuanNvbg=='
        url_unformatted = 'aHR0cHM6Ly9jZWRyaWNtb29yZWpyLmdpdGh1Yi5pby90aW1lem9uemUvaW5kZXguanNvbg=='
        url = Shift.format.chr(url_unformatted, "format")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.api_keys = response.json().get(self.current_key_type, {})
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            self.api_keys = {}
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error occurred: {e}")
            self.api_keys = {}
        except requests.exceptions.Timeout as e:
            print(f"Timeout occurred: {e}")
            self.api_keys = {}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.api_keys = {}
        except requests.exceptions.SSLError as e:
            print(f"SSL error occurred: {e}")
            self.api_keys = {} 

    def set_key_type(self, new_key_type):
        """Temporarily change the key type."""
        self.current_key_type = new_key_type
        self.fetch_api_keys()

    def reset_key_type(self):
        """Reset the key type to the default and refetch the API keys."""
        self.current_key_type = self.default_key_type
        self.fetch_api_keys()
        
    def get_random_key(self):
        """Get a random API key from the available keys."""
        keys = list(self.api_keys.keys())
        if not keys:
            raise NoAPIKeysError("No API keys available")
        
        random_key = random.choice(keys)
        while random_key == self.last_key and len(keys) > 1:
            random_key = random.choice(keys)
        
        self.last_key = random_key
        api_key_unformatted = self.api_keys[random_key]['key']
        api_key = Shift.format.str(api_key_unformatted, "format")
        return api_key

    def set_use_api_key(self, use_api_key):
        self.use_api_key = use_api_key
        if self.use_api_key:
            self.initialize()

    def update_base_url(self, new_url):
        """
        Update the base URL for the API utility.

        Parameters:
        new_url (str): The new base URL for the API endpoint.
        """
        self.base_url = new_url

    def extract_rate_limit_info(self, headers):
        """Extract rate limit information from response headers."""
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower.endswith('-limit'):
                self.rate_limit_limit = int(value)
            elif key_lower.endswith('-remaining'):
                self.rate_limit_remaining = int(value)
            elif key_lower.endswith('-reset'):
                self.rate_limit_reset = int(value)
        
        return {
            'x-ratelimit-limit': self.rate_limit_limit,
            'x-ratelimit-remaining': self.rate_limit_remaining,
            'x-ratelimit-reset': self.rate_limit_reset
        }

    def log_rate_limit_status(self):
        """Log the current rate limit status."""
        if self.rate_limit_reset:
            reset_time = UnixTime.Date(self.rate_limit_reset)
        else:
            reset_time = 'unknown'

    def make_request(self, params, api_key_param_name="key", headers=None):
        """ Make a request to the specified API. """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 2:
            time.sleep(2 - time_since_last_request)

        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            if self.rate_limit_reset is not None:
                reset_time = UnixTime.Date(self.rate_limit_reset)
                print(f"Rate limit exceeded. Please wait until {reset_time} to make more requests.")
                return {
                    'status': 'error',
                    'message': f'Rate limit exceeded. Please wait until {reset_time} to make more requests.',
                    'rate_limit_info': self.extract_rate_limit_info({})
                }
            else:
                print("Rate limit exceeded. Please try again later.")
                return {
                    'status': 'error',
                    'message': 'Rate limit exceeded. Please try again later.',
                    'rate_limit_info': self.extract_rate_limit_info({})
                }

        if self.use_api_key:
            api_key = self.get_random_key()
            params[api_key_param_name] = api_key
        
        if 'format' not in params:
            params['format'] = 'json'

        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            rate_limit_info = self.extract_rate_limit_info(response.headers)
            self.last_request_time = time.time()
            self.log_rate_limit_status()

            return {
                'response': response.json(),
                'rate_limit_info': rate_limit_info
            }
        except Exception as e:
            self.log_rate_limit_status()

            return {
                'status': 'error',
                'message': str(e),
                'rate_limit_info': self.extract_rate_limit_info({})
            }


class TimezoneOffset:
    """Converts a numeric or string time offset into a formatted string representing the offset in hours and minutes."""
    @staticmethod
    def format(offset):
        if isinstance(offset, str):
            offset = offset.strip()
            if offset == "UTC":
                return "+00:00"
            if offset.isupper():
                return offset
            if re.match(r'^[+-]\d{2}:\d{2}$', offset):
                return offset
        # Handle the case where offset is given as a string with hours and optional minutes
        pattern_hm = r'^([+-]?)(\d{1,2})(?::?(\d{1,2})?)?$'
        match_hm = re.match(pattern_hm, str(offset).strip())
        if match_hm:
            sign, hours_str, minutes_str = match_hm.groups()
            sign = '+' if sign != '-' else '-'
            try:
                hours = int(hours_str)
                minutes = int(minutes_str) if minutes_str else 0

                if minutes >= 60:
                    additional_hours = minutes // 60
                    minutes = minutes % 60
                    hours += additional_hours
                if hours > 14:
                    hours = 14
                elif hours < -14:
                    hours = -14
                formatted_time = f"{sign}{hours:02}:{minutes:02}"
                return formatted_time
            except ValueError:
                return None
        # Handle the case where offset is given as total seconds
        pattern_seconds = r'^([+-]?)(\d+)$'
        match_seconds = re.match(pattern_seconds, str(offset).strip())
        if match_seconds:
            sign, offset_str = match_seconds.groups()
            sign = '+' if sign != '-' else '-'
            try:
                total_seconds = int(offset_str)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                if hours > 14:
                    hours = 14
                elif hours < -14:
                    hours = -14
                formatted_time = f"{sign}{abs(hours):02}:{minutes:02}"
                return formatted_time
            except ValueError:
                return None
        return None



class tzoneDataManager:
    """ Manages the loading of json data """
    def __init__(self):
        self.timezonedata = get_timezone_data()
        self.restructured_data = self.__restructure_data()

    def __restructure_data(self):
        """Restructure the time zone data with zoneName as the key."""
        if self.timezonedata:
            restructured_data = {}
            for entry in self.timezonedata:
                zone_name = entry['zoneName']
                restructured_data[zone_name] = {
                    'countryCode': entry['countryCode'],
                    'countryName': entry['countryName'],
                    'Offset': entry['Offset'],
                    'UTC offset (STD)': entry.get('UTC offset (STD)'),
                    'UTC offset (DST)': entry.get('UTC offset (DST)'),
                    'Abbreviation (STD)': entry.get('Abbreviation (STD)'),
                    'Abbreviation (DST)': entry.get('Abbreviation (DST)'),
                    'timezone_object': entry.get('timezone_object')
                }
            return restructured_data
        return None


class ZoneInfoManager:
    def __init__(self, timezonedata, rq_instance=None):
        self.__data = timezonedata
        self.__Request = rq_instance

    def __dir__(self):
        original_dir = super().__dir__()
        return [item for item in original_dir if not item.startswith('_')]

    def __update_api_url(self, new_url):
        """ Update the base URL for the Request utility."""
        if not self.__Request:
            return None
        self.__Request.update_base_url(new_url)

    def __update_key_type(self, new_key_type):
        """ Temporarily update the API key type for the Request utility. """
        if not self.__Request:
            return None
        original_key_type = self.__Request.current_key_type
        self.__Request.set_key_type(new_key_type)
        return original_key_type

    @property
    def CountryCodes(self):
        """Return a sorted list of unique country codes in the time zone data."""
        return sorted({entry['countryCode'] for entry in self.__data.values()})
       
    @property
    def CountryNames(self):
        """Return a sorted list of unique country names in the time zone data."""
        return sorted({entry['countryName'] for entry in self.__data.values()})
       
    @property
    def MyTimeZone(self):
        """ Get the current timezone details for users region. """
        if not self.__Request:
            return None
        original_key_type = self.__update_key_type("DependentVersion")
        original_url = self.__Request.base_url
        temp = Shift.type.map('aHR0cHM6Ly9hcGkuaXBnZW9sb2NhdGlvbi5pby90aW1lem9uZQ==', ret=True)
        self.__Request.update_base_url(temp)
        try:
            result = self.__Request.make_request(params={}, api_key_param_name='apiKey')
        finally:
            if original_key_type:
                self.__Request.set_key_type(original_key_type)
            if original_url:
                self.__Request.update_base_url(original_url)
        return result['response'] if 'response' in result else result
       
    @property       
    def ObservesDST(self):
        """Return a dictionary categorizing time zones by their observance of daylight saving time (DST)."""
        zones_with_dst = []
        zones_without_dst = []
        for zone_name, details in self.__data.items():
            dst_value = details['UTC offset (DST)']
            if dst_value is None or (isinstance(dst_value, str) and dst_value.isalpha() and dst_value.isupper()):
                zones_without_dst.append(zone_name)
            else:
                zones_with_dst.append(zone_name)
        return {'observes_dst': zones_with_dst, 'does_not_observe_dst': zones_without_dst}
       
    @property
    def Offsets(self):
        """Return a dictionary mapping offsets to a list of time zones with that offset."""
        zones_by_offset = {}
        for zone_name, details in self.__data.items():
            offset = details['Offset']
            if offset not in zones_by_offset:
                zones_by_offset[offset] = []
            zones_by_offset[offset].append(zone_name)
        return zones_by_offset

    @property
    def Zones(self):
        """Return a sorted list of all time zone names."""
        return sorted(self.__data.keys())

    @property
    def ZonesByCountry(self):
        """Return a dictionary mapping country codes to their respective time zones."""
        zones_by_country = {}
        for zone_name, details in self.__data.items():
            country_code = details['countryCode']
            if country_code not in zones_by_country:
                zones_by_country[country_code] = []
            zones_by_country[country_code].append(zone_name)
        return zones_by_country
       
    def FilterZoneDetail(self, zone_name):
        """
        Retrieve detailed information for a specific time zone.

        This method returns the timezone details associated with the specified zone name. 
        If the zone name does not exist in the dataset, it returns an empty dictionary.

        Parameters:
        - zone_name (str): The name of the time zone for which details are to be retrieved.

        Returns:
        - dict: A dictionary containing the details of the specified time zone, or an empty dictionary if the zone name is not found.
        """
        return self.__data.get(zone_name, {})

    def ConvertTimeZone(self, from_zone, to_zone, year=None, month=None, day=None, hour=None, minute=None, second=None):
        """
        Convert time from one time zone to another.

        Parameters:
        from_zone (str): The source time zone.
        to_zone (str): The destination time zone.
        year (int): The year (e.g., 2021).
        month (int): The month (1-12).
        day (int): The day of the month (1-31).
        hour (int): The hour (0-23).
        minute (int): The minute (0-59).
        second (int): The second (0-59).
        """
        timestamp = UnixTime.Timestamp(year, month, day, hour, minute, second)
        if not self.__Request:
            return None
        params = {
            'from': from_zone,
            'to': to_zone,
            'time': timestamp
        }
        result = self.__Request.make_request(params)
        if 'response' in result:
            data = result['response']
            return [zone for zone in data['zones'] if zone['zoneName'] in [from_zone, to_zone]]
        else:
            return result

    def CurrentTimebyZone(self, zone_name):
        """
        Get the current time for a specific timezone with region.

        Parameters:
        zone_name (str): The name of the time zone (e.g., 'America/New_York').
        """
        if not self.__Request:
            return None

        original_url = self.__Request.base_url
        temp = Shift.type.map('aHR0cDovL3dvcmxkdGltZWFwaS5vcmcvYXBpL3RpbWV6b25lLw==', zone_name, ret=True)
        self.__Request.update_base_url(temp)
        try:
            result = self.__Request.make_request(params={})
        finally:
            self.__Request.update_base_url(original_url)
        if 'response' in result:
            return result['response']["datetime"]
        else:
            return result






TimeZoner = None

try:
    rq_instance = Request(use_api_key=True)
    timezonedata = tzoneDataManager().restructured_data
    TimeZoner = ZoneInfoManager(timezonedata, rq_instance)
except Exception as e:
    print(f"Failed to initialize TimeZoner due to: {e}")

# TimeZoner Fail
if TimeZoner is None:
    class ImportError(Exception):
        def __init__(self, message="TimeZoner could not be imported correctly and cannot be used."):
            self.message = message
            super().__init__(self.message)
    
    TimeZoner = lambda *args, **kwargs: (_ for _ in ()).throw(ImportError())


__all__ = ['TimeZoner']


