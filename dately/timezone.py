import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
import random
import os
import tempfile
import pickle
import pytz
import shutil
import sys
# import base64

from .utils import check_version_sufficiency

# Retrieve the current Python version as a string (e.g., "3.9.1")
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

# Check if the current Python version is sufficient (greater than version 3.8)
if check_version_sufficiency(python_version):
    from zoneinfo import ZoneInfo  # Import ZoneInfo for time zone handling
    version_sufficient = True
else:
    version_sufficient = False


    
    
class APIManager:
    """
    APIManager handles interactions with the IP geolocation API, including fetching API keys and constructing API URLs.

    Attributes:
        base_url (str): The base URL for the API endpoint.
        api_keys (dict): A dictionary of API keys fetched from a remote server.
        last_key (str): The last API key used.
        api_url (str): The complete API URL including the API key.

    Methods:
        __init__():
            Initializes the APIManager with default URLs and fetches API keys.

        fetch_api_keys():
            Fetches API keys from a remote server.

        get_random_key():
            Selects a random API key from the fetched keys and constructs the API URL.

        __get_all_keys():
            Returns a list of all API keys.
    """
    def __init__(self):
        self.base_url = 'https://api.ipgeolocation.io/timezone?apiKey='
        self.api_keys = self.fetch_api_keys()
        self.last_key = None
        self.api_url = None

    def fetch_api_keys(self):
        url = 'https://timezonzedata.netlify.app/data.json'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except ConnectionError as e:
            print("Failed to connect to server:", e)
            return {}  
        except HTTPError as e:
            print("HTTP error occurred:", e)
            return {}  
        except Timeout as e:
            print("The request timed out:", e)
            return {}  
        except ValueError as e:
            print("Invalid JSON:", e)
            return {}  
        except Exception as e:
            print("An error occurred:", e)
            return {}

    def binhex(self, binary_string):
        integer_value = int(binary_string, 2)
        hex_string = hex(integer_value)
        hex_string = hex_string[2:]
        return hex_string

##    def dbinhex(self, data, mode):
##        if mode == "e":
##            return base64.b64encode(data.encode('utf-8')).decode('utf-8')
##        elif mode == "d":
##            return base64.b64decode(data).decode('utf-8')
##        else:
##            raise ValueError("Invalid mode. Use 'e' or 'd'.")
    
    def get_random_key(self):
        keys = list(self.api_keys.keys())
        random_key = random.choice(keys)
        while random_key == self.last_key:
            random_key = random.choice(keys)
        self.last_key = random_key
        api_key_binary = self.api_keys[random_key]['key']
        api_key_hex = self.binhex(api_key_binary)
        #fixed_base = f'{self.dbinhex(self.base_url, "d")}'
        #self.api_url = f'{fixed_base}{api_key_hex}'
        self.api_url = f'{self.base_url}{api_key_hex}'
        return api_key_hex

    def __get_all_keys(self):
        return [details['key'] for details in self.api_keys.values()]





class TimezoneOffset:
    """
    TimezoneOffset represents a timezone offset and provides methods to format and display the offset.

    Attributes:
        offset (str or float): The timezone offset, which can be a string or a float.

    Methods:
        __init__(offset):
            Initializes the TimezoneOffset with the given offset.
        
        offset_format():
            Returns the offset formatted as a string in the format HH:MM.
        
        __str__():
            Returns the string representation of the offset.
        
        __repr__():
            Returns the string representation of the offset.
    """
    def __init__(self, offset):
        self.offset = offset

    def offset_format(self):
        number = self.offset
        if number == '':
            return ''
           
        if isinstance(number, str):
            number = float(number)
        
        sign = '+' if number >= 0 else '-'
        abs_number = abs(number)
        hours = int(abs_number)
        minutes = int((abs_number - hours) * 60)
        formatted_time = f"{sign}{hours:02}:{minutes:02}"
        return formatted_time

    def __str__(self):
        return str(self.offset)
    
    def __repr__(self):
        return str(self.offset)




