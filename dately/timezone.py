import os
import json
import time
import re
import pandas as pd

from .mskutils import *
from .sysutils import DataImport
from .connect import HTTP


def get_timezone_data():
    return DataImport.load_timezone_data()

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
    def __init__(self, timezonedata, http_instance=None):
        self.__data = timezonedata
        self.__HTTP = http_instance

    def __dir__(self):
        original_dir = super().__dir__()
        return [item for item in original_dir if not item.startswith('_')]

    def __update_key_type(self, new_key_type):
        """ Temporarily update the API key type for the HTTP utility. """
        if not self.__HTTP:
            return None
        original_key_type = self.__HTTP.current_key_type
        self.__HTTP.set_key_type(new_key_type)
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
        if not self.__HTTP:
            return None
        original_key_type = self.__update_key_type("DependentVersion")
        original_url = self.__HTTP.base_url
        temp = Shift.type.map('aHR0cHM6Ly9hcGkuaXBnZW9sb2NhdGlvbi5pby90aW1lem9uZQ==', ret=True)
        self.__HTTP.update_base_url(temp)
        try:
            result = self.__HTTP.make_request(params={}, api_key_param_name='apiKey')
        finally:
            if original_key_type:
                self.__HTTP.set_key_type(original_key_type)
            if original_url:
                self.__HTTP.update_base_url(original_url)
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
        if not self.__HTTP:
            return None
        params = {
            'from': from_zone,
            'to': to_zone,
            'time': timestamp
        }
        result = self.__HTTP.make_request(params)
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
        if not self.__HTTP:
            return None

        original_url = self.__HTTP.base_url
        temp = Shift.type.map('aHR0cDovL3dvcmxkdGltZWFwaS5vcmcvYXBpL3RpbWV6b25lLw==', zone_name, ret=True)
        self.__HTTP.update_base_url(temp)
        try:
            result = self.__HTTP.make_request(params={})
        finally:
            self.__HTTP.update_base_url(original_url)
        if 'response' in result:
            return result['response']["datetime"]
        else:
            return result

    def Object(self, zone_name=None, current=False, as_datetime=False):
        """
        Get the timezone object for a given zone name or the current timezone, optionally returning current datetime.

        :param zone_name: String representing the zone name, used if 'current' is False.
        :param current: Boolean, if True, fetches the timezone object for the current user timezone and ignores 'zone_name'.
        :param as_datetime: Boolean, if True, returns the current datetime in the fetched timezone.
        :return: The timezone object associated with the zone name or current timezone, or None if not found. 
                 If as_datetime is True, returns the current datetime in that timezone.
        """
        if current:
            current_timezone = self.MyTimeZone.get('timezone', None) if self.MyTimeZone else None
            if current_timezone:
                return self.Object(zone_name=current_timezone, current=False, as_datetime=as_datetime)
            else:
                print("Current timezone data not available.")
                return None
        else:
            zone_data = self.__data.get(zone_name)
            if zone_data:
                timezone_object = zone_data.get('timezone_object')
                if as_datetime and timezone_object:
                    if hasattr(timezone_object, 'zone'):
                        from datetime import datetime
                        current_time = datetime.now(timezone_object)
                        return current_time
                    else:
                        print(f"The timezone object for {zone_name} does not support datetime operations.")
                        return None
                return timezone_object
            else:
                print(f"Timezone {zone_name} not found.")
                return None

TimeZoner = None

try:
    http_instance = HTTP(use_api_key=True)
    timezonedata = tzoneDataManager().restructured_data
    TimeZoner = ZoneInfoManager(timezonedata, http_instance)
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





