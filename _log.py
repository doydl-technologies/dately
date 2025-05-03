# -*- coding: utf-8 -*-

import logging

# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.

# Dedicated logger (“dately”) so user can enable/disable it
logger = logging.getLogger("dately")
logger.addHandler(logging.NullHandler())  # Prevents "No handler found" warnings
