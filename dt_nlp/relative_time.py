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

import re
import random

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import numbr

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from .temporal_preprocessing import PhraseEngine
from .arithmetic import timeline



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
def handle_time_boundaries(tokens):
    """
    Handle time boundary expressions like 'start of', 'middle of', or 'end of' followed by a time anchor.

    If the expression matches the pattern '[start|middle|end] of <time anchor>', this function
    ensures that the anchor includes a directional modifier ('this', 'next', 'last').
    If none is present, it assumes 'this' by default. It then attempts to parse the anchor
    into a normalized form using `_parse_simple_relative_anchor`.
    """	
    # Step 1: Basic pattern check — only proceed if the structure is at least 3 tokens and 
    # matches the canonical form: boundary preposition ("start/middle/end") + "of" + time anchor.
    if len(tokens) >= 3 and tokens[0] in {"start", "middle", "end"} and tokens[1] == "of":
        
        # Step 2: Extract everything after "of" — this represents the syntactic anchor 
        # (e.g., "next year", "last quarter", etc.).
        anchor_tokens = tokens[2:]

        # Step 3: Ensure the anchor contains a temporal direction marker. 
        # If none is present, insert "this" as a default determiner. This aligns with how 
        # English temporal grammar implicitly assumes current period when unspecified.
        has_direction = any(word in {"next", "last", "this", "previous"} for word in anchor_tokens)
        if not has_direction and anchor_tokens:
            anchor_tokens.insert(0, "this")

        # Step 4: Normalize and validate the anchor using grammar-aware anchor parser.
        # This function checks if the anchor is a recognized relative structure (e.g., "last quarter").
        anchor_parse = _parse_simple_relative_anchor(" ".join(anchor_tokens))
        
        # Step 5: If normalization fails (invalid grammar or unrecognized anchor), discard.
        if not anchor_parse:
            return None

        # Step 6: Return a clean, normalized token list in the canonical format:
        #   [boundary, "of", normalized anchor...]
        return [tokens[0], "of"] + anchor_parse

    # Fallback: If the input doesn't match the expected boundary form, skip transformation.
    return None
   

def _parse_simple_relative_anchor(anchor_phrase):
    """
    Parses time anchor expressions such as "last year", "first quarter", or "middle of year".
    Does not handle retrospective constructs like "two years ago".
    """
    # Normalize and tokenize the input for consistent downstream parsing
    tokens = anchor_phrase.lower().strip().split()
    if not tokens:
        return None

    # Recognized temporal direction markers and canonical time units
    DIRECTIONS = {"next", "last", "this", "previous", "past"}
    UNITS = {"week", "month", "year", "quarter", "season"} \
            | set(timeline.months) \
            | set(timeline.quarters) \
            | set(timeline.seasons)

    first = tokens[0]

    # If the expression starts with a temporal direction like "last" or "past",
    # it's valid if followed directly by a time unit (e.g., "last quarter")
    if first in DIRECTIONS:
        if len(tokens) >= 2 and tokens[1] in UNITS:
            return tokens

        # Alternatively, allow a number between the direction and unit,
        # e.g., "past 2 years" or "last 3 quarters"
        if (len(tokens) >= 3
            and PhraseEngine.numbers.to_type(tokens[1], target="cardinalNumber", as_str=True) is not None
            and tokens[2] in UNITS):
            num = PhraseEngine.numbers.to_type(tokens[1], target="cardinalNumber", as_str=True)
            return [first, str(num)] + tokens[2:]

        # If the direction exists but isn't followed by a recognized structure, reject it
        return None

    # Handle expressions like "first quarter" or "third month",
    # which represent ordinal positions within a larger time period
    ord_val = PhraseEngine.numbers.num_type(first) in ('ordinalWord', 'ordinalNumber') 
    if ord_val is not None and len(tokens) > 1:
        if tokens[1] in UNITS or tokens[1] in timeline.quarters:
            return tokens

    # Support mid-span expressions like "start of year" or "middle of spring"
    # which refer to a sub-segment of a larger time unit
    if first in {"start", "middle", "end"} and len(tokens) >= 3 and tokens[1] == "of":
        if tokens[2] in UNITS:
            return [first, "of"] + tokens[2:]

    # If the expression does not match any valid temporal anchor grammar, return None
    return None


