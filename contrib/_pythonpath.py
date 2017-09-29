__metaclass__ = type

import sys
import os

# See if we can find launchpadlib and waddlib
try:
    import launchpadlib
    import wadllib
except ImportError:
    # Modify sys.path to add trunk/lib.
    HOME = os.environ['HOME']
    trunk_path = os.environ.get(
        'LP_TRUNK_PATH',
        os.path.join(HOME, 'canonical/lp-branches/trunk'))
    sys.path.insert(0, os.path.join(trunk_path, 'lib'))
