# -*- coding: utf-8 -*-

import sys
import os
import builtins

# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
def is_interactive() -> bool:
    """
    Return True when running inside an interactive shell
    (plain CPython REPL, IPython/Jupyter, RStudio–reticulate, Spyder, PyCharm,
    VS Code interactive, IDLE, bpython, ptpython, etc.).
    """
    return (
        # ── Classic CPython REPL / “python -i” ───────────────────────────────
        hasattr(sys, "ps1") or
        sys.flags.interactive or
        os.getenv("PYTHONINSPECT") == "1"
        # ── IPython / Jupyter family ─────────────────────────────────────────
        or getattr(builtins, "__IPYTHON__", False)
        or "ipykernel" in sys.modules
        # ── RStudio reticulate backend ───────────────────────────────────────
        or "rpytools" in sys.modules
        or any("reticulate" in m for m in sys.modules)
        # ── IDE-specific interactive consoles ────────────────────────────────
        or "spyder" in sys.modules                        # Spyder
        or "idlelib" in sys.modules                       # IDLE
        or "pydevd" in sys.modules or "pydevconsole" in sys.modules  # PyCharm console
        or ("debugpy" in sys.modules and                 # VS Code interactive / debug
            os.getenv("TERM_PROGRAM") == "vscode")
        or os.getenv("PYCHARM_HOSTED") == "1"             # PyCharm run config
        # ── Alternative shells ───────────────────────────────────────────────
        or "bpython" in sys.modules
        or "ptpython" in sys.modules
    )

