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

"""
Understanding the Module
────────────────────────────────────────────────────
This module provides foundational utilities for structured time representation,
standardized access to temporal units, and numeric-linguistic conversion. It is 
composed of two key components:

1. `DateHelper` — a semantic interface for canonical month, day, quarter, and 
   season information. It handles leap-year logic, start/mid/end date expansion, 
   and normalized indexing across a variety of time units.

2. `NumericConverter` — a utility for bidirectional transformation between 
   cardinal and ordinal forms, both numeric ("2nd") and linguistic ("second").

Together, these tools form a reliable core for time normalization and conversion 
within any natural language pipeline involving dates, durations, or calendrical logic.

Role in the NLP Pipeline
────────────────────────────────────────────────────
This module is typically invoked after language normalization and prior to any 
temporal resolution or execution logic. It prepares and structures input into 
predictable, computable formats that downstream systems can reason over.

`DateHelper` plays a critical role in generating valid reference points for 
anchoring, containment, and windowing across months, quarters, and seasons — 
especially in the presence of vague or partial user input.

`NumericConverter` ensures consistency across user representations like 
"second", "2", and "2nd", which are common in natural expressions of time.

Core Focus
────────────────────────────────────────────────────
- Normalize and canonicalize temporal units (months, weekdays, seasons, quarters)
- Provide date metadata (start/mid/end) for each time entity
- Handle leap years when computing monthly/seasonal boundaries
- Support alias mapping and reverse lookup across time vocabularies
- Expose time lists with views for formatting (e.g., `.upper`, `.sorted`)
- Convert between ordinal/cardinal words and numbers using `numbr`
- Provide rich wrappers for month objects (e.g., `.mmddyy`, `.d`, `.mmm`, etc.)
- Support structured formatting and comparisons for all date values

Note
────────────────────────────────────────────────────
This module does not interpret raw user input or perform fuzzy parsing.
It assumes input has already been normalized and focuses on deterministic
transformation, lookup, and formatting.

`DateHelper` is often coupled with language-level preprocessors and downstream
date engines. `NumericConverter` complements this by ensuring type consistency
in numeric reasoning tasks.

It forms a shared utility layer across higher-level temporal modules.
"""
import time
import math
import re

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import numbr



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
class DateHelper:
    """
    A utility class for managing and transforming structured temporal data.

    The DateHelper class provides canonical representations and access methods 
    for time-related units such as months, weekdays, quarters, and seasons.
    It supports dynamic year-based calculations (e.g., leap year handling), 
    and provides convenient views for standardized formatting, indexing, 
    sorting, and deduplication.

    Features include:
        - Normalized mapping for months, weekdays, quarters, and seasons
        - Computed start, middle, and end dates for each time unit
        - Leap year-aware handling of months and seasons
        - Indexable dictionaries for reverse lookups
        - List wrapper with helper views (upper/lower/capitalized/sorted/unique)
        - Nested dict wrappers for enriched access to structured date info

    Attributes:
        year (int): The reference year for resolving time-specific ranges.
        months (IndexedDict): Mapping of month aliases to canonical names with indexable lookup.
        days (IndexedDict): Mapping of day aliases and numeric indices to canonical weekday names.
        quarters (QuarterDict): Custom dict with access to sorted short-form quarter keys.
        seasons (SeasonDict): Mapping of season aliases to canonical forms with calculated boundaries.
        time_units (set): Base time unit identifiers (e.g., "day", "week", "month", etc.).
        special_units (dict): Semantic categories like "weekday", "weekend", "season", and "quarter".

    Note:
        This class is designed to support higher-level temporal language parsing and
        normalization systems by providing structured, canonical, and year-aware
        access to core temporal concepts.

        Seasonal boundaries in this class follow the meteorological definition 
        (e.g., winter starts on December 1st), rather than astronomical.
    """	
    class MonthInfo:
        """
        A wrapper for month metadata including its name, numeric index, and day count.
        """
        def __init__(self, name, number, days, year=None):
            self._name = name          # "April"
            self._number = number      # 4
            self._days = days          # 30
            self._year = year					 # yyyy            

        @property
        def m(self):
            return self._number

        @property
        def mm(self):
            return str(self._number).zfill(2)

        @property
        def mmm(self):
            return self._name[:3]

        @property
        def mmmm(self):
            return self._name
           
        @property
        def mmmmm(self):
            return self._name[0]           

        @property
        def d(self):
            return self._days
           
        @property
        def dd(self):
            return str(self._days).zfill(2)
           
        @property
        def yy(self):
            return str(self._year)[2:]
           
        @property
        def yyyy(self):
            return self._year            
           
        @property
        def name(self):
            return self._name
           
        @property
        def year(self):
            return self._year          

        def __eq__(self, other):
            if isinstance(other, DateHelper.MonthInfo):
                return (self._name, self._number, self._days) == (other._name, other._number, other._days)
            return False

        def to_dict(self):
            return {
                "m": self._number,
                "mm": str(self._number).zfill(2),
                "mmm": self._name[:3],
                "mmmm": self._name,
                "mmmmm": self._name[0],                
                "d": self._days,
                "dd": str(self._days).zfill(2),                
                "yy": str(self._year)[2:], 
                "yyyy": self._year,                 
            }
            
        def __repr__(self):
            return str(self.to_dict())

        def __str__(self):
            return str(self.to_dict())
           
        def __getattr__(self, name):
            """
            Dynamically returns combinations like .mmmdd, .mmddyy, etc.
            using values from to_dict().
            """
            parts = ['yyyy', 'yy', 'dd', 'd', 'mmmmm', 'mmmm', 'mmm', 'mm', 'm']
            available = {k: str(v) for k, v in self.to_dict().items()}

            result = ''
            working_name = name

            while working_name:
                match = next((p for p in parts if working_name.startswith(p)), None)
                if not match:
                    raise AttributeError(f"'MonthInfo' object has no attribute '{name}'")
                result += available.get(match, '')
                working_name = working_name[len(match):]
            return result

    class TypedValue:
        """
        A wrapper that allows flexible access to a single value or dictionary of values
        as either `int` or `str`. Used to enhance date components like month/day for
        both singular and grouped contexts.
        """    
        def __init__(self, value):
            """
            Initializes the wrapper with a single value or a dictionary of values.
            """        
            self._value = value

        @property
        def int(self):
            """
            Returns the integer form of the wrapped value(s).
            """        
            if isinstance(self._value, dict):
                return {k: int(v._value if isinstance(v, DateHelper.TypedValue) else v) for k, v in self._value.items()}
            return int(self._unwrap(self._value))

        @property
        def str(self):
            """
            Returns the string form of the wrapped value(s).
            """        
            if isinstance(self._value, dict):
                return {k: str(v._value if isinstance(v, DateHelper.TypedValue) else v) for k, v in self._value.items()}
            return str(self._unwrap(self._value))

        def _unwrap(self, val):
            return val._value if isinstance(val, DateHelper.TypedValue) else val

        def __str__(self):
            return str(self._value)

        def __repr__(self):
            return repr(self._value)

        def __getitem__(self, key):
            if isinstance(self._value, dict):
                return self._value[key]
            raise TypeError("Cannot index into a non-dict value.")

        def items(self):
            if isinstance(self._value, dict):
                return self._value.items()
            raise AttributeError("Value is not a dict.")

    class DateComponent:
        """
        A lightweight wrapper for a MM/DD date string, exposing its components
        (`mm` and `dd`) with type-flexible access (via TypedValue).
        """    
        def __init__(self, date_str):
            """
            Args:
                date_str (str): A string in MM/DD format.
            """        
            self.date_str = date_str
            parts = date_str.split('/')
            self._mm = parts[0]
            self._dd = parts[1]

        @property
        def mm(self):
            """Returns the month component with str/int access."""        
            return DateHelper.TypedValue(self._mm)

        @property
        def dd(self):
            """Returns the day component with str/int access."""        
            return DateHelper.TypedValue(self._dd)

        def __str__(self):
            return self.date_str

        def __repr__(self):
            return f"'{self.date_str}'"

        def __eq__(self, other):
            return self.date_str == other

        def __len__(self):
            return len(self.date_str)

    class DateFrame:
        """
        A wrapper around a dictionary of month data. Supports dynamic
        attribute access to 'start', 'middle', and 'end' date values,
        returned as DateFieldGroup objects.
        """    
        def __init__(self, data):
            """
            Args:
                data (dict): A dict of months to date ranges.
            """        
            self._data = data

        def __getattr__(self, attr):
            """
            Allows access to nested 'start', 'middle', and 'end' values.

            Returns:
                DateFieldGroup: Object exposing .mm and .dd across months.
            """        
            if attr in ['start', 'middle', 'end']:
                return DateHelper.DateFieldGroup(attr, {
                    month: details[attr]
                    for month, details in self._data.items()
                })
            raise AttributeError(f"No attribute named '{attr}' exists.")

        def __getitem__(self, key):
            return self._data[key]

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._data.items()

        def values(self):
            return self._data.values()

        def __iter__(self):
            return iter(self._data)

        def __repr__(self):
            return str(self._data)
           
    class DateFieldGroup:
        """
        A group of dates (e.g., all 'start' dates across months) that exposes
        unified access to day and month components via TypedValue.
        """    
        def __init__(self, label, data):
            """
            Args:
                label (str): The group label ('start', 'middle', or 'end').
                data (dict): Mapping of keys (like month names) to MM/DD strings.
            """        
            self._label = label 
            self._data = data   

        def __getattr__(self, attr):
            """
            Access month or day components across all items.

            Returns:
                TypedValue over dict[str, str or int]
            """        
            if attr in ['dd', 'mm']:
                return DateHelper.TypedValue({
                    month: getattr(DateHelper.DateComponent(date_str), attr)
                    for month, date_str in self._data.items()
                })
            return self._data

        def __repr__(self):
            return str(self._data)

    class DateRecord:
        """
        A wrapper for a single month's data (start/middle/end), allowing dot-access
        to any component and automatic DateComponent conversion when accessing start/mid/end.
        """    
        def __init__(self, data):
            """
            Args:
                data (dict): Dict with keys like 'start', 'middle', 'end'.
            """        
            if not data:
                raise ValueError("No month data available for the given input.")
            self._data = data

        def __getattr__(self, name):
            """
            Allows direct access to date fields like 'start', 'middle', 'end',
            returning them wrapped as DateComponent.
            """        
            value = self._data.get(name)
            if value is None:
                raise AttributeError(f"No attribute named '{name}' exists.")
            if name in ['start', 'middle', 'end']:
                return DateHelper.DateComponent(value)
            return value

        def __getitem__(self, key):
            try:
                return self._data[key]
            except KeyError:
                raise KeyError(f"No item found with key '{key}'.")

        def __repr__(self):
            return str(self._data)
    
    class OrderedSet(set):
        """
        A set-like class that preserves insertion order.

        Used for scenarios where set semantics are needed but original key order matters.
        """
        def __init__(self, iterable):
            super().__init__()
            self._items = []
            seen = set()
            for item in iterable:
                if item not in seen:
                    seen.add(item)
                    self._items.append(item)

        def __iter__(self):
            return iter(self._items)

        def __repr__(self):
            return f"{{{', '.join(repr(i) for i in self._items)}}}"

        def __contains__(self, item):
            return item in self._items

        def __len__(self):
            return len(self._items)
    
    class List(list):
        """
        A list subclass that provides additional views for string transformation and structure.

        Useful for representing normalized temporal lists (e.g., quarters, weekdays),
        this wrapper allows for easy access to upper/lower/capitalized versions,
        sorted lists, and de-duplicated entries.

        Properties:
            upper (list[str]): List of all elements as uppercase strings.
            lower (list[str]): List of all elements as lowercase strings.
            capitalize (list[str]): List of all elements with capitalization applied.
            sorted (list): Alphabetically sorted version of the list.
            unique (list): List with duplicates removed while preserving order.
        """    	
        @property
        def upper(self):
            """
            Returns a new list with all elements converted to uppercase strings.

            Returns:
                list[str]: Uppercased string versions of each element in the list.
            """        	
            return [str(i).upper() for i in self]

        @property
        def lower(self):
            """
            Returns a new list with all elements converted to lowercase strings.

            Returns:
                list[str]: Lowercased string versions of each element in the list.
            """        	
            return [str(i).lower() for i in self]

        @property
        def capitalize(self):
            """
            Returns a new list with each element capitalized.

            Returns:
                list[str]: Capitalized string versions of each element in the list.
            """        	
            return [str(i).capitalize() for i in self]

        @property
        def sorted(self):
            """
            Returns a sorted version of the list in ascending order.

            Returns:
                list: Alphabetically or numerically sorted list, depending on contents.
            """        	
            return sorted(self)

        @property
        def unique(self):
            """
            Returns a new list with duplicates removed, preserving original order.

            Returns:
                list: De-duplicated version of the list.
            """        	
            return list(dict.fromkeys(self))
        
        def __dir__(self):
            return ['upper', 'lower', 'sorted', 'capitalize', 'unique']

    class QuarterDict(dict):
        """
        A specialized dictionary for quarter-related mappings.

        Provides a `.list` property that returns a List containing
        short-form quarter keys (e.g., "q1", "q2", etc.) in sorted order.

        Properties:
            list (List): A sorted list of two-character quarter keys.
        """    	
        # @property
        # def list(self):
        #     return DateHelper.List(sorted([k for k in self.keys() if len(k) == 2]))
        @property
        def list(self):
            return DateHelper.List(sorted(set(self.values())))
        
        def __dir__(self):
            return ['list']

    class SeasonDict(dict):
        """
        A dictionary wrapper for seasonal data with contextual information.

        Designed to hold season mappings (e.g., "spring" → "Spring") and
        calculate start/middle/end boundaries for each season using the parent
        DateHelper instance.

        Initialized with a reference to the parent DateHelper to resolve
        year-aware seasonal boundaries.

        Properties:
            list (List): List of season keys.
            info (dict): Dictionary of structured season data with formatted
                         start, middle, and end dates based on the current year.
        """
        class DateInfoFormatter:
            """
            A helper class to format the dates with or without the year included.
            This class will mimic a dictionary's behavior by default and provide additional
            properties for different date formats.
            """
            def __init__(self, data, parent):
                self.data = data  # includes full MM/DD/YYYY structure
                self._parent = parent  # reference to DateHelper

            @property
            def mmdd(self):
                return {season: {key: self._format_date(date, include_year=False, format="mmdd") for key, date in dates.items()} for season, dates in self.data.items()}
               
            @property
            def mm(self):
                return {season: {key: self._format_date(date, include_year=False, format="mm") for key, date in dates.items()} for season, dates in self.data.items()} 
               
            @property
            def dd(self):
                return {season: {key: self._format_date(date, include_year=False, format="dd") for key, date in dates.items()} for season, dates in self.data.items()}         
               
            @property
            def yyyy(self):
                return {season: {key: self._format_date(date, include_year=False, format="yyyy") for key, date in dates.items()} for season, dates in self.data.items()}                

            @property
            def mmddyy(self):
                return self.MMDDYYView(self.data, self._parent)
            
            def _format_date(self, date_str, include_year, format=None):
                """ Formats a date string as MM/DD or MM/DD/YYYY."""            	
                month, day, year = date_str.split('/')
                if format in (None, "mmddyy"):
                    return f"{month}/{day}" if not include_year else f"{month}/{day}/{year}"

                if format == "mm":
                    return f"{month}" if not include_year else f"{month}/{year}"

                if format == "dd":
                    return f"{day}" if not include_year else f"{day}/{year}"

                if format == "mmdd":
                    return f"{month}/{day}" if not include_year else f"{month}/{day}/{year}"     
                   
                if format == "yyyy":
                    return f"{year}" if not include_year else f"{month}/{day}/{year}"                    

            def year(self, new_year):
                """
                Generates a new DateInfoFormatter with dates adjusted to the given year.

                Args:
                    new_year (int): The reference year to recalculate season dates.

                Returns:
                    DateInfoFormatter: A new instance with updated date mappings for the given year.
                """
                return self._compute_with_year(new_year)
            
            def _compute_with_year(self, new_year):
                """Generates season date information with year included for a given year."""
                seasonal_data = self._parent.adj_seasons(year=new_year, include_year=True)
                return DateHelper.SeasonDict.DateInfoFormatter(seasonal_data, parent=self._parent)        

            class MMDDYYView:
                """Dict-like wrapper around mmddyy data with .year() support."""
                def __init__(self, data, parent):
                    self._data = data
                    self._parent = parent

                def year(self, new_year):
                    """Returns a recomputed mmddyy dict for the given year."""
                    return DateHelper.SeasonDict.DateInfoFormatter(self._data, parent=self._parent).year(new_year).mmddyy

                def __getitem__(self, key):
                    return self._data[key]

                def __iter__(self):
                    return iter(self._data)

                def __len__(self):
                    return len(self._data)

                def keys(self):
                    return self._data.keys()

                def values(self):
                    return self._data.values()

                def items(self):
                    return self._data.items()

                def __repr__(self):
                    return repr(self._data)

                def __str__(self):
                    return str(self._data)

                def __contains__(self, key):
                    return key in self._data

                def __dir__(self):
                    return dir(self._data) + ['year']            
                
            # Dictionary-like hooks
            def __getitem__(self, key):
                return self.data[key]

            def __iter__(self):
                return iter(self.data)

            def __len__(self):
                return len(self.data)

            def keys(self):
                return self.data.keys()

            def values(self):
                return self.data.values()

            def items(self):
                return self.data.items()

            # Make REPL display a dict
            def __repr__(self):
                """
                Defines how this object is represented in the REPL (and in general debugging).
                We'll show the content of self.data directly as a dictionary.
                """
                return repr(self.data)

            def __str__(self):
                """
                Defines how this object is turned into a string (e.g. when printed).
                We'll also return the dictionary representation with years included by default.
                """
                return str(self.data)

            def __dir__(self):
                default_attrs = [f for f in super().__dir__() if f.startswith("__") and f.endswith("__")]
                public_attrs = ['mmdd', 'mmddyy', 'mm', 'dd','yyyy','year']
                return sorted(set(default_attrs + public_attrs))

        def __init__(self, data, parent):
            """
            Initializes the SeasonDict with season mappings and a reference to the parent DateHelper.

            The parent reference is used to access year-aware seasonal boundaries when generating
            contextual information such as start, middle, and end dates for each season.

            Parameters:
                data (dict): A dictionary mapping season aliases (e.g., "autumn") to canonical names (e.g., "Fall").
                parent (DateHelper): The parent DateHelper instance used for resolving seasonal boundaries.
            """
            super().__init__(data)
            self._parent = parent  # reference to DateHelper

        @property
        def list(self):
            """
            Returns the keys of the SeasonDict (season names) wrapped in a ListWrapper.

            The ListWrapper provides utility views such as .upper, .lower, .capitalize, .sorted,
            and .unique, enabling easy formatting and manipulation of the season list.

            Returns:
                ListWrapper: A wrapped list of season keys.
            """
            return DateHelper.List(self.keys())
        
        @property
        def info(self):
            """
            Provides year-aware start, middle, and end dates for each season.

            Returns:
                dict: A dictionary where each key is a canonical season name and the value is
                      another dictionary with "start", "middle", and "end" dates formatted as
                      MM/DD/YYYY.
            """
            seasons_dict = self._parent.adj_seasons(year=self._parent.year, include_year=True)
            return self.DateInfoFormatter(seasons_dict, parent=self._parent)       

        def __dir__(self):
            return ['list', 'info']

    class IndexedDict(dict):
        """
        A dictionary with an optional index view based on a custom indexing function.

        Useful for reverse lookup scenarios such as mapping names to numbers or
        canonicalizing aliases. The index view supports case transformations.

        Parameters:
            data (dict): The base dictionary.
            index_func (callable, optional): A function that builds an index view 
                                             from the base dictionary.

        Properties:
            index (IndexView or None): A derived dictionary based on the index_func,
                                       with access to case-transformed key views.
        """   	
        class IndexView(dict):
            """
            A dictionary subclass that provides case-normalized views of its keys.

            Useful for flexible key lookups or displaying keys in various text formats.
            """            
            def __init__(self, data, parent):
                """
                Initializes the IndexView with a dictionary of indexed data.

                Parameters:
                    data (dict): The index dictionary to wrap.
                """                
                super().__init__(data)
                self._parent = parent  # reference to DateHelper to access OrderedSet                

            @property
            def lower(self):
                """
                Returns a version of the index with all keys lowercased.

                Returns:
                    dict: Lowercase-key version of the index.
                """                
                return {k.lower(): v for k, v in self.items()}

            @property
            def upper(self):
                """
                Returns a version of the index with all keys uppercased.

                Returns:
                    dict: Uppercase-key version of the index.
                """                
                return {k.upper(): v for k, v in self.items()}

            @property
            def capitalize(self):
                """
                Returns a version of the index with all keys capitalized.

                Returns:
                    dict: Capitalized-key version of the index.
                """                
                return {k.capitalize(): v for k, v in self.items()}
               
            @property
            def orderedset(self):
                """
                Returns an OrderedSet of the index keys, preserving original order.

                Returns:
                    OrderedSet: A set-like structure with preserved insertion order.
                """
                return self._parent.OrderedSet(self.keys())
               
            def __getitem__(self, key):
                if key in self: # Try normal (string) key lookup first
                    return super().__getitem__(key)
                try: # Try reverse lookup: value -> key
                    # Search for the key that has this value
                    for k, v in self.items():
                        if v == key:
                            return k
                except Exception as e:
                    raise KeyError(f"Invalid index or reverse lookup value: {key}") from e
                raise KeyError(f"Index key or reverse value '{key}' not found.")               

            def __dir__(self):
                return ['upper', 'lower', 'capitalize', 'orderedset']                
          

        def __init__(self, data, index_func=None, parent=None):
            """
            Initializes the IndexedDict with a base dictionary and an optional indexing function.

            Parameters:
                data (dict): The core dictionary.
                index_func (callable, optional): A function that receives this dictionary and 
                                                 returns a custom index (e.g., reverse mapping).
            """            
            super().__init__(data)
            self._index_func = index_func
            self._parent = parent  # used to pass DateHelper to IndexView            

        @property
        def index(self):
            """
            Returns a case-flexible index view of the dictionary, based on the index_func.

            The index is created by applying the provided index_func to the base dictionary,
            and then wrapped in an IndexView that supports lower, upper, and capitalized
            key access.

            Returns:
                IndexView or None: An indexed view of the dictionary, or None if no index_func was provided.
            """            
            if self._index_func:
                index_data = self._index_func(self)
                return self.IndexView(index_data, parent=self._parent)
            return None
        
        def __dir__(self):
            return ['index']

    def __init__(self, year=None):
        """
        Initializes a DateHelper instance with normalized temporal unit mappings.

        Sets up internal dictionaries for months, days, quarters, and seasons,
        along with utility structures for indexing and capitalization handling.

        Parameters:
            year (int, optional): Reference year for resolving seasonal and monthly
                                  boundaries. Defaults to the current system year.
        """    	
        self.year = year or time.localtime().tm_year
        self.months = self.IndexedDict(
            self._create_valid_months(),
            index_func=lambda d: {
                i.lower(): idx + 1
                for idx, i in enumerate(dict.fromkeys(d.values()))
            },
            parent=self
        )         
        self.days = self.IndexedDict(
            self._create_valid_days(),
            index_func=lambda d: {
                d[i].lower(): i
                for i in range(7)
                if isinstance(i, int) and i in d
            },
            parent=self
        )
        self.quarters = self.QuarterDict(self._create_valid_quarters())
        self.seasons = self.SeasonDict(self._create_valid_seasons(), parent=self)      
        self.time_units = {"day", "week", "month", "season", "quarter", "year", "half"}
        self.special_units = {"weekend": "Weekend", "weekday": "Weekday", "quarter": "Quarter", "season": "Season"}

    @staticmethod
    def is_leap_year(year):
        """
        Determines whether a given year is a leap year.

        Parameters:
            year (int): The year to evaluate.

        Returns:
            bool: True if the year is a leap year, False otherwise.
        """    	
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
       
    def _ret_months(self, month):
        month_map = self.months
        
        # Normalize input to lowercase string
        str_month = str(month).lower()

        # Case 1: if input is a string (abbreviation or full), look it up in month_map
        if str_month in month_map:
            return month_map[str_month]
        
        # Case 2: if input is a month number (as string or int), reverse lookup in month_map.index
        try:
            month_num = int(str_month)
            for full_name, index in month_map.index.items():
                if index == month_num:
                    return full_name.capitalize()
        except ValueError:
            pass

        return None
       
    def _create_valid_months(self):
        """
        Constructs a dictionary of normalized month aliases.

        Returns:
            dict: Mapping of lowercase month strings (and abbreviations)
                  to their canonical capitalized form.
        """    	
        return {
            "january": "January", "jan": "January",
            "february": "February", "feb": "February",
            "march": "March", "mar": "March",
            "april": "April", "apr": "April",
            "may": "May",
            "june": "June", "jun": "June",
            "july": "July", "jul": "July",
            "august": "August", "aug": "August",
            "september": "September", "sep": "September", "sept": "September",
            "october": "October", "oct": "October",
            "november": "November", "nov": "November",
            "december": "December", "dec": "December",
        }

    def _create_valid_days(self):
        """
        Constructs a dictionary of normalized weekday aliases and numeric indices.

        Includes full day names, common abbreviations, and index-based keys (0–6).

        Returns:
            dict: Mapping of various day representations to their canonical form.
        """    	
        days = {
            "monday": "Monday", "mon": "Monday",
            "tuesday": "Tuesday", "tue": "Tuesday", "tues": "Tuesday",
            "wednesday": "Wednesday", "wed": "Wednesday",
            "thursday": "Thursday", "thu": "Thursday", "thur": "Thursday", "thurs": "Thursday",
            "friday": "Friday", "fri": "Friday",
            "saturday": "Saturday", "sat": "Saturday",
            "sunday": "Sunday", "sun": "Sunday",
            "day": "Day",
            "days": "Day",
        }
        canonical_order = []
        seen = set()
        for name in days.values():
            if name != "Day" and name not in seen:
                seen.add(name)
                canonical_order.append(name)
        for i, day in enumerate(canonical_order):
            days[i] = day
        return days

    def _create_valid_quarters(self):
        """
        Constructs a dictionary of normalized quarter aliases.

        Returns:
            dict: Mapping of common quarter phrases (e.g., "first quarter", "q1")
                  to a standard short-form (e.g., "q1").
        """    	
        return {
            # Q1 variations
            "q1": "q1", "quarter 1": "q1", "first quarter": "q1", "1st quarter": "q1", "1st q": "q1", 
            "1q": "q1", "qtr 1": "q1", "quarter one": "q1", "qtr 1": "q1", "first qtr": "q1", 
            "1st qtr": "q1", "1st q": "q1", "1q": "q1", "qtr 1": "q1", "qtr one": "q1", 
            "q one": "q1", "quarter i": "q1", "qtr i": "q1", "quarter first": "q1", "1 q": "q1", 
            "quarter-1": "q1", "q-1": "q1", "qtr-1": "q1", "quarter1": "q1", "firstquarter": "q1", 
            "1stquarter": "q1", "1stq": "q1", "1q": "q1", "qtr1": "q1", "quarterone": "q1", 
            "qtr1": "q1", "firstqtr": "q1", "1stqtr": "q1", "1stq": "q1", "1q": "q1", 
            "qtr1": "q1", "qtrone": "q1", "qone": "q1", "quarteri": "q1", "qtri": "q1", 
            "quarterfirst": "q1", "1q": "q1", "quarter-1": "q1", "q-1": "q1", "qtr-1": "q1",

            # Q2 variations
            "q2": "q2", "quarter 2": "q2", "second quarter": "q2", "2nd quarter": "q2", "2nd q": "q2", 
            "2q": "q2", "qtr 2": "q2", "quarter two": "q2", "qtr 2": "q2", "second qtr": "q2", 
            "2nd qtr": "q2", "2nd q": "q2", "2q": "q2", "qtr 2": "q2", "qtr two": "q2", 
            "q two": "q2", "quarter ii": "q2", "qtr ii": "q2", "quarter second": "q2", "2 q": "q2", 
            "quarter-2": "q2", "q-2": "q2", "qtr-2": "q2", "quarter2": "q2", "secondquarter": "q2", 
            "2ndquarter": "q2", "2ndq": "q2", "2q": "q2", "qtr2": "q2", "quartertwo": "q2", 
            "qtr2": "q2", "secondqtr": "q2", "2ndqtr": "q2", "2ndq": "q2", "2q": "q2", 
            "qtr2": "q2", "qtrtwo": "q2", "qtwo": "q2", "quarterii": "q2", "qtrii": "q2", 
            "quartersecond": "q2", "2q": "q2", "quarter-2": "q2", "q-2": "q2", "qtr-2": "q2",

            # Q3 variations
            "q3": "q3", "quarter 3": "q3", "third quarter": "q3", "3rd quarter": "q3", "3rd q": "q3", 
            "3q": "q3", "qtr 3": "q3", "quarter three": "q3", "qtr 3": "q3", "third qtr": "q3", 
            "3rd qtr": "q3", "3rd q": "q3", "3q": "q3", "qtr 3": "q3", "qtr three": "q3", 
            "q three": "q3", "quarter iii": "q3", "qtr iii": "q3", "quarter third": "q3", "3 q": "q3", 
            "quarter-3": "q3", "q-3": "q3", "qtr-3": "q3", "quarter3": "q3", "thirdquarter": "q3", 
            "3rdquarter": "q3", "3rdq": "q3", "3q": "q3", "qtr3": "q3", "quarterthree": "q3", 
            "qtr3": "q3", "thirdqtr": "q3", "3rdqtr": "q3", "3rdq": "q3", "3q": "q3", 
            "qtr3": "q3", "qtrthree": "q3", "qthree": "q3", "quarteriii": "q3", "qtriii": "q3", 
            "quarterthird": "q3", "3q": "q3", "quarter-3": "q3", "q-3": "q3", "qtr-3": "q3",

            # Q4 variations
            "q4": "q4", "quarter 4": "q4", "fourth quarter": "q4", "4th quarter": "q4", "4th q": "q4", 
            "4q": "q4", "qtr 4": "q4", "quarter four": "q4", "qtr 4": "q4", "fourth qtr": "q4", 
            "4th qtr": "q4", "4th q": "q4", "4q": "q4", "qtr 4": "q4", "qtr four": "q4", 
            "q four": "q4", "quarter iv": "q4", "qtr iv": "q4", "quarter fourth": "q4", "4 q": "q4", 
            "quarter-4": "q4", "q-4": "q4", "qtr-4": "q4", "quarter4": "q4", "fourthquarter": "q4", 
            "4thquarter": "q4", "4thq": "q4", "4q": "q4", "qtr4": "q4", "quarterfour": "q4", 
            "qtr4": "q4", "fourthqtr": "q4", "4thqtr": "q4", "4thq": "q4", "4q": "q4", 
            "qtr4": "q4", "qtrfour": "q4", "qfour": "q4", "quarteriv": "q4", "qtriv": "q4", 
            "quarterfourth": "q4", "4q": "q4", "quarter-4": "q4", "q-4": "q4", "qtr-4": "q4"
        }

    def _create_valid_seasons(self):
        """
        Constructs a dictionary of normalized season names.

        Returns:
            dict: Mapping of lowercase season names and synonyms (e.g., "autumn")
                  to their canonical capitalized form (e.g., "Fall").
        """    	
        return {"winter": "Winter", "summer": "Summer", "spring": "Spring", "fall": "Fall", "autumn": "Fall"}

    def _create_seasonal_date_template(self, year=None):
        """
        Constructs a dictionary of base season date strings (MM/DD),
        following the meteorological definition of the seasons. 
        Adjusts the end-of-February date based on whether the given 
        year is a leap year.
        """
        cy = int(year) if year is not None else self.year
        feb_end = "02/29" if self.is_leap_year(cy) else "02/28"        
        
        return {
            "winter": {"start": "12/01", "middle": "01/15", "end": feb_end},
            "spring": {"start": "03/01", "middle": "04/15", "end": "05/31"},
            "summer": {"start": "06/01", "middle": "07/15", "end": "08/31"},
            "fall":   {"start": "09/01", "middle": "10/15", "end": "11/30"}
        }

    def _create_valid_days_in_months(self, year=None):
        """
        Constructs a dictionary of base season date strings (MM/DD),
        following the meteorological definition of the seasons. 
        Adjusts the end-of-February date based on whether the given 
        year is a leap year.
        """
        cy = int(year) if year is not None else self.year
        leap = self.is_leap_year(cy)      
        
        return {
            "January": 31, "February": 29 if leap else 28,
            "March": 31, "April": 30, "May": 31, "June": 30,
            "July": 31, "August": 31, "September": 30,
            "October": 31, "November": 30, "December": 31
        }

    def days_in_month(self, month=None, year=None):
        """
        Returns the number of days in a given month and year, or all months if no month is specified.

        This method accounts for leap years when determining the number of days in February. The month
        can be provided as either an integer (1–12) or a string (e.g., "March", "mar").

        Args:
            month (int or str, optional): The target month. Can be:
                - An integer from 1 to 12.
                - A string name or alias of the month (e.g., "jan", "February").
                If omitted, returns a dictionary of all months and their corresponding day counts.
            year (int, optional): The target year. If not provided, defaults to the instance's `self.year`.

        Returns:
            int or dict:
                - If a valid month is provided, returns the number of days in that month.
                - If no month is provided, returns a dictionary mapping all month names to their day counts.
        """    	
        current_year = int(year) if year is not None else self.year
        days_dict = self._create_valid_days_in_months(current_year)

        if not month:
            return {
                name: DateHelper.MonthInfo(name, i + 1, days, current_year)
                for i, (name, days) in enumerate(days_dict.items())
            }

        if isinstance(month, int):
            if 1 <= month <= 12:
                month_name = list(days_dict.keys())[month - 1]
                return DateHelper.MonthInfo(month_name, month, days_dict[month_name], current_year)
        elif isinstance(month, str):
            canonical = self.months.get(month.lower())
            if canonical:
                index = list(days_dict.keys()).index(canonical) + 1
                return DateHelper.MonthInfo(canonical, index, days_dict[canonical], current_year)
        raise ValueError(f"Invalid month: {month}")

    def adj_months(self, m=None, year=None):
        """
        Returns start, middle, and end dates for each month in the given year.

        Parameters:
            m (str or int, optional): Specific month name or alias, or index of the month (1-12) as an integer or a string.
                                      If provided, only that month's range will be returned.
            year (int, optional): Year to use when determining the number of days in February.
                                  Defaults to the instance's reference year.

        Returns:
            dict or None: Dictionary of date ranges for each month (or a single month),
                          formatted as MM/DD strings.
        """    	
        current_year = int(year) if year is not None else self.year
        # leap = self.is_leap_year(current_year)
        days_in_month = self._create_valid_days_in_months(current_year)     
        months = {}
        for i, (month, days) in enumerate(days_in_month.items(), start=1):
            mid_day = days // 2
            months[month] = {"start": f"{i:02d}/01", "middle": f"{i:02d}/{mid_day:02d}", "end": f"{i:02d}/{days:02d}"}
        if m:
            if isinstance(m, str) and m.isdigit():
                m = int(m)
            if isinstance(m, int) and 1 <= m <= 12:
                month_key = list(days_in_month.keys())[m - 1]
                return DateHelper.DateRecord(months.get(month_key))
            return DateHelper.DateRecord(months.get(self.months.get(m.lower())))
        return DateHelper.DateFrame(months)
    
    def adj_weeks_months(self, m=None, year=None):
        """
        Returns the number of weeks in each month for a given year, or for a specific month if specified.

        This method calculates the number of calendar weeks in each month by dividing the number of days
        by 7 and rounding up (i.e., partial weeks count as a full week). It supports optional filtering
        by month, which can be passed as either an integer (1–12) or a string (month name).

        Args:
            m (int or str, optional): The month to retrieve weeks for. Can be:
                - An integer (1 to 12) representing the calendar month.
                - A string (e.g., "March" or "mar") representing the month name.
                If omitted, returns data for all months.
            year (int, optional): The year to evaluate. If not provided, defaults to `self.year`.

        Returns:
            dict or int:
                - If `m` is provided: a dictionary containing the number of weeks for the requested month.
                - If `m` is not provided: a dictionary mapping all month names to their week counts.
        """            
        current_year = int(year) if year is not None else self.year
        days_in_month = self._create_valid_days_in_months(current_year)
        
        # Calculate weeks
        weeks_in_month = {month: math.ceil(days / 7) for month, days in days_in_month.items()}
        
        if m:
            if isinstance(m, str) and m.isdigit():
                m = int(m)
            if isinstance(m, int) and 1 <= m <= 12:
                month_key = list(weeks_in_month.keys())[m - 1]
                return {month_key: weeks_in_month[month_key]}
            if isinstance(m, str):
                mnth = self._ret_months(m)
                month_key = mnth.capitalize()
                return {month_key: weeks_in_month.get(month_key)}
            return None
        return weeks_in_month
   
    def adj_quarters(self, q=None):
        """
        Returns start, middle, and end dates for each quarter.

        Parameters:
            q (str, optional): Specific quarter name (e.g., "q1"). If provided,
                               only that quarter's range is returned.

        Returns:
            DateHelper.DateRecord or DateHelper.DateFrame: Structured date access for quarters.
        """
        quarters = {
            "q1": {"start": "01/01", "middle": "02/15", "end": "03/31"},
            "q2": {"start": "04/01", "middle": "05/15", "end": "06/30"},
            "q3": {"start": "07/01", "middle": "08/15", "end": "09/30"},
            "q4": {"start": "10/01", "middle": "11/15", "end": "12/31"},
        }
        if q:
            q_key = self.quarters.get(q.lower())
            if q_key and q_key in quarters:
                return DateHelper.DateRecord(quarters[q_key])
            else:
                raise ValueError(f"Invalid quarter: '{q}'")
        return DateHelper.DateFrame(quarters)    

    def adj_seasons(self, season=None, year=None, include_year=False):
        """
        Returns start, middle, and end dates for each season, factoring in leap years,
        and optionally includes the year in the date strings.

        Returns:
            DateHelper.DateRecord or DateHelper.DateFrame
        """
        current_year = int(year) if year is not None else self.year
        template = self._create_seasonal_date_template(current_year)
        
        if include_year:
            seasonal_dict = {}
            for period, date in template.items():
                start_month, start_day = map(int, date['start'].split('/'))
                mid_month, mid_day = map(int, date['middle'].split('/'))
                end_month, end_day = map(int, date['end'].split('/'))

                start_year = current_year - 1 if start_month == 12 else current_year
                mid_year = current_year if period == "winter" else start_year
                end_year = current_year if period == "winter" else start_year

                seasonal_dict[period] = {
                    "start": f"{start_month:02d}/{start_day:02d}/{start_year}",
                    "middle": f"{mid_month:02d}/{mid_day:02d}/{mid_year}",
                    "end": f"{end_month:02d}/{end_day:02d}/{end_year}",
                }
        else:
            seasonal_dict = template

        if season:
            season_key = self.seasons.get(season.lower())
            if season_key and season_key.lower() in seasonal_dict:
                return DateHelper.DateRecord(seasonal_dict[season_key.lower()])
            else:
                raise ValueError(f"Invalid season: '{season}'")
        
        return DateHelper.DateFrame(seasonal_dict)

    def __dir__(self):
        return ['months', 'year', 'days', 'quarters', 'seasons', 'time_units', 'special_units', 'is_leap_year', 'adj_months', 'adj_quarters', 'adj_seasons', 'adj_weeks_months', 'days_in_month']



