import os
import json
import tempfile
import shutil
import requests
import time
import random
import re
import pandas as pd

from .mskutils import *
from .sysutils import *

TimeZoner = None


class NoAPIKeysError(Exception):
    """Exception raised when no API keys are available."""
    pass
   
class Request:
    def __init__(self, base_url='aHR0cDovL2FwaS50aW1lem9uZWRiLmNvbS92Mi4xL2xpc3QtdGltZS16b25lP2tleT0=', use_api_key=True):
        """ Initialize the API utility with the given base URL. """
        self.base_url = Shift.format.chr(base_url, "format")
        self.use_api_key = use_api_key
        self.api_keys = {}
        self.last_key = None
        self.last_request_time = 0
        self.rate_limit_limit = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        if self.use_api_key:
            self.initialize()
            
    def initialize(self):
        """Initialize the API utility by fetching API keys if not already present."""
        if not self.api_keys:
            self.fetch_api_keys()

    def fetch_api_keys(self):
        """Fetch API keys from the specified URL and store them in the api_keys dictionary."""
        url_unformatted = 'aHR0cHM6Ly90aW1lem9uemVkYXRhLm5ldGxpZnkuYXBwL2RhdGEuanNvbg=='
        url = Shift.format.chr(url_unformatted, "format")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.api_keys = response.json()
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

    def update_base_url(self, new_url):
        """ Update the base URL for the API utility. """
        self.base_url = new_url

    def set_use_api_key(self, use_api_key):
        self.use_api_key = use_api_key
        if self.use_api_key and not self.api_keys:
            self.initialize()

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

    def make_request(self, params, headers=None):
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
            params['key'] = api_key

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



