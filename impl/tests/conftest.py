"""Make `vqlaw` importable when the conformance suite is run on its own.

The conformance corpus is the artifact that makes this a specification rather
than a document, and its whole claim is that a third party can execute it with
no access to our data. So it has to run standalone:

    python -m pytest impl/tests/

It did not. `import vqlaw` resolved only because another module in the same
session, `concordance/build_concordance.py`, inserts `impl/` on `sys.path` as an
import side effect. The suite passed in a combined run and failed by itself,
which is the exact shape a third party would hit first and we would never see.

This lives in the test directory rather than a level above on purpose. A
conftest in the collected directory is always loaded; one above it is skipped
whenever pytest resolves rootdir to the test directory, which is what happens
when the suite is invoked by absolute path from an unrelated working directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