class numbers:
    """
    A utility class for detecting and converting between numeric and linguistic
    representations of cardinal and ordinal values.

    This class provides type detection and transformation across the four major
    numeric forms encountered in natural language inputs:
        - Cardinal Number (e.g., 2)
        - Cardinal Word (e.g., "two")
        - Ordinal Number (e.g., "2nd")
        - Ordinal Word (e.g., "second")

    It leverages the `numbr` library to perform conversions and wraps the logic
    in a consistent, type-safe API. Common use cases include normalization of
    numeric phrases in time expressions (e.g., "third quarter", "2nd week").
    """
    # num_type = staticmethod(numbr.Type)
    @staticmethod
    def num_type(value):
        """
        Infer the numeric representation type of a given input value.

        This method classifies the input into one of four types based on its structure and content:
            - "Cardinal Number" for digit-only numbers (e.g., 42, "100")
            - "Ordinal Number" for ordinal numerals with suffixes (e.g., "1st", "22nd")
            - "Cardinal Word" for spelled-out cardinal numbers (e.g., "four", "eighteen")
            - "Ordinal Word" for spelled-out ordinal numbers (e.g., "third", "twentieth")

        Parameters:
            value (str | int): The input to analyze.

        Returns:
            str or None: The detected representation name, or None if it cannot be determined.
        """    	
        result = numbr.Type(value)
        if isinstance(result, str) and " " in result:
            parts = result.strip().split()
            return parts[0].lower() + parts[1].capitalize()
        return result
       
    # to_type = staticmethod(numbr.Cast)
    @staticmethod
    def to_type(value, target=None, as_str=False):
        """
        Convert a numeric value from its current representation to a target representation.

        This method routes the conversion using the internal type map and the `numbr` module's converters.
        If no conversion is needed or the target is unspecified, it either returns the detected type or the original value.

        Parameters:
            value (str | int): The numeric value to convert.
            target (str | None): The target representation to convert to. Must be one of:
                "Cardinal Number", "Cardinal Word", "Ordinal Number", "Ordinal Word".
            as_str (bool, optional): If True, return numeric results as strings. Default is False.

        Returns:
            str | int: The converted result in the requested representation.
        """
        return numbr.Cast(value, target=target, as_str=as_str)    
    
    
   
       
timeline = DateHelper()



__all__ = ["timeline", "numbers"]


