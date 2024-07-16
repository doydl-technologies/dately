import requests
import time
import random
from collections import deque
from .mskutils import *
from .sysutils import UnixTime


class UserAgentRandomizer:
    """
    A class responsible for randomizing user agents from a predefined list of popular user agents across different platforms and browsers.
    This class now includes a mechanism to reduce the likelihood of selecting a user agent that has been chosen frequently in the recent selections.

    Attributes:
        user_agents (dict): A class-level dictionary containing user agents categorized by platform and browser combinations. Each platform has its own nested dictionary with browser-specific user agents.
        recent_selections (deque): A deque to track the history of the last five selections to dynamically adjust selection probabilities.

    Methods:
        get_random_user_agent(): Randomly selects and returns a user agent string from the aggregated list of all available user agents, with adjustments based on recent usage to discourage frequent repeats.
    """
    user_agents = {
        "Desktop User-Agents": {
            "Windows and Edge/Chrome/Safari": {
                "1": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Edge/114.0.1823.79',
                "2": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
                "3": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Edg/114.0.1823.79',
                "4": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
                "5": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
                "6": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Edg/114.0.1823.79',
            },
            "Mac OS and Safari/Chrome/Firefox": {
                "1": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
                "2": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/15.0 Safari/601.3.9',
                "3": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
                "4": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0',
                "5": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
            },
            "Linux and Chrome/Firefox": {
                "1": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
                "2": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
                "3": 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
                "4": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',
                "5": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
            }
        }
    }

    recent_selections = deque(maxlen=5)

    @staticmethod
    def get_random_user_agent():
        """
        Retrieves a random user agent string from the predefined list of user agents across various platforms and browsers.
        Adjusts the selection process based on the history of the last five selections to discourage frequently repeated choices.
        """
        all_user_agents = []
        for category in UserAgentRandomizer.user_agents.values():
            for subcategory in category.values():
                all_user_agents.extend(subcategory.values())

        choice = random.choice(all_user_agents)
        while UserAgentRandomizer.recent_selections.count(choice) >= 3:
            choice = random.choice(all_user_agents)

        UserAgentRandomizer.recent_selections.append(choice)
        return choice




class HTTPLite:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HTTPLite, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, base_url=None):
        if not self.initialized:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': UserAgentRandomizer.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1', 
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1', 
                'Referer': 'https://www.google.com'
            })
            self.last_request_time = None
            self.initialized = True
        self.base_url = Shift.format.chr(base_url, "format")
        
    def update_base_url(self, new_url):
        """ Update the base URL for the class"""
        self.base_url = new_url

    def random_delay(self):
        if self.last_request_time is not None:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < 3:
                time.sleep(3 - elapsed_time)
        self.last_request_time = time.time()

    def make_request(self, params):
        """
        Sends a request to the server with specified parameters to format the response.

        Args:
            params (dict): A dictionary specifying the desired response format. Valid keys and values include:
                'json': Request the response in JSON format.
                'xml': Request the response in XML format.
                'csv': Request the response in CSV format.
                'text' or 'plain': Request the response in plain text format.
                'html': Request the response in HTML format.
                
        Returns:
            dict: A dictionary containing the server's response. The format of the response
            depends on the 'format' parameter provided:
                - For 'json', returns the response as a JSON-decoded dictionary.
                - For all other formats, returns the response as a plain string.

        Notes:
            - If no 'format' is specified in params, the response defaults to JSON format.
            - The method automatically handles necessary delays between requests to manage load.
        """
        self.random_delay()
        
        if 'format' not in params:
            params['format'] = 'json'

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            if params['format'] == 'json':
                return {'response': response.json()}
            else:
                return {'response': response.text}
        except Exception:
            return None


class NoAPIKeysError(Exception):
    """Exception raised when no API keys are available."""
    pass

class HTTP:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HTTP, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_url='aHR0cDovL2FwaS50aW1lem9uZWRiLmNvbS92Mi4xL2xpc3QtdGltZS16b25lP2tleT0=', use_api_key=True, default_key_type="FullVersion"):
        if not hasattr(self, 'initialized'):
            self.session = requests.Session()
            self.base_url = Shift.format.chr(base_url, "format")
            self.use_api_key = use_api_key
            self.api_keys = {}
            self.last_key = None
            self.last_request_time = None
            self.rate_limit_limit = None
            self.rate_limit_remaining = None
            self.rate_limit_reset = None
            self.default_key_type = default_key_type
            self.current_key_type = default_key_type
            self.initialized = True
            self.user_agent = self.session.headers.update({
                'User-Agent': UserAgentRandomizer.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',  # Do Not Track request header
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',  # Tells the server to upgrade insecure requests
                'Referer': 'https://www.google.com'  # Set to: traffic is coming from Google
            })
            
            if self.use_api_key:
                self.initialize()

    def initialize(self):
        """Initialize the API utility by fetching API keys if not already present."""
        if not self.api_keys:
            self.fetch_api_keys()

    def fetch_api_keys(self):
        """Fetch API keys from the specified URL and store them in the api_keys dictionary."""
        url_unformatted = 'aHR0cHM6Ly96b256ZXMubmV0bGlmeS5hcHAvZGF0YS5qc29u'
        url = Shift.format.chr(url_unformatted, "format")
        try:
            response = self.session.get(url, timeout=10)
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

    def random_delay(self):
        """Ensure there is at least a 3 second delay between requests."""
        if self.last_request_time is not None:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < 3:
                time.sleep(3 - elapsed_time)
        self.last_request_time = time.time()


    def make_request(self, params, api_key_param_name="key", headers=None, response_format='json'):
        """ Make a request to the specified API. """
        if headers is None:
            headers = {}
        else:
            headers = headers.copy()

        if self.use_api_key:
            headers.pop('Referer', None) 
            api_key = self.get_random_key()
            params[api_key_param_name] = api_key
        else:
            if 'Referer' not in headers:
                headers['Referer'] = 'https://www.google.com'

        self.random_delay()  # Delay between requests to mimic human behavior

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

        if 'format' not in params:
            params['format'] = 'json'

        try:
            response = self.session.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            rate_limit_info = self.extract_rate_limit_info(response.headers)

            if response_format == 'json':
                return {
                    'response': response.json(),
                    'rate_limit_info': rate_limit_info
                }
            else:
                return {
                    'response': response.text,
                    'rate_limit_info': rate_limit_info
                }

        except Exception as e:
            self.log_rate_limit_status()
            return {
                'status': 'error',
                'message': str(e),
                'rate_limit_info': self.extract_rate_limit_info({})
            }


__all__ = ['HTTP', 'HTTPLite']



