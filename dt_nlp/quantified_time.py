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
def _parse_quantified_time_expression(phrase):
    """
    Processes temporal expressions that include a quantifiable numeric component
    (e.g., "3 days ago", "2 weeks ago"). It extracts the numeric value and verifies
    that the phrase refers to a valid time unit.

    If the phrase is correctly structured, the function returns a list containing
    the extracted number and the associated time unit. Otherwise, it returns None.
    """

    # Normalize expressions by removing possessive forms, such as in "last year's events" or
    # "this week's meeting". Possessive constructions introduce unnecessary syntactic 
    # complexity and can interfere with token-based pattern matching. This step ensures
    # a clean lexical structure by removing "'s" or other possessive suffixes that 
    # don't contribute meaningful temporal information for our parsing logic.
    phrase = PhraseEngine.temporal_inflect.remove_possessive_ownership(phrase)
    
    # Define canonical "X ago" patterns where X is a temporal unit. These units include:
    # - Standard duration terms: days, weeks, months, years (excluding fractional terms like "half")
    # - Weekday and weekend references (e.g., "weekend ago")
    # - Named days (e.g., "Monday ago"), months ("March ago"), seasons ("Fall ago")
    # - Quarter references ("Q1 ago")
    #
    # These patterns serve as anchors for identifying temporal expressions that may
    # lack explicit numeric quantifiers, such as "week ago", which we will normalize
    # to "1 week ago" for consistent downstream processing.
    _patterns = (
        [[unit, "ago"] for unit in sorted({unit for unit in timeline.time_units if unit != "half"}.union({"weekend"}))] +
        [[unit, "ago"] for unit in [str(f) for f in list(timeline.days) if f not in ["day", "days"] and not str(f).isdigit()]] +
        # [[unit, "ago"] for unit in [f for f in list(timeline.months)]] +
        [[unit, "ago"] for unit in list(set(timeline.seasons.list))] +
        [[unit, "ago"] for unit in ["q1", "q2", "q3", "q4"]]
    )
    # Check for a match against any of the canonical patterns defined above. If a match is found,
    # this indicates the phrase likely begins with an unquantified time unit (e.g., "day ago").
    # In such cases, we insert an explicit quantifier ("1") at the start of the phrase to
    # standardize the format — for example, converting "week ago" → "1 week ago".
    # This normalization is important for ensuring uniformity before number extraction.
    if PhraseEngine.match.lexical(
        phrase,
        lexical_match=_patterns,
        token_index=[0, 1],
        exact=True
    ):
        phrase = PhraseEngine.sub.any(
            phrase,
            replacements={" ".join(p): f"1 {' '.join(p)}" for p in _patterns},
            prefix=False,
            return_tokens=False
        )     
    
    # Handle a separate but semantically equivalent case: expressions starting with "a",
    # such as "a month ago" or "a weekend ago". These are conceptually identical to "1 month ago",
    # but the indefinite article "a" needs to be replaced with the explicit quantifier "1"
    # for reliable numeric parsing. This step systematically scans for such constructs and rewrites them.
    _updated_patterns = [["a"] + x[:] for x in _patterns]
    if PhraseEngine.match.lexical(
        phrase,
        lexical_match=_updated_patterns,
        token_index=[0, 1],
        exact=True
    ):
        phrase = PhraseEngine.sub.any(
            phrase,
            replacements={" ".join(p): "1 " + " ".join(p[1:]) if p[0] == "a" else " ".join(p) for p in _updated_patterns},
            prefix=True,
            return_tokens=False
        )

    # Some temporal expressions are preceded by adverbial modifiers that convey confidence levels
    # or estimation — e.g., "roughly 3 weeks ago", "about 2 days ago", "exactly 1 year ago".
    # While useful in natural conversation, these modifiers add no computational value for
    # temporal resolution. Hence, we remove them to simplify the surface structure of the phrase.
    if PhraseEngine.match.lexical(
        phrase,
        lexical_match=[['roughly'], ['about'], ['exactly']],
        token_index=0,
        exact=False
    ):
        phrase = PhraseEngine.sub.any(
            phrase,
            replacements={"exactly": "", "about": "", "roughly": ""},
            prefix=True,
            return_tokens=False
        )
        
    # Perform a general normalization pass over the cleaned phrase. This step includes:
    # - Spelling correction
    # - Article removal ("a", "the")
    # - Singularization of plural time units (e.g., "days" → "day")
    # - Replacement of idiomatic constructs like "a couple of" → "couple"
    #
    # The purpose of this step is to unify all forms of equivalent temporal expressions
    # into a canonical representation suitable for rule-based parsing or model-based resolution.
    phrase_tokenized = PhraseEngine.normalize(
        phrase,
        prefix_replace=None,
        remove_article=['a', 'the'],
        singularize=True, # Make time unit singular if applicable then tokenize the phrase
        replacements={"couple of": "couple", "a couple": "couple"}
        ) 
    
    # If the phrase becomes empty after normalization, it likely did not contain any valid
    # or recognizable temporal content. We return None in this case to signal that no match
    # should be processed further.
    if not phrase_tokenized:
        return None

    # We focus exclusively on past-referencing phrases in this routine.
    # If the normalized phrase does not include "ago", we discard it here.
    # This check allows the parser to cleanly separate "3 days ago" from
    # similar-looking expressions like "in 3 days" or "after 2 days".
    if "ago" not in phrase_tokenized:
        return None

    # Directly return atomic temporal references like "today", "yesterday", or "tomorrow"
    # without further processing. These are already in a fully resolved state and require
    # no quantification or normalization beyond their surface form.
    if len(phrase_tokenized) == 1:
        if phrase_tokenized[0] in ["today", "yesterday", "tomorrow"]:
            return phrase_tokenized
           
    # # Remove any residual "of" tokens that may have survived earlier transformations,
    # # such as in expressions like "a couple of days ago". These are structurally
    # # unnecessary and could interfere with index-based extraction of number + unit pairs.
    # phrase_tokenized = PhraseEngine.drop.of(phrase_tokenized, return_tokens=True)    
    
    # Handle vague quantifiers such as "couple", "few", "several", and "many".
    # These are mapped to numeric ranges internally, and a random value is selected
    # to simulate a concrete instance. This facilitates converting "a couple days ago"
    # into something parseable like "2 days ago".
    phrase_tokenized = PhraseEngine.sub.approximate_words(phrase_tokenized, 0, return_tokens=True)    
    
    # After normalization, the first token must be either a number-like term
    # (e.g., "2", "three") or a quarter reference like "q1". If neither condition is met,
    # the phrase cannot be interpreted as a quantified temporal expression.
    if not PhraseEngine.numbers.num_type(phrase_tokenized[0]) and phrase_tokenized[0] not in timeline.quarters.list:
        return None
       
    # If the first token is a valid numeric word, convert it to its digit representation.
    # This ensures uniformity in downstream processing, as all numerical values will
    # appear in cardinal form (e.g., "three" → "3").
    quantifiable_number = PhraseEngine.numbers.to_type(phrase_tokenized[0], target="cardinalNumber", as_str=True) if PhraseEngine.numbers.num_type(phrase_tokenized[0]) else None
    if quantifiable_number:
        phrase_tokenized[0] = quantifiable_number
        
    # If the first token is neither numeric nor a recognized quarter even after normalization,
    # the expression is not processable under this parser’s logic and should be discarded.        
    if not quantifiable_number and phrase_tokenized[0] not in timeline.quarters.list:
        return None
       
    # Special-case shortcut: if the normalized phrase is exactly "1 day ago",
    # rewrite it to the simpler and more semantically precise "yesterday".
    # This transformation improves interpretability for downstream logic.
    if phrase_tokenized and phrase_tokenized[-1].lower() == "ago":
        search = phrase_tokenized[-1].lower()
        if phrase_tokenized == ['1', 'day', 'ago']:
            return ["yesterday"]
    
    # As a final step, return the normalized phrase in lowercase, ensuring casing consistency.
    # Strip any leftover "of" artifacts again to guard against improperly collapsed phrases.
    # If for any reason the token list is now empty, return None to indicate failure to parse.   
    
    # return PhraseEngine.drop.of([token.lower() for token in phrase_tokenized], return_tokens=True) if [token.lower() for token in phrase_tokenized] else None
    
    tokens = [token.lower() for token in phrase_tokenized]    
    return tokens if tokens else None   


__all__ = ["_parse_quantified_time_expression"]

