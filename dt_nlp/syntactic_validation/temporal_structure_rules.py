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
This module performs syntactic-level analysis and validation of temporal
expressions, covering five primary structural types: containment, anchoring,
intersection, compound, and relative. It identifies structural patterns,
enforces grammatical constraints, and validates hierarchical relationships
between temporal units based on rank, modifiers, and phrase logic.

Role in the NLP Pipeline:
──────────────────────────────────────────────
This module serves as the first pass in temporal expression analysis.
It classifies input phrases structurally before passing them to deeper layers
such as semantic interpretation, resolution, or execution. Its output helps
determine whether a temporal phrase is structurally valid and what type
of structural behavior it encodes.

Core Focus:
──────────────────────────────────────────────
- Classify temporal phrases into structural types using syntactic cues
- Validate the well-formedness of containment, anchoring, and intersection patterns
- Handle compound expressions that merge anchoring and containment
- Parse and interpret relative time expressions and offsets
- Extract structured parts (modifiers, anchors, contained units) for downstream logic

Note:
──────────────────────────────────────────────
This module focuses solely on structural and syntactic validation.
It does **not** evaluate semantic realism (e.g., "55th day of the week").
That logic belongs to the `semantic_validation` layer.
"""
import re

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ..arithmetic import numbers
from ..temporal_preprocessing import PhraseEngine
from ..temporal_core.temporal_units import (
    named_units,
    base_unit_map,
    global_rank,
    _unit_map,
    normalize_named_unit,
    # _norm_ordinals,
    base_temporal_units,
    is_valid_containment_with_partial,
)


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.



# 1. Containment (hierarchical nesting)
#────────────────────────────────────────────────────────────────────────────
# Describes a smaller temporal unit nested within a larger one.
# Uses explicit grammatical signals like "of":
#   e.g. "day of the week", "week of April", "month of 2022"
#
# Structure Pattern:
#   <contained_unit> of <container_unit>
#
# Validation:
# - The units must follow a proper hierarchy (smaller → larger)
# - Optionally validated against contextual bounds (e.g. only 7 days in a week)

temporal_units = {
    "day_of_month":  {"dimension": "monthly_position", "rank": 1},
    "day_of_week":   {"dimension": "weekly_cycle",      "rank": 1},
    "week_of_month": {"dimension": "monthly_cycle",     "rank": 2},
    "week_of_year":  {"dimension": "annual_week",       "rank": 3},
    "month":         {"dimension": "annual_structure",  "rank": 4},
    "quarter":       {"dimension": "annual_structure",  "rank": 5},
    "season":        {"dimension": "annual_structure",  "rank": 6},
    "half_year":     {"dimension": "multiannual",       "rank": 7},
    "year":          {"dimension": "chronological",     "rank": 8},
}

def extract_containment_parts(tokens):
    """
    Extracts (contained, container) from a containment phrase like:
    ['9th', 'day', 'of', 'week'] → ('day', 'week')
    """
    if "of" not in tokens:
        return None

    idx = tokens.index("of")
    if idx < 1 or idx >= len(tokens) - 1:
        return None

    contained = tokens[idx - 1]
    container = tokens[idx + 1]
    return contained, container


def _is_hierarchy_correct(smaller, larger):
    """
    Returns True if `smaller` is strictly finer‐grained than `larger`,
    i.e. rank(smaller) < rank(larger).
    """
    def normalize(token):
        """
        Turn any string like "day", "march", "friday", "month" into one of
        the base units: "day", "week", "month", "quarter", or "year".
        """
        t = token.strip().lower()
        # 2a. direct base-unit synonyms
        if t in global_rank:
            return t
        # 2b. named instance → generic key
        if t in named_units:
            unit_key, _ = named_units[t]
            return base_unit_map[unit_key]
        # 2c. fine‐grained key → base unit
        if t in temporal_units:
            return base_unit_map[t]
        raise ValueError(f"Unknown time unit: {token!r}")

    b1 = normalize(smaller)
    b2 = normalize(larger)
    return global_rank[b1] < global_rank[b2]


def is_containment_structure(tokens):
    """
    Returns True if `tokens` form a pure containment phrase:
      <smaller_unit> of <larger_unit>
    """
    if "of" not in tokens:
        return False

    idx = tokens.index("of")
    # must have at least one token on each side
    if idx < 1 or idx >= len(tokens) - 1:
        return False

    # Avoid misclassifying compound phrases ("... of next month")
    if tokens[idx + 1] in {'from', 'starting from', 'next', 'last', 'this'}:
        return False

    contained_tok = tokens[idx - 1]
    container_tok = tokens[idx + 1]

    try:
        # normalize_named_unit maps named tokens → base units ("day","week","month",...)
        contained_base = normalize_named_unit(contained_tok)
        container_base = normalize_named_unit(container_tok)
    except ValueError:
        return False

    # check granularity: smaller(rank) < larger(rank)
    return _is_hierarchy_correct(contained_base, container_base)



# 2. Anchoring (relative to a reference point)
#────────────────────────────────────────────────────────────────────────────
# Positions a temporal unit in relation to the present or another reference.
# Uses directional modifiers like "next", "last", "this", "from", etc.
#   e.g. "next week", "last quarter", "this Friday", "starting from March"
#
# Structure Pattern:
#   <modifier> <unit>
#
# Validation:
# - Modifier must be valid for the unit (e.g. "next" applies to "month", not "2024")
# - Handles both absolute references ("this year") and dynamic ones ("from May")

anchor_modifier_valid_units = { # Each modifier maps to a set of allowed base temporal units
    "next": {"day", "week", "month", "quarter", "year"},
    "last": {"day", "week", "month", "quarter", "year"},
    "this": {"day", "week", "month", "quarter", "year", "season"},
    # "ago": {"day", "week", "month", "quarter", "year"}, 
    "from": {"month", "quarter", "year"},  # often used in ranges
    "starting from": {"month", "quarter", "year"},  # range anchor
}

def _normalize_anchor(token):
    """
    Take either:
      - A raw named unit ("march", "q2", "friday", "summer")
      - A base unit       ("day", "week", "month", "quarter", "year")
    Return the normalized base unit.
    """
    t = token.strip().lower()
    # 1) If it's already a base unit, return as‑is
    if t in anchor_modifier_valid_units["next"] | \
            anchor_modifier_valid_units["last"] | \
            anchor_modifier_valid_units["this"] | \
            anchor_modifier_valid_units["from"] | \
            anchor_modifier_valid_units["starting from"]:
        return t
    # 2) Otherwise map named units → generic unit keys, then to base
    if t in named_units:
        unit_key, _ = named_units[t]
        return base_unit_map[unit_key]
    raise ValueError(f"Cannot normalize anchor token: {token!r}")

# def is_valid_anchor(modifier, token):
#     """
#     Unified check for whether `modifier` (next/last/this/…) can apply to `token`,
#     where `token` may be either a raw named time token or a base unit.
#     """
#     base = _normalize_anchor(token)
#     valid = anchor_modifier_valid_units.get(modifier.lower(), set())
#     return base in valid
   
