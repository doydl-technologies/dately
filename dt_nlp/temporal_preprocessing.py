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
This module handles structural normalization, grammatical rewriting, and 
morphological harmonization for temporal expressions. It acts as a bridge 
between raw, user-generated language and the stricter requirements of 
downstream parsing and classification systems.

Rather than just correcting spelling, it focuses on shaping temporal phrases 
into canonical, well-formed forms — suitable for syntactic structure validation, 
semantic resolution, and execution in calendrical or timeline systems.

Role in the NLP Pipeline
────────────────────────────────────────────────────
This module sits between surface-level fuzzy correction and the structural 
parsing layer. It receives cleaned-up user input and prepares it by enforcing 
consistency in modifiers, number forms, and syntactic patterns.

It is typically invoked before structure validation, enabling 
higher-confidence recognition of containment, anchoring, intersection, 
and relative forms.

Core Focus
────────────────────────────────────────────────────
- Normalize modifiers (e.g. "this past" → "last")
- Collapse and unify prepositional phrases ("in" → "of")
- Singularize and pluralize temporal units contextually
- Convert ordinal/cardinal phrases to numeric form
- Merge multi-token dates (e.g., "july 4 2022") into unified forms
- Remove or insert implicit temporal anchors ("this", "the", etc.)
- Provide structured tokenization logic that reflects real-world date semantics

