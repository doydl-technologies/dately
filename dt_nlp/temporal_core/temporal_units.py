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
This module defines the centralized registry for all named temporal units
and provides core utilities for normalization, ranking, and preprocessing.
It converts raw tokens (e.g. '4th', 'March', 'Q2') into standardized base units
(e.g. 'day', 'month', 'quarter') that support structural and semantic analysis
downstream in the NLP pipeline.

Role in the NLP Pipeline:
────────────────────────────────────────────────────
This module underpins all structural and semantic operations by offering
consistent unit mapping, ordinal normalization, and grammatical interpretation.
It is used by syntactic structure classifiers, semantic validators, and
temporal interpreters to ensure internal consistency across time-related logic.

Core Focus:
────────────────────────────────────────────────────
- Normalize raw tokens into canonical base units
- Maintain hierarchical relationships between units (via rank system)
- Provide utilities to infer or preprocess temporal phrases (e.g., remove 'this')
- Act as a shared dependency across containment, anchoring, intersection, and bounds validation

Note:
────────────────────────────────────────────────────
This module is infrastructure-level. It performs no classification or scoring.
It only enables higher-level logic through normalization, mapping, and rank control.
"""
import re

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ..arithmetic import numbers, timeline
from ..temporal_preprocessing import PhraseEngine



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

# Dictionary for all literal → unit mappings
named_units = {
    # days of week
    "monday":    ("day_of_week", 1),
    "tuesday":   ("day_of_week", 2),
    "wednesday": ("day_of_week", 3),
    "thursday":  ("day_of_week", 4),
    "friday":    ("day_of_week", 5),
    "saturday":  ("day_of_week", 6),
    "sunday":    ("day_of_week", 7),

    "mon":    ("day_of_week", 1),
    "tue":    ("day_of_week", 2),
    "wed":    ("day_of_week", 3),
    "thu":    ("day_of_week", 4),
    "fri":    ("day_of_week", 5),
    "sat":    ("day_of_week", 6),
    "sun":    ("day_of_week", 7),
    
    "weekend": ("day_range", None),
    # "week end": ("day_range", None),    
    
    # months
    "january":   ("month", 1),
    "february":  ("month", 2),
    "march":     ("month", 3),
    "april":     ("month", 4),
    "may":       ("month", 5),
    "june":      ("month", 6),
    "july":      ("month", 7),
    "august":    ("month", 8),
    "september": ("month", 9),
    "october":   ("month", 10),
    "november":  ("month", 11),
    "december":  ("month", 12),

    "jan":   ("month", 1),
    "feb":   ("month", 2),
    "mar":   ("month", 3),
    "apr":   ("month", 4),
    "may":   ("month", 5),
    "jun":   ("month", 6),
    "jul":   ("month", 7),
    "aug":   ("month", 8),
    "sep":   ("month", 9),
    "oct":   ("month", 10),
    "nov":   ("month", 11),
    "dec":   ("month", 12),

    # quarters
    "q1": ("quarter", 1),
    "q2": ("quarter", 2),
    "q3": ("quarter", 3),
    "q4": ("quarter", 4),

    # seasons (northern hemisphere standard)
    "spring": ("season", 1),
    "summer": ("season", 2),
    "fall":   ("season", 3),
    "autumn": ("season", 3),  # synonym for fall
    "winter": ("season", 4),
}

# Days of Month (auto-generated)
for i in range(1, 32):
    cardinal = str(i)
    ordinal = numbers.to_type(i, 'ordinalNumber', as_str=True)
    named_units[cardinal] = ("day_of_month", i)
    named_units[ordinal] = ("day_of_month", i)
    
named_units.update({
    **{str(i): ("day_of_month", i) for i in range(1, 32)},
    **{numbers.to_type(i, 'ordinalNumber', as_str=True): ("day_of_month", i) for i in range(1, 32)},
    **{f"month {i}": ("month", i) for i in range(1, 13)},
    **{numbers.to_type(i, 'ordinalNumber', as_str=True) + " month": ("month", i) for i in range(1, 13)},
    **{str(i): ("month", i) for i in range(1, 13) if str(i) not in named_units}
})

# Collapse all fine-grained types to core units (day, week, month, quarter, year).
base_unit_map = {
    "day_of_month":  "day",
    "day_of_week":   "day",
    "week_of_month": "week",
    "week_of_year":  "week",
    "month":         "month",
    "quarter":       "quarter",
    "season":        "quarter",   # treat season like a “quarter”
    "half_year":     "year",      # treat half‐year as same level as year
    "year":          "year",
    "day_range":		 "day",    
}

# Containment and hierarchy checking i.e. smaller → larger
global_rank = {
    "day":     1,
    "week":    2,
    "month":   3,
    "quarter": 4,
    "year":    5,
}

base_temporal_units = {"day", "week", "month", "quarter", "year"}

_unit_map = {
    "day": "day", "days": "day",
    "week": "week", "weeks": "week",
    "month": "month", "months": "month",
    "quarter": "quarter", "quarters": "quarter",
    "year": "year", "years": "year",
    "weekend": "day",    
}

def _norm_ordinals(token):
    """
    Converts embedded ordinal strings like '4th' or 'twentieth' into cardinals.
    Preserves punctuation/delimiters.
    """
    token = " ".join(token.split()) # normalize whitespace
    parts = re.split(r'(\W+)', token) # Split the text while preserving delimiters
    for index, w in enumerate(parts):
        if numbers.num_type(w) == 'ordinalNumber':
            parts[index] = numbers.to_type(w, 'cardinalNumber', as_str=True)
    return ''.join(parts) # Join everything back together


def normalize_named_unit(token):
    """
    Normalize a named time token to one of the five base units:
    "day", "week", "month", "quarter", "year".

    Handles:
    - Ordinals (e.g. "4th" → "4")
    - Named tokens ("march", "q2", "monday")
    - Mapped types (e.g. "day_of_week" → "day")

    Raises:
        ValueError if token is not recognized as temporal.
    """
    t = token.strip().lower()
    t = _norm_ordinals(t)

    # NEW: Handle partial dates like 'april 2025'
    if PhraseEngine.is_partial_date([t], include_year=True, return_val=False):
        parts = PhraseEngine.is_partial_date([t], include_year=True, return_val=True)
        return "day" if parts.get("day") else "month"

    # Try to match against known named units
    if t in named_units:
        unit_key, _ = named_units[t]
        return base_unit_map.get(unit_key, unit_key)

    # As fallback, if already a base unit
    if t in base_unit_map.values():
        return t

    raise ValueError(f"Unknown temporal token: {token!r}")
   
   
def is_valid_containment_with_partial(container_tokens):
    if PhraseEngine.is_partial_date(container_tokens, include_year=True):
        # Accept this as a container — valid containment
        return True
    else:
        # Must be a broader unit like 'month', 'year', etc.
        normalized = normalize_named_unit(container_tokens[-1])
        return normalized in {"month", "quarter", "year"}
   
def remove_unnecessary_this(tokens):
    """
    Remove the word "this" when it precedes a named temporal unit
    (e.g., "this March" → "March"), but only when it is safe to do so.

    This is used to avoid over-anchoring during structural analysis,
    particularly in containment phrases that are not anchored by intention.

    Args:
        tokens (list of str): A list of tokenized temporal words.

    Returns:
        list of str: A filtered list of tokens with unnecessary "this" removed
                     before named units like months, days of the week, or quarters.
    """
    NAMED_UNITS = set((
        # [unit for unit in sorted({unit for unit in timeline.time_units if unit != "half"}.union({"weekend"}))] +
        [unit for unit in [str(f) for f in list(timeline.days) if f not in ["day", "days"] and not str(f).isdigit()]] +
        [unit for unit in [f for f in list(timeline.months)]] +
        # [unit for unit in list(set(timeline.seasons.list))] +
        timeline.quarters.list
    ))

    output = []
    i = 0
    while i < len(tokens):
        if tokens[i].lower() == "this" and i + 1 < len(tokens):
            next_word = tokens[i + 1].lower()
            if next_word in NAMED_UNITS:
                # Skip "this" (do not append it)
                i += 1  # Move to next token (the named unit)
                continue  # We'll append the next one below
        output.append(tokens[i])
        i += 1

    return output

def insert_prepositions(tokens):
    """
    Insert the preposition "of" where appropriate:
      1. If the first token is a positional descriptor
         (e.g. "start", "middle", "end"), insert "of" right after it.
      2. If there are at least two tokens recognized as "basic" units
         (including partial dates), then insert "of" immediately after the first basic token,
         unless the token immediately following is "starting".
      3. Preserve fixed phrases (like "starting from") as blocks.
    """
    # Helper to decide if a token is a basic time unit.
    def _is_basic_token(token):
        t = token.lower()
        # 1) Any literal in named_units counts as a basic unit
        if t in named_units:
            return True
        # 2) Any broad base unit (day, week, month, quarter, year)
        if t in set(base_unit_map.values()):
            return True
        # 3) Partial dates also count
        try:
            return PhraseEngine.is_partial_date([token], include_year=True, return_val=False)
        except Exception:
            return False

    # If "of" is already there, do nothing
    if any(tok.lower() == "of" for tok in tokens):
        return tokens[:]

    # Step 1: Preserve fixed phrases like "starting from"
    result = []
    i = 0
    while i < len(tokens):
        if tokens[i].lower() == "starting" and i+1 < len(tokens) and tokens[i+1].lower() == "from":
            result.extend(tokens[i:i+2])
            i += 2
        else:
            result.append(tokens[i])
            i += 1
    tokens = result

    # Pattern 1: Positional descriptors
    pos = {"start", "middle", "end"}
    if tokens and tokens[0].lower() in pos and (len(tokens) == 1 or tokens[1].lower() != "of"):
        return [tokens[0], "of"] + tokens[1:]

    # Pattern 2: Insert "of" between two basic tokens
    basic_idxs = [i for i,t in enumerate(tokens) if _is_basic_token(t)]
    if len(basic_idxs) >= 2:
        idx = basic_idxs[0]
        # only insert if not "of" or start of a fixed phrase already
        if idx+1 < len(tokens) and tokens[idx+1].lower() not in {"of", "starting"}:
            return tokens[:idx+1] + ["of"] + tokens[idx+1:]
    return tokens
   
