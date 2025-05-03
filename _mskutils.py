# -*- coding: utf-8 -*-



import base64
import re

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._webutils import is_valid_url


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

class Shift:
    class bool:
        @staticmethod
        def bytes(s):
            """Check if string s is a valid base64-encoded value."""
            if len(s) % 4 != 0:
                return False
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', s):
                return False
            try:
                decoded_bytes = base64.b64decode(s, validate=True)
                decoded_str = decoded_bytes.decode('utf-8')
                return True
            except (base64.binascii.Error, UnicodeDecodeError):
                return False

        @staticmethod
        def bin(s):
            """Check if string s is valid binary (composed only of 0s and 1s in groups of 8)."""
            if not all(c in '01' for c in s):
                return False
            if len(s) % 8 != 0:
                return False
            try:
                bytes_list = [s[i:i+8] for i in range(0, len(s), 8)]
                decoded_chars = [chr(int(byte, 2)) for byte in bytes_list]
                decoded_str = ''.join(decoded_chars)
                return True
            except ValueError:
                return False

    class format:
        @staticmethod
        def chr(data, call, fallback_attempted=False):
            """Convert to/from base64. For 'format', decode base64.
               If the result is empty or an error occurs, try binary decoding."""
            if call == "unformat":
                if not Shift.bool.bytes(data):
                    return base64.b64encode(data.encode('utf-8')).decode('utf-8')
            elif call == "format":
                if is_valid_url(data):
                    return data
                if Shift.bool.bytes(data):
                    try:
                        result = base64.b64decode(data).decode('utf-8')
                        if not result:
                            raise ValueError("Decoded result is empty.")
                        return result
                    except (base64.binascii.Error, UnicodeDecodeError, ValueError):
                        if not fallback_attempted:
                            return Shift.format.str(data, "format", fallback_attempted=True)
                        else:
                            raise ValueError("Invalid base64 input and binary fallback failed.")
                else:
                    if not fallback_attempted:
                        return Shift.format.str(data, "format", fallback_attempted=True)
                    else:
                        raise ValueError("Input not valid base64 and binary fallback already attempted.")
            else:
                raise ValueError("Invalid call. Use 'unformat' or 'format'.")

        @staticmethod
        def str(data, call, fallback_attempted=False):
            """Convert to/from binary. For 'format', decode a binary string.
               If the result is empty or an error occurs, try base64 decoding."""
            if call == "unformat":
                if not Shift.bool.bin(data):
                    return ''.join(format(ord(char), '08b') for char in data)
            elif call == "format":
                if Shift.bool.bin(data):
                    try:
                        chars = [chr(int(data[i:i+8], 2)) for i in range(0, len(data), 8)]
                        result = ''.join(chars)
                        if not result:
                            raise ValueError("Decoded binary result is empty.")
                        return result
                    except ValueError:
                        if not fallback_attempted:
                            return Shift.format.chr(data, "format", fallback_attempted=True)
                        else:
                            raise ValueError("Invalid binary input and base64 fallback failed.")
                else:
                    if not fallback_attempted:
                        return Shift.format.chr(data, "format", fallback_attempted=True)
                    else:
                        raise ValueError("Input not valid binary and base64 fallback already attempted.")
            else:
                raise ValueError("Invalid call. Use 'unformat' or 'format'.")

    class type:
        @staticmethod
        def map(s, add=None, ret=False):
            formatted = Shift.format.chr(s, "format")
            str_formatted = formatted
            if add:
                str_formatted += add
            unformatted = Shift.format.chr(str_formatted, "unformat")
            if ret:
                return Shift.format.chr(unformatted, "format")
            return unformatted



# Define public interface
__all__ = ['Shift']
