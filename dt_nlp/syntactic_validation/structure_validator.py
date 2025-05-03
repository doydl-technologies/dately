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
This module orchestrates the structural validation of temporal expressions
through a majority-voting system across five primary syntactic structures:
anchoring, containment, intersection, compound, and relative. It serves as
a control layer that interprets input tokens, scores structural dominance,
and validates their syntactic integrity using specialized rule-based checks.

Role in the NLP Pipeline:
──────────────────────────────────────────────
This module operates after tokenization and preprocessing, acting as the
structural classification engine before semantic interpretation. It determines
which structural type best describes a phrase, assigns a confidence score,
and flags ambiguity or potential structural overlap. This classification
informs downstream interpretation, resolution, and calendar logic.

Core Focus:
──────────────────────────────────────────────
- Run all structure-type classifiers in permutation order (first-match-wins)
- Compute majority votes across structure types for robust classification
- Validate phrases using structure-specific rules (e.g. containment hierarchy)
- Detect and parse partial dates and deictic terms (e.g. "today", "July 4")
- Output normalized structure labels, confidence, parts, and reasons

Note:
──────────────────────────────────────────────
This module focuses purely on structure and syntactic relationships.
It does **not** assess calendar realism, numeric bounds, or contextual logic.
Those checks are delegated to the `semantic_validation` layer.
"""
from itertools import permutations
from collections import Counter
from typing import List

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ..temporal_preprocessing import PhraseEngine
from ..temporal_core.temporal_units import (
    remove_unnecessary_this,
    insert_prepositions,
    normalize_named_unit,
)

from .temporal_structure_rules import (
    is_compound_structure,
    is_anchoring_structure,
    is_containment_structure,
    is_intersection_structure,
    is_relative_structure,
    validate_compound_structure,
    parse_relative_structure,
    extract_containment_parts,
    extract_compound_parts,
    is_valid_anchor,
    _is_hierarchy_correct,
)



# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
structure_checkers = {
    "compound": is_compound_structure,
    "anchoring": is_anchoring_structure,
    "containment": is_containment_structure,
    "intersection": is_intersection_structure,
    "relative": is_relative_structure,    
}

structure_permutations = list(permutations(structure_checkers.keys()))

def structural_majority_vote(tokens) -> Counter:
    vote_counts = Counter()
    for ordering in structure_permutations:
        for label in ordering:
            if structure_checkers[label](tokens):
                vote_counts[label] += 1
                break  # first match wins
    return vote_counts

def analyze_structure_votes(tokens):
    votes = structural_majority_vote(tokens)
    total = sum(votes.values())

    if not votes:
        return {
            "structure": None,
            "confidence": 0.0,
            "ambiguous": True,
            "votes": {},
            "co_occurrence": [],
            "reason": "No structure matched"
        }

    sorted_votes = votes.most_common()
    top, top_count = sorted_votes[0]
    confidence = top_count / total
    ambiguous = confidence <= 0.5

    # Optional: capture close runners-up (within 2 votes of the winner)
    co_occurring = [label for label, count in sorted_votes
                    if count >= top_count - 2 and label != top]

    return {
        "structure": top,
        "confidence": confidence,
        "ambiguous": ambiguous,
        "votes": dict(votes),
        "co_occurrence": co_occurring,
        "reason": "Multiple structures co-dominant" if ambiguous else "Dominant structure clear"
    }


def validate_temporal_structure(tokens, this_anchor_removal=True, auto_add_prepositions=True):
    """
    Classify, score, and validate the structural integrity of a temporal phrase.
    Returns:
    {
      "structure": <dominant_structure or None>,
      "confidence": <0.0–1.0>,
      "ambiguous": <bool>,
      "votes": {...},
      "co_occurrence": [...],
      "valid": <bool>,
      "reason": <str>,
      "parts": {...}  # if available
    }
    """    
    deictic_tokens = {
        "today": {"unit": "day", "offset": 0},
        "yesterday": {"unit": "day", "offset": -1},
        "tomorrow": {"unit": "day", "offset": 1},
        "tommorrow": {"unit": "day", "offset": 1},  # common misspelling
    }
    
    if auto_add_prepositions:
        tokens = insert_prepositions(tokens)
        
    if this_anchor_removal:
        tokens = remove_unnecessary_this(tokens)
        
    # Deictic expression shortcut
    if len(tokens) == 1:
        t = tokens[0].lower()
        if t in deictic_tokens:
            return {
                "structure": "relative",
                "confidence": 1.0,
                "ambiguous": False,
                "votes": {"relative": 120},
                "co_occurrence": [],
                "valid": True,
                "reason": f"Recognized deictic term → '{t}'",
                "parts": deictic_tokens[t]
            }    

    # Early check: if this is a standalone partial date, it's automatically an intersection
    if (
        len(tokens) == 2
        and tokens[0].lower() == "this"
        and PhraseEngine.is_partial_date([tokens[1]], include_year=True, return_val=False)
    ):
        tokens = [tokens[1]]  # Strip "this" if it's a wrapper around a partial date

    if PhraseEngine.is_partial_date(tokens, include_year=True, return_val=False):
        parts = PhraseEngine.is_partial_date(tokens, include_year=True, return_val=True)
        return {
            "structure": "intersection",
            "confidence": 1.0,
            "ambiguous": False,
            "votes": {"intersection": 120},
            "co_occurrence": [],
            "valid": True,
            "reason": "Valid partial date → intersection structure",
            "parts": parts
        }
        
    votes = structural_majority_vote(tokens)
    total = sum(votes.values())

    if not votes:
        return {
            "structure": None,
            "confidence": 0.0,
            "ambiguous": True,
            "votes": {},
            "co_occurrence": [],
            "valid": False,
            "reason": "No structure matched",
            "parts": {}
        }

    sorted_votes = votes.most_common()
    top_structure, top_count = sorted_votes[0]
    confidence = top_count / total
    ambiguous = confidence <= 0.5
    co_occurring = [label for label, count in sorted_votes
                    if count >= top_count - 2 and label != top_structure]

    valid = False
    reason = "Structure identified but not validated"
    parts = {}

    try:
        if top_structure == "compound":
            extracted = extract_compound_parts(tokens)
            if extracted:
                contained, anchor, modifier = extracted
                valid, reason = validate_compound_structure(contained, anchor, modifier)
                parts = {
                    "contained": contained,
                    "anchor": anchor,
                    "modifier": modifier
                }
        elif top_structure == "anchoring":
            if len(tokens) >= 2:
                modifier = tokens[0]
                anchor = tokens[1]
                valid = is_valid_anchor(modifier, anchor)
                reason = "Valid anchoring" if valid else "Invalid anchoring modifier or unit"
                parts = {"modifier": modifier, "anchor": anchor}
                
        # elif top_structure == "containment":
        #     valid = is_containment_structure(tokens)
        #     reason = "Valid containment" if valid else "Invalid containment relationship"
        
        elif top_structure == "containment":
            extracted = extract_containment_parts(tokens)
            if extracted:
                contained, container = extracted
                parts = {"contained": contained, "anchor": container}
                valid = _is_hierarchy_correct(
                    normalize_named_unit(contained),
                    normalize_named_unit(container)
                )
                reason = "Valid containment" if valid else "Invalid containment relationship"
            
        elif top_structure == "intersection":
            valid = is_intersection_structure(tokens)
            reason = "Valid intersection" if valid else "Invalid intersection"
            
        elif top_structure == "relative":
            extracted = parse_relative_structure(tokens)
            if extracted:
                valid = True
                reason = "Valid relative expression"
                parts = extracted
            else:
                valid = False
                reason = "Could not parse relative structure"
    except Exception as e:
        valid = False
        reason = f"Validation error: {e}"

    return {
        "structure": top_structure,
        "confidence": confidence,
        "ambiguous": ambiguous,
        "votes": dict(votes),
        "co_occurrence": co_occurring,
        "valid": valid,
        "reason": reason,
        "parts": parts
    }




















