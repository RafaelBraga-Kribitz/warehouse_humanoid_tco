"""Make the governance test helpers importable as top-level modules.

tests/governance/ is a package (has __init__.py), so under pytest's prepend
import mode the bare `from _ratchet import ...` used by the finding verification
tests would not resolve. Inserting this directory onto sys.path fixes that and
keeps the test files readable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
