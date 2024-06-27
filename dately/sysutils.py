import time

# Define public interface
__all__ = ['UnixTime']

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