def _parse_subexpression(sub_tokens):
    """
    Parses sub-time expressions like:
      - "first 5 days"
      - "middle 3 months"
      - "second half"
      - "third Monday"

    This logic recognizes ordinal-based segments (optionally with numeric scopes)
    applied to well-known temporal units or weekday names. Expressions that
    don’t match this structure are rejected as invalid.
    
    Returns:
        A list of cleaned tokens if a valid temporal substructure is recognized,
        or None otherwise.
    """
    # Special cases for pseudo-ordinal markers frequently used in date references
    # These are interpreted like ordinals even though they aren't numeric in nature
    SPECIAL_ORDINALS = {
        "middle": 2,  # Treated as roughly equivalent to "second"
        "start": 1,   # Synonym for "first"
        "end": -1     # Used in parsing but does not imply ordinal ranking
    }
    
    if not sub_tokens:
        return None

    # Identify whether the first token is an ordinal expression.
    # This could be a word like "first", "third", or a marker like "middle".
    maybe_ordinal_value = (
        PhraseEngine.numbers.to_type(sub_tokens[0], 'ordinalWord') or
        SPECIAL_ORDINALS.get(sub_tokens[0])
    )
    if maybe_ordinal_value is None:
        # If the first word doesn't represent an ordinal (e.g., "third") or special case,
        # then the phrase doesn't match an expected sub-time pattern
        return None

    # If the second token is a cardinal number (e.g., "5" in "first 5 days"),
    # extract it for later validation.
    try:
        cardinal_number = None
        if len(sub_tokens) >= 2:
            card_val = PhraseEngine.numbers.to_type(
                sub_tokens[1], target="cardinalNumber", as_str=True
            )
            if card_val is not None:
                cardinal_number = card_val
    except ValueError:
        # If parsing fails unexpectedly, we still allow fallback to original phrasing
        return sub_tokens

    # Determine the position where the time unit should appear,
    # depending on whether a cardinal number precedes it.
    idx_for_unit = 1 if cardinal_number is None else 2
    if idx_for_unit >= len(sub_tokens):
        return None  # Not enough tokens left to include a time unit

    sub_unit = sub_tokens[idx_for_unit]

    # Validate that the detected time unit is recognized:
    # - Standard units like "week", "month", etc.
    # - Weekday names like "monday", "friday", etc.
    RECOGNIZED_SUBUNITS = {"day", "week", "month", "quarter", "year", "half"}
    recognized_dow = set(
        str(f).lower()
        for f in timeline.days
        if f not in {"day", "days"} and not str(f).isdigit()
    )
    recognized_sub = RECOGNIZED_SUBUNITS.union(recognized_dow)

    if sub_unit not in recognized_sub:
        return None  # Invalid or unsupported time unit

    # If the expression has passed all structural checks, return it as a normalized sequence
    return [str(tok).lower() for tok in sub_tokens]