Note
────────────────────────────────────────────────────
This module does not classify or validate structural patterns.
It enables them by standardizing expressions for later processing.
It is tightly coupled with `LexicalFuzzer` (for spelling correction) 
and `numbers` (for numeric normalization), and acts as a foundation 
for structure recognition and semantic evaluation downstream.
"""
import re
import random
import inspect
import functools

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import numbr

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from .string_similarity.spell_correction import LexicalFuzzer
from .arithmetic import timeline, numbers



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.


# CONVERT WORDS BETWEEN SINGULAR AND PLURAL FORMS
#────────────────────────────────────────────────────────────────────────────
# The TemporalInflection class provides methods for handling pluralization and singularization of 
# time-related words such as months, seasons, quarters, and days of the week.
class TemporalInflection:
    """
    A utility class for handling singular and plural transformations of various time-related terms.

    This class provides methods to:
    - Convert plural words (e.g., "months") to their singular forms (e.g., "month").
    - Pluralize words based on predefined rules.
    - Handle specific cases for time units, days, months, seasons, and quarters.
    - TemporalInflection entire phrases containing pluralized words.
    """
    def __init__(self, quarters=timeline.quarters, months=timeline.months, days=timeline.days, seasons=timeline.seasons):
        self.plural_to_singular = {}

        # Build up a reverse lookup map for known plural forms
        self._load_canonical_plural_map(months)
        self._load_canonical_plural_map(days)
        self._load_canonical_plural_map(seasons)
        self._load_canonical_plural_map(quarters)

        # Handle irregular or rule-based plurals for core time units
        self.time_units_plural_to_singular = {
            "days": "day",
            "weeks": "week",
            "months": "month",
            "quarters": "quarter",
            "years": "year",
            "weekends": "weekend",
            "weekdays": "weekday",
            "seasons": "season",
        }
        
    def _load_canonical_plural_map(self, mapping):
        """For each canonical time term, generate expected plural variants like "s"/"ies"."""    	
        for k, v in mapping.items():
            canonical = v.lower()
            plural_s = canonical + "s"
            plural_ies = canonical[:-1] + "ies" if canonical.endswith("y") and canonical != "may" else None
            self.plural_to_singular[plural_s] = canonical
            if plural_ies:
                self.plural_to_singular[plural_ies] = canonical
            
    def _pluralize_word(self, word):
        """Converts a word to its plural form based on common English rules."""
        word = self.remove_possessive_ownership(word)        
        if word.lower() in set(timeline.days.index.keys()):
            return word + "s"
        elif word.endswith('y') and word.lower() not in {"may"}:
            return word[:-1] + 'ies'
        elif word == 'weekend':
            return word + 's'
        elif word == 'weekday':
            return word + 's'           
        elif word == 'month':
            return 'Months'
        elif word == 'year':
            return 'Years'
        else:
            return word + 's'

    def _pluralize_keys_and_values(self, valid_dict):
        """ Generates a dictionary with pluralized keys and values."""
        plural_dict = {}
        for key, value in valid_dict.items():
            plural_key = self._pluralize_key(key)
            plural_value = self._pluralize_word(value)
            plural_dict[plural_key.lower()] = plural_value.lower()
            self.plural_to_singular[plural_key.lower()] = key.lower()
            self.plural_to_singular[plural_value.lower()] = value.lower()
        return plural_dict

    def _pluralize_key(self, key):
        """ Converts a key to its plural form based on known patterns."""
        if key.startswith("quarter"):
            return key + "s"
        elif key.endswith(" 1"):
            return key[:-2] + " 1s"
        elif key.endswith(" 2"):
            return key[:-2] + " 2s"
        elif key.endswith(" 3"):
            return key[:-2] + " 3s"
        elif key.endswith(" 4"):
            return key[:-2] + " 4s"
        elif key.endswith("quarter"):
            return key[:-1] + "s"
        else:
            return key + "s"

    def _singularize_word(self, word):
        """
        Converts a plural form of a word into its singular form using a series of checks:        
            - Remove common possessive suffixes            
            - Check against known time unit mappings.            
            - Check preloaded canonical plural mappings.
            - Define exceptions: words that end in "s" but should not be singularized.
            - Fallback rule: handle words ending in "ies" (e.g., "cities" -> "city")
            - Fallback rule: remove the trailing "s" if it exists and isn't part of a double "ss"        
        
        """
        original_word = word
        word = word.strip().lower()
        
        if word.endswith("’s") or word.endswith("'s"):
            word = word[:-2]
        elif word.endswith("s’") or word.endswith("s'"):
            word = word[:-1]
        
        if word in self.time_units_plural_to_singular:
            return self.time_units_plural_to_singular[word]
        
        if word in self.plural_to_singular:
            return self.plural_to_singular[word]
        
        exceptions = {"this", "previous"}
        if word in exceptions:
            return original_word
        
        if word.endswith("ies"):
            return word[:-3] + "y"
        
        elif word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        
        return original_word   
    
    def remove_possessive_ownership(self, word):
        """
        Removes possessive endings from a word to normalize it for further processing.
        """
        if word.endswith("’s") or word.endswith("'s"):
            return word[:-2]
        elif word.endswith("s’") or word.endswith("s'"):
            return word[:-2]
        return word   
       
    # Singularization Interfaces
    # -----------------------------   
    def singularize(self, valid_input):
        if isinstance(valid_input, str): # Case 1: String input
            singular = self._singularize_word(valid_input)
            return singular
        elif isinstance(valid_input, set): # Case 2: Set input
            return {self._singularize_word(item) for item in valid_input}
        elif isinstance(valid_input, dict): # Case 3: Dictionary input
            result = {}
            for key, value in valid_input.items():
                singular = self._singularize_word(value)
                result[key.lower()] = singular
            return result
        elif isinstance(valid_input, list): # Case 4: List input   
            return [self._singularize_word(item) for item in valid_input]
        else:
            raise TypeError("Input must be a string, dictionary, or set")
       
    def singularize_phrase(self, phrase):
        """Converts all plural words in a phrase to their singular forms using the generic singularize()."""
        if isinstance(phrase, str):
            words = phrase.split()
        elif isinstance(phrase, list):
            words = phrase        
        singular_words = self.singularize(words)
        return ' '.join(singular_words)       

    # Pluralization Interfaces
    # -----------------------------   
    def pluralize(self, valid_input):
        if isinstance(valid_input, str): # Case 1: String input
            plural = self._pluralize_word(valid_input)
            self.plural_to_singular[plural.lower()] = valid_input.lower()
            return plural.lower()
        elif isinstance(valid_input, dict): # Case 2: Dictionary input
            result = {}
            for key, value in valid_input.items():
                plural_value = self._pluralize_word(value)
                key_lower = key.lower()
                plural_lower = plural_value.lower()
                self.plural_to_singular[plural_lower] = value.lower()
                result[key_lower] = plural_lower
            return result
        elif isinstance(valid_input, set): # Case 3: Set input
            plural_set = set()
            for item in valid_input:
                plural_item = self._pluralize_word(item)
                self.plural_to_singular[plural_item.lower()] = item.lower()
                plural_set.add(plural_item.lower())
            return plural_set
        elif isinstance(valid_input, list): # Case 4: List input
            plural_list = []
            for item in valid_input:
                plural_item = self._pluralize_word(item)
                self.plural_to_singular[plural_item.lower()] = item.lower()
                plural_list.append(plural_item.lower())
            return plural_list
        else:
            raise TypeError("Input must be a string, dictionary, or set")
       
    def pluralize_phrase(self, phrase):
        """ Converts all singular words in a phrase to their plural forms."""
        if isinstance(phrase, str):
            words = phrase.split()
        elif isinstance(phrase, list):
            words = phrase
        plural_words = [self.pluralize(word) for word in words]
        return ' '.join(plural_words)        
       
    def __dir__(self):
        return ['singularize_phrase', 'pluralize', 'singularize', 'pluralize_phrase', 'remove_possessive_ownership']




# EXPRESSION TOKENIZATION FOR TEMPORAL PHRASES
#────────────────────────────────────────────────────────────────────────────
# The Expression class provides flexible parsing for temporal expressions that
# may be passed as strings or lists. It normalizes input, applies custom 
# tokenization logic for partial dates (e.g., "july 4 2022"), and supports 
# optional merging of year tokens. 
#
# The accompanying @expr decorator automatically wraps function arguments
# so that downstream logic can always assume a consistent Expression interface.
class Expression:
    """
    Class for expressions that can be initialized
    with either a str or a list. It provides a single tokenize method
    that applies custom date-aware tokenization logic.
    """
    def __init__(self, value):
        self.original_type = type(value)  # Store the original type    	
        if isinstance(value, list):
            self.raw = ' '.join(str(x) for x in value) # Convert list input to a single string.
        elif isinstance(value, str):
            self.raw = " ".join(value.split())             
        else:
            raise TypeError("Expression only supports str or list input.")

    def tokenize(self, tokenize_date=False, include_year=True, numeric_plausibility=False):
        """
        Tokenizes the expression based on the provided parameters.

        Args:
            tokenize_date (bool): If True, performs simple whitespace splitting.
                                  If False (default), applies custom date-aware merging.
            include_year (bool): If True, attempts to merge a year token when present.
        
        Returns:
            list of str: A list of normalized tokens.
        """
        if tokenize_date:
            return self.raw.split()

        tokens = re.sub(r',', '', self.raw.lower()).split()
        tokens = self._merge_day_of_month(tokens, numeric_plausibility=numeric_plausibility)
        tokens = self._merge_date_tokens(tokens, include_year=include_year, numeric_plausibility=numeric_plausibility)
        tokens = self._merge_month_year(tokens)
        return tokens
       
    def _merge_date_tokens(self, tokens, include_year=True, numeric_plausibility=False):
        """
        Merges tokens representing date expressions into single tokens,
        such as converting "july 04" into "july 4" and optionally including
        a subsequent year token.

        Args:
            tokens (list of str): List of tokens to be merged.
            include_year (bool): Include year token if present.
            numeric_plausibility (bool): Ensure day values are valid for the given month.

        Returns:
            list of str: List of tokens with merged date expressions.
        """
        merged = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.lower() in timeline.months:
                processed = False
                if i + 1 < len(tokens):
                    day_token = tokens[i + 1]
                    try:
                        day_value = int(numbers.to_type(day_token, 'cardinalNumber', as_str=True))
                        max_days = timeline.days_in_month(token).d
                    
                        if (not numeric_plausibility and day_value) or (numeric_plausibility and day_value <= max_days):
                            if include_year and i + 2 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 2]):
                                merged.append(f"{token} {day_value} {tokens[i + 2]}")
                                i += 3
                            else:
                                merged.append(f"{token} {day_value}")
                                i += 2
                            processed = True
                            continue
                    except Exception:
                        pass
                if not processed:
                    merged.append(token)
                    i += 1
            else:
                merged.append(token)
                i += 1
        return merged     
      
    def _merge_day_of_month(self, tokens, numeric_plausibility=False):
        """
        Detects and merges date-like patterns:
          - "<ordinal/cardinal> day of <month>"
          - "<ordinal/cardinal> day <month>"
          - "<ordinal/cardinal> of <month>"
          - with optional year at the end

        Converts them into a partial date: "month <day> [<year>]".

        Skips merging if the phrase starts with an anchoring modifier
        like "next", "last", "this", etc.
        """
        if tokens and tokens[0].lower() in {"next", "last", "this", "from", "starting", "past"}:
            return tokens  # skip anchored expressions

        merged = []
        i = 0
        while i < len(tokens):
            try:
                num_type = numbers.num_type(tokens[i])
                if (
                    i + 1 < len(tokens) and
                    num_type in {"ordinalNumber", "cardinalNumber", "ordinalWord", "cardinalWord"}
                ):
                    num = numbers.to_type(tokens[i], "cardinalNumber", as_str=True)

                    if ( # Case 1: "<ordinal> day of <month> [<year>]"
                        tokens[i + 1] == "day" and
                        i + 3 < len(tokens) and
                        tokens[i + 2] == "of" and
                        tokens[i + 3] in set(timeline.months) and
                        (not numeric_plausibility or int(num) <= timeline.days_in_month(tokens[i + 3]).d)
                    ):
                        if i + 4 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 4]):
                            merged.append(f"{tokens[i + 3]} {num} {tokens[i + 4]}")
                            i += 5
                        else:
                            merged.append(f"{tokens[i + 3]} {num}")
                            i += 4
                        continue

                    elif ( # Case 2: "<ordinal> day <month> [<year>]"
                        tokens[i + 1] == "day" and
                        i + 2 < len(tokens) and
                        tokens[i + 2] in set(timeline.months) and
                        (not numeric_plausibility or int(num) <= timeline.days_in_month(tokens[i + 2]).d)
                    ):
                        if i + 3 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 3]):
                            merged.append(f"{tokens[i + 2]} {num} {tokens[i + 3]}")
                            i += 4
                        else:
                            merged.append(f"{tokens[i + 2]} {num}")
                            i += 3
                        continue

                    elif ( # Case 3: "<ordinal> of <month> [<year>]"
                        tokens[i + 1] == "of" and
                        i + 2 < len(tokens) and
                        tokens[i + 2] in set(timeline.months) and
                        (not numeric_plausibility or int(num) <= timeline.days_in_month(tokens[i + 2]).d)
                    ):
                        if i + 3 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 3]):
                            merged.append(f"{tokens[i + 2]} {num} {tokens[i + 3]}")
                            i += 4
                        else:
                            merged.append(f"{tokens[i + 2]} {num}")
                            i += 3
                        continue
            except Exception:
                pass
            merged.append(tokens[i])
            i += 1
        return merged      
      
    def _merge_month_year(self, tokens):
        """
        Detects and merges patterns like:
          - "<month> <year>"
        Only when they appear at the end of a phrase or are otherwise unmerged.
        """
        merged = []
        i = 0
        while i < len(tokens):
            if (
                i + 1 < len(tokens)
                and tokens[i] in set([unit for unit in [f for f in list(timeline.months)]])
                and re.fullmatch(r"(?:\d{2}|\d{4})", tokens[i + 1])
            ):
                merged.append(f"{tokens[i]} {tokens[i + 1]}")
                i += 2
            else:
                merged.append(tokens[i])
                i += 1
        return merged

    def __repr__(self):
        return f"Expression({self.raw!r})"

    def __str__(self):
        return self.raw

def expr(func):
    """
    Decorator that ensures the 'expression' argument for the function
    is wrapped as an Expression instance.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        if 'expression' in bound.arguments:
            expr_val = bound.arguments['expression']
            if not isinstance(expr_val, Expression):
                bound.arguments['expression'] = Expression(expr_val)
        return func(*bound.args, **bound.kwargs)
    return wrapper





       
   