class tzoneObjectManager:
    """
    tzoneObjectManager manages the serialization and deserialization of timezone information.

    Attributes:
        timezone_str (str): The string representation of the timezone.
        timezone (ZoneInfo or pytz.timezone): The timezone object.
        storage_dir (str): The directory where the timezone files are stored.
        pklfilename (str): The filename for the pickled timezone object.
        filename (str): The full path to the pickled timezone object file.

    Methods:
        __init__(timezone_str, storage_dir=None):
            Initializes the tzoneObjectManager with a timezone string and optional storage directory.

        get_temp_storage_dir():
            Static method that returns the path to the temporary storage directory, creating it if it doesn't exist.

        clean_old_files():
            Deletes old timezone pickle files from the storage directory.

        save_timezone():
            Saves the current timezone object to a pickle file.

        tzone_instance():
            Loads the timezone object from a pickle file if it exists, or returns the current timezone object.

        timezone_file_exists(cls, timezone_str):
            Class method that checks if a timezone pickle file exists for the given timezone string.

        cleanup():
            Removes the storage directory and all its contents.
    """
    def __init__(self, timezone_str, storage_dir=None):
        self.timezone_str = timezone_str
        self.timezone = None
        self.storage_dir = storage_dir or self.get_temp_storage_dir()
        self.pklfilename = f'{self.timezone_str.replace("/", ".&.")}.pkl'
        self.filename = os.path.join(self.storage_dir, self.pklfilename)
    
    @staticmethod
    def get_temp_storage_dir():
        temp_dir = tempfile.gettempdir()
        tz_temp_dir = os.path.join(temp_dir, "dately_timezone_manager")
        if not os.path.exists(tz_temp_dir):
            os.makedirs(tz_temp_dir)
        return tz_temp_dir
    
    def clean_old_files(self):
        for f in os.listdir(self.storage_dir):
            if f.endswith('.pkl'):
                os.remove(os.path.join(self.storage_dir, f))
    
    def save_timezone(self):
        if self.timezone_str:
            try:
                if version_sufficient:
                    self.timezone = ZoneInfo(self.timezone_str)
                else:
                    self.timezone = pytz.timezone(self.timezone_str)
                self.clean_old_files()
                with open(self.filename, 'wb') as f:
                    pickle.dump(self.timezone, f)
            except Exception as e:
                print(f"Error saving timezone: {e}")

    def tzone_instance(self):
        if not self.timezone:
            if os.path.exists(self.filename):
                try:
                    with open(self.filename, 'rb') as f:
                        self.timezone = pickle.load(f)
                except Exception as e:
                    print(f"Error loading timezone: {e}")
                    return None
            else:
                print("Timezone file not found, please save the timezone first.")
                return None
        return self.timezone
    
    @classmethod
    def timezone_file_exists(cls, timezone_str):
        filename = f'{timezone_str.replace("/", ".&.")}.pkl'
        storage_dir = cls.get_temp_storage_dir()
        return os.path.exists(os.path.join(storage_dir, filename))
    
    def cleanup(self):
        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)