## MAIN PARSING LOGIC FOR INTERPRETING STRUCTURED RELATIVE TIME EXPRESSIONS.
##━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _parse_named_relative_expression(phrase):
    """
    Parses relative date/time expressions such as:
      - "last 2 quarters"
      - "middle of this year"
      - "first 5 days of next month"
      - "yesterday", "tomorrow", etc.

    This function assumes pre-tokenization and performs both normalization and
    hierarchical decomposition to recognize common temporal grammar structures.
    """
    # Handle partial dates like "July 5th" or "July 1"
    # These are directly promoted to their canonical representation
    if PhraseEngine.is_partial_date(phrase):
        parsed_tokens = PhraseEngine.sub.ordinal_cardinal(phrase)
        if parsed_tokens and (len(parsed_tokens) == 1):
            parsed_tokens.insert(0, "this")  # Default to "this" for reference-less dates
        return parsed_tokens

    # Normalize expressions like "a day" or "a week" → "1 day", "1 week"
    # Helps unify indefinite article usage into a quantitative form
    if PhraseEngine.match.lexical(
        phrase,
        lexical_match=[["a", unit] for unit in sorted({unit for unit in timeline.time_units}.union({"weekend"}))],        
        token_index=[0, 1],
        exact=True
    ):
        phrase = PhraseEngine.sub.any(phrase, replacements={"a": "1"}, prefix=True, return_tokens=False)

    # Normalize expressions like "the day", "the week" → "day", "week"
    # Strips out definite articles to match canonical units
    if PhraseEngine.match.lexical(
        phrase,
        lexical_match=[["the", unit] for unit in sorted({unit for unit in timeline.time_units}.union({"weekend"}))],        
        token_index=[0, 1],
        exact=True
    ):
        phrase = PhraseEngine.sub.any(phrase, replacements={"the": ""}, prefix=True, return_tokens=False)

    # Normalize whitespace and spacing artifacts
    phrase = PhraseEngine.clean_gaps(phrase)

    # Remove possessive suffixes like "'s" or "s’" from tokens for clarity
    phrase = PhraseEngine.temporal_inflect.remove_possessive_ownership(phrase)

    # Apply standardization routines: collapsing modifiers, replacing synonyms,
    # stripping determiners, and harmonizing plurals/singulars
    phrase_tokenized = PhraseEngine.normalize(
        phrase,
        prefix_replace={
            "following": "next",
            "past": "last",
            "this past": "last",
            "the start": "start",
            "the end": "end",
            "the beginning": "start",
            "beginning": "start",
            "the middle": "middle",
            "halfway through": "middle"
        },
        remove_article=['the'],
        singularize=True,
        replacements={
            "of the current": "of this",
            "of the": "of this",
            "mid": "middle"
        }
    )

    if not phrase_tokenized:
        return None

    # Drop unnecessary "this" markers in composite phrases
    phrase_tokenized = PhraseEngine.drop.this(phrase_tokenized, return_tokens=True)

    # Replace sequences like "this past" with "last"
    phrase_tokenized = PhraseEngine.sub.past(phrase_tokenized, return_tokens=True)

    # Re-map "in" to "of" to conform to nested temporal grammars
    phrase_tokenized = PhraseEngine.sub.In(phrase_tokenized, return_tokens=True)

    # If phrase is just "today", "yesterday", "tomorrow", return directly
    if len(phrase_tokenized) == 1:
        if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["today", "yesterday", "tomorrow"]):
            return phrase_tokenized

    # Skip phrases starting with vague quantifiers like "couple" or "few"
    if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["couple", "few", "several", "many"], token_index=0):
        return None

    # Exclude retrospective expressions like "2 years ago"
    if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["ago"]):
        return None

    # Resolve approximates like "few" to a randomized fixed value (e.g., 3–5)
    try:
        phrase_tokenized = PhraseEngine.sub.approximate_words(phrase_tokenized, 1, return_tokens=True)
    except IndexError:
        pass

    # Drop redundant "1" tokens after temporal modifiers like "last" or "next"
    phrase_tokenized = PhraseEngine.drop.one(phrase_tokenized, return_tokens=True)

    # Collapse "this day" into canonical "today" format
    if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["this"], token_index=0):
        if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["this", "day"], token_index=None, exact=True):
            return ["today"]
        elif PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["this", "weekday"], token_index=None, exact=True):
            return phrase_tokenized

    # Normalize expressions like "last day" or "next 1 day" → "yesterday" / "tomorrow"
    if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["last", "next", "previous"], token_index=0, exact=False):
        if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=[["next", "day"], ["next", "1", "day"]], token_index=None, exact=True):
            return ["tomorrow"]
        elif PhraseEngine.match.lexical(phrase_tokenized, lexical_match=[["last", "day"], ["last", "1", "day"], ["previous", "day"], ["previous", "1", "day"]], token_index=None, exact=True):
            return ["yesterday"]

    # Handle time boundary expressions like "start of last quarter"
    boundary_result = handle_time_boundaries(phrase_tokenized)
    if boundary_result:
        return boundary_result

    # Handle edge cases like "day of", where it's just a day extracted from a container
    if PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["day", "of"], token_index=[0, 1], exact=True):
        return [PhraseEngine.drop.of(phrase_tokenized, return_tokens=True)[1]]
    elif PhraseEngine.match.lexical(phrase_tokenized, lexical_match=["this", "day", "of"], token_index=[0, 2], exact=True):
        return [PhraseEngine.drop.of(phrase_tokenized, return_tokens=True)[2]]

    # Handle structures like:
    # - "first Monday of next month"
    # - "third day of last quarter"
    # - "middle 3 months of this year"
    if "of" in phrase_tokenized:
        idx_of = phrase_tokenized.index("of")
        left_side = phrase_tokenized[:idx_of]
        right_side = phrase_tokenized[idx_of + 1:]

        # Ensure the right-side anchor has direction, default to "this" if missing
        if not any(word in {"next", "last", "this", "previous"} for word in right_side) and right_side:
            right_side.insert(0, "this")

        anchor_parse = _parse_simple_relative_anchor(" ".join(right_side))
        if not anchor_parse:
            return None

        # If left side is a recognized weekday (e.g., "Friday")
        if left_side[0] in set(str(f) for f in list(timeline.days) if f not in {"day", "days"} and not str(f).isdigit()):
            left_parse = left_side

        # If left side starts with an ordinal or a normalized quarter label
        elif PhraseEngine.numbers.num_type(left_side[0]) in ('ordinalNumber', 'ordinalWord'):
            left_side[0] = PhraseEngine.numbers.to_type(left_side[0], 'ordinalWord')
            left_parse = left_side
        elif left_side[0] in timeline.quarters.list:
            left_parse = left_side
        elif left_side[0] in {"last", "previous", "next"}:
            left_parse = left_side

        # Otherwise, attempt to interpret as quantifier-based temporal segment
        else:
            left_parse = _parse_subexpression(left_side)
            if not left_parse:
                return None

        parsed = left_parse + ["of"] + anchor_parse
        return parsed if parsed else None

    # Simple fallback cases (e.g., "first quarter", "second week")
    ordinal = None
    ord_value = numbr.ordinalWordToOrdinalNum(phrase_tokenized[0])
    if ord_value is not None:
        ordinal = True
        phrase_tokenized[0] = ord_value
    elif numbr.ordinalNumToCardinalWord(phrase_tokenized[0]):
        ordinal = True

    # If the first token is a cardinal but not a valid partial date, skip it
    if not ordinal:
        if not PhraseEngine.is_partial_date(" ".join(map(str, phrase_tokenized)).lower()):
            if PhraseEngine.numbers.num_type(phrase_tokenized[0]) == "cardinalNumber":
                return None

    parsed_tokens = [token.lower() for token in phrase_tokenized]
    if not parsed_tokens:
        return None

    # Add an implicit "this" if it's just a single unit (e.g., "month" → "this month")
    if len(parsed_tokens) == 1:
        parsed_tokens.insert(0, "this")

    return parsed_tokens


__all__ = ["_parse_named_relative_expression"]