# NORMALIZE TEMPORAL PHRASES AND TOKEN SEQUENCES
#────────────────────────────────────────────────────────────────────────────
# The TemporalPhraseEngine class provides methods for cleaning, standardizing,
# and transforming temporal expressions prior to parsing. It includes support 
# for article removal, token correction, prefix replacement, and structural 
# normalization of phrases involving quarters, modifiers, and ambiguous patterns.
class TemporalPhraseEngine:
    """
    A utility class for standardizing and preprocessing natural language temporal expressions.

    This class provides methods to:
    - Remove unnecessary articles and modifiers (e.g., "the", "a", "this past").
    - Replace patterns like "in" → "of" for time hierarchy resolution.
    - Normalize quarter references (e.g., "second quarter" → "q2").
    - Apply pluralization/singularization transformations via TemporalInflection.
    - Correct token spelling using hybrid Levenshtein + Jaro-Winkler algorithms.
    - Tokenize and return cleaned temporal phrases for downstream parsing.
    """
    def __init__(self):
        self.temporal_inflect = TemporalInflection()
        # self.numbers = numbers.__class__()        
        self.numbers = numbers()   
        self.quantifier_ranges = {
            "couple": (2, 2), 	# Always 2
            "few": (3, 5),      # Randomly choose between 3 and 5
            "several": (6, 9),  # Randomly choose between 6 and 9
            "many": (10, 15)  	# Randomly choose between 10 and 15 
        }      
        self.ordinal_words_set = self._ordinal_set(vocab=list(LexicalFuzzer.vocabulary))        
        self.ordinal_numbers_set = {word for word in LexicalFuzzer.vocabulary if re.compile(r'^\d+(st|nd|rd|th)$').match(word)}         
        self.drop = self.DropClass()
        self.sub = self.SubstituteClass(parent=self)
        self.match = self.MatchClass()  
        self.insert = self.InsertClass()      

    # ========= Substitute =================================================================================================== 
    class SubstituteClass:
        def __init__(self, parent):
            self.parent = parent  
            
        @expr     	
        def past(self, expression, return_tokens=True):
            """
            Converts ["this", "past"] or ["the", "past"] sequences into ["last"].
            Ensures past modifiers are consistent across temporal expressions.
            """
            tokens = expression.tokenize()  
            i = 0
            while i < len(tokens) - 1:
                if tokens[i] in {"this", "the"} and tokens[i + 1] == "past":
                    tokens[i] = "last"
                    del tokens[i + 1]
                else:
                    i += 1
            return tokens if return_tokens else ' '.join(tokens)
           
        @expr
        def In(self, expression, return_tokens=True):
            """
            Replaces 'in' with 'of' in hierarchical time expressions.
            For example: ["first", "Monday", "in", "January"] becomes ["first", "Monday", "of", "January"].
            """
            tokens = expression.tokenize()  
            i = 0
            while i < len(tokens) - 1:
                if tokens[i] == "in" and (
                    tokens[i + 1] in timeline.months or  
                    tokens[i + 1] in timeline.seasons or
                    tokens[i + 1] in timeline.quarters or 
                    tokens[i + 1] in {"week", "month", "year", "quarter", "season"}
                ):
                    tokens[i] = "of"
                i += 1
            return tokens if return_tokens else ' '.join(tokens)

        @expr
        def any(self, expression, replacements, prefix=False, return_tokens=True):
            """
            Applies token or prefix-based replacements to a temporal expression.

            This method is designed to normalize strings or token sequences by:
            - Replacing specific prefixes (e.g., "the beginning" → "start") when `prefix=True`.
            - Replacing individual tokens or compound phrases using a flat replacement dictionary when `prefix=False`.

            Supports both raw text (string) and pre-tokenized input (list of strings). 
            Can return either a modified string or a token list.

            Args:
                expression (str | list): Input expression to normalize — can be a raw string or a list of tokens.
                replacements (dict): Mapping of patterns (prefixes or tokens) to their replacement values.
                prefix (bool): If True, will look for matching prefixes in the expression (from start only).
                               If False, performs token-by-token replacement, including for compound phrases.
                return_tokens (bool): If True, output is a list of tokens. If False, returns a joined string.

            Returns:
                str | list: The normalized expression, either as a string or token list depending on `return_tokens`.
                            Returns the original input if no replacements apply.
            """
            tokens = expression.tokenize()            
            if prefix:
                text_lower = " ".join(tokens).lower()
                for prefix, replacement in replacements.items():
                    prefix_tokens = prefix.split()
                    prefix_length = len(prefix_tokens)
                    if text_lower.startswith(prefix):
                        new_tokens = [replacement] + tokens[prefix_length:]
                        if return_tokens:
                            return new_tokens
                        return " ".join(new_tokens)
            else:
                i = 0
                while i < len(tokens):
                    for original, replacement in replacements.items():
                        original_tokens = original.split()
                        original_length = len(original_tokens)
                        if tokens[i:i+original_length] == original_tokens: # Check if the slice of tokens matches the original_tokens
                            tokens[i:i+original_length] = [replacement]  # Replace the entire phrase
                            i += original_length - 1  # Adjust index to skip replaced tokens
                            break
                    i += 1
            if return_tokens:
                return self.parent.clean_gaps(tokens)
            return self.parent.clean_gaps(" ".join(tokens))
           
        @expr           
        def approximate_words(self, expression, token_index=None, return_tokens=True):
            """
            Replaces an approximate number word with a randomly chosen numeral string.

            The mapping is defined in self.parent.quantifier_ranges:
              - "couple" always becomes "2"
              - "few" becomes a random integer between 3 and 5
              - "several" becomes a random integer between 6 and 9
              - "many" becomes a random integer between 10 and 15

            This method accepts either a string or a list of tokens. If a string is provided,
            it will be split into tokens. If a token_index is given, the token at that index 
            is inspected and replaced if it matches an approximate number. If no token_index is provided,
            the method will modify the first token that is found in the mapping.

            Args:
                expression (str or list): The temporal expression as a raw string or a list of tokens.
                token_index (int, optional): The index of the token to inspect and potentially replace.
                                             If not provided, the first matching token is replaced.
                return_tokens (bool): If True, return the result as a list of tokens.
                                      If False, join the tokens and return as a string.

            Returns:
                str or list: The updated expression in the requested format.
            """
            tokens = expression.tokenize()            
            if token_index is not None:
                token_index = int(str(token_index))            	
                if token_index < 0 or token_index >= len(tokens):
                    raise IndexError("Token index out of range.")
                indices = [token_index]
            else:
                indices = range(len(tokens))

            for idx in indices:
                token = tokens[idx].lower()
                if token in self.parent.quantifier_ranges:
                    low, high = self.parent.quantifier_ranges[token]
                    tokens[idx] = str(random.randint(low, high))
                    break  # Only replace the first matching token
            return tokens if return_tokens else " ".join(tokens)
        
        @expr
        def ordinal_cardinal(self, expression):
            """
            Converts ordinal and cardinal expressions into their numeric string equivalents.

            This method processes a temporal phrase or token list and replaces any ordinal or 
            spelled-out number (e.g., "first", "twenty-second", "four") with its corresponding 
            integer string form (e.g., "1", "22", "4").

            This normalization helps standardize numeric expressions across phrases 
            before resolution or interpretation.

            Args:
                expression (str or list): A temporal expression as a string or list of tokens.

            Returns:
                list: A list of tokens with ordinal/cardinal values replaced by their numeric strings.
            """            
            tokens = expression.tokenize() 
            tokenized = []
            for token in tokens:
                if self.parent.is_partial_date(token):
                    try:
                        monthname, daytype = token.split() # Expected format: "Month Day", e.g., "July 11"
                        if daytype: # Check what format day number is in
                            if self.parent.numbers.num_type(daytype) == 'ordinalWord':
                                converted_number = self.parent.numbers.to_type(daytype, 'ordinalNumber')
                            elif self.parent.numbers.num_type(daytype) == 'cardinalWord':
                                converted_number = self.parent.numbers.to_type(daytype, 'cardinalNumber', as_str=True)
                            else:
                                converted_number = None
                        if converted_number:
                            tokenized.append(f"{monthname} {converted_number}")
                        else:
                            tokenized.append(token)
                    except ValueError:
                        tokenized.append(token)
                    continue
                try:
                    if self.parent.numbers.num_type(token) == 'ordinalWord':
                        converted = self.parent.numbers.to_type(token, 'ordinalNumber')
                        tokenized.append(converted)                             
                    elif self.parent.numbers.num_type(token) == 'cardinalWord':
                        converted = self.parent.numbers.to_type(token, 'cardinalNumber', as_str=True)
                        tokenized.append(converted)
                    else:
                        tokenized.append(token)                        
                except:            
                    tokenized.append(token)
            return tokenized

        def partial_date(self, expression, include_year=True):
            """
            Merges expression like ["july", "5"], ["july", "1st"], or ["july", "first"]
            into ["july 5"], ["july 1st"], or ["july first"], respectively.

            - Check 1: <Month> <NumericDay>   → "july 5"
            - Check 2: <Month> <OrdinalNum>   → "july 1st"
            - Check 3: <Month> <OrdinalWord>  → "july first"

            Args:
                expression (list of str): Tokenized input text.
                include_year (bool): Whether to include a trailing year in the match.

            Returns:
                list of str: Token list with combined month-day pairs.
            """
            if isinstance(expression, str):
                tokens = re.sub(r',', '', expression.lower()).split()
            else:
                tokens = [str(exp).lower().replace(',', '') for exp in expression]
            merged = []
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if token in timeline.months.keys():
                    processed = False
                    if i + 1 < len(tokens):
                        day_token = tokens[i + 1]
                        # Check 1: "<Month> <NumericDay>"
                        if re.fullmatch(r'0?[1-9]|1[0-9]|2[0-9]|3[01]', day_token):
                            day_value = day_token.lstrip('0')
                            if include_year and i + 2 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 2]):
                                merged.append(f"{token} {day_value} {tokens[i + 2]}")
                                i += 3
                            else:
                                merged.append(f"{token} {day_value}")
                                i += 2
                            processed = True
                            continue
                        # Check 2: "<Month> <OrdinalNumber>"
                        ordinal_pattern = r'(?:[1-9]|1[0-9]|2[0-9]|3[01])(st|nd|rd|th)'
                        if re.fullmatch(ordinal_pattern, day_token):
                            if include_year and i + 2 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 2]):
                                merged.append(f"{token} {day_token} {tokens[i + 2]}")
                                i += 3
                            else:
                                merged.append(f"{token} {day_token}")
                                i += 2
                            processed = True
                            continue
                        # Check 3: "<Month> <OrdinalWord>"
                        if day_token in self.parent.ordinal_words_set:
                            if include_year and i + 2 < len(tokens) and re.fullmatch(r'(?:\d{2}|\d{4})', tokens[i + 2]):
                                merged.append(f"{token} {day_token} {tokens[i + 2]}")
                                i += 3
                            else:
                                merged.append(f"{token} {day_token}")
                                i += 2
                            processed = True
                            continue
                    if not processed:
                        merged.append(token)
                else:
                    merged.append(token)
                i += 1
            return merged        
        
        def __dir__(self):
            default_attrs = [f for f in super().__dir__() if f.startswith("__") and f.endswith("__")]
            public_attrs = ['In', 'any', 'approximate_words', 'past', 'ordinal_cardinal', 'partial_date']
            return sorted(set(default_attrs + public_attrs))                
           
           
    # ========= Drop ===================================================================================================           
    class DropClass:
        def __init__(self):
            # nothing to configure yet — keeping it clean for now
            pass

        @expr
        def this(self, expression, return_tokens=False):
            """
            Remove redundant 'this' when it conflicts with clearer anchors
            ('last', 'past', or a numeric/ordinal) immediately following it.
            """
            def _is_numeric_like(tok):
                """
                Returns True if the token represents any numeric concept.
                """
                tok = str(tok).lower()
                return any([
                    numbr.cardinalNumToCardinalWord(tok),
                    numbr.cardinalWordToCardinalNum(tok),
                    numbr.ordinalWordToCardinalWord(tok),
                    numbr.ordinalNumToCardinalWord(tok),
                ])

            valid_units = {"week", "weeks", "month", "months", "year", "years", "quarter", "quarters"}

            # Detect original type
            input_is_str = isinstance(expression, str)            
            tokens = expression.tokenize()             

            cleaned = []
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if token == "this":
                    next_token = tokens[i + 1] if i + 1 < len(tokens) else ""
                    if next_token in valid_units:
                        cleaned.append("this")
                    elif next_token in {"last", "past", "previous"} or _is_numeric_like(next_token):
                        pass
                    else:
                        cleaned.append("this")
                else:
                    cleaned.append(token)
                i += 1
            if return_tokens:
                return cleaned
            return ' '.join(cleaned) if input_is_str else cleaned
           
        @expr
        def useless_of(self, expression, return_tokens=True):
            """
            Remove “of” when it is only syntactic filler.

            Drops:
              • last <time-unit> of <scope>           → last <time-unit> <scope>
                (but **not** when time-unit is “day” – rule #6 needs it)
              • <time-unit> of <direction|date-part>  → <time-unit> …
              • ordinal <time-unit> of next …         → ordinal <time-unit> next …

            Keeps:
              • first/last/Nth <weekday|day> of <scope>
              • anything where the token before “of” is *not* a recognised time-unit.
            """
            tokens = expression.tokenize()

            PERIODS = set(timeline.days.index.keys())        \
                       | set(timeline.months.keys())            \
                       | set(timeline.seasons.keys())           \
                       | set(timeline.quarters.keys())

            # “day” must NOT be in this set, otherwise we’d strip the ‘of’ that
            # rule #6 depends on.
            TIME_UNITS = {"week", "month", "quarter", "season", "year"}
            DIRECTIONS = {"this", "next", "last", "previous"}
            DAYS = set(timeline.days.index.keys())

            keep = []
            i = 0
            while i < len(tokens):
                if tokens[i] == "of" and 0 < i < len(tokens) - 1:
                    prev_tok = tokens[i - 1].lower()
                    next_tok = tokens[i + 1].lower()

                    # 1)  last <time-unit> of <scope>
                    if prev_tok in TIME_UNITS and next_tok in PERIODS:
                        i += 1
                        continue

                    # 2)  <time-unit> of <direction>
                    if prev_tok in TIME_UNITS and next_tok in DIRECTIONS:
                        i += 1
                        continue
                       
                    # 3)  
                    if prev_tok in DAYS and next_tok in DIRECTIONS:
                        i += 1
                        continue                       

                    # note: we no longer strip “of” when prev_tok == "day"
                    # so patterns like ["last","day","of","april"] are preserved
                    # for the resolver’s rule #6.
                # default – keep token
                keep.append(tokens[i])
                i += 1
            return keep if return_tokens else " ".join(keep)

        @expr
        def of(self, expression, return_tokens=True):            
            """
            Removes any occurrence of the word 'of' from tokens.

            Args:
                expression (str or list): A phrase or token list.
                return_tokens (bool): If True, returns a list of tokens; otherwise returns a string.
            """
            tokens = expression.tokenize()              
            result = []
            for token in tokens:
                parts = token.split()
                filtered_parts = [part for part in parts if part.lower() != 'of']
                if filtered_parts:
                    result.append(' '.join(filtered_parts))
            return result if return_tokens else ' '.join(result)

        @expr
        def one(self, expression, return_tokens=True):            
            """
            Removes the token '1' if it immediately follows 'next', 'last', or 'this'.
            This prevents redundant numeric markers in temporal expressions.
            """
            tokens = expression.tokenize()              
            i = 0
            while i < len(tokens) - 1:
                if tokens[i] in {'next', 'last', 'this', 'previous'} and tokens[i+1] == '1':
                    del tokens[i+1]
                else:
                    i += 1
            return tokens if return_tokens else ' '.join(tokens)

        def article(self, expression, article_type='definite', only_ordinal=False, return_tokens=True):
            """
            Removes specified articles ('the' or 'a') from the start of a phrase or list of tokens.

            Args:
                expression (str or list): The phrase or tokens from which the article is to be removed.
                article_type (str): Type of article to remove ('definite' for "the", 'indefinite' for "a").
                only_ordinal (bool): If True and `article_type` is 'definite', removes "the" only when followed by an ordinal.
                return_tokens (bool): If True, returns a list of tokens; otherwise, returns a concatenated string.

            Returns:
                str or list: The modified phrase or tokens with the specified article removed.
            """
            if isinstance(expression, list):
                expression = ' '.join(expression)  # Convert list of tokens to a single string for processing

            if article_type in ['definite', 'the']:
                if only_ordinal:
                    pattern = r"""^the (
                        first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|
                        eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|
                        eighteenth|nineteenth|twentieth|twenty-first|twenty-second|
                        twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|
                        twenty-eighth|twenty-ninth|thirtieth|thirty-first|\d+(st|nd|rd|th)
                    )\b"""
                    modified_expression = re.sub(pattern, r'\1', expression, flags=re.IGNORECASE)
                else:
                    modified_expression = re.sub(r"^the\s+", "", expression, flags=re.IGNORECASE)
            elif article_type in ['indefinite', 'a']:
                modified_expression = re.sub(r"^a\s+", "", expression, flags=re.IGNORECASE)
            else:
                modified_expression = expression  # Return original if article_type does not match any known types
            if return_tokens:
                return modified_expression.split()  # Return as list of tokens
            return modified_expression  # Return as a single string           
       
        @expr       
        def partial_date_year(self, expression, return_tokens=False):
            if return_tokens:
                pass
            
            tokens = expression.tokenize()              
            month_regex = r'(?:' + '|'.join(timeline.months) + r')'
            pattern = rf'\b({month_regex})(?:\s(0?[1-9]|[12][0-9]|3[01]))?\s(?:\d{{2}}|\d{{4}})\b'            
            updated_tokens = []
            for token in tokens:
                match = re.match(pattern, token, flags=re.IGNORECASE)
                if match:
                    month = match.group(1)
                    day = match.group(2)
                    if day:
                        updated_tokens.append(f"{month} {day}")
                    else:
                        updated_tokens.append(month)
                else:
                    updated_tokens.append(token)
            return updated_tokens
       
        def __dir__(self):
            default_attrs = [f for f in super().__dir__() if f.startswith("__") and f.endswith("__")]
            public_attrs = ['of', 'one', 'this', 'article', 'partial_date_year', 'useless_of']
            return sorted(set(default_attrs + public_attrs)) 
           
           
    # ========= Match ===================================================================================================               
    class MatchClass:
        def __init__(self):
            # nothing to configure yet — keeping it clean for now
            pass        

        @expr  
        def lexical(self, expression, lexical_match, token_index=None, exact=False):
            """
            Checks whether a token or sequence of tokens matches one or more expected lexical units.

            When exact is False (default), this method checks if any token (or a specific token 
            if token_index is provided) matches one of the target lexical units.

            When exact is True, the method requires an exact sequence match:
              - If token_index is provided as an int, the token at that position must match.
              - If token_index is provided as a list or tuple (start, end), the contiguous subsequence 
                (interpreted as inclusive) must exactly match the target sequence.
              - If no token_index is provided and exact is True, the entire token list must exactly match
                one of the candidate sequences if lexical_match is a list of sequences; otherwise, it is compared
                against a single target sequence.

            Args:
                expression (str or list of str): The input, either as a string (which will be tokenized) or a list of tokens.
                lexical_match (str, list of str, or list of list/tuple of str): 
                    The target lexical unit(s) to check against. This can be:
                      - A single string (e.g., "ago"),
                      - A list of strings (e.g., ["today", "tomorrow"]),
                      - Or a list of candidate sequences (e.g., [["next", "day"], ["next", "1", "day"]]).
                token_index (int, str, list, or tuple, optional): The index or range to inspect.
                    If a single index (int, or single-element list/string), only that token is checked.
                    If a two-element list or tuple, it denotes a range (start, end) that is treated as inclusive.
                exact (bool, optional): If True, requires an exact sequence match; otherwise, performs loose matching.

            Returns:
                bool: True if a match is found under the specified conditions, False otherwise.
            """
            tokens = expression.tokenize()              
            if isinstance(lexical_match, str):
                target = [lexical_match.lower()]
                candidate_sequences = None
            elif isinstance(lexical_match, list):
                if lexical_match and all(isinstance(item, (list, tuple)) for item in lexical_match):
                    candidate_sequences = [[w.lower() for w in seq] for seq in lexical_match]
                    target = None
                else:
                    candidate_sequences = None
                    target = [word.lower() for word in lexical_match]
            else:
                raise TypeError("lexical_match must be a string or a list (of strings or sequences).")

            def check_subsequence(seq):
                seq_lower = [t.lower() for t in seq]
                if candidate_sequences is not None:
                    return any(seq_lower == cand for cand in candidate_sequences)
                else:
                    return seq_lower == target if exact else any(t in target for t in seq_lower)

            if token_index is not None:
                if isinstance(token_index, list):
                    if len(token_index) == 1:
                        token_index = int(str(token_index[0]))
                    elif len(token_index) == 2:
                        token_index = tuple(int(str(i)) for i in token_index)
                    else:
                        raise ValueError("token_index list must have one or two elements.")
                elif isinstance(token_index, (int, str)):
                    token_index = int(token_index)
                elif isinstance(token_index, tuple):
                    if len(token_index) != 2:
                        raise ValueError("token_index tuple must have exactly two elements.")
                    token_index = tuple(int(str(i)) for i in token_index)
                else:
                    raise TypeError("token_index must be an int, a string, a list, or a tuple.")

                if isinstance(token_index, int):
                    if token_index < 0 or token_index >= len(tokens):
                        raise IndexError("Token index out of range.")
                    return tokens[token_index].lower() in (target if target is not None else sum(candidate_sequences, []))
                elif isinstance(token_index, tuple):
                    start, end = token_index
                    if start < 0 or end >= len(tokens) or start > end:
                        return False  # Avoid raising an IndexError; just return False
                    return check_subsequence(tokens[start:end + 1])
            else:
                return check_subsequence(tokens)


    # ========= Insert ===================================================================================================    
    class InsertClass:
        def __init__(self):
            # nothing to configure yet — keeping it clean for now
            pass

        @expr  
        def this(self, expression, return_tokens=True):
            """
            Inserts an implicit temporal direction ('this') into a list of tokens if none exists.

            - If a single-token exception like 'today', 'tomorrow', 'yesterday',
              we skip insertion.
            - Otherwise, we look for any named period (month, weekday, season, quarter)
              that is not already preceded by 'this', 'next', 'last', or an ordinal/number 
              that merges it into an ordinal expression (e.g., "first Monday").
            - If found, insert 'this' before it and return immediately.
            """
            def _remove_redundant_this(tokens):
                month_names = set(list(timeline.adj_months().keys()))    
                result = []
                i = 0
                while i < len(tokens):
                    if i <= len(tokens) - 3:
                        if (tokens[i].lower() == "this" and 
                            tokens[i+1].lower() in month_names and 
                            tokens[i+2].isdigit()):
                            i += 1
                            continue
                    result.append(tokens[i])
                    i += 1
                return result
            
            DIRECTION = {"this", "next", "last", 'previous'}
            EXCEPTIONS = {"today", "yesterday", "tomorrow"}
            NAMED_PERIODS = set(
                k.lower() for k in (
                    list(timeline.adj_months().keys())
                    + list(timeline.days.index.keys())
                    + list(timeline.adj_quarters().keys())
                    + list(timeline.seasons.keys())
                )
            )
            tokens = expression.tokenize()              
            if len(tokens) == 1 and tokens[0].lower() in EXCEPTIONS:
                return tokens
            for i, token in enumerate(tokens):
                tok = token.lower()

                if tok in NAMED_PERIODS:
                    if i > 0:
                        prev = tokens[i-1].lower()
                        if prev.isdigit() or numbers.num_type(prev) in {'ordinalNumber', 'ordinalWord'}:                          
                            continue

                    j = i - 1
                    while j >= 0:
                        p = tokens[j].lower()
                        if p in DIRECTION:
                            return tokens
                        if not (p.isdigit() or numbers.num_type(p) in {'ordinalNumber', 'ordinalWord'}):                             
                            break
                        j -= 1
                    return tokens[:i] + ['this'] + tokens[i:]
            return _remove_redundant_this(tokens) if return_tokens else ' '.join(_remove_redundant_this(tokens))

    @expr
    def clean_gaps(self, expression):
        """
        Cleans up gaps or empty elements in a string or list.

        Args:
            expression (str or list): The input to be cleaned. 
                - If a string, extra whitespace (spaces, tabs, newlines) is removed and 
                  words are separated by a single space.
                - If a list, all falsy values (e.g., empty strings, None, 0) are removed.
        """    
        if expression.original_type is str:
            return " ".join(expression.raw.split())
        else:
            return expression.tokenize()
       
    def _ordinal_set(self, vocab):
        ordinal_word_pattern = re.compile(
            r'\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|'
            r'eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|'
            r'twentieth|twenty-first|twenty-second|twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|twenty-eighth|twenty-ninth|'
            r'thirtieth|thirty-first)\b',
            re.IGNORECASE
        )

        ordinal_words = set()
        for term in vocab:
            match = ordinal_word_pattern.search(term)
            if match:
                ordinal_words.add(match.group(0).lower())

        words = sorted(ordinal_words)
        compound_no_hyphens = [word.replace("-", " ") for word in words if "-" in word]
        full_ordinal_set = set(words + compound_no_hyphens)
        return sorted(full_ordinal_set)

    @expr         
    def _hyphenate_word_numbers(self, expression):
        """
        Adds hyphens to spelled-out compound numbers like 'twenty two' -> 'twenty-two'.
        """
        expr = expression.tokenize()        
        pattern = r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s(one|two|three|four|five|six|seven|eight|nine)\b"
        return re.sub(pattern, r"\1-\2", expr, flags=re.IGNORECASE)

    @expr         
    def is_partial_date(self, expression, include_year=False, return_val=False):
        """
        Checks if a string matches any of the following patterns:
        - Check 1: "<Month> <NumericDay>"
        - Check 2: "<Month> <OrdinalNumber>"
        - Check 3: "<Month> <OrdinalWord>"
        - Check 5: "<Month> <NumericDay> <Year>"
        - Check 6: "<Month> <OrdinalNumber> <Year>"
        - Check 7: "<Month> <OrdinalWord> <Year>"        

        Args:
            expression (str): The input string to check.
            include_year (bool): If True, accept month-year pairs like "may 2025".
            return_val (bool): If True, return the details of the date found in a dictionary.

        Returns:
            bool or dict: True if the string matches any valid partial date format, or
                          dict with month, day, and optionally year if return_val is True.
        """
        tokens = expression.tokenize()
        if len(tokens) == 1 and len(tokens[0].split()) > 1:
            tokens = ' '.join([str(t) for t in tokens]).split()
            
        if len(tokens) < 2 or len(tokens) > 3:
            return False
           
        month = tokens[0]
        value = tokens[1]
        year = tokens[2] if len(tokens) == 3 else None
        if month not in timeline.months.keys():
            return False

        month_max_days = int(timeline.days_in_month(month, year=year).d)
        year_pattern = r'(?:\d{2}|\d{4})'
        if include_year and len(tokens) == 2 and re.fullmatch(year_pattern, value):
            if return_val:
                return {"month": month, "day": None, "year": value}
            return True
        
        checks = [
            len(tokens) == 2 and self.numbers.num_type(value) == 'cardinalNumber' and 1 <= int(self.numbers.to_type(value, target='cardinalNumber')) <= month_max_days,
            len(tokens) == 2 and self.numbers.num_type(value) == 'ordinalNumber' and 1 <= int(self.numbers.to_type(value, target='cardinalNumber')) <= month_max_days,
            len(tokens) == 2 and self.numbers.num_type(value) == 'ordinalWord',
            year and re.fullmatch(year_pattern, year) and self.numbers.num_type(value) == 'cardinalNumber' and 1 <= int(self.numbers.to_type(value, target='cardinalNumber')) <= month_max_days,
            year and re.fullmatch(year_pattern, year) and self.numbers.num_type(value) == 'ordinalNumber' and 1 <= int(self.numbers.to_type(value, target='cardinalNumber')) <= month_max_days,
            year and re.fullmatch(year_pattern, year) and self.numbers.num_type(value) == 'ordinalWord',
        ]
        if any(checks):
            if return_val:
                day_val = None
                year_val = None

                if len(tokens) == 2:
                    if self.numbers.num_type(value) in {'cardinalNumber', 'ordinalNumber', 'ordinalWord'}:
                        day_val = value
                elif len(tokens) == 3:
                    day_val = value
                    year_val = year

                return {
                    "month": month,
                    "day": day_val,
                    "year": year_val
                }
            return True
        return False

    def inflect(self, expression, mode="singular", return_tokens=True):
        """
        Inflects a temporal expression (string or list of tokens) to either singular or plural form.

        Args:
            expression (str or list): Input phrase or token list to be inflected.
            mode (str): Either 'singular' or 'plural'.
            return_tokens (bool): If True, returns list of tokens. If False and input is a string, returns a string.

        Returns:
            str or list: Inflected version of the input in the requested form.
        """
        if mode not in {"singular", "plural"}:
            return expression 
        if isinstance(expression, str):
            result = (
                self.temporal_inflect.singularize_phrase(expression)
                if mode == "singular"
                else self.temporal_inflect.pluralize_phrase(expression)
            )
            return result.split() if return_tokens else result
        elif isinstance(expression, list):
            return (
                self.temporal_inflect.singularize(expression)
                if mode == "singular"
                else self.temporal_inflect.pluralize(expression)
            )
        return expression

    def normalize(self, phrase, prefix_replace=None, remove_article=None, singularize=False, replacements=None):
        """
        Standardizes and tokenizes a temporal phrase through several preprocessing steps.
        
        This method:
        - Corrects spelling using LexicalFuzzer.hybrid_correction.
        - Canonicalizes quarter references (e.g., "first quarter" → "q1").
        - Optionally removes specified articles ("a", "the").
        - Replaces specified prefixes to ensure consistency.
        - Optionally converts plural words to singular.
        - Applies custom token replacements.
        - Returns a list of normalized tokens, or None if the expression is too short.
        
        Args:
            phrase (str): The raw temporal phrase.
            prefix_replace (dict): Mapping for prefix replacements.
            remove_article (list or str): Articles to remove, can be 'indefinite', 'definite', or both.
            singularize (bool): Flag to convert plural words to singular.
            replacements (dict): Additional token replacements.
        
        Returns:
            list of str or None: The tokenized and standardized phrase.
        """    
        # Clean extra spaces.
        phrase = " ".join(phrase.split())
        
        # Spell-correct tokens using LexicalFuzzer's hybrid approach.
        phrase_tokens = LexicalFuzzer.hybrid_correction(phrase)
        if not phrase_tokens:
            return None
        
        phrase = ' '.join(phrase_tokens)
        
        # Normalize quarter references.
        phrase = self.sub.any(phrase, replacements={k: v for k, v in timeline.quarters.items() if k != v}, prefix=False, return_tokens=False)  
        
        # Handle article removal.
        if remove_article:
            if isinstance(remove_article, str):
                remove_article = [remove_article]
            remove_article = [article.lower() for article in remove_article]
            if 'definite' in remove_article or 'the' in remove_article:
                phrase = self.drop.article(phrase, article_type='definite', only_ordinal=False, return_tokens=False)
            if 'indefinite' in remove_article or 'a' in remove_article:
                phrase = self.drop.article(phrase, article_type='indefinite', only_ordinal=False, return_tokens=False)
        
        if prefix_replace:
            phrase = self.sub.any(phrase, replacements=prefix_replace, prefix=True, return_tokens=False) 
        
        if replacements:
            phrase = self.sub.any(phrase, replacements=replacements, prefix=False, return_tokens=False)  
        
        if singularize:
            phrase = self.inflect(phrase, mode="singular", return_tokens=False)  
        phrase = phrase.lower().strip()

        tokens = Expression(phrase).tokenize()       
        if not tokens:
            return None 
        return tokens
       
    def __dir__(self):
        default_attrs = [f for f in super().__dir__() if f.startswith("__") and f.endswith("__")]
        public_attrs = [
            'quantifier_ranges', 'drop', 'inflect_phrase', 'inflect_tokens', 'normalize',
            'sub', 'inflect', 'match', 'insert', 'extract', 'is_partial_date', 'ordinal_number',
            'ordinal_words_set', 'ordinal_numbers_set', 'temporal_inflect', 'numbers', 'clean_gaps'
            ]
        return sorted(set(default_attrs + public_attrs))  

  
# Instantiate the TemporalPhraseEngine class.
PhraseEngine = TemporalPhraseEngine()



__all__ = ["PhraseEngine"]