class DatelyTz:
    """
    DatelyTz is a class that manages timezone-related data and operations.

    Attributes:
        geo (dict): Geographical data including country codes and names.
        timezone (str): The timezone identifier.
        timezone_offset (TimezoneOffset): Timezone offset information.
        timezone_offset_with_dst (TimezoneOffset): Timezone offset with DST applied.
        is_dst (str): Indicator if DST is currently applied.
        dst_savings (str): The amount of time saved during DST.
        dst_exists (str): Indicator if DST exists in the timezone.
        dst_start (dict): Details of the DST start event.
        dst_end (dict): Details of the DST end event.
        tzone_manager (tzoneObjectManager): Manager for timezone objects.
        tzone_timezone (optional): The timezone instance managed by `tzoneObjectManager`.

    Methods:
        __init__(data):
            Initializes the DatelyTz instance with the given data.
        
        _from_api(cls, api_manage):
            Class method to create a DatelyTz instance from API data.
        
        tzone_instance():
            Manages the timezone instance, either loading or saving it as needed.

    """
    def __init__(self, data):
        """
        Initializes the DatelyTz instance with the given data.

        Args:
            data (dict): A dictionary containing timezone and geographical data.
        """
        self.geo = data.get('geo', {})
        self.timezone = data.get('timezone', '')
        self.timezone_offset = TimezoneOffset(data.get('timezone_offset', ''))
        self.timezone_offset_with_dst = TimezoneOffset(data.get('timezone_offset_with_dst', ''))
        self.is_dst = data.get('is_dst', '')
        self.dst_savings = data.get('dst_savings', '')
        self.dst_exists = data.get('dst_exists', '')
        self.dst_start = data.get('dst_start', {})
        self.dst_end = data.get('dst_end', {})
        self.tzone_manager = tzoneObjectManager(self.timezone)
        self.tzone_timezone = None

    @classmethod
    def _from_api(cls, api_manage):
        """
        Class method to create a DatelyTz instance from API data.

        Args:
            api_manage: An object that manages API keys and URLs.

        Returns:
            DatelyTz: A new instance of DatelyTz populated with data from the API.
            None: If an error occurs during the API request.
        """
        try:
            api_key = api_manage.get_random_key()
            response = requests.get(api_manage.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

        except ConnectionError as e:
            print("Failed to connect to API:", e)
            return None  
        except HTTPError as e:
            print("HTTP error occurred:", e)
            return None  
        except Timeout as e:
            print("The request timed out:", e)
            return None  
        except Exception as e:
            print("An error occurred:", e)
            return None  
        
        def __safe_get(d, keys, default=''):
            assert isinstance(keys, list)
            for key in keys:
                try:
                    d = d[key]
                except KeyError:
                    return default
            return d
        
        filtered_data = {
            'geo': {
                'country_code2': __safe_get(data, ['geo', 'country_code2']),
                'country_code3': __safe_get(data, ['geo', 'country_code3']),
                'country_name': __safe_get(data, ['geo', 'country_name']),
                'country_name_official': __safe_get(data, ['geo', 'country_name_official'])
            },
            'timezone': data.get('timezone', ''),
            'timezone_offset': data.get('timezone_offset', ''),
            'timezone_offset_with_dst': data.get('timezone_offset_with_dst', ''),
            'is_dst': data.get('is_dst', ''),
            'dst_savings': data.get('dst_savings', ''),
            'dst_exists': data.get('dst_exists', ''),
            'dst_start': {
                'utc_time': __safe_get(data, ['dst_start', 'utc_time']),
                'duration': __safe_get(data, ['dst_start', 'duration']),
                'gap': __safe_get(data, ['dst_start', 'gap']),
                'dateTimeAfter': __safe_get(data, ['dst_start', 'dateTimeAfter']),
                'dateTimeBefore': __safe_get(data, ['dst_start', 'dateTimeBefore']),
                'overlap': __safe_get(data, ['dst_start', 'overlap'])
            },
            'dst_end': {
                'utc_time': __safe_get(data, ['dst_end', 'utc_time']),
                'duration': __safe_get(data, ['dst_end', 'duration']),
                'gap': __safe_get(data, ['dst_end', 'gap']),
                'dateTimeAfter': __safe_get(data, ['dst_end', 'dateTimeAfter']),
                'dateTimeBefore': __safe_get(data, ['dst_end', 'dateTimeBefore']),
                'overlap': __safe_get(data, ['dst_end', 'overlap'])
            }
        }

        return cls(filtered_data)
       
    def tzone_instance(self):
        """
        Manages the timezone instance, either loading or saving it as needed.
        """
        if tzoneObjectManager.timezone_file_exists(self.timezone):
            self.tzone_manager.tzone_instance()
        else:
            self.tzone_manager.save_timezone()
        self.tzone_timezone = self.tzone_manager.tzone_instance()


api_manage = APIManager()
DatelyTzInstance = DatelyTz._from_api(api_manage)
DatelyTzInstance.tzone_instance()


class DataFromIP:
    """
    Retrieves and manages timezone-related attributes based on the user's IP address.

    The class initializes with data obtained from an instance of DatelyTz, which includes comprehensive timezone and geographical information.

    Attributes:
        geo (dict): A dictionary containing geographical data.
            - country_code2 (str): Two-letter country code (ISO 3166-1 alpha-2).
            - country_code3 (str): Three-letter country code (ISO 3166-1 alpha-3).
            - country_name (str): Full country name.
            - country_name_official (str): Official country name.

        timezone (str): The IANA timezone identifier (e.g., "America/New_York").

        timezone_offset (TimezoneOffset): The standard time offset from UTC for the timezone.

        timezone_offset_with_dst (TimezoneOffset): The time offset from UTC with Daylight Saving Time (DST) applied.

        is_dst (str): Indicator if Daylight Saving Time (DST) is currently applied ("yes" or "no").

        dst_savings (str): The amount of time (in hours) saved during Daylight Saving Time.

        dst_exists (str): Indicator if Daylight Saving Time (DST) exists in the timezone ("yes" or "no").

        dst_start (dict): Details of the DST start event.
            - utc_time (str): The UTC time when DST starts.
            - duration (str): Duration of the DST start event.
            - gap (str): The gap time created by the DST start.
            - dateTimeAfter (str): The local date and time after DST starts.
            - dateTimeBefore (str): The local date and time before DST starts.
            - overlap (str): The overlap time created by the DST start.

        dst_end (dict): Details of the DST end event.
            - utc_time (str): The UTC time when DST ends.
            - duration (str): Duration of the DST end event.
            - gap (str): The gap time created by the DST end.
            - dateTimeAfter (str): The local date and time after DST ends.
            - dateTimeBefore (str): The local date and time before DST ends.
            - overlap (str): The overlap time created by the DST end.

        tzone_timezone (optional): The timezone instance as a pytz or ZoneInfo object, representing the timezone.

    Methods:
        __init__(DatelyTzInstance):
            Initializes the DataFromIP instance with data from a DatelyTzInstance.
    """

    def __init__(self, DatelyTzInstance):
        """
        Initializes the DataFromIP instance with data from a DatelyTzInstance.

        Parameters:
            DatelyTzInstance (DatelyTz): An instance of the DatelyTz class containing the timezone-related data.
        
        Sets the following attributes:
            geo (dict): Geographical data including country codes and names.
            timezone (str): The timezone identifier.
            timezone_offset (TimezoneOffset): Timezone offset information.
            timezone_offset_with_dst (TimezoneOffset): Timezone offset with DST applied.
            is_dst (str): Indicator if DST is currently applied.
            dst_savings (str): The amount of time saved during DST.
            dst_exists (str): Indicator if DST exists in the timezone.
            dst_start (dict): Details of the DST start event.
            dst_end (dict): Details of the DST end event.
            tzone_timezone (optional): The timezone as a pytz or ZoneInfo object.
        """
        self.geo = DatelyTzInstance.geo 
        self.timezone = DatelyTzInstance.timezone 
        self.timezone_offset = DatelyTzInstance.timezone_offset 
        self.timezone_offset_with_dst = DatelyTzInstance.timezone_offset_with_dst 
        self.is_dst = DatelyTzInstance.is_dst 
        self.dst_savings = DatelyTzInstance.dst_savings 
        self.dst_exists = DatelyTzInstance.dst_exists 
        self.dst_start = DatelyTzInstance.dst_start 
        self.dst_end = DatelyTzInstance.dst_end 
        self.tzone_timezone = DatelyTzInstance.tzone_timezone


tz = DataFromIP(DatelyTzInstance)


__all__ = ['tz']