# def is_valid_anchor(modifier, token):
#     """
#     Accepts either a named unit ("march") *or* a full partial date ("april 2023")
#     and decides if the modifier can apply.
#     """
#     # allow partial dates as valid anchor targets
#     if PhraseEngine.is_partial_date([token], include_year=True, return_val=False):
#         return modifier.lower() in {"this", "last", "next"}
#     base = _normalize_anchor(token)
#     valid_units = anchor_modifier_valid_units.get(modifier.lower(), set())
#     return base in valid_units
  

def is_valid_anchor(modifier, token):
    """
    Accepts either a named unit ("march") *or* a full partial date ("april 2023")
    and decides if the modifier can apply.
    """
    mod = modifier.lower()

    # Handle partial date targets like "march 2023"
    if PhraseEngine.is_partial_date([token], include_year=True, return_val=False):
        parts = PhraseEngine.is_partial_date([token], include_year=True, return_val=True)
        # Infer base anchor level from the date parts
        if "day" in parts:
            base = "day"
        elif "month" in parts and "year" in parts:
            base = "month"
        else:
            base = "year"  # fallback

        valid_targets = anchor_modifier_valid_units.get(mod, set())
        return base in valid_targets

    # Handle non-partial date anchors (like "march" or "q2")
    base = _normalize_anchor(token)
    valid_units = anchor_modifier_valid_units.get(mod, set())
    return base in valid_units
   
   
def parse_anchoring_range(phrase):
    def normalize_unit(token):
        t = token.strip().lower()
        if t in _unit_map:
            return _unit_map[t]
        raise ValueError(f"Unknown unit: {token!r}")
    
    tokens = phrase.strip().lower().split()
    
    if not tokens or tokens[0] not in set(anchor_modifier_valid_units.keys()):
        return None

    modifier = tokens[0]
    count = 1
    unit_token = None

    # Detect an explicit cardinal number
    if len(tokens) >= 3 and numbers.num_type(tokens[1]) in {'cardinalNumber', 'cardinalWord'}:
        count = int(numbers.to_type(tokens[1], target='cardinalNumber'))
        unit_token = tokens[2]
    elif len(tokens) >= 2:
        unit_token = tokens[1]
    else:
        return None

    try:
        unit = normalize_unit(unit_token)
    except ValueError:
        return None

    return {
        "structure": "anchoring_range",
        "modifier": modifier,
        "count": count,
        "unit": unit
    }  

