import base64
import re
from .webutils import is_valid_url

# Define public interface
__all__ = ['Shift']

class Shift:
    class bool:
        @staticmethod
        def bytes(s):
            """ base64 """
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
            """ Binary """
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
        def chr(data, call):
            """ base64 """
            if call == "unformat":
                if not Shift.bool.bytes(data):
                    return base64.b64encode(data.encode('utf-8')).decode('utf-8')
            elif call == "format":
                if is_valid_url(data):
                    return data
                
                if Shift.bool.bytes(data):
                    try:
                        return base64.b64decode(data).decode('utf-8')
                    except (base64.binascii.Error, UnicodeDecodeError):
                        raise ValueError("Invalid base64 input.")
            else:
                raise ValueError("Invalid call. Use 'unformat' or 'format'.")
        @staticmethod
        def str(data, call):
            """ Binary """
            if call == "unformat":
                if not Shift.bool.bin(data):
                    return ''.join(format(ord(char), '08b') for char in data)
            elif call == "format":
                if Shift.bool.bin(data):
                    try:
                        chars = [chr(int(data[i:i+8], 2)) for i in range(0, len(data), 8)]
                        return ''.join(chars)
                    except ValueError:
                        raise ValueError("Invalid binary input.")
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
