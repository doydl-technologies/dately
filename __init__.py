# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# `dately` is a precision-first library for parsing, interpreting, and normalizing time expressions
# across both structured data and natural language. Built for developers and data teams working in
# time-sensitive domains, it delivers deterministic behavior, high-performance parsing, and
# transparent reasoning around temporal meaning.
#
# Designed for integration into NLP pipelines, ETL processes, scheduling engines, and cross-platform
# applications, `dately` supports everything from ISO formats and user-generated timestamps to
# phrases like “next Friday” or “Q2 2025.” Its symbolic parser bridges the gap between language and
# logic, enabling interpretable, testable, and production-grade handling of ambiguous or implicit
# time references.
#
# Features include format inference, batch-safe transformations, timezone normalization, and a
# modular architecture for composable workflows. Whether you're resolving date strings in a chatbot
# or aligning logs across systems, `dately` brings clarity, consistency, and control to temporal data.
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

"""
**dately** is a robust, cross-platform Python library engineered for high-precision, high-throughput
processing of date and time data. It unifies temporal parsing, transformation, normalization, and
reasoning into a coherent framework that addresses both structured datetime manipulation and the
interpretation of free-form natural language time expressions. Designed for developers, data
scientists, and system architects who treat temporal accuracy as a first-class concern, *dately*
delivers deterministic behavior, structural flexibility, and deep extensibility, making it suitable
for a wide spectrum of use cases—ranging from backend systems and ETL pipelines to conversational
agents and time-sensitive user interfaces.

At its foundation, **dately** abstracts the idiosyncrasies of operating system differences
(Unix-like systems vs. Windows), datetime format inconsistencies, locale-dependent ambiguities, and
malformed or user-generated inputs. It is particularly adept at bridging the divide between
machine-readable and human-generated temporal data, offering utilities that maintain semantic
integrity and consistent behavior across platforms, languages, and data formats.

─────────────────────────────────────────────────────────────────────────────────────
✓ Structural Parsing and Transformation 
─────────────────────────────────────────────────────────────────────────────────────
The library’s core parsing engine operates across scalar and vectorized data structures—
supporting Python strings and datetime objects, as well as NumPy arrays, Pandas Series, JSON-style
dictionaries, and nested collections. This versatility allows dately to function as a drop-in
replacement or augmentation to standard libraries like `datetime`, `dateutil`, and `pytz`, while
offering significantly more nuanced handling of edge cases and malformed input.

A key component of this system is the `DateFormatFinder`, a high-performance inference engine
capable of deducing `strptime`-compatible format strings from unstructured or loosely formatted
date strings. Whether the input is ISO 8601-compliant, written in localized formats, or expressed
in natural language, `DateFormatFinder` intelligently reconstructs the underlying pattern to enable
lossless parsing and further transformation.

Beyond parsing, dately provides finely-grained manipulation of datetime components via functions
such as `extract_datetime_component`, `replace_datestring`, and `replace_timestring`. These
operations respect input structure and batch dimensions, ensuring shape consistency and
immutability across list-like or tabular data—essential for functional programming pipelines and
composable data transformations.

─────────────────────────────────────────────────────────────────────────────────────
✓ Time Zone Normalization and Cross-Platform Precision
─────────────────────────────────────────────────────────────────────────────────────
One of dately’s most differentiated capabilities lies in its advanced time zone infrastructure.
Unlike libraries that depend on system-level time zone behavior or fail to reconcile
inconsistencies across platforms, dately introduces a fully normalized, OS-agnostic layer for time
zone operations. It supports conversions between IANA zone identifiers and UTC offsets, manages
daylight saving time (DST) transitions with high fidelity, and enables temporal classification
based on geopolitical and regional rules.

Moreover, the library resolves long-standing compatibility issues with the `strftime`/`strptime`
family of format specifiers—particularly those that misbehave or are unsupported in Windows
environments. Through regex-driven patching, intelligent specifier substitution, and output-aware
postprocessing, dately guarantees format consistency across Linux, Windows, and macOS. This feature
is especially valuable in CI/CD workflows, cross-platform APIs, Docker-based services, and
multi-environment scheduling applications.

─────────────────────────────────────────────────────────────────────────────────────
✓ Performance and Vectorized Workflows 
─────────────────────────────────────────────────────────────────────────────────────
dately has been optimized for high-performance execution. It employs vectorized operations
throughout its API and optionally leverages Cython and compiled C extensions to accelerate
time-critical workflows. This makes it ideal for integration into high-volume data engineering
tasks, including time-series feature extraction, log processing, and real-time data ingestion
pipelines.

Utilities such as `convert_date`, `sequence` (for generating inclusive or offset-aware date ranges),
and composable format converters allow users to build modular, declarative pipelines for datetime
transformation. Each utility is designed for integration into larger systems, with support for
input validation, error recovery, and structural introspection.

─────────────────────────────────────────────────────────────────────────────────────
✓ Natural Language Processing (NLP) for Temporal Reasoning 
─────────────────────────────────────────────────────────────────────────────────────
In addition to structured parsing, dately features a purpose-built symbolic NLP engine for
resolving natural language time expressions into discrete datetime values or bounded intervals.
This engine does not rely on opaque machine learning models; instead, it uses a deterministic,
rule-based architecture that offers full transparency and auditability—critical for
compliance-heavy domains such as healthcare, legal tech, and financial systems.

The NLP pipeline consists of five stages:
1. **Lexical Normalization** – Converts words to their numeric or canonical forms (e.g., 
   “second Friday” → ordinal(2), weekday=Friday).
2. **Grammar Parsing** – Applies symbolic pattern recognition to identify structural motifs like 
   anchored offsets or nested intervals.
3. **Calendar Logic Resolution** – Translates abstract concepts (e.g., “weekends,” “next quarter”) 
   into concrete calendar dates using arithmetic models.
4. **Contextual Grounding** – Resolves ambiguous references (e.g., “this month”) relative to a 
   configurable `reference_date`.
5. **Structured Output Emission** – Produces standardized `datetime.date` objects or normalized 
   ranges ready for downstream use.

This NLP component handles a wide array of expressions—absolute dates, ordinal references,
recurring intervals, seasonal phrases, and anchored relative durations. It excels at parsing
partially specified input (e.g., “Q3 2023”), vague phrasings (“a week before tax day”), and
colloquial constructs (“last few Fridays”). Crucially, the outputs are consistent, interpretable,
and suitable for rule-based scheduling, time-based querying, or human-in-the-loop validation
systems.

─────────────────────────────────────────────────────────────────────────────────────
✓ Integrated, Modular Design Philosophy 
─────────────────────────────────────────────────────────────────────────────────────
What sets dately apart is its deliberate emphasis on modularity, clarity, and cross-domain
applicability. Its components can be used independently or orchestrated together, allowing
developers to treat time not merely as a data field, but as a richly structured domain of meaning.
Whether you're building a chatbot that schedules meetings, a pipeline that deduplicates
time-stamped records, or an application that reconciles logs across time zones, dately offers the
primitives and abstractions needed to ensure reliable temporal computation.

By harmonizing symbolic reasoning, deterministic NLP, and high-throughput engineering, dately
elevates temporal data from an error-prone nuisance to a rigorously modeled, first-class element of
modern software architecture.
"""
from . import core as __core
from ._api import set_week_start


