import re
from urllib.parse import urljoin

# Define public interface
__all__ = ['is_valid_url', 'absolute_url']

def is_valid_url(string):
    # Define a regular expression pattern for a valid URL
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
