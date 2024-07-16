import time
import re
import pandas as pd
from html.parser import HTMLParser

from .mskutils import *
from .sysutils import DataImport
from .connect import HTTPLite
from .webutils import absolute_url

def get_holiday_urls():
    return DataImport.load_holiday_urls()

class parse_href_calendar(HTMLParser):
    """
    A custom HTML parser designed to extract calendar data from HTML content,
    specifically looking for tables with an id of 'holidays-table'. This parser
    captures data within the table tags, cleans the data, and processes it to
    include date information with appropriate year adjustments.

    Attributes:
        in_table (bool): Indicates if the parser is currently within the table of interest.
        in_data_tag (bool): Tracks if the parser is inside a data tag (<td> or <th>).
        capture_data (bool): Determines if the parser should capture the text data inside tags.
        data (list): Holds the processed rows of data extracted from the table.
        row (list): Temporarily stores data from a single row of the table.
        html_content (str): Stores the HTML content to be parsed.
        current_year (int): Stores the current year extracted from system's local time.
        current_year_found (int or None): Stores the year found in the HTML title or defaults to current_year.
    """
    def __init__(self):
        """
        Initializes the parser with default values and attributes. Inherits from HTMLParser.
        """
        super().__init__()
        self.in_table = False
        self.in_data_tag = False 
        self.capture_data = False
        self.data = []
        self.row = []
        self.html_content = None 
        self.current_year = time.localtime().tm_year 
        self.current_year_found = None 

    def set_html_content(self, html_content):
        """
        Sets the HTML content for the parser and initiates the parsing process.

        Args:
            html_content (str): The HTML content to parse.
        """
        self.html_content = html_content
        self.feed(html_content)
        self.extract_year_from_title() 
        
    def handle_starttag(self, tag, attrs):
        """
        Handles the start tag of an HTML element. Sets flags and initializes structures
        depending on the tag type and context.

        Args:
            tag (str): The tag of the HTML element.
            attrs (list of tuples): Attributes of the HTML element.
        """
        if tag == 'table':
            if ('id', 'holidays-table') in attrs:
                self.in_table = True

        if self.in_table:
            if tag in ['tr']:
                self.row = []
            if tag in ['td', 'th']:
                self.in_data_tag = True
                self.capture_data = True 

    def handle_endtag(self, tag):
        """
        Handles the end tag of an HTML element. Manages flags and stores data
        depending on the tag type and the context.

        Args:
            tag (str): The tag of the HTML element.
        """
        if tag == 'table':
            self.in_table = False
        if self.in_table and tag in ['tr']:
            self.data.append(self.row)
        if tag in ['td', 'th']:
            self.in_data_tag = False
            self.capture_data = False

    def handle_data(self, data):
        """
        Processes the textual data within HTML tags. Data is cleaned and appended
        to the current row or added to the last element of the row.

        Args:
            data (str): The text data within HTML tags.
        """
        if self.in_table and self.capture_data:
            cleaned_data = data.strip()
            if cleaned_data:
                if self.in_data_tag:
                    self.row.append(cleaned_data)
                else:
                    self.row[-1] += cleaned_data

    def extract_year_from_title(self):
        """
        Extracts the year from the HTML title tag, if present, otherwise defaults
        to the current year. The extracted year is stored in current_year_found.
        """
        title_match = re.search(r'<title>(.*?)</title>', self.html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            year_match = re.search(r'\b\d{4}\b', title)
            if year_match:
                self.current_year_found = int(year_match.group(0))
            else:
                self.current_year_found = self.current_year
        else:
            self.current_year_found = self.current_year

    def clean_data(self):
        """
        Cleans the captured data by removing empty sublists, weekdays, and properly
        formatting date entries with the correct year. Rows without a date are excluded.
        """
        def cleanup_empty_sublists(data):
            return [sublist for sublist in data if sublist]

        def remove_weekdays(data):
            weekday_pattern = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$", re.IGNORECASE)

            def clean_list(input_list):
                cleaned = []
                for item in input_list:
                    if isinstance(item, list):
                        cleaned.append(clean_list(item))
                    elif isinstance(item, str):
                        if not weekday_pattern.match(item):
                            cleaned.append(item)
                    else:
                        cleaned.append(item)
                return cleaned
            return clean_list(data)

        def add_year_to_dates(data, year):
            date_pattern = re.compile(r'([A-Za-z]{3} \d{1,2})')
            
            def process_item(item):
                if isinstance(item, list):
                    return [process_item(sub_item) for sub_item in item]
                elif isinstance(item, str):
                    match = date_pattern.match(item)
                    if match:
                        date_string = f"{match.group(1)} {year}"
                        formatted_date = time.strptime(date_string, '%b %d %Y')
                        return time.strftime('%Y-%m-%d', formatted_date)
                return item
            return [process_item(item) for item in data]

        def trim_columns(data):
            return [row[:3] for row in data]

        def has_valid_date(row):
            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
            return len(row) > 0 and date_pattern.match(row[0])

        cleaned_list = cleanup_empty_sublists(self.data)
        cleaned_list = remove_weekdays(cleaned_list)
        cleaned_list = add_year_to_dates(cleaned_list, self.current_year_found)
        cleaned_list = trim_columns(cleaned_list)

        # Ensure the title row is included
        title_row = cleaned_list[0] if cleaned_list and cleaned_list[0] == ['Date', 'Name', 'Type'] else None
        data_rows = [row for row in cleaned_list if has_valid_date(row)]
        
        if title_row:
            self.data = [title_row] + data_rows
        else:
            self.data = data_rows

    def get_cleaned_data(self):
        """
        Returns the cleaned and formatted data extracted from the HTML content.

        Returns:
            list: The cleaned data with date modifications applied.
        """
        self.clean_data()
        return self.data 


class HolidayManager:
    """
    Manages and retrieves holiday data for various countries by year.

    Attributes:
        __data (list): A list of dictionaries containing URL mappings for holiday data.
        __current_year (int): Stores the current year derived from the system's local time.
        __HTTPLite (object): An instance of a request handling class, used to make HTTP requests.
    """
    def __init__(self, instance_http=None):
        self.__data = get_holiday_urls()
        self.__countries = sorted([entry['Country'] for entry in self.__data])
        self.__current_year = time.localtime().tm_year
        self.__HTTPLite = instance_http

    def __dir__(self):
        original_dir = super().__dir__()
        return [item for item in original_dir if not item.startswith('_')]

    class __transform_data:
        """
        A nested class within HolidayManager that handles the transformation of raw holiday data into
        various formats like lists, dictionaries, or pandas DataFrames.

        Attributes:
            data (list): The raw data to transform.
            keys (list): The keys for the dictionary or DataFrame conversion, extracted from the first row of data.
        """
        def __init__(self, data):
            self.data = data
            self.keys = data[0]

        def to_dataframe(self):
            """Converts the data into a pandas DataFrame."""
            return pd.DataFrame(self.data[1:], columns=self.keys)

        def to_dict_list(self):
            """Converts the data into a list of dictionaries."""
            return [dict(zip(self.keys, values)) for values in self.data[1:]]

        def raw_data(self):
            """Returns the original raw data without any transformation."""
            return self.data
    
    def __get_link_by_country(self, country_name, year=None):
        """
        Get the URL for the holiday data for a specific country and year.
        
        Args:
        - country_name (str): The name of the country.
        - year (int, optional): The year for which to get the holidays. Defaults to current year.
        
        Returns:
        - str: The absolute URL or None if the country is not found.
        """
        if year is None:
            year = self.__current_year
        for entry in self.__data:
            if entry["Country"] == country_name:
                return absolute_url(entry["Link"], f'{year}')
        return None

    @property
    def ListCountries(self):
        """
        Returns a list of country names for which holiday data is available.

        Returns:
            list: A list of country names with available holiday data.
        """
        return self.__countries


    def Holiday(self, country_name, year=None, format='list'):
        """
        Retrieves and processes the holiday data for a specified country and year, returning it in various formats.

        Args:
            country_name (str): The name of the country.
            year (int, optional): The year for which to get the holidays. Defaults to None.
            format (str, optional): The format of the output ('list', 'dict', or 'df'). Defaults to 'list'.

        Returns:
            mixed: The processed holiday data in the requested format.
        """   	
        if country_name not in self.__countries:
            raise ValueError(f"Country '{country_name}' not found in the list of available countries.")
        
        if not self.__HTTPLite:
            return None

        url = self.__get_link_by_country(country_name=country_name, year=year)
        self.__HTTPLite.update_base_url(url)
        try:
            result = self.__HTTPLite.make_request(params={'format': 'html'})
        finally:
            self.__HTTPLite.update_base_url(None)

        if 'response' in result:
            html_content = result['response']
            parser = parse_href_calendar()
            parser.set_html_content(html_content)
            data = parser.get_cleaned_data()
            transformer = self.__transform_data(data)
            
            if format == 'dict':
                return transformer.to_dict_list()
            elif format == 'df':
                return transformer.to_dataframe()
            else:
                return transformer.raw_data()
        else:
            return result

Holidate = None

try:
    instance_http = HTTPLite(base_url='dGltZS5pcy8=')
    Holidate = HolidayManager(instance_http)
except Exception as e:
    print(f"Failed to initialize Holidate due to: {e}")

# Holidate Fail
if Holidate is None:
    class ImportError(Exception):
        def __init__(self, message="Holidate could not be imported correctly and cannot be used."):
            self.message = message
            super().__init__(self.message)
    
    Holidate = lambda *args, **kwargs: (_ for _ in ()).throw(ImportError())

__all__ = ['Holidate']




