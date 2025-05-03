# -*- coding: utf-8 -*-

import random
from collections import OrderedDict
import time
import threading

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import requests
import requests_cache

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._log import logger       
from ._mskutils import Shift
from ._sysutils import UnixTime
from ._webutils import UserAgentRandomizer, find_os_in_user_agent, findhost



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
class NoAPIKeysError(Exception):
    """Exception raised when no API keys are available."""
    pass

class HTTPLite:
    """
    Advanced HTTP Client with:
      - caching (via requests_cache)
      - concurrency support
      - random user-agent
      - optional API key management
      - optional base64-decoded URLs
      - rate limit tracking
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HTTPLite, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, base_url=None, expire_after=600, use_api_key=False, default_key_type="FullVersion"):
        """
        :param base_url: Optional base URL (could be base64-encoded)
        :param expire_after: Cache expiration in seconds
        :param use_api_key: Whether to enable API key usage
        :param default_key_type: Key type to fetch from the remote JSON
        """
        if not self.initialized:
            self.session = requests_cache.CachedSession(
                cache_name='http_cache',
                backend='memory',
                expire_after=expire_after,
                allowable_codes=(200,),
                allowable_methods=('GET',),
            )
            self.session.headers.update({
                "User-Agent": UserAgentRandomizer.get(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Priority": "u=0, i",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": random.choice(["same-origin", "same-site"]),
                "Sec-Fetch-User": "?1",
                "Referer": "https://www.google.com"
            })
            # Determine the OS from the User-Agent and update headers accordingly
            user_agent = self.session.headers['User-Agent']
            os_name = find_os_in_user_agent(user_agent)
            self.session.headers.update({"Sec-Ch-Ua-Platform": os_name})

            # Track requests for concurrency/delays
            self.last_request_time = None
            self.last_host = None
            self.code = None
            self.content_type = None

            # Rate limit info
            self.rate_limit_limit = None
            self.rate_limit_remaining = None
            self.rate_limit_reset = None

            # API key usage
            self.use_api_key = use_api_key
            self.default_key_type = default_key_type
            self.current_key_type = default_key_type
            self.api_keys = {}
            self.last_key = None

            # If we want to do base64 decode for the url
            self.base_url = self._maybe_decode_base64(base_url)
            self.host = findhost(self.base_url) if self.base_url else None

            # If using API keys, fetch them at once
            if self.use_api_key:
                self.initialize_api_keys()

            self.initialized = True
        else:
            # Already initialized => we only possibly re-decode the base_url if changed
            self.base_url = self._maybe_decode_base64(base_url)
            self.host = findhost(self.base_url) if self.base_url else None

    def _maybe_decode_base64(self, url_str):
        """
        If url_str is base64-encoded, decode it. Otherwise, return as is.
        """
        if not url_str:
            return None
        try:
            # If it decodes cleanly, it was base64
            decoded = Shift.format.chr(url_str, "format")
            return decoded
        except Exception:
            # Not valid base64, so just return original
            return url_str

    # ---------------------------
    # API Key Management
    # ---------------------------
    def initialize_api_keys(self):
        """Fetch the API keys if not already loaded."""
        if not self.api_keys:
            self._fetch_api_keys()

    def _fetch_api_keys(self):
        """
        Load keys from a remote JSON.
        """
        url_unformatted = 'aHR0cHM6Ly96b256ZXMubmV0bGlmeS5hcHAvZGF0YS5qc29u'
        url = Shift.format.chr(url_unformatted, "format")
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # fetch the dict for current_key_type, fallback empty if missing
            self.api_keys = data.get(self.current_key_type, {})
        except Exception as e:
            logger.warning(f"Error fetching API keys: {e}")
            self.api_keys = {}

    def set_key_type(self, new_key_type):
        """Change key type and refetch keys."""
        self.current_key_type = new_key_type
        self._fetch_api_keys()

    def reset_key_type(self):
        """Reset to default and refetch."""
        self.current_key_type = self.default_key_type
        self._fetch_api_keys()

    def _get_random_key(self):
        """Select a random key from the loaded dictionary."""
        keys_list = list(self.api_keys.keys())
        if not keys_list:
            raise NoAPIKeysError("No API keys available.")
        random_key = random.choice(keys_list)
        # Avoid repeating the same key if we can
        while random_key == self.last_key and len(keys_list) > 1:
            random_key = random.choice(keys_list)
        self.last_key = random_key

        # The actual key is base64-encoded. Need Shift.format.str() to decode
        api_key_unformatted = self.api_keys[random_key]['key']
        api_key = Shift.format.str(api_key_unformatted, "format")
        return api_key

    # ---------------------------
    # Rate Limit Handling
    # ---------------------------
    def _extract_rate_limit_info(self, headers):
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower.endswith('-limit'):
                self.rate_limit_limit = int(value)
            elif key_lower.endswith('-remaining'):
                self.rate_limit_remaining = int(value)
            elif key_lower.endswith('-reset'):
                self.rate_limit_reset = int(value)

    def _log_rate_limit_status(self):
        if self.rate_limit_reset:
            reset_time = UnixTime.Date(self.rate_limit_reset)
            logger.info(f"Rate limit resets at {reset_time} (Unix epoch: {self.rate_limit_reset}).")
        else:
            logger.info("Rate limit reset time unknown.")

    # ---------------------------
    # URL, Headers, Delay
    # ---------------------------
    def update_base_url(self, new_url):
        self.base_url = self._maybe_decode_base64(new_url)        
        self.host = findhost(self.base_url)

    def random_delay(self, concurrent=False, delay_enabled=False):
        """
        If delay_enabled, inject a random or minimal delay.
        If concurrent is True => random 1-5s
        Otherwise => ensure 3s gap from last request if same host.
        """
        if not delay_enabled:
            return
        if concurrent:
            delay = random.uniform(1, 5)
            time.sleep(delay)
        else:
            # non-concurrent => ensure 3s gap for the same host
            if self.last_host and self.last_host == self.host:
                if self.last_request_time is not None:
                    elapsed_time = time.time() - self.last_request_time
                    if elapsed_time < 3:
                        time.sleep(3 - elapsed_time)
            self.last_request_time = time.time()
            self.last_host = self.host

    def shuffle_headers(self):
        """
        Randomly shuffle the order of request headers for extra obfuscation.
        """
        header_items = list(self.session.headers.items())
        random.shuffle(header_items)
        self.session.headers = OrderedDict(header_items)

    def update_header(self, key, value):
        self.session.headers.update({key: value})

    def get_headers(self, key=None):
        headers = dict(self.session.headers)
        if key:
            return headers.get(key, f"Header '{key}' not found")
        return headers

    def verify_content_type(self, type_input):
        """
        Return 'html' or 'json' based on content type.
        """
        html_patterns = [r'text', r'html', r'charset', r'utf']
        json_patterns = [r'application', r'json']
        content_type = (type_input or '').lower()

        def matches_any(patterns, content):
            return any(re.search(pattern, content) for pattern in patterns)

        if matches_any(html_patterns, content_type):
            return "html"
        elif matches_any(json_patterns, content_type):
            return "json"
        else:
            return None

    def cache_settings(self, expire_after=None, clear_cache=False):
        """
        Update the cache expiration time and optionally clear the cache.

        :param expire_after: New expiration time in seconds (e.g., 300 for 5 minutes).
        :param clear_cache: If True, clears the current cache.
        """
        if clear_cache:
            self.session.cache.clear()
            logger.info("Cache cleared.")

        if expire_after is not None:
            self.session.cache.expire_after = expire_after
            logger.info(f"Cache expiration updated to {expire_after} seconds.")

    # ---------------------------
    # Making Requests
    # ---------------------------
    def make_request(self, params, concurrent=False, return_url=True, delay_enabled=True, api_key_param_name="key"):
        """
        :param params: dict of query params
        :param concurrent: bool => indicates we might run multiple calls in threads
        :param return_url: bool => if True, wrap response in [{url: response_data}]
        :param delay_enabled: bool => if True, enforce random/min delay
        """
        try:
            # If not specifying format => default to 'html'
            if 'format' not in params:
                params['format'] = 'json'

            # Possibly shuffle headers each time
            self.shuffle_headers()

            # If using API keys => put it in params
            if self.use_api_key:
                # api_key_param_name = "key"
                api_key = self._get_random_key()
                params[api_key_param_name] = api_key

            # Actually make the request
            response = self.session.get(self.base_url, params=params)
            self.code = response.status_code
            self.content_type = response.headers.get('Content-Type')

            # If not from cache => do the delay after the request
            if not response.from_cache:
                self.random_delay(concurrent=concurrent, delay_enabled=delay_enabled)

            # Raise if 4xx/5xx
            response.raise_for_status()

            # Extract rate limit info if provided in headers
            self._extract_rate_limit_info(response.headers)

            # Check if rate limit is used up
            if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
                self._log_rate_limit_status()
                return self._handle_rate_limit_exceeded(concurrent, return_url)

            # Force JSON response handling
            response_data = {"response": response.json() if params['format'] == 'json' else response.text}   

            # Return shapes
            if concurrent:
                return response_data
            else:
                if return_url:
                    return [{self.base_url: response_data}]
                else:
                    return response_data

        except requests.exceptions.HTTPError as e:
            error_message = {"error": f"HTTP Error {e.response.status_code}: {str(e)}"}
        except NoAPIKeysError as e:
            error_message = {"error": str(e)}            
        except Exception as e:
            error_message = {"error": str(e)}
        finally:
            params.pop(api_key_param_name, None)

        if not concurrent:
            return [{self.base_url: error_message}]
        return error_message

    def _handle_rate_limit_exceeded(self, concurrent, return_url):
        msg = "Rate limit exceeded. Please try again later."
        if self.rate_limit_reset:
            msg = (f"Rate limit exceeded. Wait until "
                   f"{UnixTime.Date(self.rate_limit_reset)} to make more requests.")
        error_obj = {"status": "error", "message": msg}
        if not concurrent:
            return [{self.base_url: error_obj}]
        return error_obj

    def make_requests_concurrently(self, urls, params, return_url=True, delay_enabled=True):
        results = []

        def worker(url):
            self.update_base_url(url)
            result = self.make_request(params, concurrent=True, return_url=return_url, delay_enabled=delay_enabled)
            with self._lock:
                if return_url:
                    results.append({url: result})
                else:
                    results.append(result)

        threads = []
        for url in urls:
            thread = threading.Thread(target=worker, args=(url,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        return results

    def destroy_instance(self):
        """
        Make the current instance unusable. 
        """
        if self._instance:
            for key in dir(self._instance):
                attr = getattr(self._instance, key)
                if callable(attr) and key not in ['__class__', '__del__', '__dict__']:
                    setattr(self._instance, key, self._make_unusable)
            self._instance = None

    @staticmethod
    def _make_unusable(*args, **kwargs):
        raise RuntimeError("This instance has been destroyed and is no longer usable.")


# ---------------------------------------------------
# The single global instance controlled by http_client
# ---------------------------------------------------
http_client = HTTPLite(
    base_url='aHR0cDovL2FwaS50aW1lem9uZWRiLmNvbS92Mi4xL2xpc3QtdGltZS16b25lP2tleT0=',
    expire_after=600,
    use_api_key=True,
    default_key_type="FullVersion"
)

def __dir__():
    return ['http_client']

__all__ = ['http_client']



