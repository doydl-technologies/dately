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
This module implements a high-level parser for interpreting natural-language
temporal phrases and converting them into concrete `date` or `(start, end)` ranges.
It supports a wide range of linguistic forms, including anchored periods,
quantified spans, ordinal references, and relative modifiers (e.g., "3 Fridays ago").

Its core engine, `RelativeDateResolver`, is complemented by normalization logic,
semantic guards, and syntactic validation layers to enable precise calendar resolution.

Role in the NLP Pipeline:
────────────────────────────────────────────────────
This module acts as the semantic executor in the temporal NLP stack.
It consumes already-tokenized, partially-normalized input and computes
a concrete temporal resolution. It is invoked after structure validation,
and integrates with the rest of the pipeline by exposing a callable interface
via `parse_temporal()`.

It also includes `_auditor`, a structured diagnostic utility that enforces
semantic well-formedness before resolution (e.g., "55th day of week" → invalid).

Core Focus:
────────────────────────────────────────────────────
- Interpret structured and unstructured temporal expressions
- Handle "this/next/last" logic and their hierarchical scopes
- Support expressions like "first 5 days of next month"
- Evaluate semantic plausibility (e.g. range sizes, ordinal containment)
- Serve as the front-facing computation engine for relative temporal inference
"""
import re
from datetime import datetime as dt, timedelta as td, date as d
from copy import deepcopy

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from .dt_nlp.relative_time import _parse_named_relative_expression
from .dt_nlp.quantified_time import _parse_quantified_time_expression
from .dt_nlp.arithmetic import timeline
from .dt_nlp.temporal_preprocessing import PhraseEngine
from .dt_nlp.syntactic_validation.structure_validator import validate_temporal_structure
from .dt_nlp.semantic_validation.unit_bounds import validate_bounds, validate_range_bounds
from .dt_nlp.lexical_validation.vocabulary_checks import vocab_validate



# ***************************************************************
# Debug / development switch
#     • False (default)  → full validation & auditing
#     • True             → bypass structure + semantic auditing
# ***************************************************************
DEBUGGER = False

      
# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
class RelativeDateResolver:
    """
    A class for computing results of date-related expressions.
    """
    # Initialization & Settings
    #─────────────────────────────
    def __init__(self, week_start='sunday'):
        self.reference_date = d.today()
        self.Days = {k.lower(): v for k, v in {k: v for k, v in timeline.days.items() if k not in {"day", "days"}}.items() if isinstance(k, str) and k.lower() == v.lower()}             
        self.Seasons = {k: v.lower() for k, v in timeline.seasons.items()}    
        self.Quarters  = {k: v.lower() for k, v in timeline.quarters.items() if k == v}         
        self.TimeUnits = timeline.time_units.union({"weekend"}) 
        self.SeasonsOrdered = [f for f in timeline.seasons.info] # ["winter", "spring", "summer", "fall"]
        self.QuartersOrdered = timeline.quarters.list  # ["q1", "q2", "q3", "q4"]          
        self._ORDINAL_RE = re.compile(r"^(\d+)(st|nd|rd|th)$")         
        
        # Core settings
        self.week_start = self._normalize_week_start(week_start) 
        self.immediate_relative_days = {
            "yesterday": lambda ref: ref - td(days=1),
            "today": lambda ref: ref,
            "tomorrow": lambda ref: ref + td(days=1),}

    def _normalize_week_start(self, value):
        val = str(value).strip().lower()
        if val.isdigit():
            idx = int(val)
            if idx not in range(0, 7):
                raise ValueError(f"Invalid numeric weekday: {value}")
            val = self.Days.get(idx)
        val = self.Days.get(val, val) 
        if val.lower() == "sunday":
            return "sunday"
        elif val.lower() == "monday":
            return "monday"
        else:
            raise ValueError(f"Invalid week start value: {value}")
           
    def set_week_start(self, week_start):
        """Public method to update the week_start and reinitialize dependent logic."""
        self.week_start = self._normalize_week_start(week_start)
        
    def _is_ordinal(self, tok: str) -> bool:
        """True if token looks like 1st / 2nd / 23rd …"""
        return bool(self._ORDINAL_RE.match(tok))

    def _ordinal_value(self, tok: str) -> int:
        """Return 1 for 1st, 2 for 2nd …  Raises if not ordinal."""
        m = self._ORDINAL_RE.match(tok)
        if not m:
            raise ValueError(f"Not an ordinal token: {tok}")
        return int(m.group(1))

    def _add_days(self, base_date, n_days):
        return base_date + td(days=n_days)

    def _add_weeks(self, base_date, n_weeks):
        if self.week_start.lower() == 'monday':
            start_of_week = base_date - td(days=base_date.weekday())  
        elif self.week_start.lower() == 'sunday':
            start_of_week = base_date - td(days=(base_date.weekday() + 1) % 7) 
        return start_of_week + td(weeks=n_weeks)

    def _add_months(self, base_date, n_months):
        year = base_date.year
        month = base_date.month
        day = base_date.day
        total_months = (year * 12 + (month - 1)) + n_months
        new_year, new_month = divmod(total_months, 12)
        new_year, new_month = int(new_year), new_month + 1
        last_day = timeline.days_in_month(new_month, new_year).d       
        new_day = min(day, last_day)
        return d(new_year, new_month, new_day)

    def _add_years(self, base_date, n_years):
        try:
            return base_date.replace(year=base_date.year + n_years)
        except ValueError:
            return base_date.replace(year=base_date.year + n_years, day=28)
           
    def _get_current_or_previous_quarter_start(self, base, quarter_key):
        current_year = base.year
        info = timeline.adj_quarters()[quarter_key]
        start_mm, start_dd = map(int, info["start"].split("/"))
        end_mm, end_dd = map(int, info["end"].split("/"))
        start = d(current_year, start_mm, start_dd)
        end = d(current_year, end_mm, end_dd)
        if start <= base <= end:
            return start
        elif base < start:
            return self._get_previous_year_quarter_by_date(start, quarter_key)
        else:
            return start

    def _get_previous_year_quarter_by_date(self, current_start, quarter_key):
        prev_year = current_start.year - 1
        info = timeline.adj_quarters()[quarter_key]
        mm, dd = map(int, info["start"].split("/"))
        return d(prev_year, mm, dd)              
       
    def _resolve_temporal_boundary(self, base_date, start_date, end_date, direction):
        if direction == "this":
            if start_date <= base_date <= end_date:
                return "this"
            elif base_date < start_date:
                return "this"
            else:
                return "next"
        elif direction == "next":
            if base_date <= end_date:
                return "next"
            else:
                return "next"
        elif direction == "last":
            if base_date >= start_date:
                return "last"
            else:
                return "last"
        elif direction == "previous":
            if base_date >= start_date:
                return "previous"
            else:
                return "previous"
        return "this"    
    
    def _parse_date(self, date_str):
        try:
            mm, dd, yyyy = map(int, date_str.split('/'))
            return d(yyyy, mm, dd)
        except ValueError as e:
            raise ValueError(f"Failed to parse date due to incorrect format: {e}")

    def _parse_date_from_string(self, date_str):
        try:
            month, day = date_str.split()
            month_number = timeline.adj_months(m=month, year=None).start.mm.int
            year = self.reference_date.year 
            return d(year, month_number, int(day))
        except (ValueError, IndexError):
            return None
    
    def _determine_current_season(self, base_date, include_year=False):
        month = base_date.month
        year = base_date.year
        if month == 12:
            season = "winter"
            year += 1
        elif month in [1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"
        return (season, year) if include_year else season

    def _determine_current_quarter(self, base_date):
        month = base_date.month
        if month in (1, 2, 3):
            return "q1"
        if month in (4, 5, 6):
            return "q2"
        if month in (7, 8, 9):
            return "q3"
        if month in (10, 11, 12):
            return "q4"       

    def _get_season_boundaries(self, season_name, year):
        info = timeline.adj_seasons(season=season_name.lower(), year=year, include_year=True)
        if not info:
            return None
        return info
       
    def _range_from_unit(self, base_date, quantity, time_unit):
        if quantity == 0:
            return (base_date, base_date)
        going_back = (quantity < 0)
        abs_qty = abs(quantity)
        if going_back:
            end = base_date - td(days=1)
            if time_unit == "day":
                start = end - td(days=abs_qty - 1)
            elif time_unit == "week":
                start = end - td(days=7 * abs_qty - 1)
            elif time_unit == "month":
                start_anchor = end + td(days=1)
                start = self._add_months(start_anchor, -abs_qty)
            elif time_unit == "year":
                start_anchor = end + td(days=1)
                start = self._add_years(start_anchor, -abs_qty)
            else:
                return None
            return (start, end)
        else:
            start = base_date
            if time_unit == "day":
                end = start + td(days=abs_qty - 1)
            elif time_unit == "week":
                end = start + td(days=7 * abs_qty - 1)
            elif time_unit == "month":
                end = self._add_months(start, abs_qty) - td(days=1)
            elif time_unit == "year":
                end = self._add_years(start, abs_qty) - td(days=1)
            else:
                return None
            return (start, end)

    # Arithmetic Fallback Handler
    #-------------------------------------------------------  
    def _compute_arithmetic(self, tokens):
        direction = None
        quantity = 1
        time_unit = None

        for token in tokens:
            t = token.lower()
            if t in ["next", "last", "this", "previous"]:
                direction = t
            elif t.isdigit():
                quantity = int(t)
            elif t in self.TimeUnits:
                time_unit = t

        if time_unit not in self.TimeUnits:
            return None

        # Default to "this" if no direction is given
        if direction is None:
            direction = "this"

        # Normalize quantity based on direction
        if direction in ["last", "previous"]:        
            quantity = -abs(quantity)
        elif direction == "next":
            quantity = abs(quantity)
        elif direction == "this":
            quantity = 0

        base = self.reference_date

        # Handle time units
        if time_unit == "day":
            result = self._add_days(base, quantity)

        elif time_unit == "week":
            results = []
            if direction == "next":
                cursor = self._add_weeks(base, 1)
                for _ in range(abs(quantity)):
                    week_start = cursor
                    week_end = week_start + td(days=6)
                    results.append((week_start, week_end))
                    cursor = week_end + td(days=1)
                return results if len(results) > 1 else results[0]

            # elif direction == "last":
            elif direction in ["last", "previous"]:            
                cursor = self._add_weeks(base, -1)
                for _ in range(abs(quantity)):
                    week_end = cursor
                    week_start = week_end - td(days=6)
                    results.insert(0, (week_start, week_end))
                    cursor = week_start - td(days=1)
                return results if len(results) > 1 else results[0]

            else:  # "this"
                week_start = self._add_weeks(base, 0)
                week_end = week_start + td(days=6)
                return (week_start, week_end)

        elif time_unit == "month":
            result = self._add_months(base, quantity)

        elif time_unit == "year":
            result = self._add_years(base, quantity)

        elif time_unit in {"quarter", "season"}:
            direction_token = ("next" if quantity > 0 else "last" if quantity < 0 else "this")
            return _compute_named_repetitions(direction_token, abs(quantity), time_unit)

        elif time_unit == "weekend":
            results = []
            base = self.reference_date
            direction_sign = -1 if quantity < 0 else 1
            for i in range(abs(quantity)):
                result = _compute_specific_weekend("next" if direction_sign > 0 else "last", base)
                if result:
                    results.append(result)
                    base = (
                        result[1] + td(days=1)
                        if direction_sign > 0
                        else result[0] - td(days=1)
                    )
            return results if len(results) > 1 else results[0] if results else None

        else:
            return None

        _ALWAYS_RANGE_UNITS = {"week", "month", "year"}
        if (
            time_unit not in {"season", "quarter"}
            and (abs(quantity) > 1 or time_unit in _ALWAYS_RANGE_UNITS)
        ):
            return self._range_from_unit(base, quantity, time_unit)

        return result

    #--------------------------------------------
    # Main Entry Point
    #--------------------------------------------
    def compute(self, tokens):
        """
        Main entry‑point.  Accepts a list of *already normalised* tokens and
        returns either
        """
        if not tokens: return None
        tokens = [str(t).lower() for t in tokens]

        # ------------------------------------------------------------------ 
        # 0) Normalize Implicit Forward Time Expressions
        # ------------------------------------------------------------------ 
        # Handles cases where the user writes a bare quantified time span like:
        #     ["6", "months"]
        #     ["3", "weeks"]
        #     ["1", "year"]
        #
        # These are treated as forward-looking by default (i.e., as "next"),
        # so we rewrite them to:
        #     ["next", "6", "months"]
        #
        # Why:
        #   - Makes the syntax compatible with arithmetic logic downstream,
        #     which expects a direction token ("next", "last", etc.)
        #   - Prevents ambiguity and ensures consistent temporal anchoring
        #
        # Note:
        #   - This only applies if the phrase is exactly two tokens long
        #     AND the first token is a digit AND the second is a known time unit.
        #   - It's a syntactic patch for informal shorthand expressions.
        if (
            len(tokens) == 2
            and tokens[0].isdigit()
            and tokens[1] in self.TimeUnits
        ):
            tokens = ["next"] + tokens

        # ------------------------------------------------------------------ 
        # 1) Handle Nested “Ago” Modifiers with Anchor Adjustment
        # ------------------------------------------------------------------
        # This block looks for extended forms of "ago" expressions, such as:
        #     ["3", "days", "ago"]
        #     ["2", "weeks", "ago", "starting", "from", ...]
        #
        # Specifically, it handles cases where the "ago" portion affects only
        # part of the phrase and must be computed first to adjust the reference date.
        #
        # Example:
        #     ["3", "weeks", "ago", "first", "Monday"]
        #     → Step 1: shift reference date back by 3 weeks
        #     → Step 2: evaluate ["first", "Monday"] from the new anchor
        #
        # This design enables layered semantics, where "ago" is treated as a
        # modifier for the **base time**, not the entire phrase.
        #
        # Logic:
        #   - Find the "ago" token
        #   - If preceded by [<digit>, <unit>] and unit is a recognized time unit,
        #     compute the offset and shift the `reference_date`
        #   - Then evaluate the remaining leading tokens (if any) from the new anchor
        #   - Temporarily mutate the internal state (`self.reference_date`)
        #     to enable chained evaluations, then restore it afterward
        if "ago" in tokens:
            try:
                idx_ago = tokens.index("ago")
                if idx_ago >= 2:
                    quantity_token = tokens[idx_ago - 2]
                    unit_token     = tokens[idx_ago - 1]

                    if quantity_token.isdigit() and unit_token in self.TimeUnits:
                        quantity = int(quantity_token)
                        shifted_date = _compute_ago_expression(quantity, unit_token)

                        if shifted_date:
                            remaining_tokens = tokens[:idx_ago - 2]

                            # IF NO leftover tokens => just return shifted date
                            if not remaining_tokens:
                                return shifted_date
                            
                            # Otherwise, parse the leftover tokens with the new reference
                            old_ref = self.reference_date
                            self.reference_date = shifted_date
                            result = self.compute(remaining_tokens)
                            self.reference_date = old_ref
                            return result
            except Exception:
                pass
               
        # ------------------------------------------------------------------ 
        # 2) Basic “X Units Ago” Parsing
        # ------------------------------------------------------------------ 
        # Handles minimal expressions like: ["3", "days", "ago"]
        #
        # These are direct and require no reanchoring or nested scopes.
        # If pattern matches:
        #   • token[0] must be a number → quantity
        #   • token[1] must be a valid time unit (e.g. day, week, month)
        #   • token[2] must be "ago"
        #
        # It computes the offset backward from today using _compute_ago_expression()
        #
        # Example:
        #     ["5", "days", "ago"] → today - 5 days
        #
        # Note: This branch runs after the extended AGO handler (step 1),
        # and acts as a simpler fallback.
        if "ago" in tokens:
            if (
                len(tokens) == 3
                and tokens[0].isdigit()
                and tokens[2] == "ago"
            ):
                quantity = int(tokens[0])
                subunit  = tokens[1]
                return _compute_ago_expression(quantity, subunit)

        # ------------------------------------------------------------------ 
        # 3) Resolve Single-Token Relative Days (e.g., Today, Tomorrow)
        # ------------------------------------------------------------------ 
        # Captures one-word expressions that refer to self-evident relative dates.
        #
        # These tokens are stored in `self.immediate_relative_days`, which maps:
        #   "today"    → reference_date
        #   "tomorrow" → reference_date + 1 day
        #   "yesterday"→ reference_date - 1 day
        #
        # This is the simplest path: a 1-token phrase that requires no range
        # analysis or deeper structural logic.
        #
        # Example:
        #     ["today"] → returns today’s date as `datetime.date`
        if len(tokens) == 1:
            word = tokens[0]
            if word in self.immediate_relative_days:
                return self.immediate_relative_days[word](self.reference_date)

        # ------------------------------------------------------------------ 
        # 4) Ordinal Subunit Range Within Scoped Period
        # ------------------------------------------------------------------ 
        # Captures phrases like “1st 5 days of next month” where:
        #     - an ordinal rank is applied (e.g., 1st, 2nd, last, middle)
        #     - to a quantity of a unit (e.g., 5 days)
        #     - within a directional scope (e.g., next month)
        #
        # These phrases mean: “the first N <subunit>s inside the specified scope”
        # and return a slice from a list of subunit groupings inside the scope.
        #
        # Example:
        #     ["1st", "5", "day", "next", "month"] → May 1–5
        #
        # This also supports:
        #     - ["last", "2", "week", "this", "year"]
        #     - ["middle", "3", "day", "next", "week"]
        #     - ["2nd", "1", "month", "next", "quarter"]
        if (
            len(tokens) == 5
            and self._is_ordinal(tokens[0])       
            and tokens[1].isdigit()               
            and tokens[2] in self.TimeUnits       
            and tokens[3] in ["this", "next", "last"]
        ):
            ordinal_pos = self._ordinal_value(tokens[0]) 
            quantity    = int(tokens[1])                  
            subunit     = tokens[2]
            direction   = tokens[3]
            scope       = tokens[4]

            scope_range = self.compute([direction, scope])
            if not scope_range:
                return None
            if isinstance(scope_range, tuple):
                r_start, r_end = scope_range
            else:
                r_start = r_end = scope_range

            return _first_last_middle_n_subunits_in_range(
                ordinal_pos, quantity, subunit, r_start, r_end
            )

        # ------------------------------------------------------------------ 
        # 5) Nth Subunit Inside a Temporal Scope
        # ------------------------------------------------------------------ 
        # Handles expressions like “2nd Friday next month” or “3 day this week”.
        #
        # Pattern:
        #     [ordinal_or_digit, subunit, direction, scope]
        #
        # This structure is interpreted as: “Find the Nth <subunit> in the specified scope”.
        # It works whether N is written as a digit ("3") or ordinal ("3rd").
        #
        # Examples:
        #     ["2nd", "friday", "next", "month"] → 2nd Friday of next month
        #     ["3", "day", "this", "week"]       → 3rd day of this week
        #
        # Returns a date or subunit range based on its position within the computed scope.
        if len(tokens) == 4:
            qty_tok, subunit, direction, scope = tokens
            if (
                direction in ["this", "next", "last"]
                and (qty_tok.isdigit() or self._is_ordinal(qty_tok))
            ):
                quantity = (
                    int(qty_tok) if qty_tok.isdigit()
                    else self._ordinal_value(qty_tok)
                )
                return _compute_ordinal_expression(
                    quantity,
                    subunit.lower(),
                    direction.lower(),
                    scope.lower()
                )

        # ------------------------------------------------------------------ 
        # 6) Positional Subunit Selection Within a Named Period
        # ------------------------------------------------------------------ 
        # Resolves expressions that ask for a positional segment of subunits
        # within a directional named period, such as:
        #     • "start week last month"
        #     • "middle day next season"
        #
        # Pattern:
        #     [position, subunit, direction, scope]
        #
        # Semantics:
        #     - Compute the full range of the [direction, scope] (e.g., "last month")
        #     - Slice all occurrences of <subunit> within that range (e.g., weeks)
        #     - Return the one located at the specified <position>:
        #           - "start"  → first match
        #           - "middle" → center match
        #           - "end"    → last match
        #
        # This is useful for phrases like "start of the week in last month" → first week inside last month.
        if (
            len(tokens) == 4
            and tokens[0] in ["start", "middle", "end"]
            and tokens[1] in self.TimeUnits
            and tokens[2] in ["this", "next", "last"]
        ):
            position  = tokens[0]   # start / middle / end
            subunit   = tokens[1]   # day / week / month / …
            direction = tokens[2]   # this / next / last
            scope     = tokens[3]   # month / year / summer …

            scope_range = self.compute([direction, scope])
            if not scope_range:
                return None
            if isinstance(scope_range, tuple):
                r_start, r_end = scope_range
            else:
                r_start = r_end = scope_range

            return _range_position_within_scope(
                position, subunit, r_start, r_end
            )

        # ------------------------------------------------------------------ 
        # 7) Resolve “Last X of Y” Constructs
        # ------------------------------------------------------------------ 
        # Handles phrases that describe the final occurrence of a subunit within
        # a larger temporal scope, such as:
        #     • "last day of April"
        #     • "last Monday of this month"
        #
        # Pattern logic:
        #     - Must match: ["last", <subunit>, "of", ...]
        #     - Extract the scope tokens after "of" (e.g., ["april"])
        #     - Recursively compute the date range for that scope
        #
        # Resolution:
        #     - Once the range is known (e.g., April 1–30),
        #       locate the final instance of <subunit> within it
        #       using `_compute_final_subunit_in_range`.
        #
        # Example:
        #     ["last", "Monday", "of", "April"] → April 28 (if that's the last Monday)
        if "last" in tokens and "of" in tokens:
            idx_last = tokens.index("last")
            idx_of   = tokens.index("of")

            if idx_of == idx_last + 2 and (idx_of + 1) < len(tokens):
                subunit = tokens[idx_last + 1]
                scope_tokens = tokens[idx_of + 1:]

                scope_range = self.compute(scope_tokens)
                if scope_range and isinstance(scope_range, tuple) and len(scope_range) == 2:
                    r_start, r_end = scope_range
                    return _compute_final_subunit_in_range(subunit, r_start, r_end)
                return None

        # ------------------------------------------------------------------ 
        # 8) Parse Anchored Expressions Using “Starting From”
        # ------------------------------------------------------------------ 
        # Handles temporal expressions that explicitly define a custom anchor point
        # from which a time span begins. These take the form:
        #     • "next 6 months starting from April 1"
        #     • "3 weekends starting from next Saturday"
        #
        # Pattern:
        #     - Must include both "starting" and "from"
        #     - The left of "starting" is the outer time expression (e.g., "next 6 months")
        #     - The right of "from" is the custom start date (e.g., "April 1")
        #
        # Resolution steps:
        #     1. Parse the anchor date using `_compute_starting_point()`
        #     2. Temporarily override the resolver’s reference date
        #     3. Recompute the outer time expression from that reference
        #     4. Reanchor the resulting date/range to begin from the original "from" date
        #
        # Example:
        #     ["next", "6", "months", "starting", "from", "april", "1"]
        #     → returns (2025-04-01, 2025-09-30)
        if "starting" in tokens and "from" in tokens:
            return _compute_starting_from_expression(tokens)

        # ------------------------------------------------------------------ 
        # 9) Unit-Aligned Date Ranges (e.g., Week of April 3)
        # ------------------------------------------------------------------ 
        # Handles simple expressions that describe a calendar unit anchored to a
        # specific date-like token, such as:
        #     • "week of April 3"
        #     • "month of July"
        #     • "quarter of April 5"
        #
        # Pattern:
        #     - Exactly 3 tokens: [<unit>, "of", <date-part>]
        #     - <unit> is one of: "week", "month", "quarter", "season"
        #     - <date-part> can be a month name, month+day combo, etc.
        #
        # Resolution:
        #     - The `date_candidate` is parsed from the final token(s)
        #     - The <unit> is then aligned to that reference:
        #         "week"     → 7-day span starting that week
        #         "month"    → full calendar month containing the date
        #         "quarter"  → quarter that contains the date
        #         "season"   → season that contains the date
        #
        # Example:
        #     ["month", "of", "july"] → (2025-07-01, 2025-07-31)
        if len(tokens) == 3 and tokens[1] == "of":
            unit = tokens[0]
            date_str = ' '.join(tokens[2:])
            date_candidate = self._parse_date_from_string(date_str)

            if date_candidate and isinstance(date_candidate, d):
                if unit == "week":
                    start = self._add_weeks(date_candidate, 0)
                    return (start, start + td(days=6))
                elif unit == "month":
                    start = d(date_candidate.year, date_candidate.month, 1)
                    end   = self._add_months(start, 1) - td(days=1)
                    return (start, end)
                elif unit == "quarter":
                    quarter = self._determine_current_quarter(date_candidate)
                    info = timeline.adj_quarters()[quarter]
                    sm, sd = map(int, info["start"].split("/"))
                    em, ed = map(int, info["end"].split("/"))
                    return (d(date_candidate.year, sm, sd),
                            d(date_candidate.year, em, ed))
                elif unit == "season":
                    season, yr = self._determine_current_season(
                        date_candidate, include_year=True
                    )
                    info = timeline.adj_seasons(
                        season=season, year=yr, include_year=True
                    )
                    return (
                        dt.strptime(info["start"], "%m/%d/%Y").date(),
                        dt.strptime(info["end"], "%m/%d/%Y").date()
                    )
                    
        # ------------------------------------------------------------------ 
        # 10) Scoped Quantity of Subunits Within a Named Period
        # ------------------------------------------------------------------ 
        # Resolves expressions that specify *how many* of a subunit to pull from 
        # a broader named time span.
        #
        # Pattern:
        #     [direction, quantity, subunit, scope_direction, named_period]
        #     → e.g., ["next", "5", "days", "this", "month"]
        #
        # Meaning:
        #     → "Give me the *next 5 days* within *this month*"
        #     → "Take the given quantity of subunits from a scoped range"
        #
        # Components:
        #     • direction       – next / last (defines pull direction inside range)
        #     • quantity        – number of subunits to retrieve
        #     • subunit         – day, week, etc.
        #     • scope_direction – this / next / last (defines the range window)
        #     • named_period    – month / season / quarter / year / etc.
        #
        # Example:
        #     ["last", "2", "weeks", "next", "season"]
        #     → Pull the last 2 weeks of next season
        if (
            len(tokens) == 5
            and tokens[0] in ["next", "last"]
            and tokens[1].isdigit()
            and tokens[3] in ["this", "next", "last"]
        ):
            direction       = tokens[0]
            quantity        = int(tokens[1])
            subunit         = tokens[2]
            scope_direction = tokens[3]
            named_period    = tokens[4]
            return _compute_named_repetitions_in_namedperiod(
                direction, quantity, subunit, scope_direction, named_period
            )

        # ------------------------------------------------------------------ 
        # 11) Position-Based Lookup Within a Time Unit
        # ------------------------------------------------------------------ 
        # Captures expressions that refer to the *position* within a larger temporal unit.
        #
        # Pattern:
        #     [position, direction, time_unit]
        #     → e.g., ["start", "next", "month"]
        #
        # Meaning:
        #     → "Give me the beginning of next month"
        #
        # Components:
        #     • position   – start / middle / end
        #     • direction  – this / next / last
        #     • time_unit  – day / week / month / quarter / year / season
        #
        # This returns either the first subunit (start), the midpoint (middle),
        # or the final subunit (end) of the resolved range.
        if (
            len(tokens) == 3
            and tokens[0] in ["start", "middle", "end"]
            and tokens[1] in ["this", "next", "last"]
        ):
            position      = tokens[0]
            direction     = tokens[1]
            time_unit_str = tokens[2]
            return _compute_range_position(position, direction, time_unit_str)
           
        # ------------------------------------------------------------------           
        # 12) Named Unit Within Larger Scoped Unit
        # ------------------------------------------------------------------ 
        # Captures expressions like "january next year", "friday this week", etc.
        #
        # Pattern:
        #     [named, direction, big_unit]
        #     → e.g., ["january", "next", "year"]
        #
        # Meaning:
        #     → "Find the named unit inside the resolved larger unit"
        #
        # Example Interpretations:
        #     • "march next year" → the range for March in the upcoming year
        #     • "summer this year" → the summer period this year
        #     • "friday this week" → the upcoming Friday in the current week
        #
        # Requirements:
        #     • direction must be: this / next / last
        #     • big_unit must be a supported literal time-unit
        #     • named must be resolvable: a weekday, month, season, or quarter
        if len(tokens) == 3:
            named     = tokens[0]
            direction = tokens[1]
            big_unit  = tokens[2]
            if (
                direction in ["this", "next", "last"]
                and big_unit in self.TimeUnits
                and (named in timeline.months
                     or named in self.Days
                     or named in self.Seasons
                     or named in self.Quarters)
            ):
                return _compute_named_of_timeunit(named, direction, big_unit)
               
        # ------------------------------------------------------------------
        # 13) Repeated Named Units (e.g., Next 3 Fridays)
        # ------------------------------------------------------------------
        # Handles pluralized recurrence patterns like:
        #     "next 3 mondays", "last 2 summers", "next 4 q1s", etc.
        #
        # Pattern:
        #     [direction, quantity, named_unit]
        #
        # Meaning:
        #     → Generate `quantity` consecutive instances of `named_unit` in the given `direction`
        #
        # Supported named_units:
        #     • weekdays: e.g., "friday"
        #     • months:   e.g., "january"
        #     • seasons:  e.g., "spring"
        #     • quarters: e.g., "q1"
        #
        # Example:
        #     • ["next", "3", "fridays"] → next 3 fridays from today
        #     • ["last", "2", "summers"] → most recent 2 summer periods
        if (
            len(tokens) == 3
            and tokens[0] in ["next", "last"]
            and tokens[1].isdigit()
        ):
            named_unit = tokens[2]
            if (
                named_unit in self.Days
                or named_unit in timeline.months
                or named_unit in self.Seasons
                or named_unit in self.Quarters
            ):
                return _compute_named_repetitions(
                    tokens[0], int(tokens[1]), named_unit
                )
                
        # ------------------------------------------------------------------
        # 14) Compound Scoped Subunit Expressions
        # ------------------------------------------------------------------
        # Handles deeper compound patterns that represent scoped subunits:
        #     • "next day april"
        #     • "last week this month"
        #     • "this weekday next summer"
        #
        # Pattern:
        #     direction subunit (optional direction) named_period
        #         → ["last", "week", "this", "month"]
        #
        # Key logic:
        #     • The leading `direction` modifies the subunit.
        #     • The optional 2nd `direction` modifies the scope.
        #     • The scope (e.g. "april", "summer") is always at the end.
        #
        # Behavior:
        #     → Find the N-th or scoped occurrence of the subunit (e.g. "day", "week", "weekday")
        #        inside a resolved named period like a month, season, or quarter.
        #
        # Example:
        #     ["next", "monday", "of", "june"] would match this but likely appear earlier.
        #     ["last", "week", "this", "month"] → final week inside this month
        if (
            len(tokens) >= 3
            and tokens[0] in ["next", "last", "this"]
            and not tokens[1].isdigit()
        ):
            direction = tokens[0]
            subunit   = tokens[1]

            if len(tokens) == 3:
                named_period    = tokens[2]
                scope_direction = None
            elif len(tokens) == 4:
                third = tokens[2]
                named_period    = tokens[3]
                scope_direction = third if third in ["this", "next", "last"] else None
            else:
                scope_direction = None
                named_period    = tokens[-1]

            return _compute_subunit_of_namedperiod(
                direction, subunit, scope_direction, named_period
            )

        # ------------------------------------------------------------------
        # 15) Direction + Unit/Naming Fallback Handler
        # ------------------------------------------------------------------
        # Final resolution layer for phrases like:
        #     - "next month"
        #     - "this season"
        #     - "last weekend"
        #     - "next q1"
        #     - "this january"
        #     - "last friday"
        #
        # Behavior:
        #     • Resolves a direction + single token (unit or named scope).
        #     • If direction is omitted (e.g., just "january"), it defaults to "this".
        #
        # Covers:
        #     • Literal time units: "month", "season", "quarter", "week", "year", "weekend"
        #     • Named subunits: months (e.g. "april"), weekdays (e.g. "monday"),
        #       seasons (e.g. "summer"), quarters (e.g. "q2")
        #
        # This fallback is triggered when no higher-level structure matched the input.
        #
        # Example:
        #     ["next", "month"]   → (start, end) of next month
        #     ["fall"]            → treated as ["this", "fall"]
        #     ["previous", "friday"] → fallback to previous occurrence of Friday
        direction   = None
        main_token  = None

        if tokens[0] in ["next", "last", "this", "previous"]:
            direction  = tokens[0]
            main_token = tokens[1] if len(tokens) > 1 else None
        else:
            direction  = "this"
            main_token = tokens[0]

        # Literal units: "next month", "last season", etc.
        if main_token == "month":
            base = self.reference_date
            if direction == "next":
                target_month = base.month + 1
                target_year = base.year
                if target_month > 12:
                    target_month = 1
                    target_year += 1
            elif direction == "last":
                target_month = base.month - 1
                target_year = base.year
                if target_month < 1:
                    target_month = 12
                    target_year -= 1
            else:  # "this"
                target_month = base.month
                target_year = base.year
            month_names = list(timeline.months.index.keys())
            month_name = month_names[target_month - 1]
            month_info = timeline.adj_months(m=month_name, year=target_year)
            start_mm, start_dd = map(int, month_info["start"].split("/"))
            end_mm, end_dd = map(int, month_info["end"].split("/"))
            return (d(target_year, start_mm, start_dd), d(target_year, end_mm, end_dd))

        if main_token == "season":
            base = self.reference_date
            current_season = self._determine_current_season(base)
            idx = self.SeasonsOrdered.index(current_season)
            if direction == "next":
                idx = (idx + 1) % 4
                target_year = base.year if current_season != "fall" else base.year + 1
            elif direction == "last":
                idx = (idx - 1) % 4
                target_year = base.year if current_season != "winter" else base.year - 1
            else:  # "this"
                target_year = base.year
            target_season = self.SeasonsOrdered[idx]
            season_info = self._get_season_boundaries(target_season, target_year)
            start_mm, start_dd, start_year = map(int, season_info["start"].split("/"))
            end_mm, end_dd, end_year = map(int, season_info["end"].split("/"))
            return (d(start_year, start_mm, start_dd), d(end_year, end_mm, end_dd))

        if main_token == "quarter":
            base = self.reference_date
            current_quarter = self._determine_current_quarter(base)
            idx = self.QuartersOrdered.index(current_quarter)
            if direction == "next":
                idx = (idx + 1) % 4
                target_year = base.year if current_quarter != "q4" else base.year + 1
            elif direction == "last":
                idx = (idx - 1) % 4
                target_year = base.year if current_quarter != "q1" else base.year - 1
            else:  # "this"
                target_year = base.year
            target_quarter = self.QuartersOrdered[idx]
            quarter_info = timeline.adj_quarters()[target_quarter]
            start_mm, start_dd = map(int, quarter_info["start"].split("/"))
            end_mm, end_dd = map(int, quarter_info["end"].split("/"))
            return (d(target_year, start_mm, start_dd), d(target_year, end_mm, end_dd))

        if main_token == "week":
            base = self.reference_date
            if direction == "next":
                start_of_next_week = self._add_weeks(base, 1)
                end_of_next_week = start_of_next_week + td(days=6)
                return (start_of_next_week, end_of_next_week)
            elif direction == "last":
                start_of_last_week = self._add_weeks(base, -1)
                end_of_last_week = start_of_last_week + td(days=6)
                return (start_of_last_week, end_of_last_week)
            elif direction == "this":
                start_of_this_week = self._add_weeks(base, 0)
                end_of_this_week = start_of_this_week + td(days=6)
                return (start_of_this_week, end_of_this_week)

        if main_token == "weekend":
            base = self.reference_date
            weekend_start_idx = 5  # Saturday
            weekend_start = base + td((weekend_start_idx - base.weekday()) % 7)
            weekend_end = weekend_start + td(days=1)
            if direction == "this":
                if base <= weekend_end:
                    return (weekend_start, weekend_end)
                else:
                    weekend_start += td(weeks=1)
                    weekend_end += td(weeks=1)
                    return (weekend_start, weekend_end)
            elif direction == "next":
                weekend_start += td(weeks=1)
                weekend_end += td(weeks=1)
                return (weekend_start, weekend_end)
            elif direction == "last":
                weekend_start -= td(weeks=1)
                weekend_end -= td(weeks=1)
                return (weekend_start, weekend_end)

        if main_token == "year":
            return _compute_specific_year(direction)

        if main_token in self.Quarters :
            quarter_key = self.Quarters [main_token]
            return _compute_specific_quarter(direction, quarter_key)

        if main_token in self.Seasons:
            season_name = self.Seasons[main_token]
            return _compute_specific_season(direction, season_name)

        if main_token in self.Days:
            weekday = self.Days[main_token]
            return _compute_specific_weekday(direction, weekday)

        if main_token in timeline.months:
            month_name = timeline.months[main_token]
            return _compute_specific_month(direction, month_name)        

        # ------------------------------------------------------------------
        # 16) Arithmetic-Based Fallback for Quantified Durations
        # ------------------------------------------------------------------
        # Final safety net for phrases that contain numeric time values but didn’t
        # match any earlier explicit structure rules.
        #
        # Examples:
        #     • ["5", "weeks"]
        #     • ["2", "months"]
        #     • ["12", "days"]
        #
        # This logic checks if *any* token is a digit and *any* other token is a
        # known time unit. If so, it invokes `_compute_arithmetic()` to infer
        # a default directional resolution.
        #
        # Defaults:
        #     - Direction is assumed to be "this" if not stated.
        #     - Unit boundaries are used to determine the appropriate range span.
        #
        # If no valid pattern is detected, or if an exception is thrown,
        # the function returns `None`.
        try:
            if any(t.isdigit() for t in tokens) and any(t in self.TimeUnits for t in tokens):
                return self._compute_arithmetic(tokens)
            else:
                return None
        except Exception:
            return None





# ──────────────────────────────────────────────────────────────────────────────
# Temporal Subunit Computation Layer
# ──────────────────────────────────────────────────────────────────────────────
# 
# The following defines the internal logic used to compute specific temporal 
# subunits—such as weekdays, months, seasons, quarters, or custom spans—
# from natural language expressions like:
# 
#     - "next 2 Fridays"
#     - "last 3 seasons"
#     - "first weekend of next month"
#     - "middle week of this quarter"
#     - "3rd Monday in July"
#     - "2 weeks starting from May 1"
# 
# It serves as the computational engine for resolving **structural temporal 
# patterns**, after token parsing and grammar recognition are complete.
# 
# Core Responsibilities
# ──────────────────────────────────────────────────────────────────────────────
# • Interpret and resolve tokens like “next 3 months” or “last 2 weekends”.
# • Normalize expressions that refer to subunits within named periods:
#     - e.g. “1st Monday of next month”
#     - e.g. “middle week of this quarter”
# • Support iterative unit extraction (e.g. "next 4 seasons").
# • Handle complex relative expressions involving scope + direction + subunit.
# • Perform contextual anchoring based on a live reference date.
# • Use structured timeline data (calendar logic) for boundaries and validation.
# 
# Why it Exists
# ──────────────────────────────────────────────────────────────────────────────
# Natural-language temporal expressions often contain hierarchical structure—
# for example: “2nd week of April” requires:
#     → computing the range for April
#     → locating the second "week" within that range
# 
# This layer provides **precision control** over such date-bound substructures,
# including:
#     - Cardinal/ordinal unit location ("3rd", "last")
#     - Named units inside named periods ("March", "Friday", "Q2")
#     - Implicit or computed ranges ("this year", "next weekend")
# 
# Return Values
# ──────────────────────────────────────────────────────────────────────────────
# Each function returns one of:
#     • `datetime.date` — for day-specific targets
#     • `(start_date, end_date)` — for unit spans (weeks, months, etc.)
#     • `list[date or tuple]` — when resolving multiple repetitions
#     • `None` — if resolution fails or is out of scope
# 
# All computations are anchored on `resolver.reference_date`, which can be 
# temporarily shifted to accommodate contextual phrases like 
# “starting from March 15”.
def _compute_named_repetitions(direction, quantity, named_unit):
    results = []
    temp_ref = resolver.reference_date
    if named_unit == "season":
        current_season, current_year = resolver._determine_current_season(temp_ref, include_year=True)  # Added        
        index = resolver.SeasonsOrdered.index(current_season)
        step = 1 if direction == "next" else -1
        count = 0
        while count < quantity:
            index = (index + step) % 4
            if direction == "next" and index == 0:
                current_year += 1
            elif direction == "last" and index == 3:
                current_year -= 1
            season = resolver.SeasonsOrdered[index]
            info = timeline.adj_seasons(season=season, year=current_year, include_year=True)
            start = dt.strptime(info["start"], "%m/%d/%Y").date()
            end = dt.strptime(info["end"], "%m/%d/%Y").date()
            results.append((start, end))
            count += 1
        return results if quantity > 1 else results[0]

    if named_unit == "quarter":
        current_quarter = resolver._determine_current_quarter(temp_ref)
        current_year = temp_ref.year
        index = resolver.QuartersOrdered.index(current_quarter)
        step = 1 if direction == "next" else -1
        count = 0
        while count < quantity:
            index = (index + step) % 4
            if direction == "next" and index == 0:
                current_year += 1
            elif direction == "last" and index == 3:
                current_year -= 1
            quarter_key = resolver.QuartersOrdered[index]
            info = timeline.adj_quarters()[quarter_key]
            start_mm, start_dd = map(int, info["start"].split("/"))
            end_mm, end_dd = map(int, info["end"].split("/"))
            start = d(current_year, start_mm, start_dd)
            end = d(current_year, end_mm, end_dd)
            results.append((start, end))
            count += 1
        return results if quantity > 1 else results[0]

    if named_unit == "month":
        temp = resolver.reference_date
        count = 0
        step = 1 if direction == "next" else -1
        while count < quantity:
            temp = resolver._add_months(temp, step)
            current_year = temp.year
            current_month = temp.month
            month_name = timeline.months.index[current_month].lower()            
            info = timeline.adj_months(month_name, current_year)
            start_mm, start_dd = map(int, info["start"].split("/"))
            end_mm, end_dd = map(int, info["end"].split("/"))
            start = d(current_year, start_mm, start_dd)
            end = d(current_year, end_mm, end_dd)
            results.append((start, end))
            count += 1
        return results if quantity > 1 else results[0]
       
    if named_unit == "year":
        current_year = resolver.reference_date.year
        step = 1 if direction == "next" else -1
        count = 0
        results = []
        while count < quantity:
            current_year += step
            results.append((d(current_year, 1, 1), d(current_year, 12, 31)))
            count += 1
        return results if quantity > 1 else results[0]

    temp_ref = resolver.reference_date
    for _ in range(quantity):
        old_ref = resolver.reference_date
        resolver.reference_date = temp_ref

        if named_unit in resolver.Days:
            weekday = resolver.Days[named_unit]
            result = _compute_specific_weekday(direction, weekday)
        elif named_unit in timeline.months:
            month_name = timeline.months[named_unit]
            result = _compute_specific_month(direction, month_name)
        elif named_unit in resolver.Seasons:
            season_name = resolver.Seasons[named_unit]
            result = _compute_specific_season(direction, season_name)
        elif named_unit in resolver.Quarters:
            quarter_key = resolver.Quarters[named_unit]
            result = _compute_specific_quarter(direction, quarter_key)
        elif named_unit == "weekend":
            result = _compute_specific_weekend(direction)
        else:
            result = None
        if not result:
            resolver.reference_date = old_ref
            return results if results else None
        results.append(result)
        if isinstance(result, tuple):
            end_date = result[1]
            temp_ref = end_date + td(days=1) if direction == "next" else result[0] - td(days=1)
        else:
            temp_ref = result + td(days=1) if direction == "next" else result - td(days=1)
        resolver.reference_date = old_ref
    return results if quantity > 1 else results[0]

def _compute_named_repetitions_in_namedperiod(direction, quantity, subunit, scope_direction, named_period):
    if scope_direction:
        big_expr = [scope_direction, named_period]
    else:
        big_expr = [named_period]
    big_result = resolver.compute(big_expr)
    if not big_result:
        return None
    if isinstance(big_result, tuple) and len(big_result) == 2:
        range_start, range_end = big_result
    else:
        range_start = big_result
        range_end = big_result
    results = []
    if direction == "next":
        cursor = range_start
        for _ in range(quantity):
            item = _find_next_subunit_in_scope(subunit, cursor, range_end)
            if not item:
                break
            results.append(item)
            if isinstance(item, tuple):
                end_date = item[1]
                cursor = end_date + td(days=1)
            else:
                cursor = item + td(days=1)
            if cursor > range_end:
                break
    elif direction == "last":
        cursor = range_end
        for _ in range(quantity):
            item = _find_last_subunit_in_scope(subunit, range_start, cursor)
            if not item:
                break
            results.append(item)
            if isinstance(item, tuple):
                start_date = item[0]
                cursor = start_date - td(days=1)
            else:
                cursor = item - td(days=1)
            if cursor < range_start:
                break
        results.reverse()  # Ensures oldest-to-newest order    
    else:
        item = _find_this_subunit_in_scope(subunit, range_start, range_end)
        if item:
            results.append(item)
    return results if results else None       

def _compute_named_of_timeunit(named, direction, big_unit):
    big_range = resolver.compute([direction, big_unit])
    if not big_range or not isinstance(big_range, tuple):
        return None
    range_start, range_end = big_range

    if named in resolver.Quarters:
        quarter_key = resolver.Quarters[named]
        return _compute_specific_quarter(direction, quarter_key)    
    
    if named == "day":
        return _compute_sub_day_in_range(big_unit, range_start, range_end)
       
    if named in timeline.months:
        return _compute_sub_month_in_range(named, range_start, range_end)
    elif named in resolver.Days:
        return _compute_sub_weekday_in_range(named, range_start, range_end)
    elif named in resolver.Seasons:
        return _compute_sub_season_in_range(named, range_start, range_end)
    return None

def _find_next_subunit_in_scope(subunit, start_cursor, range_end):
    if subunit in resolver.Days:
        target_idx = timeline.days.index[subunit.lower()]
        cursor = start_cursor
        while cursor <= range_end:
            if cursor.weekday() == target_idx:
                return cursor
            cursor += td(days=1)
        return None
    elif subunit == "day":
        if start_cursor <= range_end:
            return start_cursor
        return None
    elif subunit == "week":
        start_of_week = resolver._add_weeks(start_cursor, 0)
        end_of_week = start_of_week + td(days=6)
        if end_of_week <= range_end:
            return (start_of_week, end_of_week)
        return None
    elif subunit == "month":
        start_of_month = resolver._add_months(start_cursor, 0)
        end_of_month = resolver._add_months(start_of_month, 1) - td(days=1)
        if end_of_month <= range_end:
            return (start_of_month, end_of_month)
        return None
    elif subunit == "quarter":
        current_q = resolver._determine_current_quarter(start_cursor)
        idx = resolver.QuartersOrdered.index(current_q)
        q_key = resolver.QuartersOrdered[idx]
        q_info = timeline.adj_quarters()[q_key]
        start_mm, start_dd = map(int, q_info["start"].split("/"))
        end_mm, end_dd = map(int, q_info["end"].split("/"))

        start_of_q = d(start_cursor.year, start_mm, start_dd)
        end_of_q = d(start_cursor.year, end_mm, end_dd)
        if end_of_q <= range_end:
            return (start_of_q, end_of_q)
        return None
    elif subunit == "season":
        current_season = resolver._determine_current_season(start_cursor)
        season_info = resolver._get_season_boundaries(current_season, start_cursor.year)
        start = resolver._parse_date(season_info["start"])
        end = resolver._parse_date(season_info["end"])
        if end <= range_end:
            return (start, end)
        return None
    return None
   
def _find_last_subunit_in_scope(subunit, range_start, end_cursor):
    if end_cursor < range_start:
        return None
    if subunit in resolver.Days:
        w_idx = timeline.days.index[subunit.lower()]
        cursor = end_cursor
        while cursor >= range_start:
            if cursor.weekday() == w_idx:
                return cursor
            cursor -= td(days=1)
        return None
    elif subunit == "day":
        if end_cursor >= range_start:
            return end_cursor
        return None
    elif subunit == "week":
        start_of_week = end_cursor - td(days=6)
        if start_of_week >= range_start:
            return (start_of_week, end_cursor)
        return None
    elif subunit == "month":
        start_of_month = d(end_cursor.year, end_cursor.month, 1)
        if start_of_month < range_start:
            return None
        real_end_day = timeline.days_in_month(end_cursor.month, end_cursor.year).d        
        end_of_month = d(end_cursor.year, end_cursor.month, real_end_day)
        if end_of_month > end_cursor:
            end_of_month = end_cursor
        return (start_of_month, end_of_month)
    elif subunit == "quarter":
        current_quarter = resolver._determine_current_quarter(end_cursor)
        q_info = timeline.adj_quarters()[current_quarter]
        start_mm, start_dd = map(int, q_info["start"].split("/"))
        end_mm, end_dd = map(int, q_info["end"].split("/"))
        start_of_q = d(end_cursor.year, start_mm, start_dd)
        end_of_q = d(end_cursor.year, end_mm, end_dd)
        if end_of_q > end_cursor:
            end_of_q = end_cursor
        if start_of_q < range_start:
            return None
        return (start_of_q, end_of_q)
    elif subunit == "season":
        current_season = resolver._determine_current_season(end_cursor)
        season_info = resolver._get_season_boundaries(current_season, end_cursor.year)
        start_s = resolver._parse_date(season_info["start"])
        end_s = resolver._parse_date(season_info["end"])
        if end_s > end_cursor:
            end_s = end_cursor
        if start_s < range_start:
            return None
        return (start_s, end_s)
    return None
   
def _first_last_middle_n_subunits_in_range(ordinal_pos, qty, subunit, r_start, r_end):
    if subunit == "half":
        mid = r_start + (r_end - r_start) // 2
        halves = [
            (r_start, mid),              
            (mid + td(days=1), r_end)  
        ]
        idx = 0 if ordinal_pos in (1, 0) else 1
        if qty > 1 or idx >= len(halves):
            return None
        return halves[idx]

    bucket = []
    cursor = r_start
    while cursor <= r_end:
        item = _find_next_subunit_in_scope(subunit, cursor, r_end)
        if not item:
            break
        bucket.append(item)
        # Advance cursor beyond this item
        cursor = (
            item[1] + td(days=1) if isinstance(item, tuple)
            else item + td(days=1)
        )

    if not bucket:
        return None

    # Determine slice start index based on ordinal_pos
    if ordinal_pos == -1:        # last
        start_idx = len(bucket) - qty
    elif ordinal_pos == 0:       # middle
        mid = len(bucket) // 2
        start_idx = max(0, mid - qty // 2)
    else:                        # 1st / 2nd / 3rd …
        start_idx = ordinal_pos - 1

    end_idx = start_idx + qty
    if start_idx < 0 or end_idx > len(bucket):
        return None

    slice_ = bucket[start_idx:end_idx]
    return slice_[0] if qty == 1 else slice_
   
def _range_position_within_scope(position, subunit, r_start, r_end):
    bucket = []
    cursor = r_start
    while cursor <= r_end:
        item = _find_next_subunit_in_scope(subunit, cursor, r_end)
        if not item:
            break
        bucket.append(item)
        cursor = (item[1] + td(days=1)) if isinstance(item, tuple) else item + td(days=1)

    if not bucket:
        return None

    if position == "start":
        return bucket[0]
    if position == "end":
        return bucket[-1]
    if position == "middle":
        mid = len(bucket) // 2
        return bucket[mid]

    return None
   
def _compute_ordinal_expression(quantity, subunit, direction, scope):
    big_expr = [direction, scope]
    big_result = resolver.compute(big_expr)
    if not big_result:
        return None
    if isinstance(big_result, tuple) and len(big_result) == 2:
        range_start, range_end = big_result
    else:
        range_start = big_result
        range_end = big_result
    return _compute_nth_subunit_in_range(quantity, subunit, range_start, range_end)

def _compute_nth_subunit_in_range(n, subunit, range_start, range_end):
    if subunit in resolver.Days:
        return _get_nth_weekday_in_range(n, subunit, range_start, range_end)
    elif subunit == "day":
        return _get_nth_day_in_range(n, range_start, range_end)
    elif subunit == "week":
        return _get_nth_week_in_range(n, range_start, range_end)
    elif subunit == "month":
        return _get_nth_month_in_range(n, range_start, range_end)
    elif subunit == "season":
        return _get_nth_season_in_range(n, range_start, range_end)
    elif subunit == "quarter":
        return _get_nth_quarter_in_range(n, range_start, range_end)
    return None

def _get_nth_weekday_in_range(n, weekday_token, range_start, range_end):
    if range_start > range_end:
        return None
    weekday_idx = timeline.days.index[weekday_token.lower()]
    found_count = 0
    cursor = range_start
    while cursor <= range_end:
        if cursor.weekday() == weekday_idx:
            found_count += 1
            if found_count == n:
                return cursor
        cursor += td(days=1)
    return None
   
def _get_nth_day_in_range(n, range_start, range_end):
    total_days = (range_end - range_start).days + 1
    if n > total_days:
        return None
    return range_start + td(days=(n - 1))
   
def _get_nth_week_in_range(n, range_start, range_end):
    start_of_nth = range_start + td(weeks=(n - 1))
    end_of_nth = start_of_nth + td(days=6)
    if end_of_nth > range_end:
        return None
    return (start_of_nth, end_of_nth)
   
def _get_nth_month_in_range(n, range_start, range_end):
    months = []
    cursor = d(range_start.year, range_start.month, 1)
    while cursor <= range_end:
        m_year, m_month = cursor.year, cursor.month
        month_info = timeline.adj_months(m=calendar.month_name[m_month], year=m_year)
        if not month_info:
            break
        mm_s, dd_s = map(int, month_info["start"].split("/"))
        mm_e, dd_e = map(int, month_info["end"].split("/"))
        start_m = d(m_year, mm_s, dd_s)
        end_m = d(m_year, mm_e, dd_e)
        if start_m < range_start:
            start_m = range_start
        if end_m > range_end:
            end_m = range_end
        if start_m <= range_end and end_m >= range_start:
            months.append((start_m, end_m))
        next_month = m_month + 1
        next_year = m_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        cursor = d(next_year, next_month, 1)
    if n > len(months):
        return None
    return months[n - 1]
   
def _compute_subunit_of_namedperiod(direction, subunit, scope_direction, named_period):
    if scope_direction:
        big_range = resolver.compute([scope_direction, named_period])
    else:
        big_range = resolver.compute([named_period])
    if not big_range:
        return None
    if isinstance(big_range, tuple) and len(big_range) == 2:
        scope_start, scope_end = big_range
    else:
        scope_start = big_range
        scope_end = big_range
    return _compute_subunit_in_range(direction, subunit, scope_start, scope_end)

def _compute_subunit_in_range(direction, subunit, scope_start, scope_end):
    if subunit in timeline.days:
        return _compute_specific_weekday_in_range(direction, subunit, scope_start, scope_end)
    elif subunit in {"week", "month", "day", "season", "quarter", "year"}:
        return _compute_specific_timeunit_in_range(direction, subunit, scope_start, scope_end)
    return None

def _compute_final_subunit_in_range(subunit, range_start, range_end):
    subunit = subunit.lower()
    if subunit in resolver.Days:
        return _find_last_weekday_in_range(subunit, range_start, range_end) # Final weekday in the range (e.g., last Friday of this month)

    elif subunit == "day":
        return range_end

    elif subunit == "week":
        end = range_end
        start = end - timedelta(days=6)
        if start >= range_start:
            return (start, end)
        else:
            return None

    elif subunit == "month":
        current = range_end.replace(day=1)
        while current >= range_start:
            month_info = timeline.adj_months(m=calendar.month_name[current.month].lower(), year=current.year)
            start_mm, start_dd = map(int, month_info["start"].split("/"))
            end_mm, end_dd = map(int, month_info["end"].split("/"))
            sub_start = date(current.year, start_mm, start_dd)
            sub_end = date(current.year, end_mm, end_dd)
            if sub_start >= range_start and sub_end <= range_end:
                return (sub_start, sub_end)
            current -= timedelta(days=1)
        return None

    elif subunit == "quarter":
        for offset in range(2):  # scan up to two years back
            year = range_end.year - offset
            for quarter in reversed(resolver.QuartersOrdered):
                info = timeline.adj_quarters()[quarter]
                sm, sd = map(int, info["start"].split("/"))
                em, ed = map(int, info["end"].split("/"))
                q_start = date(year, sm, sd)
                q_end = date(year, em, ed)
                if q_start >= range_start and q_end <= range_end:
                    return (q_start, q_end)
        return None

    elif subunit == "season":
        for offset in range(2):  # scan up to two years back
            year = range_end.year - offset
            for season in reversed(resolver.SeasonsOrdered):
                info = timeline.adj_seasons(season=season, year=year, include_year=True)
                s_start = datetime.strptime(info["start"], "%m/%d/%Y").date()
                s_end = datetime.strptime(info["end"], "%m/%d/%Y").date()
                if s_start >= range_start and s_end <= range_end:
                    return (s_start, s_end)
        return None
    return None

def _compute_specific_weekday(direction, weekday):
    base = resolver.reference_date
    current_idx = base.weekday()
    target_idx = timeline.days.index[weekday.lower()]

    if direction == "this":
        start_of_week = resolver._add_weeks(base, 0)
        offset = (target_idx - start_of_week.weekday()) % 7
        return start_of_week + td(days=offset)

    elif direction == "last":
        delta = (current_idx - target_idx)
        if delta < 0:
            delta += 7
        return base - td(days=(delta + 7))

    elif direction == "previous":
        start_of_last_week = resolver._add_weeks(base, -1) # Step 1: Get the start of *previous calendar week*
        offset = (target_idx - start_of_last_week.weekday()) % 7 # Step 2: Add offset to target weekday
        return start_of_last_week + td(days=offset)

    elif direction == "next":
        delta = (target_idx - current_idx)
        if delta <= 0:
            delta += 7
        return base + td(days=delta + 7)
    return None

def _compute_specific_year(direction):
    base = resolver.reference_date
    year = base.year
    if direction == "next":
        year += 1
    elif direction == "last":
        year -= 1
    return (d(year, 1, 1), d(year, 12, 31))
   
def _compute_specific_weekend(direction, base_date=None):
    if not base_date:
        base_date = resolver.reference_date
    weekend_start_idx = 5        
    if direction == "this":
        candidate = base_date + td((weekend_start_idx - base_date.weekday()) % 7)
        if base_date <= candidate + td(days=1):
            return (candidate, candidate + td(days=1))
    elif direction == "next":
        candidate = base_date + td((weekend_start_idx - base_date.weekday()) % 7) + td(weeks=1)
        return (candidate, candidate + td(days=1))
    elif direction == "last":
        candidate = base_date - td(days=((base_date.weekday() - weekend_start_idx) % 7 + 7))
        return (candidate, candidate + td(days=1))
    return None
   
def _compute_specific_month(direction, month_name):
    base = resolver.reference_date
    current_year = base.year
    month_info = timeline.adj_months(m=month_name, year=current_year)
    if not month_info:
        return None
    start_mm, start_dd = map(int, month_info["start"].split("/"))
    end_mm, end_dd = map(int, month_info["end"].split("/"))
    this_start = d(current_year, start_mm, start_dd)
    this_end   = d(current_year, end_mm,   end_dd)
    if direction == "this":
        return (this_start, this_end)
    elif direction == "next":
        if base < this_start:
            return (this_start, this_end)
        else:
            next_info = timeline.adj_months(m=month_name, year=current_year + 1)
            sm, sd = map(int, next_info["start"].split("/"))
            em, ed = map(int, next_info["end"].split("/"))
            return (d(current_year + 1, sm, sd), d(current_year + 1, em, ed))
    elif direction == "last":
        if base > this_end:
            return (this_start, this_end)
        else:
            last_info = timeline.adj_months(m=month_name, year=current_year - 1)
            sm, sd = map(int, last_info["start"].split("/"))
            em, ed = map(int, last_info["end"].split("/"))
            return (d(current_year - 1, sm, sd), d(current_year - 1, em, ed))
    return None

def _compute_specific_season(direction, season_name):
    base = resolver.reference_date
    current_year = base.year
    info_this = resolver._get_season_boundaries(season_name, current_year)
    this_start = resolver._parse_date(info_this["start"])
    this_end   = resolver._parse_date(info_this["end"])
    if direction == "this":
        return (this_start, this_end)
    elif direction == "next":
        if base < this_start:
            return (this_start, this_end)
        else:
            info_next = resolver._get_season_boundaries(season_name, current_year + 1)
            next_start = resolver._parse_date(info_next["start"])
            next_end   = resolver._parse_date(info_next["end"])
            return (next_start, next_end)
    elif direction == "last":
        if base > this_end:
            return (this_start, this_end)
        else:
            info_last = resolver._get_season_boundaries(season_name, current_year - 1)
            last_start = resolver._parse_date(info_last["start"])
            last_end   = resolver._parse_date(info_last["end"])
            return (last_start, last_end)
    return None 

def _compute_specific_quarter(direction, quarter_key):
    base = resolver.reference_date
    current_year = base.year
    quarter_info = timeline.adj_quarters()[quarter_key]  
    start_mm, start_dd = map(int, quarter_info["start"].split("/"))
    end_mm,   end_dd   = map(int, quarter_info["end"].split("/"))
    this_start = d(current_year, start_mm, start_dd)
    this_end   = d(current_year, end_mm,   end_dd)
    if direction == "this":
        return (this_start, this_end)
    elif direction == "next":
        if base < this_start:
            return (this_start, this_end)
        else:
            info_next = timeline.adj_quarters()[quarter_key]  # same key, next year
            next_start = d(current_year + 1, 
                           int(info_next["start"].split("/")[0]),
                           int(info_next["start"].split("/")[1]))
            next_end = d(current_year + 1, 
                         int(info_next["end"].split("/")[0]),
                         int(info_next["end"].split("/")[1]))
            return (next_start, next_end)
    elif direction == "last":
        if base > this_end:
            return (this_start, this_end)
        else:
            info_last = timeline.adj_quarters()[quarter_key]
            last_start = d(current_year - 1, 
                           int(info_last["start"].split("/")[0]),
                           int(info_last["start"].split("/")[1]))
            last_end = d(current_year - 1, 
                         int(info_last["end"].split("/")[0]),
                         int(info_last["end"].split("/")[1]))
            return (last_start, last_end)
    return None
   
def _compute_range_position(position, direction, time_unit_str):
    range_expr = [direction, time_unit_str]
    result = resolver.compute(range_expr)
    if not result:
        return None
    if isinstance(result, tuple) and len(result) == 2:
        range_start, range_end = result
    else:
        range_start = result
        range_end = result
    if position == "start":
        return range_start
    elif position == "end":
        return range_end
    elif position == "middle":
        delta = (range_end - range_start) // 2
        return range_start + delta
    return None       
 
def _compute_specific_weekday_in_range(direction, weekday_token, range_start, range_end):
    if range_start > range_end:
        return None
    w_idx = timeline.days.index[weekday_token.lower()]
    base = range_start if direction != "last" else range_end
    if direction == "next":
        cursor = range_start
        while cursor <= range_end:
            if cursor.weekday() == w_idx:
                return cursor
            cursor += td(days=1)
        return None
    elif direction == "last":
        cursor = range_end
        while cursor >= range_start:
            if cursor.weekday() == w_idx:
                return cursor
            cursor -= td(days=1)
        return None
    elif direction == "this":
        cursor = range_start
        while cursor <= range_end:
            if cursor.weekday() == w_idx:
                return cursor
            cursor += td(days=1)
        return None

def _compute_specific_timeunit_in_range(direction, time_unit, range_start, range_end):
    if range_start > range_end:
        return None
       
    if time_unit == "week":
        if direction == "next":
            start = range_start
            end = start + td(days=6)
            if end <= range_end:
                return (start, end)
        elif direction == "last":
            end = range_end
            start = end - td(days=6)
            if start >= range_start:
                return (start, end)
        elif direction == "this":
            start = range_start
            end = start + td(days=6)
            if end <= range_end:
                return (start, end)
               
    elif time_unit == "day":
        if direction == "next":
            if range_start <= range_end:
                return range_start
        elif direction == "last":
            if range_end >= range_start:
                return range_end
        elif direction == "this":
            ref = resolver.reference_date
            if range_start <= ref <= range_end:
                return ref
               
    elif time_unit == "month":
        for month_offset in range(12):
            test_date = resolver._add_months(range_start, month_offset)
            start = d(test_date.year, test_date.month, 1)
            last_day = timeline.days_in_month(start.month, start.year).d            
            end = d(start.year, start.month, last_day)
            if end > range_end:
                break
            if direction == "this" and start <= resolver.reference_date <= end:
                return (start, end)
            elif direction == "next" and start > resolver.reference_date:
                return (start, end)
            elif direction == "last" and end < resolver.reference_date:
                last = (start, end)
        if direction == "last":
            return last if 'last' in locals() else None
           
    elif time_unit == "season":
        for year_offset in range(2):  # scan 2 years forward max
            year = range_start.year + year_offset
            for season in resolver.SeasonsOrdered:
                info = resolver._get_season_boundaries(season, year)
                start = resolver._parse_date(info["start"])
                end = resolver._parse_date(info["end"])
                if end > range_end:
                    break
                if direction == "this" and start <= resolver.reference_date <= end:
                    return (start, end)
                elif direction == "next" and start > resolver.reference_date:
                    return (start, end)
                elif direction == "last" and end < resolver.reference_date:
                    last = (start, end)
        if direction == "last":
            return last if 'last' in locals() else None
           
    elif time_unit == "quarter":
        for y_offset in range(2):  # scan across 2 years
            year = range_start.year + y_offset
            for key in resolver.QuartersOrdered:
                info = timeline.adj_quarters()[key]
                start_mm, start_dd = map(int, info["start"].split("/"))
                end_mm, end_dd = map(int, info["end"].split("/"))
                start = d(year, start_mm, start_dd)
                end = d(year, end_mm, end_dd)
                if end > range_end:
                    break
                if direction == "this" and start <= resolver.reference_date <= end:
                    return (start, end)
                elif direction == "next" and start > resolver.reference_date:
                    return (start, end)
                elif direction == "last" and end < resolver.reference_date:
                    last = (start, end)
        if direction == "last":
            return last if 'last' in locals() else None
           
    elif time_unit == "weekend":
        if direction == "next":
            return _compute_specific_weekend("next", range_start)
        elif direction == "last":
            return _compute_specific_weekend("last", range_end)
        elif direction == "this":
            return _compute_specific_weekend("this", resolver.reference_date)               
           
    elif time_unit == "year":
        ref_year = resolver.reference_date.year
        if direction == "this":
            y = ref_year
        elif direction == "next":
            y = ref_year + 1
        elif direction == "last":
            y = ref_year - 1
        else:
            return None
        start = d(y, 1, 1)
        end = d(y, 12, 31)
        if range_start <= start and end <= range_end:
            return (start, end)
    return None
   
def _find_last_weekday_in_range(weekday_token, start, end):
    w_idx = timeline.days.index[weekday_token.lower()]
    cursor = end
    while cursor >= start:
        if cursor.weekday() == w_idx:
            return cursor
        cursor -= timedelta(days=1)
    return None   
   
def _compute_ago_expression(quantity, subunit):
    base = resolver.reference_date
    if subunit in {"day", "week", "month", "year"}:
        return _compute_ago_timeunit(base, quantity, subunit)
    if subunit == "quarter":
        return _compute_ago_quarter(base, quantity)  
    if subunit == "season":
        return _compute_ago_season([quantity, subunit, "ago"])         
    if subunit in resolver.Days:
        return _compute_ago_namedweekday(base, quantity, subunit)
    if subunit in resolver.Seasons:
        return _compute_ago_namedseason(base, quantity, subunit)                
    if subunit.startswith("weekend"):
        return _compute_ago_weekend(base, quantity)
    return None
   
def _compute_ago_timeunit(base, quantity, time_unit):
    if time_unit == "day":
        return base - td(days=quantity)
    elif time_unit == "week":
        return base - td(days=7 * quantity)
    elif time_unit == "month":
        return resolver._add_months(base, -quantity)
    elif time_unit == "year":
        return resolver._add_years(base, -quantity)
    return None
   
def _compute_ago_namedweekday(base, quantity, weekday_token):
    if weekday_token.lower() not in timeline.days.index:
        return None
    target_idx = timeline.days.index[weekday_token.lower()]
    found = 0
    cursor = base
    while cursor >= d(1970, 1, 1):  # safety floor
        if cursor.weekday() == target_idx:
            found += 1
            if found == quantity:
                return cursor
        cursor -= td(days=1)
    return None    
   
def _compute_ago_season(token, rnge=False):
    current_season, current_year = resolver._determine_current_season(resolver.reference_date, include_year=True) # Added
    num_seasons_ago = int(token[0])
    current_index = resolver.SeasonsOrdered.index(current_season)
    cycles = num_seasons_ago // 4
    remainder = num_seasons_ago % 4
    new_index = (current_index - remainder) % 4
    additional_year_offset = 1 if remainder > current_index else 0
    total_year_offset = cycles + additional_year_offset
    target_year = current_year - total_year_offset
    target_season = resolver.SeasonsOrdered[new_index]
    season_info = timeline.adj_seasons(season=target_season, year=target_year, include_year=True)
    if rnge:
        parsed_info = {k: dt.strptime(v, '%m/%d/%Y').date() for k, v in season_info.items()}
        return parsed_info
    else:
        return dt.strptime(season_info['start'], '%m/%d/%Y').date()         

def _compute_ago_namedseason(base, quantity, season_token):
    season_token = season_token.lower()
    current_season, current_year = resolver._determine_current_season(base, include_year=True) # Added    
    current_idx = resolver.SeasonsOrdered.index(current_season)
    target_idx = resolver.SeasonsOrdered.index(season_token)
    extra = 0 # compute how many extra years we step back due to misalignment
    target_year = current_year - (quantity + extra)
    season_info = timeline.adj_seasons(season=season_token, year=target_year, include_year=True)
    return dt.strptime(season_info["start"], "%m/%d/%Y").date()       

def _compute_ago_weekend(base, quantity):
    offset =  (base.weekday() - 5) % 7
    last_saturday = base - td(days=offset)
    last_sunday = last_saturday + td(days=1)
    if last_sunday > base:
        last_sunday = base
    start_of_target = last_saturday - td(weeks=(quantity-1))
    end_of_target = start_of_target + td(days=1)
    return (start_of_target, end_of_target)

def _compute_ago_quarter(base, quantity):
    current_quarter = resolver._determine_current_quarter(base)
    current_idx = resolver.QuartersOrdered.index(current_quarter)
    current_year = base.year
    count = 0
    while count < quantity:
        current_idx -= 1
        if current_idx < 0:
            current_idx = 3
            current_year -= 1
        count += 1
    q_key = resolver.QuartersOrdered[current_idx]
    mm, dd = map(int, timeline.adj_quarters()[q_key]["start"].split("/"))
    return d(current_year, mm, dd)
   
def _compute_sub_month_in_range(month_token, range_start, range_end):
    month_name = timeline.months[month_token]
    target_year = range_start.year
    month_info = timeline.adj_months(month_name, target_year)
    if not month_info:
        return None
    mm_start, dd_start = map(int, month_info["start"].split("/"))
    mm_end, dd_end = map(int, month_info["end"].split("/"))
    sub_start = d(target_year, mm_start, dd_start)
    sub_end = d(target_year, mm_end, dd_end)
    if sub_start < range_start or sub_end > range_end:
        return None
    return (sub_start, sub_end)
   
def _compute_sub_weekday_in_range(weekday_token, range_start, range_end):
    day_name = resolver.Days[weekday_token] 
    target_idx = timeline.days.index[weekday_token] 
    temp = range_start
    while temp <= range_end:
        if temp.weekday() == target_idx:
            return temp
        temp += td(days=1)
    return None
   
def _compute_sub_season_in_range(season_token, range_start, range_end):
    season_name = resolver.Seasons[season_token]
    target_year = range_start.year
    season_info = resolver._get_season_boundaries(season_name, target_year)
    if not season_info:
        return None
    sub_start = resolver._parse_date(season_info["start"])
    sub_end = resolver._parse_date(season_info["end"])
    if sub_start < range_start or sub_end > range_end:
        return None
    return (sub_start, sub_end)
   
def _compute_sub_day_in_range(self, day_token, range_start, range_end):
    parsed_date = resolver._parse_date(day_token)
    if not parsed_date:
        return None
    if range_start <= parsed <= range_end: # Check if inside the range
        return parsed # Return either a single date or a 1-day range
    return None

def _compute_starting_from_expression(tokens):
    try:
        start_idx = [i for i, t in enumerate(tokens) if t.lower() == "starting"][0]
        from_idx = [i for i, t in enumerate(tokens) if t.lower() == "from"][0]
    except IndexError:
        return None 
    left_part = tokens[:start_idx]  # e.g. ["next", "6", "month"]
    right_part = tokens[from_idx + 1:]  # e.g. ["january 1"]
    if not left_part or not right_part:
        return None
    start_date = _compute_starting_point(right_part)
    if not start_date:
        return None
    original_ref = resolver.reference_date
    resolver.reference_date = start_date
    outer_result = resolver.compute(left_part)
    resolver.reference_date = original_ref
    if not outer_result:
        return None
    return _apply_starting_point(outer_result, start_date)

def _compute_outer_timeunit(tokens):
    result = resolver.compute(tokens)
    if isinstance(result, d):
        try:
            if len(tokens) >= 2 and tokens[0].isdigit() and tokens[1] in resolver.TimeUnits:
                quantity = int(tokens[0])
                time_unit = tokens[1]
                return resolver._range_from_unit(result, quantity, time_unit)
        except Exception:
            return result  # fallback

    return result
  
def _compute_starting_point(tokens):
    if len(tokens) == 1:
        token = tokens[0].lower()
        if token in resolver.immediate_relative_days:
            return resolver.immediate_relative_days[token](resolver.reference_date)
        try:
            month, day = token.split()
            day = int(day)
            month = month.lower()
            if month in timeline.months:
                month_number = timeline.adj_months(m=month, year=None).start.mm.int
                year = resolver.reference_date.year
                return d(year, month_number, day)
        except ValueError:
            pass
        if token in timeline.months:
            result = resolver.compute(["this", token])
            return result[0] if isinstance(result, tuple) else result
        if token in resolver.Days:
            result = resolver.compute(["this", token])
            return result[0] if isinstance(result, tuple) else result
        if token in resolver.Seasons:
            result = resolver.compute(["this", token])
            return result[0] if isinstance(result, tuple) else result
        if token in timeline.quarters:
            result = resolver.compute(["this", token])
            return result[0] if isinstance(result, tuple) else result
    result = resolver.compute(tokens)
    return result[0] if isinstance(result, tuple) else result

def _apply_starting_point(outer_result, start_date):
    if isinstance(outer_result, tuple) and len(outer_result) == 2:
        orig_start, orig_end = outer_result

        if orig_start <= start_date <= orig_end:
            return (start_date, orig_end)
        else:
            duration = (orig_end - orig_start).days
            new_start = start_date
            new_end = new_start + td(days=duration)
            return (new_start, new_end)
        
    return outer_result



class _auditor:
    """
    End-to-end diagnostic utility for structurally and semantically validating
    tokenized temporal expressions.

    This component coordinates multi-level linguistic inference by performing:
      1. Syntactic constituency analysis over temporal spans
      2. Ordinal containment validation (e.g. "55th day of the week" → invalid)
      3. Cardinal quantity bound-checking within anchored time frames (e.g. "last 8 weeks of April")

    Suitable for use in pipelines involving relative time normalization, event anchoring,
    or temporal parsing where semantic well-formedness must be confirmed.
    """
    def __init__(
        self,
        *,
        drop_of_default=False,
        drop_this_default=False,
        # Dependency injection for modular evaluation
        structural_validator=validate_temporal_structure,
        ordinal_bounds_validator=validate_bounds,
        range_bounds_validator=validate_range_bounds,
    ):
        self.drop_of_default = drop_of_default
        self.drop_this_default = drop_this_default

        # Injected validator functions
        self._validate_structure = structural_validator
        self._validate_ord_bounds = ordinal_bounds_validator
        self._validate_rng_bounds = range_bounds_validator

    def _analysis(self, raw_tokens):
        """
        Executes deep syntactic and semantic evaluation on a tokenized phrase.

        Args:
            raw_tokens (List[str]): A list of lexical tokens representing a temporal phrase.

        Returns:
            Dict[str, Any]: A structured report capturing grammatical form,
                            ordinal bounds consistency, cardinal range validity,
                            and a final boolean judgment (`semantically_valid`).
        """
        # ── 1. Syntactic evaluation (structure/constituency) ──
        result = self._validate_structure(
            raw_tokens,
            this_anchor_removal=True,         # Drop "this" if it's a no-op
            auto_add_prepositions=True,       # Add implicit 'of', 'in', etc. if necessary
        )

        # ── 2. Ordinal containment validation ──
        bounds_ok, reason_b = self._validate_ord_bounds(result, raw_tokens)
        result["semantic_bounds_ok"] = bounds_ok
        result["semantic_reason"] = reason_b

        # ── 3. Cardinal quantifier validation ──
        range_ok, reason_r = self._validate_rng_bounds(raw_tokens)
        result["range_bounds_ok"] = range_ok
        result["range_reason"] = reason_r

        # ── 4. Final semantic verdict ──
        result["semantically_valid"] = bounds_ok and range_ok

        return result

    def _token_proc(
        self,
        tokens,
        *,
        drop_of=None,
        drop_this=None
    ):
        """
        Perform light lexical preprocessing on input token list.

        Args:
            tokens (List[str]): Input token sequence.
            drop_of (bool): If True, remove 'of' as a stopword.
            drop_this (bool): If True, remove temporal anchors like 'this'.

        Returns:
            List[str]: A cleaned token list variant.
        """
        if drop_of is None:
            drop_of = self.drop_of_default
        if drop_this is None:
            drop_this = self.drop_this_default

        if drop_of:
            tokens = PhraseEngine.drop.of(tokens, return_tokens=True)
        if drop_this:
            tokens = PhraseEngine.drop.this(tokens, return_tokens=True)
        return tokens

    def analyze(self, tokens):
        """
        Attempts structural + semantic validation across up to 4 variations
        of the input: toggling presence of 'of' and 'this'.

        This improves robustness against tokenization drift or minor phrasing variance.

        Args:
            tokens (List[str]): Raw input token list.

        Returns:
            Dict[str, Any] or None: First valid analysis result found, or None if all fail.
        """
        for drop_of in (False, True):
            for drop_this in (False, True):
                variant = self._token_proc(
                    deepcopy(tokens),
                    drop_of=drop_of,
                    drop_this=drop_this
                )
                try:
                    result = self._analysis(variant)
                    if result.get("valid") and result.get("semantically_valid"):
                        return result
                except Exception:
                    continue
        return None

def parse_temporal(phrase, *, skip_validation=DEBUGGER, parse=True, clean_tokens=True):
    """
    Parse a natural-language temporal phrase or pre-tokenized input and return a concrete date or date range.

    Parameters
    ----------
    phrase : str | list[str]
        The raw phrase to interpret (e.g. "last Friday of this month") or a list of already-tokenized strings.
        - If a string, it will be normalized and tokenized internally.
        - If a list, it is assumed to be pre-tokenized input.
    
    skip_validation : bool, optional
        If True, bypasses structural and semantic validation checks (e.g., malformed expressions).
        Default is False.

    parse : bool, optional
        If True (default), applies full phrase-level parsing including handling "ago" logic
        and named relative expressions. If False, assumes phrase is already tokenized and skips that step.

    clean_tokens : bool, optional
        If True (default), performs token-level normalization (e.g., removing "the", converting ordinals).

    Returns
    -------
    datetime.date
        A specific date if the phrase resolves to a singular point in time.
    (datetime.date, datetime.date)
        A start-end tuple representing a date range (e.g. a week or a month).
    ("datetime", str)
        If the input is a simple partial date or named month (e.g. "April").
    None
        If parsing fails or input is invalid.
    """    
    try:
        if isinstance(phrase, list):
            tokens = [str(x).lower() for x in phrase]
            phrase = ' '.join(str(x) for x in phrase)            
        elif isinstance(phrase, str):
            phrase = ' '.join(str(phrase).split()).lower() 
            tokens = phrase.lower().split()
        else:
            raise TypeError("Unsupported type for 'phrase'. Must be list or str.")

        if parse:
            if not phrase:
                return None

        # 1) Shortcut for plain month names or partial dates
        if phrase in set(timeline.months.keys()) | set(k.capitalize() for k in timeline.months) | set(timeline.months.values()):
            return ("datetime", phrase)

        if PhraseEngine.is_partial_date([phrase], include_year=True):
            return ("datetime", phrase)

        if parse:
            # 2) Choose parse path by presence of "ago"
            if PhraseEngine.match.lexical(phrase, ["ago"], token_index=None, exact=False):
                tokens = _parse_quantified_time_expression(phrase)
            else:
                tokens = _parse_named_relative_expression(phrase)

        # 3) Partial‑date fallback
        if PhraseEngine.is_partial_date(tokens):
            joined = " ".join(' '.join(str(x) for x in tokens).split())
            return ("datetime", joined)

        if clean_tokens:
            # 4) Token cleanup & normalization
            tokens = PhraseEngine.sub.any(tokens, {"the": ""}, prefix=False, return_tokens=True)
            tokens = PhraseEngine.sub.partial_date(tokens, include_year=True)
            tokens = PhraseEngine.sub.ordinal_cardinal(tokens)

        # 5) Structural + semantic validation unless skipped
        if not skip_validation:
            if not tokens:
                return None  # No tokens to validate
            result = _audit.analyze(tokens)
            if not result:
                return None

        # 6) Final prep: normalize "this" for implicit anchor handling
        if tokens and (skip_validation or vocab_validate(PhraseEngine.drop.partial_date_year(tokens))):
            toks = PhraseEngine.insert.this(tokens, return_tokens=True)
            toks = PhraseEngine.drop.this(toks, return_tokens=True)

            # A.  Attempt with “of” first if the pattern needs it
            # - starts with "last ..."            (rule 6 in resolver)
            # - or exactly 3-token  "<unit> of <date-part>"  (rule 8)
            needs_of = (
                (toks and toks[0] == "last") or
                (len(toks) == 3 and toks[1] == "of")
            )
            if needs_of:
                result = resolver.compute(toks)
                if result is not None:
                    return result

            # B.  Otherwise (or if step A failed) ⇒ drop “of” and retry
            toks_no_of = PhraseEngine.drop.of(toks, return_tokens=True)
            return resolver.compute(toks_no_of)
        return None
    except Exception:
        return None



# Core temporal resolver for anchoring and interpreting relative date phrases
resolver = RelativeDateResolver(week_start="sunday")

# Static instance for structural and semantic validation of temporal expressions
_audit = _auditor()


__all__ = ["parse_temporal"]








# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ╭──────────────────────────────────────────────────────────────────────────────╮
# │                              DEVELOPMENT NOTE                                 │
# ├───────────────────────────────────────────────────────────────────────────────┤
# │ This section is part of an upcoming feature:                                  │
# │   → HOLIDAY DATA PROCESSING & NORMALIZATION                                   │
# │                                                                               │
# │ Description:                                                                  │
# │   Logic here is intended to support integration of regional holiday data      │
# │   into the temporal parsing pipeline (e.g. identifying "the week after        │
# │   Thanksgiving", "next business day after a holiday", etc.).                  │
# │                                                                               │
# │ Status:                                                                       │
# │   This code is currently inactive and COMMENTED OUT. It is safe to leave      │
# │   in the codebase, as it has no runtime impact.                               │
# │                                                                               │
# │ Planned Activation: Q3 2025                                                   │
# │                                                                               │
# │ Action Items (when ready):                                                    │
# │   [ ] Refactor or uncomment `HolidayDataProcessor` class                      │
# │   [ ] Connect holiday normalization to main parser                            │
# │   [ ] Add unit/integration tests                                              │
# │   [ ] Remove this development note when stable                                │
# │                                                                               │
# │ Related Tickets/Docs:                                                         │
# │   #247 – “Holiday-aware temporal parser”                                      │
# │   internal/wiki/holiday-normalization-spec                                    │
# ╰──────────────────────────────────────────────────────────────────────────────╯
# 
# 
# 
# import numbr # Third-Party Library
# import time
# import random
# import calendar as cal
# import unicodedata
# import pandas as pd # Third-Party Library
# 
# try:
#     # from ._datetime_scan import DateTimeScan as _d_Scan
#     # from ._sysutils import DataImport
#     # from ._holiday import HolidayManager
#     # from ._connect import http_client    
# except (ImportError, ModuleNotFoundError):
#     try:
#         # from _datetime_scan import DateTimeScan as _d_Scan
#         # from _sysutils import DataImport
#         # from _holiday import HolidayManager
#         # from _connect import http_client         
#     except (ImportError, ModuleNotFoundError):
#         # from dately._datetime_scan import DateTimeScan as _d_Scan
#         # from dately._sysutils import DataImport
#         # from dately._holiday import HolidayManager
#         # from dately._connect import http_client 
#         
# ## HOLIDAY LOGIC
# ##─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# # Retrieves and processes the holiday data for a specified country and year, returning it in various formats.
# #  
# # Args:
# #     country_name (str): The name of the country.
# #     year (int, optional): The year for which to get the holidays. Defaults to None.
# #     format (str, optional): The format of the output ('list', 'dict', or 'df'). Defaults to 'list'.
# #  
# # Returns:
# #     mixed: The processed holiday data in the requested format.
# class HolidayDataProcessor:
#     """
#     A robust class for fetching and normalizing holiday data with in-memory caching 
#     on top of the built-in requests_cache in http_client.
# 
#     Attributes:
#         holiday_manager (HolidayManager): Manages fetching holiday data from remote.
#         default_country (str): Default country to fetch holidays for if none provided.
#         _cache (dict): In-memory cache keyed by (country, year, format) => final data.
#     """
#     def __init__(self, 
#                  holiday_manager: HolidayManager = None, 
#                  default_country: str = None,  # <-- now optional
#                  # default_base_url: str = "dGltZS5pcy8="
#                  ):
#         """
#         Initialize the HolidayDataProcessor.
# 
#         :param holiday_manager: If provided, use that manager. Otherwise, create one using `http_client`.
#         :param default_country: Default country to fetch holiday data for.
#         """
#         self.default_country = default_country
#         # self.default_base_url = default_base_url
# 
#         # If no manager is provided, instantiate one with the global http_client
#         if holiday_manager is None:
#             # # Optionally override the base URL on the global http_client:
#             # http_client.update_base_url(self.default_base_url)
#             http_client.update_base_url("dGltZS5pcy8=")            
#             holiday_manager = HolidayManager(http_client)
# 
#         self.holiday_manager = holiday_manager
# 
#         # Our own in-memory cache: {(country, year, format): pd.DataFrame or list or dict}
#         self._cache = {}
# 
#     def fetch_holiday_data(self, 
#                            country_name: str = None, 
#                            year: int = None):
#         """
#         Retrieve & process holiday data for a given country + year, returning 
#         either a DataFrame, list, or dict, as requested.
# 
#         :param country_name: Country name. Defaults to self.default_country if None.
#         :param year: Year to fetch. Defaults to the system's current year in `HolidayManager` if None.
#         :return: The holiday data in the requested format (DataFrame, dict, or list), or None if no data.
#         """
#         if not country_name:
#             country_name = self.default_country
#             if not country_name:
#                 return None  # Early exit if no country specified
# 
#         return_format = "df"
#         
#         # Check our in-memory cache first
#         cache_key = (country_name, year, return_format)
#         if cache_key in self._cache:
#             return self._cache[cache_key]
# 
#         # Not in cache => fetch from the manager
#         data = self.holiday_manager.Holiday(
#             country_name=country_name,
#             year=year,
#             format=return_format
#         )
#         if data is None:
#             return None  # The manager returned nothing (HTTP or other error)
#         
#         # If we asked for a DataFrame, remove duplicates, drop "Type", etc. 
#         if return_format == 'df' and isinstance(data, pd.DataFrame):
#             data = data.drop_duplicates(subset=["Name", "Date"]).drop(columns=["Type"]).copy()
# 
#         # Store the final result in our in-memory cache
#         self._cache[cache_key] = data
#         return data
# 
#     def set_default_country(self, name: str):
#         if not isinstance(name, str) or not name.strip():
#             return None
#         self.default_country = name.strip()
# 
#     def normalize_holiday_names(self, df: pd.DataFrame, to_dict: bool = False):
#         """
#         Cleans/normalizes the 'Name' column of a holiday DataFrame and optionally 
#         returns a dict of normalized -> original values.
# 
#         :param df: A DataFrame with 'Name' and 'Date' columns.
#         :param to_dict: If True, returns a dict instead of a DataFrame.
#         :return: A modified DataFrame with extra normalization columns, or a dict if to_dict=True.
#         """
#         def strip_accents(text):
#             return ''.join(
#                 c for c in unicodedata.normalize('NFD', text)
#                 if unicodedata.category(c) != 'Mn'
#             )
# 
#         def basic_normalize(name: str) -> str:
#             # Remove parentheses & contents
#             name = re.sub(r"\(.*?\)", "", name)
#             # Remove punctuation
#             name = re.sub(r"[^\w\s]", "", name)
#             return name.strip()
# 
#         def remove_common_suffixes(name: str) -> str:
#             return re.sub(
#                 r"\b(Day|Eve|Festival|Celebration|Holiday)\b$",
#                 "",
#                 name,
#                 flags=re.IGNORECASE
#             ).strip()
# 
#         def remove_stopwords(name: str) -> str:
#             stopwords = {'of', 'the', 'and', 'a'}
#             return ' '.join(
#                 word for word in name.split()
#                 if word.lower() not in stopwords
#             )
# 
#         def collapse_spaces(name: str) -> str:
#             return re.sub(r"\s+", " ", name).strip()
# 
#         # Copy to avoid mutating user’s data
#         dataframe = df.copy()
# 
#         # Step-by-step normalization
#         dataframe['Normalized_Original'] = dataframe['Name']
#         dataframe['Normalized_1_Basic'] = dataframe['Name'].apply(basic_normalize)
#         dataframe['Normalized_2_Lowercase'] = dataframe['Normalized_1_Basic'].str.lower()
# 
#         # Branch A: Full normalization (suffixes removed)
#         dataframe['Normalized_3_NoSuffix'] = dataframe['Normalized_2_Lowercase'].apply(remove_common_suffixes)
#         dataframe['Normalized_4_NoStopwords'] = dataframe['Normalized_3_NoSuffix'].apply(remove_stopwords)
#         dataframe['Normalized_5_NoAccents'] = dataframe['Normalized_4_NoStopwords'].apply(strip_accents)
#         dataframe['Normalized_6_Collapsed'] = dataframe['Normalized_5_NoAccents'].apply(collapse_spaces)
# 
#         # Branch B: Keep suffixes (less aggressive)
#         dataframe['Normalized_4B_NoStopwords_WithSuffix'] = dataframe['Normalized_2_Lowercase'].apply(remove_stopwords)
#         dataframe['Normalized_5B_NoAccents_WithSuffix'] = dataframe['Normalized_4B_NoStopwords_WithSuffix'].apply(strip_accents)
#         dataframe['Normalized_6B_Collapsed_WithSuffix'] = dataframe['Normalized_5B_NoAccents_WithSuffix'].apply(collapse_spaces)
# 
#         if to_dict:
#             return self._generate_holiday_lookup_dict(dataframe)
#         return dataframe
# 
#     def _generate_holiday_lookup_dict(self, dataframe: pd.DataFrame):
#         """
#         Internal helper to build a dict from the final normalized columns.
#         e.g. { 'presidents day': { 'holiday': 'Presidents Day', 'year': '2023', ... }, ... }
#         """
#         holiday_lookup = {}
#         # Identify columns that have normalized data (and not the original)
#         norm_cols = [
#             col for col in dataframe.columns
#             if col.startswith("Normalized_") and col != "Normalized_Original"
#         ]
# 
#         for col in norm_cols:
#             for norm_val, original_val, date_val in zip(
#                 dataframe[col], 
#                 dataframe['Name'], 
#                 dataframe['Date']
#             ):
#                 if isinstance(norm_val, str):
#                     key = norm_val.strip().lower()
#                     if key and key not in holiday_lookup:
#                         # Build a dict of details
#                         year, month, day = date_val.split("-")
#                         holiday_lookup[key] = {
#                             # "name": original_val,
#                             # "date": date_val,                               
#                             "holiday": original_val,
#                             "year": year,
#                             "month": month,
#                             "day": day,
#                         }
#         return holiday_lookup if holiday_lookup else None
# 
# 
# # # Create an instance (by default pointing to the base64-decoded URL in http_client)
# # holidayLookup = HolidayDataProcessor()
# 
# # # First call: data is fetched from remote (or from requests_cache if previously fetched)
# # holiday_data = holidayLookup.fetch_holiday_data(country_name="United States", year=2023)
# # 
# # # # Update Country
# # # holidayLookup.set_default_country("Canada")
# # # holiday_data = holidayLookup.fetch_holiday_data()
# # 
# # # Normalize
# # normalized_holiday_data = holidayLookup.normalize_holiday_names(holiday_data, to_dict=True)
# # normalized_holiday_data.get("new years")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



























