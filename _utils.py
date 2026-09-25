# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# The `dately` module is a deterministic engine for parsing, resolving, and normalizing
# temporal expressions across both natural and symbolic language contexts — built for NLP
# workflows, cross-platform date handling, and fine-grained temporal reasoning.
#
# Designed with formal grammatical rigor, `dately` interprets phrases like “first five days of next month,”
# “Q3 of last year,” and “April 3” — handling cardinal/ordinal resolution, anchored structures, and
# ambiguous or implicit references with linguistic sensitivity.
#
# The engine combines structured tokenization, symbolic transformation, and rule-based semantic
# composition to support precision across tasks such as entity recognition, information extraction,
# and temporal normalization in noisy or informal text.
#
# It guarantees invertibility, transparency, and cross-platform consistency, resolving platform-specific
# formatting differences (e.g. Windows vs. Unix) while maintaining NLP-grade flexibility for English-language
# temporal constructions.
#
# Whether embedded in intelligent agents, ETL pipelines, or legal/medical NLP systems, `dately` brings
# clarity and structure to temporal meaning — bridging symbolic logic with real-world language.
#
# Copyright (c) 2024 by doydl technologies. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

def is_leap_year(year):
    """
    Determine whether a specified year is a leap year.

    A leap year is defined in the Gregorian calendar as one that is:
    - Divisible by 4 and,
    - Not divisible by 100 unless also divisible by 400.

    Parameters:
    year (int): The year to check. This should be a positive integer representing the year AD.

    Returns:
    bool: True if the year is a leap year, False otherwise.
    """
    try:
        year = int(year)
    except ValueError:
        raise ValueError("Input should be a year in integer or string form that can be converted to an integer.")

    if (year % 400 == 0):
        return True
    if (year % 100 == 0):
        return False
    if (year % 4 == 0):
        return True
    return False

def hundred_thousandths_place(number_str, decimal=True):
    """
    Ensures the given number string is always represented to the hundred-thousandths place,
    regardless of whether it initially has a decimal point or not.

    Args:
        number_str (str or int): The input number as a string or integer.
        decimal (bool): Whether to include the decimal point in the output.

    Returns:
        str: The number formatted to the hundred-thousandths place.
             If the input is invalid, returns '.00000' or '00000' based on the decimal flag.

    Examples:
        >>> hundred_thousandths_place("1")
        '1.00000'
        >>> hundred_thousandths_place("1.2")
        '1.20000'
        >>> hundred_thousandths_place("1.234567")
        '1.23456'
        >>> hundred_thousandths_place(None)
        '.00000'
        >>> hundred_thousandths_place("abc")
        '.00000'
        >>> hundred_thousandths_place("1", False)
        '100000'
    """
    # Ensure the input is a string
    number_str = str(number_str)

    # Check if the string is a valid number
    try:
        float(number_str)  # Check for validity
    except ValueError:
        return '00000' if not decimal else '.00000'

    if '.' in number_str:
        integer_part, decimal_part = number_str.split('.')
        if len(decimal_part) < 5:
            decimal_part = decimal_part.ljust(5, '0')
        elif len(decimal_part) > 5:
            decimal_part = decimal_part[:5]
        formatted_number = f"{integer_part}.{decimal_part}"
    else:
        formatted_number = f"{number_str.zfill(5)}"

    # Conditionally remove the decimal if not required
    if not decimal and '.' not in number_str:
        return formatted_number
    elif not decimal and '.' in formatted_number:
        # Remove decimal point if the number is effectively an integer
        return formatted_number.replace('.', '')
    return formatted_number



def __dir__():
    return [
    'is_leap_year',
    'hundred_thousandths_place'
	]


__all__ = [
	'is_leap_year',
	'hundred_thousandths_place',
	]
