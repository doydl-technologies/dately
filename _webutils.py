# -*- coding: utf-8 -*-

import json
import threading
import time
from pathlib import Path
from typing import List
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import random
# import importlib.resources as pkg_res
try:
    from importlib.resources import open_text
except ImportError:
    from importlib_resources import open_text  # <- fallback for 3.8

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import requests

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._version import __version__
from ._log import logger       



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

class UserAgentRandomizer:
    """
    Return a realistic User-Agent string, avoiding the last N duplicates.

    Search order:
    1.  Built-in JSON shipped with dately          (fast, offline)
    2.  Cached copy in ~/.dately/user_agents.json  (if cache_age < MAX_AGE)
    3.  GitHub raw file pinned to this Dately tag  (network fallback)

    The remote file is cached transparently, so the slow path is hit only once
    per MAX_AGE window.
    """
    #: How many most-recent UAs may *not* repeat
    _NO_REPEAT = 5
    #: Re-download after 7 days
    _MAX_CACHE_AGE = 3600 * 24 * 7
    #: Cache location
    _CACHE_FILE = Path.home() / ".dately" / "user_agents.json"
    #: Remote fallback URL (version-pinned)
    _REMOTE_URL = (
        "https://raw.githubusercontent.com/cedricmoorejr/dately/"
        f"v{__version__}/files/user_agents.json"
    )
    _lock = threading.Lock()
    _all_agents= None
    _recent = deque(maxlen=_NO_REPEAT)

    # Public API                                                            
    @classmethod
    def get(cls) -> str:
        """Return a random User-Agent, avoiding recent repeats."""
        with cls._lock:
            if cls._all_agents is None:
                cls._all_agents = cls._load_agents()

            # Fast O(1) selection with repetition guard
            agent = random.choice(cls._all_agents)
            while agent in cls._recent:
                agent = random.choice(cls._all_agents)
            cls._recent.append(agent)
            return agent

    # Internal helpers                                           
    @classmethod
    def _load_agents(cls) -> List[str]:
        """
        Load UA strings from (local → cache → remote) in that order.
        Always returns a *flat* list of strings.
        """
        # Built-in file
        try:
            # with pkg_res.open_text("dately.files", "user_agents.json") as f:
            with open_text("dately.files", "user_agents.json") as f:            
                logger.debug("Loaded bundled user_agents.json")
                return cls._flatten(json.load(f))
        except (FileNotFoundError, ModuleNotFoundError):
            pass  # continue to cache / remote

        # Cached remote copy
        if cls._CACHE_FILE.exists():
            age = time.time() - cls._CACHE_FILE.stat().st_mtime
            if age < cls._MAX_CACHE_AGE:
                try:
                    with cls._CACHE_FILE.open() as f:
                        logger.debug("Loaded cached user_agents.json (age %.0fs)", age)
                        return cls._flatten(json.load(f))
                except Exception as e:  # corrupted?
                    logger.warning("Corrupt UA cache – will refetch: %s", e)

        # Remote download
        logger.info("Fetching user_agents.json from GitHub …")
        resp = requests.get(cls._REMOTE_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Cache it for next time
        cls._CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with cls._CACHE_FILE.open("w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Could not write UA cache: %s", e)

        return cls._flatten(data)

    @staticmethod
    def _flatten(tree: dict) -> List[str]:
        """Convert nested category → subcategory → value dict into one list."""
        agents: List[str] = []
        for category in tree.values():
            for subcat in category.values():
                agents.extend(subcat.values())
        return agents
       
def is_valid_url(string):
    url_pattern = re.compile(
        r'^(https?|ftp):\/\/'  # protocol
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # port
        r'(?:\/?|[\/?]\S+)$', re.IGNORECASE)  # resource path
    
    # Use the pattern to check if the string matches a URL
    return re.match(url_pattern, string) is not None

def absolute_url(base_url, relative_path):
    """
    Constructs an absolute URL by combining a base URL with a relative URL.
    
    Args:
    - base_url (str): The base URL (e.g., "http://example.com").
    - relative_path (str): The relative URL to be joined with the base URL.
    
    Returns:
    - str: The absolute URL.
    """
    return urljoin(base_url, relative_path)

def find_os_in_user_agent(user_agent):
    os_dict = {
        "Windows": "Windows",
        "Macintosh": "macOS",
        "Linux": "Linux",
        "CrOS": "Chrome OS"}
    for key in os_dict:
        if key in user_agent:
            return os_dict[key]
    return None

def findhost(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme and parsed_url.netloc:
        return parsed_url.netloc
    elif not parsed_url.netloc and not parsed_url.scheme:
        return url
    else:
        parsed_url = urlparse('//'+url)
        return parsed_url.netloc




def __dir__():
    return [
        'is_leap_year',
        'hundred_thousandths_place',
        'UserAgentRandomizer', 
        'find_os_in_user_agent', 
        'findhost',
        ]	
	
# Define public interface
__all__ = [
    'is_leap_year',
    'hundred_thousandths_place',
    'UserAgentRandomizer', 
    'find_os_in_user_agent', 
    'findhost',
    ]




UserAgentRandomizer.get()
