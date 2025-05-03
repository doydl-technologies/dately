# -*- coding: utf-8 -*-

# import logging

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._log import logger
from ._temporal_scan import resolver


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

# Library-level convenience: tweak the singleton’s week start in one call
def set_week_start(day):
    """
    Set the first day of the week used by the resolver.

    This method updates the internal `week_start` configuration, which affects
    how calendar-based computations (such as weeks, weekends, or expressions like
    "start of next week") are anchored and resolved. It supports either a weekday
    name ("sunday" or "monday") or a numeric index (0–6), where:
        - 0 = Monday
        - 6 = Sunday

    Parameters:
    ──────────────────────────   
    week_start : str | int
        The desired first day of the week. Accepts:
          - A string: "sunday" or "monday"
          - An integer: 0 (for Monday) or 6 (for Sunday)
    
    Returns:
    ──────────────────────────
    None    
    
    Example:
    ──────────────────────────   
    >>> resolver.set_week_start("monday")
    >>> resolver.set_week_start(0)         # Also sets to Monday
    """
    resolver.set_week_start(day)
    
    # Informative log message (quiet unless the user enables it) -------------
    logger.info("Week-start updated → %s", resolver.week_start.capitalize())

__all__ = ["set_week_start"]