__all__ = [
    'extract_datetime_component',
    'detect_date_format',
    'convert_date',
    'replace_timestring',
    'replace_datestring',
    'sequence',
    'parse',
    'set_week_start',    
    'Holidate',
    'TimeZoner',
]

# Reference functions using __core alias
extract_datetime_component =  __core.extract_datetime_component
detect_date_format =  __core.detect_date_format
convert_date =  __core.convert_date
replace_timestring =  __core.replace_timestring
replace_datestring =  __core.replace_datestring
sequence =  __core.sequence
parse =  __core.parse

# Remove core to keep namespace clean
del core

# Import the real types and the factory functions for lazy loading
from ._timezone import ZoneInfoManager, get_TimeZoner
from ._holiday import HolidayManager, get_Holidate
from ._proxy import proxyObj as _proxyObj

# -----------------------------
# TimeZoner - Stub for Autocomplete/Docs
# -----------------------------
class TimeZonerStub:
    """
    TimeZoner manages all timezone interactions.

    Methods:
        ConvertTimeZone(from_zone, to_zone, year=None, month=None, day=None, hour=None, minute=None, second=None)
        CurrentTimebyZone(zone_name)
        FilterZoneDetail(zone_name)
    
    Properties:
        Zones, ZonesByCountry, Offsets, ObservesDST, CountryNames, CountryCodes
    """
    def ConvertTimeZone(self, from_zone, to_zone, year=None, month=None, day=None, hour=None, minute=None, second=None): pass
    def CurrentTimebyZone(self, zone_name): pass
    def FilterZoneDetail(self, zone_name): pass

    @property
    def Zones(self): pass
    @property
    def ZonesByCountry(self): pass
    @property
    def Offsets(self): pass
    @property
    def ObservesDST(self): pass
    @property
    def CountryNames(self): pass
    @property
    def CountryCodes(self): pass

# Lazy load wrapper for TimeZoner
TimeZoner: ZoneInfoManager = _proxyObj('dately._timezone', 'get_TimeZoner')
TimeZoner.__doc__ = TimeZonerStub.__doc__

# -----------------------------
def timezoner_stub_dir():
    return ['ConvertTimeZone', 'CurrentTimebyZone', 'FilterZoneDetail',
            'Zones', 'ZonesByCountry', 'Offsets', 'ObservesDST',
            'CountryNames', 'CountryCodes']
TimeZoner.__dir__ = timezoner_stub_dir

# --------------------------------------
# Holidate - Stub for Autocomplete/Docs
# --------------------------------------
class HolidateStub:
    """
    Holidate manages holiday data retrieval.

    Methods:
        ListCountries
        Holiday(country_name, year=None, format='list')
    """
    @property
    def ListCountries(self): pass

    def Holiday(self, country_name, year=None, format='list'): pass

# Lazy load wrapper for Holidate
Holidate: HolidayManager = _proxyObj('dately._holiday', 'get_Holidate')
Holidate.__doc__ = HolidateStub.__doc__

# -----------------------------
def holidate_stub_dir():
    return ['ListCountries', 'Holiday']
   
Holidate.__dir__ = holidate_stub_dir

# ------------------------------------------
# Expose all symbols defined in __init__.py
# ------------------------------------------
def __dir__():
    base_dir = globals().keys()
    base_dir = [f for f in base_dir if f.startswith("__") and f.endswith("__")]   
    return sorted(set(base_dir).union(
        {
            'extract_datetime_component', 'detect_date_format', 'convert_date',
            'replace_timestring', 'replace_datestring', 'sequence', 'parse',
            'set_week_start', 'Holidate', 'TimeZoner'
            }
        )
                  )
                  