class parse_zoneinfo_html_table:
    """
    This class is designed to parse an HTML IANA Time Zones table from a specified URL, clean the HTML content,
    and structure the table data in a format suitable for data analysis using pandas.
    """
    def __init__(self, url='aHR0cHM6Ly90aW1lYXBpLmlvL2RvY3VtZW50YXRpb24vaWFuYS10aW1lem9uZXM='):
        self.url = Shift.format.chr(url, "format")
        self.html_content = self.fetch_html_content()

    def fetch_html_content(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status() 
            return response.text
        except Exception as e:
            return None

    def clean_html(self, raw_html):
        try:
            clean_re = re.compile('<.*?>')
            clean_text = re.sub(clean_re, '', raw_html)
            clean_text = clean_text.replace('&#x2B;', '+')
            clean_text = clean_text.replace('&nbsp;', ' ')
            return clean_text
        except Exception as e:
            return None

    def extract_tag_contents(self, html, tag_name, first_only=False):
        try:
            pattern = f'<{tag_name}.*?>.*?</{tag_name}>'
            tags = re.findall(pattern, html, re.DOTALL)
            if first_only:
                return tags[0] if tags else None
            return tags
        except Exception as e:
            return []

    def extract_table_from_html(self):
        try:
            table_html = self.extract_tag_contents(self.html_content, 'table', first_only=True)
            if not table_html:
                return None, None
            headers = []
            headers_html = self.extract_tag_contents(table_html, 'tr', first_only=True)
            for header_content in self.extract_tag_contents(headers_html, 'th'):
                headers.append(self.clean_html(header_content).strip())
            rows = []
            row_tags = self.extract_tag_contents(table_html, 'tr')[1:]
            for row_html in row_tags:
                row_data = []
                for cell_content in self.extract_tag_contents(row_html, 'td'):
                    row_data.append(self.clean_html(cell_content).strip())
                rows.append(row_data)

            return headers, rows
        except Exception as e:
            return None, None

    def replace_empty_with_none(self, table_data):
        try:
            return [[None if item == '' else item for item in sublist] for sublist in table_data]
        except Exception as e:
            return None

    def to_dataframe(self):
        headers, rows = self.extract_table_from_html()
        if headers is None or rows is None:
            return None
        updated_rows = self.replace_empty_with_none(rows)
        try:
            return pd.DataFrame(updated_rows, columns=headers)
        except Exception as e:
            return None
 
 

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
    """ Manages the saving and loading of json data """
    def __init__(self, timezonedata=None, storage_dir=None):
        self.timezonedata = timezonedata
        self.IANAtbl = parse_zoneinfo_html_table().to_dataframe()
        self.storage_dir = storage_dir or self.get_temp_storage_dir()
        self.jsonfilename = 'tzdata.json'
        self.filename = os.path.join(self.storage_dir, self.jsonfilename)

    @staticmethod
    def get_temp_storage_dir():
        """Get or create the temporary storage directory."""
        temp_dir = tempfile.gettempdir()
        tz_temp_dir = os.path.join(temp_dir, "dately_timezone_manager")
        if not os.path.exists(tz_temp_dir):
            os.makedirs(tz_temp_dir)
        return tz_temp_dir

    def clean_old_files(self):
        """Remove old JSON files from the storage directory."""
        for f in os.listdir(self.storage_dir):
            if f.endswith('.json'):
                os.remove(os.path.join(self.storage_dir, f))

    @classmethod
    def data_file_exists(cls):
        """Check if the data file exists in the storage directory."""
        filename = 'tzdata.json'
        storage_dir = cls.get_temp_storage_dir()
        return os.path.exists(os.path.join(storage_dir, filename))

    def load_data_from_file(self):
        """Load time zone data from the JSON file if it exists."""
        if self.data_file_exists():
            with open(self.filename, 'r') as f:
                self.timezonedata = json.load(f)
        else:
            self.timezonedata = None
        self.timezonedata = self.__restructure_data()

    def __merge_with_iana_data(self):
        """Merge the time zone data with IANA table data and format offsets."""
        if self.timezonedata and self.IANAtbl is not None:
            for info in self.timezonedata:
                zone_name = info['zoneName']
                row = self.IANAtbl[self.IANAtbl['IANA Time Zone'] == zone_name.strip()]

                if not row.empty:
                    std_offset = row['UTC offset (STD)'].values[0]
                    dst_offset = row['UTC offset (DST)'].values[0]
                    std_abbr = row['Abbreviation (STD)'].values[0]
                    dst_abbr = row['Abbreviation (DST)'].values[0]

                    info.update({
                        'UTC offset (STD)': std_offset,
                        'UTC offset (DST)': dst_offset,
                        'Abbreviation (STD)': std_abbr,
                        'Abbreviation (DST)': dst_abbr
                    })

            for record in self.timezonedata:
                if 'Offset' in record and record['Offset'] is not None:
                    record['Offset'] = TimezoneOffset.format(record['Offset'])
                if 'UTC offset (STD)' in record and record['UTC offset (STD)'] is not None:
                    record['UTC offset (STD)'] = TimezoneOffset.format(record['UTC offset (STD)'])
                if 'UTC offset (DST)' in record and record['UTC offset (DST)'] is not None:
                    record['UTC offset (DST)'] = TimezoneOffset.format(record['UTC offset (DST)'])
                if 'Abbreviation (STD)' in record and record['Abbreviation (STD)'] is not None:
                    record['Abbreviation (STD)'] = TimezoneOffset.format(record['Abbreviation (STD)'])
                if 'Abbreviation (DST)' in record and record['Abbreviation (DST)'] is not None:
                    record['Abbreviation (DST)'] = TimezoneOffset.format(record['Abbreviation (DST)'])

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
                    'Abbreviation (DST)': entry.get('Abbreviation (DST)')
                }
            return restructured_data
        return None

    def save_data_to_file(self):
        """Save the time zone data to a JSON file after merging with IANA data."""
        self.clean_old_files()
        self.__merge_with_iana_data()

        if self.timezonedata:
            with open(self.filename, 'w') as f:
                json.dump(self.timezonedata, f, indent=4)
        self.timezonedata = self.__restructure_data()

    def cleanup(self):
        """Remove the storage directory and all its contents."""
        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)


