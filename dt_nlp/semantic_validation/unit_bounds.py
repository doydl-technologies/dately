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
──────────────────────────────────────────────
This module enforces **semantic bounds** on ordinal containment structures within
temporal expressions. It defines numeric constraints for common containment
relationships (e.g., "5th Friday of a month" is valid; "55th day of a week" is not).
It supplements syntactic structure validation by evaluating numeric realism.

Role in the NLP Pipeline:
──────────────────────────────────────────────
Once a phrase has been classified and structurally validated (via syntactic rules),
this module serves as a **secondary validation layer** to ensure the expression is
semantically plausible. For example, a structure may be syntactically valid
but refer to an impossible unit position — this module flags such issues.

Core Focus:
──────────────────────────────────────────────
- Define a comprehensive dictionary of max allowed values for temporal units
- Evaluate whether an ordinal falls within realistic bounds for its container
- Normalize unit types using shared mappings from core temporal logic
- Provide developer-friendly reasons for why a phrase passed or failed

Note:
──────────────────────────────────────────────
This module is only triggered for containment or compound structures involving
**ordinal indexing** (e.g., "3rd Monday", "55th day"). It assumes structural
validation has already succeeded, and is designed for **post-syntactic enforcement**
within the semantic_validation layer.
"""
# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ..arithmetic import numbers
from ..temporal_preprocessing import PhraseEngine
from ..temporal_core.temporal_units import normalize_named_unit


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
unitContextMaxBounds = {
    # Core units
    ('day', 'week'): 7,
    ('weekday', 'week'): 5,
    ('weekend', 'week'): 2,
    ('day', 'month'): 31,
    ('day', 'year'): 366,
    ('weekday', 'month'): 23,
    ('weekday', 'year'): 262,
    ('week', 'month'): 5,
    ('week', 'year'): 53,
    ('month', 'year'): 12,
    ('quarter', 'year'): 4,
    ('season', 'year'): 4,
    ('day', 'quarter'): 92,
    ('day', 'season'): 92,
    ('weekday', 'quarter'): 66,
    ('weekday', 'season'): 66,
    ('week', 'quarter'): 14,
    ('week', 'season'): 14,
    ('month', 'quarter'): 3,
    ('month', 'season'): 3,

    # Specific months — leap-safe
    ('day', 'january'): 31,
    ('day', 'february'): 29,
    ('day', 'march'): 31,
    ('day', 'april'): 30,
    ('day', 'may'): 31,
    ('day', 'june'): 30,
    ('day', 'july'): 31,
    ('day', 'august'): 31,
    ('day', 'september'): 30,
    ('day', 'october'): 31,
    ('day', 'november'): 30,
    ('day', 'december'): 31,
    ('day', 'jan'): 31,
    ('day', 'feb'): 29,
    ('day', 'mar'): 31,
    ('day', 'apr'): 30,
    ('day', 'may'): 31,
    ('day', 'jun'): 30,
    ('day', 'jul'): 31,
    ('day', 'aug'): 31,
    ('day', 'sep'): 30,
    ('day', 'oct'): 31,
    ('day', 'nov'): 30,
    ('day', 'dec'): 31,

    # Optional: quarters as containers for months or weeks
    ('month', 'q1'): 3,
    ('month', 'q2'): 3,
    ('month', 'q3'): 3,
    ('month', 'q4'): 3,
    ('week', 'q1'): 14,
    ('week', 'q2'): 14,
    ('week', 'q3'): 14,
    ('week', 'q4'): 14,
    ('weekday', 'q1'): 66,
    ('weekday', 'q2'): 66,
    ('weekday', 'q3'): 66,
    ('weekday', 'q4'): 66,
    ('day', 'q1'): 92,
    ('day', 'q2'): 92,
    ('day', 'q3'): 92,
    ('day', 'q4'): 92,

    # Optional: seasons as containers for months
    ('month', 'spring'): 3,
    ('month', 'summer'): 3,
    ('month', 'fall'): 3,
    ('month', 'autumn'): 3,
    ('month', 'winter'): 3,

    # Weekday of month
    ('monday', 'month'): 5,
    ('tuesday', 'month'): 5,
    ('wednesday', 'month'): 5,
    ('thursday', 'month'): 5,
    ('friday', 'month'): 5,
    ('saturday', 'month'): 5,
    ('sunday', 'month'): 5,

    # Weekday of quarter
    ('monday', 'quarter'): 14,
    ('tuesday', 'quarter'): 14,
    ('wednesday', 'quarter'): 14,
    ('thursday', 'quarter'): 14,
    ('friday', 'quarter'): 14,
    ('saturday', 'quarter'): 14,
    ('sunday', 'quarter'): 14,

    # Weekday of season (same as quarter)
    ('monday', 'season'): 14,
    ('tuesday', 'season'): 14,
    ('wednesday', 'season'): 14,
    ('thursday', 'season'): 14,
    ('friday', 'season'): 14,
    ('saturday', 'season'): 14,
    ('sunday', 'season'): 14,

    # Weekday of year (based on max 53 weeks)
    ('monday', 'year'): 53,
    ('tuesday', 'year'): 53,
    ('wednesday', 'year'): 53,
    ('thursday', 'year'): 53,
    ('friday', 'year'): 53,
    ('saturday', 'year'): 53,
    ('sunday', 'year'): 53,

    # Weekday of month
    ('mon', 'month'): 5,
    ('tue', 'month'): 5,
    ('wed', 'month'): 5,
    ('thu', 'month'): 5,
    ('fri', 'month'): 5,
    ('sat', 'month'): 5,
    ('sun', 'month'): 5,

    # Weekday of quarter
    ('mon', 'quarter'): 14,
    ('tue', 'quarter'): 14,
    ('wed', 'quarter'): 14,
    ('thu', 'quarter'): 14,
    ('fri', 'quarter'): 14,
    ('sat', 'quarter'): 14,
    ('sun', 'quarter'): 14,

    # Weekday of season (same as quarter)
    ('mon', 'season'): 14,
    ('tue', 'season'): 14,
    ('wed', 'season'): 14,
    ('thu', 'season'): 14,
    ('fri', 'season'): 14,
    ('sat', 'season'): 14,
    ('sun', 'season'): 14,

    # Weekday of year (based on max 53 weeks)
    ('mon', 'year'): 53,
    ('tue', 'year'): 53,
    ('wed', 'year'): 53,
    ('thu', 'year'): 53,
    ('fri', 'year'): 53,
    ('sat', 'year'): 53,
    ('sun', 'year'): 53,

    # Days in a weekend
    ('day', 'weekend'): 2,
    ('weekday', 'weekend'): 0,  # Explicitly disallowed for clarity
}

rangeContextMaxBounds = {
    # days
    ("day",  "week"):    7,
    ("day",  "month"):   31,
    ("day",  "quarter"): 92,
    ("day",  "year"):    366,

    # weeks
    ("week", "month"):   5,
    ("week", "quarter"): 14,
    ("week", "year"):    53,

    # months
    ("month", "quarter"): 3,
    ("month", "season"):  3,
    ("month", "year"):    12,

    # quarters
    ("quarter", "year"): 4,
}

FILLER_WORDS = {"this", "the"}
DIRECTIONAL = {"last", "next"}


def extract_ordinal(token):
    """Return 55 for '55th', 3 for 'third', else None."""
    try:
        if numbers.num_type(token) == "ordinalNumber":
            return int(numbers.to_type(token, "cardinalNumber"))
    except Exception:
        pass
    return None

def extract_cardinal(token):
    """
    Returns 8 for '8', 'eight'; 3 for 'three', else None.
    """
    try:
        if numbers.num_type(token) in {"cardinalNumber", "cardinalWord"}:
            return int(numbers.to_type(token, "cardinalNumber"))
    except Exception:
        pass
    return None


def is_within_unit_bounds(contained_unit, container_unit, ordinal):
    """
    Checks if an ordinal index (e.g. '55th') is valid for the given containment pair.
    """
    key = (contained_unit.lower(), container_unit.lower())
    max_allowed = unitContextMaxBounds.get(key)

    if max_allowed is None:
        return True, "No upper bound defined for this unit pair"

    if ordinal <= max_allowed:
        return True, f"{ordinal} is within bounds for {contained_unit} of {container_unit} (max {max_allowed})"
    else:
        return False, f"{ordinal} exceeds max bound for {contained_unit} of {container_unit} (max {max_allowed})"


def validate_bounds(structure_result, original_tokens):
    """
    Inspect a structure‑validator result and decide whether the phrase
    violates any numeric bounds. Returns (is_ok, reason).
    """
    if structure_result["structure"] not in {"containment", "compound"}:
        return True, "Bound check skipped — structure does not involve ordinal containment"

    parts = structure_result.get("parts", {})
    contained  = parts.get("contained")
    container  = parts.get("anchor")  # anchor == container in compound output
    ordinal_val = extract_ordinal(original_tokens[0]) if original_tokens else None

    # If no ordinal present (e.g., 'day of april'), nothing to bound‑check.
    if ordinal_val is None:
        return True, "No ordinal index detected — bounds check not applicable"

    # # Normalize units to base keys.
    # try:
    #     contained_unit = normalize_named_unit(contained)
    #     container_unit = normalize_named_unit(container)
    # except Exception as e:
    #     return False, f"Normalization error: {e}"

    # Normalise units to base keys.
    try:
        # 1) Handle partial‑date containers
        if PhraseEngine.is_partial_date([container], include_year=True, return_val=False):
            parts = PhraseEngine.is_partial_date([container], include_year=True, return_val=True)
            container_unit = "day" if parts.get("day") else "month"
        else:
            container_unit = normalize_named_unit(container)
        contained_unit = normalize_named_unit(contained)
    except Exception as e:
        return False, f"Normalization error: {e}"

    is_ok, reason = is_within_unit_bounds(contained_unit, container_unit, ordinal_val)
    return is_ok, reason

def validate_range_bounds(tokens):
    """
    Validate expressions like
      "last 8 weeks of month",
      "next 3 days this quarter",
      "last 8 week month"
    Returns (ok: bool, reason: str).
    """
    t = [x.lower() for x in tokens]

    # Must start with a directional modifier + cardinal
    if len(t) < 3 or t[0] not in DIRECTIONAL:
        return True, "Not a directional span expression"

    # Extract the numeric count
    try:
        count = int(numbers.to_type(t[1], "cardinalNumber"))
    except Exception:
        return True, "No cardinal span detected"

    # Next token is the span-unit (e.g. "week" or "weeks")
    raw_unit = t[2]
    try:
        span_unit = normalize_named_unit(raw_unit)
    except ValueError:
        return True, "Cannot normalize span unit"

    # Find the container token:
    #   - If there's an "of", skip past it and any fillers;
    #   - Else, assume the last token is the container (skip fillers).
    if "of" in t:
        idx = t.index("of") + 1
    else:
        # Everything after the span-unit is potential container/fillers
        idx = 3

    # Skip over any filler words
    while idx < len(t) and t[idx] in FILLER_WORDS:
        idx += 1

    if idx >= len(t):
        return True, "No container found for range expression"

    try:
        container_unit = normalize_named_unit(t[idx])
    except ValueError:
        return True, "Cannot normalize container unit"

    # Finally, look up the bound
    max_allowed = rangeContextMaxBounds.get((span_unit, container_unit))
    if max_allowed is None:
        return True, "No max span defined for this unit pair"

    if count <= max_allowed:
        return True, f"{count} is within bounds for {span_unit}s of {container_unit} (max {max_allowed})"
    else:
        return False, f"{count} exceeds max span for {span_unit}s of {container_unit} (max {max_allowed})"