def is_anchoring_structure(tokens):
    return tokens and tokens[0] in set(anchor_modifier_valid_units.keys())

# 3. Intersection (Cross-Frame Filtering)
#────────────────────────────────────────────────────────────────────────────
# Combines two units to form a logical overlap or filter.
#   e.g. "Friday April", "April 5", "May 2022", "Q2 2023"
#
# Structure Pattern:
#   <unit1> <unit2> — unordered, both refer to time
#
# Validation:
# - Must be valid intersectable pair (e.g. "day" + "month", "month" + "year")
# - No same-grain overlaps unless explicitly allowed (e.g. "Monday and Tuesday" is fine, but not "week week")
# - Partial dates (e.g. "July 4") are treated as natural intersections

intersection_pairs = {
    "day": {"week", "month", "quarter", "year"},
    "week": {"month", "quarter", "year"},
    "month": {"quarter", "year"},
    "quarter": {"year"},

    # if I ever expose them directly (otherwise they'll normalize to 'quarter' or 'year'):    
    "season":    {"month", "quarter", "year"},
    "half_year": {"month", "quarter", "year"},
}


# Define a blacklist of (base_unit_A, base_unit_B) pairs
# that should never be allowed to intersect.
# Here we forbid same‐grain intersections:
illegal_intersection_pairs = {
    # same-level units
    ("day", "day"),
    ("week", "week"),
    ("month", "month"),
    ("quarter", "quarter"),
    ("year", "year"),

    # fuzzy or redundant overlaps
    ("season", "season"),
    ("half_year", "half_year"),
    ("quarter", "season"),
    ("week", "week_of_month"),
    ("week", "week_of_year"),
}

def _can_intersect_units(token_a, token_b, include_illegal=True):
    """
    True if their normalized base units are allowed to intersect.
    Same-unit intersections (e.g. "Tuesday and Friday") are allowed too.
    """
    ua = normalize_named_unit(token_a)
    ub = normalize_named_unit(token_b)
    if include_illegal:
        if (ua, ub) in illegal_intersection_pairs or (ub, ua) in illegal_intersection_pairs:
            return False
    if ua == ub:
        return True
    return (ub in intersection_pairs.get(ua, set()) or ua in intersection_pairs.get(ub, set()))

def _parse_intersection_structure(token_a, token_b):
    """
    If token_a and token_b form a valid intersection, return a dict,
    otherwise return None.
    """
    try:
        if _can_intersect_units(token_a, token_b):
            return {
                "structure": "intersection",
                "token_1": token_a,
                "token_2": token_b,
                "normalized": (normalize_named_unit(token_a), normalize_named_unit(token_b))
            }
    except ValueError:
        pass
    return None

def _parse_intersection_phrase(phrase):
    """
    Parses a phrase and returns intersection structure if valid,
    otherwise None.
    """
    phrase = phrase.strip().lower().replace(',', '')
    if ' in ' in phrase:
        a, b = phrase.split(' in ', 1)
    else:
        parts = phrase.split()
        if len(parts) == 2:
            a, b = parts
        else:
            return None
    return _parse_intersection_structure(a, b)


def is_intersection_structure(tokens):
    if len(tokens) == 2:
        return _parse_intersection_structure(tokens[0], tokens[1]) is not None
    if "in" in tokens and len(tokens) == 3:
        idx = tokens.index("in")
        return _parse_intersection_structure(tokens[idx - 1], tokens[idx + 1]) is not None
    return False


# 4. Compound (Anchoring + Containment)
#────────────────────────────────────────────────────────────────────────────
# Combines containment and anchoring to create a fully scoped reference.
#   e.g. "second Friday of next month", "first day of this quarter"
#
# Structure Pattern:
#   <ordinal/cardinal> <contained_unit> of <modifier> <anchor_unit>
#
# Validation:
# - Validates both:
#     • Containment: e.g. "Friday" within "month"
#     • Anchoring: e.g. "next month"
# - Optionally checks contextual bounds (e.g. no "6th Friday of February")

def extract_compound_parts(tokens):
    if "of" not in tokens:
        return None  # not compound
       
    idx = tokens.index("of")
    left = tokens[:idx]
    right = tokens[idx+1:]

    if not left or not right:
        return None

    modifier = None
    if right[0] in {'from', 'starting from', 'next', 'last', 'this'}:
        modifier = right[0]
        anchor_token = right[1] if len(right) > 1 else None
    else:
        anchor_token = right[0]

    contained_token = left[-1]
    return contained_token, anchor_token, modifier