class DatelyTz:
    """DatelyTz class is responsible for managing timezone data retrieval."""
    def __init__(self, rq_instance=None):
        """Initialize the DatelyTz class. Loads data from file if it exists, otherwise fetches from the API and saves it."""
        self.tzone_manager = tzoneDataManager()
        self.Request = rq_instance

        if tzoneDataManager.data_file_exists():
            self.tzone_manager.load_data_from_file()
            self.timezonedata = self.tzone_manager.timezonedata
        else:
            self.timezonedata = self._from_api()
            self.tzone_manager.timezonedata = self.timezonedata
            self.tzone_manager.save_data_to_file()
            
            self.tzone_manager.load_data_from_file()
            self.timezonedata = self.tzone_manager.timezonedata

    def _from_api(self):
        """Fetch data from the API with a controlled request interval. Formats and returns the data."""
        if not self.Request:
            return None
        params = {}
        result = self.Request.make_request(params)
        if 'response' in result:
            data = result['response']
            return self._format_api_data(data)
        else:
            return result

    def _format_api_data(self, data):
        """Format the API data, adjusting offsets and handling zone information. Returns the formatted data."""
        if 'zones' in data:
            zones_data = data['zones']
            formatted_zones = [
                {
                    ('Offset' if k == 'gmtOffset' else k): (TimezoneOffset.format(v) if k == 'gmtOffset' else v)
                    for k, v in zone.items() if k != 'timestamp'
                }
                for zone in zones_data
            ]
            return formatted_zones
        else:
            return data


class ZoneInfoManager:
    """
    A class to manage and query time zone information.

    Attributes:
    -----------
    Zones : list
        A sorted list of all time zone names.
    CountryCodes : list
        A sorted list of unique country codes present in the time zone data.
    ZonesByCountry : dict
        A dictionary mapping country codes to a list of their respective time zones.
    Offsets : dict
        A dictionary mapping offsets to a list of time zones with that offset.
    CountryNames : list
        A sorted list of unique country names present in the time zone data.
    ObservesDST : dict
        A dictionary categorizing time zones by their observance of daylight saving time (DST).

    Methods:
    --------
    FilterZoneDetail(zone_name):
        Retrieve detailed information for a specific time zone.
    ConvertTimeZone(from_zone, to_zone, year=None, month=None, day=None, hour=None, minute=None, second=None):
        Convert time from one time zone to another.
    CurrentTimebyZone(zone_name):
        Get the current time for a specific time zone.
    """
    def __init__(self, timezonedata, rq_instance=None):
        self.__data = timezonedata
        self.__Request = rq_instance
        self.Zones = sorted(self.__data.keys())
        self.CountryCodes = sorted(self.__get_unique_country_codes())
        self.ZonesByCountry = self.__get_zones_by_country()
        self.Offsets = self.__get_zones_by_offset()
        self.CountryNames = sorted(self.__get_unique_country_names())
        self.ObservesDST = self.__get_zones_by_dst_observance()

    def __dir__(self):
        original_dir = super().__dir__()
        return [item for item in original_dir if not item.startswith('_')]

    def __get_unique_country_codes(self):
        return {entry['countryCode'] for entry in self.__data.values()}

    def __get_unique_country_names(self):
        return {entry['countryName'] for entry in self.__data.values()}

    def __get_zones_by_country(self):
        zones_by_country = {}
        for zone_name, details in self.__data.items():
            country_code = details['countryCode']
            if country_code not in zones_by_country:
                zones_by_country[country_code] = []
            zones_by_country[country_code].append(zone_name)
        return zones_by_country

    def __get_zones_by_offset(self):
        zones_by_offset = {}
        for zone_name, details in self.__data.items():
            offset = details['Offset']
            if offset not in zones_by_offset:
                zones_by_offset[offset] = []
            zones_by_offset[offset].append(zone_name)
        return zones_by_offset
       
    def __get_zones_by_dst_observance(self):
        zones_with_dst = []
        zones_without_dst = []
        for zone_name, details in self.__data.items():
            dst_value = details['UTC offset (DST)']
            if dst_value is None or (isinstance(dst_value, str) and dst_value.isalpha() and dst_value.isupper()):
                zones_without_dst.append(zone_name)
            else:
                zones_with_dst.append(zone_name)
        return {'observes_dst': zones_with_dst, 'does_not_observe_dst': zones_without_dst}

    def __update_api_url(self, new_url):
        """ Update the base URL for the Request utility."""
        if not self.__Request:
            return None
        self.__Request.update_base_url(new_url)

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
        # Convert the provided date and time components to a Unix timestamp
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


try:
    rq_instance = Request(use_api_key=True)
    tz = DatelyTz(rq_instance)
    timezonedata = tz.tzone_manager.timezonedata
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
