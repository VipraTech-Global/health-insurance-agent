"""Domain failures that must remain distinct from technical processing errors."""


class PinnedStateChanged(RuntimeError):
    """The customer profile or live knowledge release changed during a turn."""


class AccountErased(RuntimeError):
    """Owner-scoped work was fenced by an account-erasure generation change."""


class TurnLeaseLost(RuntimeError):
    """A stale or expired conversation worker must not mutate customer state."""


class TurnCancellationRequested(RuntimeError):
    """Customer cancellation fenced the next durable mutation boundary."""


class UnsupportedComparisonError(ValueError):
    """Generated comparison prose failed deterministic support or neutrality validation."""
