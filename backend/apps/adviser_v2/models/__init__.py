"""Public model surface for the approved 63-entity CoverGuide design.

The retained ``accounts.User`` model implements the approved Account entity. The
remaining 62 concrete entities are deliberately split by domain below while Django
loads them as one replacement application.
"""

from .catalogue import *  # noqa: F403
from .comparisons import *  # noqa: F403
from .corpus import *  # noqa: F403
from .customer import *  # noqa: F403
from .operations import *  # noqa: F403
