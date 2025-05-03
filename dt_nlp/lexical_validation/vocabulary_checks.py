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
This module performs lexical-level integrity checks on temporal expressions.
Its primary role is to ensure that all tokens in a user-provided phrase are
legitimate members of the canonical temporal vocabulary — either recognized
keywords (e.g. “week”, “march”) or interpretable numeric values (e.g. “3”, “fifth”).

It acts as a lightweight gatekeeper before deeper syntactic or semantic analysis,
providing a fast way to reject malformed or irrelevant input.

Role in the NLP Pipeline
────────────────────────────────────────────────────
Lexical validation typically occurs as the **first-pass filter** in the pipeline.
It precedes structure parsing, number conversion, and semantic evaluation.

When paired with fuzzy correction tools (e.g., `LexicalFuzzer`), it ensures that
either:
  - All tokens are already valid, or
  - Invalid tokens can be detected early and optionally corrected downstream.

Core Focus
────────────────────────────────────────────────────
- Detect out-of-vocabulary tokens in temporal expressions
- Accept well-formed numerics (e.g. "1", "3rd", "five") even if not in the vocabulary
- Reject ambiguous or disallowed values like "0"
- Support both raw strings and pre-tokenized lists
- Serve as a pre-validation utility before parsing or correction

Note
────────────────────────────────────────────────────
This module is strictly concerned with **lexical membership**.
It does not attempt to correct spelling, infer structure, or resolve semantics.
For fuzzy matching and recovery, use the companion module `string_similarity.spell_correction`.
"""
# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ..string_similarity.spell_correction import LexicalFuzzer


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
def vocab_validate(expression):
    """
    Validates that every token in the input expression exists in
    the canonical temporal vocabulary.

    Whole numbers (except "0") are considered
    valid even if not present in the canonical vocabulary.
    """
    def _is_cardinal(keyword):
        return keyword.isdigit()
    
    # Convert expression to keywords if it's a string.        
    if isinstance(expression, str):
        keywords = expression.split()
    elif isinstance(expression, list):
        keywords = expression
    else:
        raise TypeError("Input must be a string or a list of keywords.")
    
    # Iterate through keywords, skipping whole numbers.
    for keyword in keywords:
        if _is_cardinal(keyword):
            if keyword == "0":  # Explicitly reject "0"
                return False
            continue
           
        # If the keyword (in lowercase) is not in the canonical vocabulary, return False.
        if keyword.lower() not in LexicalFuzzer.vocabulary:
            return False
    return True

