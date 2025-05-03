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
Understanding The Module
─────────────────────────────
This module provides intelligent token correction for natural language phrases,
specifically designed for temporal expression parsing. It aims to correct misspellings
(e.g., "secnd" → "second") while allowing optional control over whether ordinal terms
(like "2nd", "twenty-first") should be corrected or preserved.

Key Features:
-----------------------------
- Recognizes and optionally preserves ordinal expressions (1st–366th, "twenty-second", etc.)
- Automatically hyphenates compound number expressions (e.g., "twenty two" → "twenty-two")
- Uses fuzzy matching (Levenshtein and Jaro-Winkler) to correct tokens to known temporal words

Core Components:
-----------------------------
- `CANONICAL_TEMPORAL_TERMS`: A set of valid time-related words, including singular and plural forms
- `ALL_ORDINALS`: A combined set of numeric, word-based, and hyphenated ordinals
- `Levenshtein` & `JaroWinkler`: Distance algorithms used to compare similarity between tokens
"""
import re

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import numbr


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.


# ──────────────────────────────────────────────────────────────────────────────────────
# CANONICAL TEMPORAL TERMS
# These are the raw temporal surface forms expected in natural language expressions.
# The goal is to ensure we have a strong lexical base for fuzzy string matching,
# token normalization, and spelling correction across various temporal concepts.
# This includes singular/plural forms, possessive variants, and alternate inflections.
# ──────────────────────────────────────────────────────────────────────────────────────
CANONICAL_TEMPORAL_TERMS = {
    # ─ Absolute time units ─
    # Represent base time measurement units (ordered from smallest to largest).
    "day", "days", "day's", "days'",
    "week", "weeks", "week's", "weeks'",
    "month", "months", "month's", "months'",
    "quarter", "quarters", "quarter's", "quarters'",
    "season", "seasons", "season's", "seasons'",
    "year", "years", "year's", "years'",
    "half",

    # ─ Weekdays ─
    # Captures all variations of the seven-day cycle, including plural and possessive forms.
    "sunday", "mondays", "monday", "sundays",
    "tuesday", "tuesdays",
    "wednesday", "wednesdays",
    "thursday", "thursdays",
    "friday", "fridays",
    "saturday", "saturdays",
    "weekday", "weekdays", "weekday's", "weekdays'",
    "weekend", "weekends", "weekend's", "weekends'",

    # ─ Months ─
    # Includes every month name and possible plural/possessive variants.
    # Some forms (e.g., "januaries") are rare but possible in certain temporal phrases.
    "january", "januarys", "januaries", "january's", "januarys'", "januaries'",
    "february", "februarys", "februaries", "february's", "februarys'", "februaries'",
    "march", "marches", "march's", "marches'",
    "april", "aprils", "april's", "aprils'",
    "may", "mays", "may's", "mays'",
    "june", "junes", "june's", "junes'",
    "july", "julys", "julies", "july's", "julys'",
    "august", "augusts", "august's", "augusts'",
    "september", "septembers", "september's", "septembers'",
    "october", "octobers", "october's", "octobers'",
    "november", "novembers", "november's", "novembers'",
    "december", "decembers", "december's", "decembers'",

    # ─ Quarters ─
    # Compact representations for business/financial time periods.
    "q1", "q2", "q3", "q4",

    # ─ Seasons ─
    # Common seasonal terms across both meteorological and colloquial usage.
    "spring", "springs", "spring's", "springs'",
    "summer", "summers", "summer's", "summers'",
    "fall", "falls", "fall's", "falls'",
    "winter", "winters", "winter's", "winters'",
    "autumn", "autumns", "autumn's", "autumns'",

    # ─ Relative day references ─
    # Words that refer to dates relative to the current date (e.g., "today", "tomorrow").
    "today", "todays", "today's",
    "tomorrow", "tomorrows", "tomorrow's",
    "yesterday", "yesterdays", "yesterday's",

    # ─ Temporal modifiers ─
    # Modifiers that describe placement in time ("next", "last") or location within a period.
    "start", "starting","middle", "end",
    "of", "this", "next", "last", "from", "previous", "in", "on",

    # ─ Durational markers ─
    "ago",
}

def _to_ordinal_words(day):
    """
    Converts a numeric day value into its corresponding ordinal word form (e.g., 1 -> "first").
    """    
    try:
        day_int = int(day)
    except (ValueError, TypeError):
        return None

    word = numbr.intToOrdinalWords(day_int)
    if not word:
        return None

    return word
   
def _to_ordinal_number(day):
    """
    Converts a numeric day value into its ordinal number form (e.g., 1 -> "1st").
    """    
    try:
        day_int = int(day)
    except (ValueError, TypeError):
        return None

    suffix = numbr.ordinalSuffix(day_int)
    if not suffix:
        return None

    return f"{day_int}{suffix}"

def _hyphenate_word_numbers(text):
    """
    Converts compound cardinal number phrases into hyphenated form.
    """	
    # NLP pre-processing trick:
    # Turns "twenty three" into "twenty-three", which helps match things like "twenty-third"
    # Useful for aligning fuzzy tokens with ordinal patterns.
    pattern = r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s(one|two|three|four|five|six|seven|eight|nine)\b"
    return re.sub(pattern, r"\1-\2", text, flags=re.IGNORECASE)

def _is_cardinal(token):
    """
    Checks whether a token is a cardinal number (i.e. an integer).

    Used to identify tokens like "1", "12", or "365"
    that represent whole numeric quantities in temporal expressions.
    """	
    return token.isdigit()

def expand_dates(monthnames, terms):
    """
    Expands date expressions in the form of "<month> <day>" (e.g., "apr 05") into 
    both ordinal number (e.g., "apr 5th") and ordinal word (e.g., "apr fifth") forms.
    """	
    def _extract_mmdd(terms):
        # Build a regex pattern using the keys of _MONTH_DAYS
        month_pattern = r'\b(' + '|'.join(monthnames.keys()) + r')\s0*(\d{1,2})\b'

        # Extract terms that match the pattern exactly as in the original set, without normalization
        # Match month name or abbreviation followed by space and a day (with or without leading zero)
        raw_date_terms = sorted([
            term for term in terms
            if re.fullmatch(month_pattern, term, re.IGNORECASE)
        ])
        return raw_date_terms
    
    date_terms = _extract_mmdd(terms)
    transformed_dates = []

    for date in date_terms:
        parts = date.split()
        if len(parts) != 2:
            continue  # Skip malformed entries

        month = parts[0]
        day_part = parts[1]

        ordinal_number = _to_ordinal_number(day_part)
        if ordinal_number:
            transformed_dates.append(f"{month} {ordinal_number}")

        ordinal_words = _to_ordinal_words(day_part)
        if ordinal_words:
            transformed_dates.append(f"{month} {ordinal_words}")

    return transformed_dates

# ───────────────────────────────────────────────────────────────────────────────────────────
# PARTIAL DATES
# These are used to represent incomplete date expressions like "march 05" or "november 12".
# Format: "month dd" (always lowercase month + 2-digit day with leading zero).
# Useful for pattern matching or date normalization in NLP pipelines.
# ───────────────────────────────────────────────────────────────────────────────────────────

# Days in each month (leap year variant for February)
_MONTH_DAYS = {
    "january": 31, "jan": 31,
    "february": 29, "feb": 29,
    "march": 31, "mar": 31,
    "april": 30, "apr": 30,
    "may": 31,
    "june": 30, "jun": 30,
    "july": 31, "jul": 31,
    "august": 31, "aug": 31,
    "september": 30, "sep": 30,
    "october": 31, "oct": 31,
    "november": 30, "nov": 30,
    "december": 31, "dec": 31
}

# All "month day" combinations (e.g., "january 01", "february 14")
PARTIAL_DATES = set()
for month, days in _MONTH_DAYS.items():
    for day in range(1, days + 1):
        PARTIAL_DATES.add(f"{month} {day}")      	
        PARTIAL_DATES.add(f"{month} {day:02}")
        
# Augment the canonical terms with partial dates
CANONICAL_TEMPORAL_TERMS.update(PARTIAL_DATES)   
ORDINAL_DATE_TERMS = expand_dates(_MONTH_DAYS, CANONICAL_TEMPORAL_TERMS)

# ────────────────────────────────────────────────────────────────────────────────
# ORDINALS
# These are used in expressions like "second Monday", "21st of March", etc.
# Including both numeric suffixes (1st, 2nd...) and lexical (first, second...).
# ────────────────────────────────────────────────────────────────────────────────

# e.g., "1st", "2nd", ..., "366th"
NUMERIC_ORDINALS = {f"{i}{numbr.ordinalSuffix(i)}" for i in range(1, 367)}

# e.g., "first", "second", ..., "thousandth"
LEXICAL_ORDINALS = {
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
    "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth",
    "eighteenth", "nineteenth", "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth",
    "seventieth", "eightieth", "ninetieth", "hundredth", "thousandth"
}

# e.g., "twenty-first", "thirty-first"
COMPOUND_ORDINAL_WORDS = {
    "twenty-first", "twenty-second", "twenty-third", "twenty-fourth", "twenty-fifth",
    "twenty-sixth", "twenty-seventh", "twenty-eighth", "twenty-ninth",
    "thirty-first"
}

# Used in regex for ordinal matching (e.g., "twenty-first")
ORDINAL_SUFFIX_PATTERN = (
    "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    "eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|"
    "eighteenth|nineteenth|twentieth|thirtieth|thirty-first"
)

# Regex to capture hyphenated ordinal phrases like "twenty-third"
HYPHENATED_ORDINAL_RE = re.compile(
    rf"^(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
    rf"-(?:{ORDINAL_SUFFIX_PATTERN})$"
)

# Merge all ordinal expressions into a single reference set
ALL_ORDINALS = NUMERIC_ORDINALS | LEXICAL_ORDINALS | COMPOUND_ORDINAL_WORDS

# Optional toggle to skip correcting ordinals during token normalization
_SKIP_ORDINAL_CORRECTION = False

# Augment the canonical terms with ordinal forms unless configured to skip them
if not _SKIP_ORDINAL_CORRECTION:
    CANONICAL_TEMPORAL_TERMS.update(LEXICAL_ORDINALS)
    CANONICAL_TEMPORAL_TERMS.update(COMPOUND_ORDINAL_WORDS)
    CANONICAL_TEMPORAL_TERMS.update(NUMERIC_ORDINALS)
    CANONICAL_TEMPORAL_TERMS.update(ORDINAL_DATE_TERMS)    
   
# ────────────────────────────────────────────────────────────────────────────────
# STRING SIMILARITY FUNCTIONS
# Includes Levenshtein edit distance and Jaro-Winkler similarity.
# These are used for correcting misspelled tokens by measuring surface-form similarity.
# Levenshtein captures edit effort (insertions/deletions/substitutions),
# Jaro-Winkler captures transpositions and prefix similarity, often used for fuzzy matching.
# ────────────────────────────────────────────────────────────────────────────────

# Levenshtein Distance — character-level edit distance
#──────────────────────────────────────────────────────────────────────────────
class Levenshtein:
    """
    Classic Levenshtein edit distance implementation (a.k.a. minimum edit distance).

    This quantifies the difference between two strings by computing the minimum number
    of operations (insertion, deletion, substitution) needed to transform one into the other.
    
    Why this matters in NLP:
    - Useful for surface-level fuzzy matching (e.g. typo correction, OCR cleanup).
    - Doesn't assume any phonetic similarity — this is purely character-based.
    - Well-suited for token normalization pipelines where small typos are likely.
    
    Note:
    - Equal cost for all operations (1 per op).
    - No support for transpositions (that’s Damerau-Levenshtein).
    - Could be memoized if needed for speed in large vocab lookups.
    """	
    def __init__(self):
        # nothing to configure yet — keeping it clean for now
        pass

    def distance(self, a, b):
        # Standard DP formulation — this matrix will store edit distances
        # dp[i][j] = min edits to convert a[0:i] to b[0:j]
        # edit ops: insert, delete, substitute (equal weight)
        dp = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]

        # iterate through each character pair
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                # if the characters match, cost = 0, else penalize with cost = 1 (substitution)
                cost = 0 if a[i - 1] == b[j - 1] else 1

                # classic edit distance choices:
                # deletion (left), insertion (up), or substitution (diag)
                # this is basically modeling channel noise: what’s the cheapest path to align the sequences?
                dp[i][j] = min(
                    dp[i - 1][j] + 1,        # deletion → removing a char from `a`
                    dp[i][j - 1] + 1,        # insertion → adding a char to match `b`
                    dp[i - 1][j - 1] + cost  # substitution (or match)
                )

        # bottom-right corner = edit distance between full strings
        # useful for surface form similarity — doesn’t account for phonetics or transpositions
        return dp[-1][-1]


# Jaro-Winkler distance
#──────────────────────────────────────────────────────────────────────────────
class JaroWinkler:
    """
    Jaro-Winkler distance for fuzzy string similarity — optimized for prefix alignment.

    This metric is particularly useful in NLP tasks where:
    - Minor character transpositions are common (e.g. typos, OCR noise).
    - Prefixes are semantically more important (e.g. person names, cities).
    - Want a bounded similarity score between [0, 1], where 1 means exact match.

    Jaro handles the character match/transposition core.
    Winkler adds a bonus for shared leading characters — good for high-similarity cases.

    Often used in:
    - Entity resolution
    - Query correction
    - Fuzzy join pipelines
    - Lexical normalization

    Note: This does *not* consider phonetics — just character order and overlap.
    """	
    def __init__(self, scaling=0.1):
        # This scaling factor determines the strength of the Winkler prefix bonus.
        # Empirically, 0.1 performs well for most linguistic applications.
        # Increasing it favors strings with long common prefixes.
        self.scaling = scaling

    def jaro_distance(self, s1, s2):
        # Canonical Jaro similarity:
        # Balances matches, transpositions, and length to reward alignment of characters with slight disorder.

        if not s1 and not s2:
            return 1.0  # Both empty — perfect match (no information to differentiate)

        # Normalize casing for character-wise comparison
        s1 = s1.lower()
        s2 = s2.lower()

        if s1 == s2:
            return 1.0  # Exact match after normalization — identity mapping

        len1, len2 = len(s1), len(s2)

        # Jaro uses a window to define which characters are "close enough" to compare
        # It's half the length of the longer string (minus one) to ensure locality
        match_distance = (max(len1, len2) // 2) - 1
        if match_distance < 0:
            match_distance = 0  # Edge case for very short strings

        # Flags for tracking matched characters between s1 and s2
        s1_matches = [False] * len1
        s2_matches = [False] * len2

        matches = 0  # Number of matched characters
        transpositions = 0  # Characters in wrong order

        ### Match Phase
        # For each character in s1, search a window around the corresponding position in s2
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)

            for j in range(start, end):
                if s2_matches[j]:
                    continue  # Already matched this character
                if s1[i] == s2[j]:
                    # Found a match — mark and break
                    s1_matches[i] = True
                    s2_matches[j] = True
                    matches += 1
                    break

        if matches == 0:
            return 0.0  # No character-level overlap

        ### Transposition Phase
        # Now walk through the matches to count how many are out of order
        s2_match_index = 0
        for i in range(len1):
            if s1_matches[i]:
                while not s2_matches[s2_match_index]:
                    s2_match_index += 1
                if s1[i] != s2[s2_match_index]:
                    transpositions += 1
                s2_match_index += 1

        transpositions /= 2  # Each transposition involves two characters

        ### Final Similarity Score
        # Combines 3 ratios: match density in s1, match density in s2, and the transposition penalty
        return ((matches / len1) + (matches / len2) + ((matches - transpositions) / matches)) / 3.0

    def jaro_winkler_distance(self, s1, s2):
        # Extension of Jaro: adds a prefix bonus to favor strings with shared beginnings
        # Useful in name-matching, where prefixes often carry higher signal (e.g., "Jonathan" vs "Jonathon")

        jaro_dist = self.jaro_distance(s1, s2)  # Get base similarity

        ### Prefix Bonus Phase
        prefix_length = 0
        max_prefix = 4  # Winkler originally limits the prefix bonus to the first 4 characters

        # Count how many leading characters match (case-insensitive)
        for c1, c2 in zip(s1.lower(), s2.lower()):
            if c1 == c2:
                prefix_length += 1
            else:
                break
            if prefix_length == max_prefix:
                break  # Cut off prefix influence after 4 chars

        # Winkler bonus: the longer the prefix, the more weight added to the score (up to limit)
        # It's scaled by the remaining distance-to-1 (so it only matters when the match is already decent)
        winkler_bonus = prefix_length * self.scaling * (1.0 - jaro_dist)

        return jaro_dist + winkler_bonus  # Final similarity score [0.0 → 1.0]


# ────────────────────────────────────────────────────────────────────────────────
# FUZZY MATCHING INTERFACE
# LexicalFuzzyMatcher provides a unified interface for surface-form correction.
# It applies string similarity techniques (Levenshtein + Jaro-Winkler) to detect
# and correct misspelled or malformed tokens based on a defined vocabulary.
# Optionally skips ordinal corrections to preserve cardinal/ordinal semantics.
# ────────────────────────────────────────────────────────────────────────────────
class LexicalFuzzyMatcher:
    def __init__(
        self,
        vocabulary,
        ignore_ordinals=_SKIP_ORDINAL_CORRECTION,
        ignore_numerals=True,
        levenshtein_threshold=1,
        jaro_winkler_threshold=0.88,
        jaro_winkler_scaling=0.1
    ):
        # Initialize with a predefined vocabulary — ideally all known temporal terms.
        self.vocabulary = set(vocabulary) if isinstance(vocabulary, list) else vocabulary

        # Whether to skip correcting ordinal expressions.
        self.ignore_ordinals = ignore_ordinals
        self.ignore_numerals = ignore_numerals        

        # Max edit distance allowed for Levenshtein-based correction.
        self.levenshtein_threshold = levenshtein_threshold

        # Minimum similarity score required for Jaro-Winkler to consider a candidate a match.
        self.jaro_winkler_threshold = jaro_winkler_threshold

        # Instantiate similarity metric objects. These are stateless utilities we’ll use per token.
        self.lev = Levenshtein()
        self.jw = JaroWinkler(scaling=jaro_winkler_scaling)

        # Store the default configuration for later resetting.
        self._default_config = {
            "vocabulary": vocabulary,
            "ignore_ordinals": ignore_ordinals,
            "ignore_numerals": ignore_numerals,
            "levenshtein_threshold": levenshtein_threshold,
            "jaro_winkler_threshold": jaro_winkler_threshold,
            "jaro_winkler_scaling": jaro_winkler_scaling,
        }

    # Settings
    # ─────────────────────────────────────
    def configure(
        self,
        vocabulary=None,
        ignore_ordinals=None,
        ignore_numerals=None,
        levenshtein_threshold=None,
        jaro_winkler_threshold=None,
        jaro_winkler_scaling=None
    ):
        """
        Dynamically updates the configuration of the LexicalFuzzyMatcher instance.

        This method allows runtime adjustments of matching behavior by selectively
        overriding internal parameters without reinstantiating the matcher. Useful 
        for fine-tuning fuzzy matching sensitivity or switching vocabularies on the fly.

        Only parameters explicitly provided will be changed; others will retain 
        their current values.

        Args:
            vocabulary (set[str], optional): The updated vocabulary set to match against.
            ignore_ordinals (bool, optional): Whether to skip fuzzy-matching known ordinal expressions.
            ignore_numerals (bool, optional): Whether to skip bare numeral correction (e.g., "1", "42").
            levenshtein_threshold (int, optional): Maximum allowed Levenshtein edit distance.
            jaro_winkler_threshold (float, optional): Minimum similarity score for accepting a Jaro-Winkler match.
            jaro_winkler_scaling (float, optional): Scaling factor for Jaro-Winkler prefix bonus (typically 0.1).
        """
        if vocabulary is not None:
            self.vocabulary = set(vocabulary) if isinstance(vocabulary, list) else vocabulary
        if ignore_ordinals is not None:
            self.ignore_ordinals = ignore_ordinals
        if ignore_numerals is not None:
            self.ignore_numerals = ignore_numerals
        if levenshtein_threshold is not None:
            self.levenshtein_threshold = levenshtein_threshold
        if jaro_winkler_threshold is not None:
            self.jaro_winkler_threshold = jaro_winkler_threshold
        if jaro_winkler_scaling is not None:
            self.jaro_winkler_scaling = jaro_winkler_scaling
            # Also update the scaling factor in the JaroWinkler instance
            self.jw.scaling = jaro_winkler_scaling

    def reset_configuration(self):
        """
        Restores the LexicalFuzzyMatcher's configuration to its original default values.

        This is useful for reverting any customizations made via `configure()` 
        and returning the matcher to a clean, stable state — especially during 
        iterative experimentation or when reusing the matcher across contexts.

        All tunable attributes including vocabulary, thresholds, and ignore flags 
        are restored to their original values defined at initialization.
        """
        defaults = self._default_config
        self.vocabulary = defaults["vocabulary"]
        self.ignore_ordinals = defaults["ignore_ordinals"]
        self.ignore_numerals = defaults["ignore_numerals"]
        self.levenshtein_threshold = defaults["levenshtein_threshold"]
        self.jaro_winkler_threshold = defaults["jaro_winkler_threshold"]
        self.jaro_winkler_scaling = defaults["jaro_winkler_scaling"]
        self.jw.scaling = defaults["jaro_winkler_scaling"]
        
    # Algorithm Helpers
    # ─────────────────────────────────────        
    # def _levenshtein(self, token, vocabulary=None):
    #     token = token.lower()
    #     vocab = vocabulary if vocabulary is not None else self.vocabulary         
    # 
    #     # Skip correction if ordinals are off and the token *is* one
    #     if self.ignore_ordinals and token in ALL_ORDINALS:
    #         return token
    # 
    #     # Skip bare numerals
    #     if self.ignore_numerals and _is_cardinal(token):
    #         return token
    #        
    #     # Already valid? Return as-is
    #     if token in vocab:
    #         return token
    # 
    #     # Compute Levenshtein distance to all known words and pick the closest match
    #     closest = min(vocab, key=lambda w: self.lev.distance(token, w))
    #     if self.lev.distance(token, closest) <= self.levenshtein_threshold:
    #         return closest  # Accept if below threshold
    #     return token  # Otherwise, don’t force a match

    # def _jaro_winkler(self, token, vocabulary=None):
    #     token = token.lower()
    #     vocab = vocabulary if vocabulary is not None else self.vocabulary         
    #     
    #     # Skip correction if ordinals are off and the token *is* one        
    #     if self.ignore_ordinals and token in ALL_ORDINALS:
    #         return token
    #        
    #     # Skip bare numerals
    #     if self.ignore_numerals and _is_cardinal(token):
    #         return token  
    #        
    #     # Already valid? Return as-is           
    #     if token in vocab:
    #         return token
    #        
    #     best_match = None
    #     best_score = 0
    #     # Iterate through known words, scoring each by similarity
    #     for word in vocab:
    #         score = self.jw.jaro_winkler_distance(token, word)
    #         if score > best_score:
    #             best_score = score
    #             best_match = word
    #     # If best score is above threshold, return it — otherwise no match.
    #     return best_match if best_score >= self.jaro_winkler_threshold else token

    def _levenshtein(self, token, vocabulary=None):
        token = token.lower()
        vocab = vocabulary if vocabulary is not None else self.vocabulary         

        # Skip correction if ordinals are off and the token *is* one
        if self.ignore_ordinals and token in ALL_ORDINALS:
            return token

        # Skip bare numerals
        if self.ignore_numerals and _is_cardinal(token):
            return token
        
        # Set
        #-----------------------------------------
        # Already valid? Return as-is  
        if isinstance(vocab, set):                           
            if token in vocab:
                return token

            # Compute Levenshtein distance to all known words and pick the closest match
            closest = min(vocab, key=lambda w: self.lev.distance(token, w))
            if self.lev.distance(token, closest) <= self.levenshtein_threshold:
                return closest  # Accept if below threshold
            return token  # Otherwise, don’t force a match

        # Dict
        # -----------------------------------------
        # Already valid? Return as-is  
        elif isinstance(vocab, dict):
            # Already valid? Return mapped value
            if token in vocab:
                return vocab[token]

            # Compute Levenshtein distance against keys
            closest = min(vocab.keys(), key=lambda w: self.lev.distance(token, w))
            if self.lev.distance(token, closest) <= self.levenshtein_threshold:
                return vocab[closest]  # Return canonical form
            return token  # Otherwise, don’t force a match
           
    def _jaro_winkler(self, token, vocabulary=None):
        token = token.lower()
        vocab = vocabulary if vocabulary is not None else self.vocabulary         

        # Skip correction if ordinals are off and the token *is* one        
        if self.ignore_ordinals and token in ALL_ORDINALS:
            return token
           
        # Skip bare numerals
        if self.ignore_numerals and _is_cardinal(token):
            return token    

        # Set
        #-----------------------------------------
        # Already valid? Return as-is  
        if isinstance(vocab, set):                           
            if token in vocab:
                return token

            best_match = None
            best_score = 0
            # Iterate through known words, scoring each by similarity
            for word in vocab:
                score = self.jw.jaro_winkler_distance(token, word)
                if score > best_score:
                    best_score = score
                    best_match = word
            # If best score is above threshold, return it — otherwise no match.
            return best_match if best_score >= self.jaro_winkler_threshold else token

        # Dict
        #-----------------------------------------
        # Already valid? Return as-is  
        elif isinstance(vocab, dict):                   
            if token in vocab:
                return vocab[token]
        
            best_match = None
            best_score = 0
            # Iterate through known words, scoring each by similarity
            for word in vocab.keys():
                score = self.jw.jaro_winkler_distance(token, word)
                if score > best_score:
                    best_score = score
                    best_match = word
            # If best score is above threshold, return it — otherwise no match.
            return best_match if best_score >= self.jaro_winkler_threshold else token


    # def match_token(self, token, vocabulary=None):
    #     # Combine both metrics into a hybrid strategy.
    #     # First try Levenshtein — precise, character-edit-based
    #     # Then fall back on Jaro-Winkler — broader, prefix-weighted phonetic similarity
    #     token = token.lower()
    #     vocab = vocabulary if vocabulary is not None else self.vocabulary
    # 
    #     # Skip correction if ordinals are off and the token *is* one
    #     if self.ignore_ordinals and token in ALL_ORDINALS:
    #         return token
    #        
    #     # Skip bare numerals
    #     if self.ignore_numerals and _is_cardinal(token):
    #         return token      
    # 
    #     # First: try Levenshtein match
    #     closest_lev = min(vocab, key=lambda w: self.lev.distance(token, w))
    #     if self.lev.distance(token, closest_lev) <= self.levenshtein_threshold:
    #         return closest_lev
    # 
    #     # Second: fallback to Jaro-Winkler
    #     best_match = None
    #     best_score = 0
    #     for word in vocab:
    #         score = self.jw.jaro_winkler_distance(token, word)
    #         if score > best_score:
    #             best_score = score
    #             best_match = word
    # 
    #     return best_match if best_score >= self.jaro_winkler_threshold else token
    
    def match_token(self, token, vocabulary=None):
        # Combine both metrics into a hybrid strategy.
        # First try Levenshtein — precise, character-edit-based
        # Then fall back on Jaro-Winkler — broader, prefix-weighted phonetic similarity
        token = token.lower()
        vocab = vocabulary if vocabulary is not None else self.vocabulary

        # Skip correction if ordinals are off and the token *is* one
        if self.ignore_ordinals and token in ALL_ORDINALS:
            return token
           
        # Skip bare numerals
        if self.ignore_numerals and _is_cardinal(token):
            return token      

        # Set
        #-----------------------------------------
        # Already valid? Return as-is 
        if isinstance(vocab, set):
            if token in vocab:
                return token

            # Levenshtein phase
            closest_lev = min(vocab, key=lambda w: self.lev.distance(token, w))
            if self.lev.distance(token, closest_lev) <= self.levenshtein_threshold:
                return closest_lev

            # Jaro-Winkler fallback
            best_match = None
            best_score = 0
            for word in vocab:
                score = self.jw.jaro_winkler_distance(token, word)
                if score > best_score:
                    best_score = score
                    best_match = word
            return best_match if best_score >= self.jaro_winkler_threshold else token

        # Dict
        #-----------------------------------------
        # Already valid? Return as-is  
        elif isinstance(vocab, dict):
            if token in vocab:
                return vocab[token]

            # Levenshtein phase
            closest_lev = min(vocab.keys(), key=lambda w: self.lev.distance(token, w))
            if self.lev.distance(token, closest_lev) <= self.levenshtein_threshold:
                return vocab[closest_lev]

            # Jaro-Winkler fallback
            best_match = None
            best_score = 0
            for word in vocab.keys():
                score = self.jw.jaro_winkler_distance(token, word)
                if score > best_score:
                    best_score = score
                    best_match = word
            return vocab[best_match] if best_score >= self.jaro_winkler_threshold else token
           

    # Fuzzy Logic
    # ─────────────────────────────────────
    def levenshtein_correction(self, phrase):
        """Applies Levenshtein correction to each token. Good for literal typos."""
        pattern = r"\w+"
        if not self.ignore_ordinals:
            # Normalize compound ordinals (e.g., “twenty three” → “twenty-three”)
            phrase = _hyphenate_word_numbers(phrase)
            pattern = r"\w+(?:-\w+)*" # Allow hyphenated forms
        raw_tokens = re.findall(pattern, phrase.lower()) # Tokenize words
        return [self._levenshtein(tok) for tok in raw_tokens]

    def jaro_winkler_correction(self, phrase):
        """Applies Jaro-Winkler correction to each token. Better for phonetic similarity."""
        pattern = r"\w+"
        if not self.ignore_ordinals:
            # Normalize compound ordinals
            phrase = _hyphenate_word_numbers(phrase)
            pattern = r"\w+(?:-\w+)*" # Allow hyphenated forms
        raw_tokens = re.findall(pattern, phrase.lower()) # Tokenize words
        return [self._jaro_winkler(tok) for tok in raw_tokens]

    def hybrid_correction(self, phrase):
        # One-stop shop: cleans a phrase and runs both fuzzy matchers on each token.
        # Think of this as a safety net for noisy user input.
        pattern = r"\w+"
        if not self.ignore_ordinals:
            # Normalize compound ordinals
            phrase = _hyphenate_word_numbers(phrase)
            pattern = r"\w+(?:-\w+)*" # Allow hyphenated forms
        raw_tokens = re.findall(pattern, phrase.lower()) # Tokenize words
        return [self.match_token(tok) for tok in raw_tokens]

    def __dir__(self):
        default_attrs = [f for f in super().__dir__() if f.startswith("__") and f.endswith("__")]
        public_attrs = ['hybrid_correction', 'levenshtein_correction', 'jaro_winkler_correction', 'vocabulary', 'configure', 'reset_configuration', 'match_token']
        return sorted(set(default_attrs + public_attrs)) 



# Instantiate the LexicalFuzzyMatcher that will act as our main fuzzy-correction engine.
# This is our front-line filter for cleaning up user-provided temporal phrases.
LexicalFuzzer = LexicalFuzzyMatcher(
    vocabulary=CANONICAL_TEMPORAL_TERMS,             # Canonical lexicon of valid temporal terms (months, days, seasons, ordinals, etc.)
    ignore_ordinals=_SKIP_ORDINAL_CORRECTION,   		 # Whether to skip fuzzy-matching ordinals (we usually want to keep these untouched).
    ignore_numerals=True,                            # Whether to skip correction for bare numerals (e.g., "1", "30", "2023") — valid as-is.
    levenshtein_threshold=1,                         # Allow a max edit distance of 1 — tight bound, good for simple typos like "dy" → "day".
    jaro_winkler_threshold=0.88,                     # Require a high phonetic similarity to trigger Jaro-Winkler correction (0.88+ is conservative).
    jaro_winkler_scaling=0.1                         # Standard Winkler bonus scaling — gives a boost to prefix matches (e.g. “feburary” → “february”).
)






__all__ = ["LexicalFuzzer"]