# def validate_compound_structure(contained_token, anchor_token, modifier=None):
#     """
#     Validates a compound structure like:
#         <contained> of <modifier> <anchor>
#     Includes support for partial date containers.
#     """
#     try:
#         contained_unit = normalize_named_unit(contained_token)
# 
#         # Check if the anchor is a partial date
#         container_unit = None
#         if PhraseEngine.is_partial_date([anchor_token], return_val=False):
#             parts = PhraseEngine.is_partial_date([anchor_token], return_val=True)
#             if "day" in parts:
#                 container_unit = "day"
#             elif "month" in parts and "year" in parts:
#                 container_unit = "month"
#             else:
#                 container_unit = "month"  # fallback if ambiguous
#         else:
#             container_unit = _normalize_anchor(anchor_token)
# 
#         # Step 1: Validate containment
#         if not _is_hierarchy_correct(contained_unit, container_unit):
#             return False, "Invalid containment: unit does not fit in anchor"
# 
#         # Step 2: Validate anchoring
#         if modifier:
#             if not is_valid_anchor(modifier, anchor_token):
#                 return False, "Invalid modifier for this anchor"
# 
#         return True, "Valid compound structure"
# 
#     except Exception as e:
#         return False, f"Validation error: {e}"

def validate_compound_structure(contained_token, anchor_token, modifier=None):
    """
    Validates a compound structure like:
        <contained> of <modifier> <anchor>
    Includes support for partial date containers.
    """
    try:
        contained_unit = normalize_named_unit(contained_token)

        # -- NEW ------------------------------------------------------------
        # Accept partial dates (e.g. "april 2023") as the container anchor
        if PhraseEngine.is_partial_date([anchor_token], include_year=True, return_val=False):
            if not is_valid_containment_with_partial([anchor_token]):
                return False, "Partial date not a valid container"
            parts = PhraseEngine.is_partial_date([anchor_token], include_year=True, return_val=True)
            container_unit = "day" if parts.get("day") else "month"
        else:
            container_unit = _normalize_anchor(anchor_token)
        # -------------------------------------------------------------------

        # Step‑1  containment hierarchy
        if not _is_hierarchy_correct(contained_unit, container_unit):
            return False, "Invalid containment: unit does not fit in anchor"

        # Step‑2  anchoring modifier
        if modifier and not is_valid_anchor(modifier, anchor_token):
            return False, "Invalid modifier for this anchor"

        return True, "Valid compound structure"

    except Exception as e:
        return False, f"Validation error: {e}"


def is_compound_structure(tokens):
    if "of" not in tokens:
        return False
    idx = tokens.index("of")
    right = tokens[idx + 1:] if idx + 1 < len(tokens) else []
    return bool(right and right[0] in set(anchor_modifier_valid_units.keys()))


# 5. Relative (Offset-Based References)
#────────────────────────────────────────────────────────────────────────────
# Refers to a range or count of units relative to the current moment.
#   e.g. "last 3 days", "next 5 weeks", "2 days ago", "3 months from now"
#
# Structure Pattern:
#   <direction/modifier> <cardinal> <unit> [optional anchor]
#
# Validation:
# - Must include direction (e.g. "ago", "next", "last", "from")
# - May imply containment ("days" within "week") but is driven by offset logic
# - Special tokens like "today", "yesterday", and "tomorrow" also fall under this structure

relative_modifiers = {"ago", "from now", "before", "after", "prior to"}

def parse_relative_structure(tokens):
    """
    Parse relative expressions like:
      - "3 days ago"
      - "2 weeks from now"
      - "5 months before March"
    
    Returns:
      {
        "unit": "day",
        "offset": -3
      }
    """
    joined = " ".join(tokens).lower()
    unit = None
    count = 1
    direction = 1

    if "ago" in joined:
        direction = -1
    elif "from now" in joined or "after" in joined:
        direction = 1
    elif "before" in joined or "prior to" in joined:
        direction = -1

    # Simple pattern match: [number] [unit] [modifier]
    for i, tok in enumerate(tokens):
        try:
            if numbers.num_type(tok) in {"cardinalNumber", "cardinalWord"}:
                count = int(numbers.to_type(tok, "cardinalNumber"))
                if i + 1 < len(tokens):
                    unit_candidate = tokens[i + 1].lower()
                    unit = normalize_named_unit(unit_candidate)
                    break
        except Exception:
            continue

    if not unit:
        return None

    return {
        "unit": unit,
        "offset": direction * count
    }
   
def is_relative_structure(tokens):
    joined = " ".join(tokens).lower()
    return any(mod in joined for mod in relative_modifiers)
