from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO

from django.conf import settings

from .ai import RelayFailure
from .relay_management import (
    MANAGED_PROVIDERS,
    RelayCredential,
    RelayManagementClient,
    RelayManagementError,
)
from .relay_routes import verify_account_readiness

OAUTH_OPERATION_SECONDS = 5 * 60
MAX_MARKER_BYTES = 4096


class RelayAccountError(RuntimeError):
    """A safe laptop-wide relay account operation failure."""


@dataclass(frozen=True, slots=True)
class PendingAccountOperation:
    oauth_state: str
    provider: str
    operation: str
    previous_credential_id: str
    expires_at: int


@dataclass(frozen=True, slots=True)
class ProviderAccountSummary:
    provider: str
    label: str
    state: str
    masked_identifier: str
    has_active_account: bool
    can_restore: bool
    login_in_progress: bool
    action_required: bool


@dataclass(frozen=True, slots=True)
class AccountLoginStart:
    provider: str
    authorization_url: str
    expires_at: int


def _selected_provider(provider: str) -> str:
    if provider not in MANAGED_PROVIDERS:
        raise RelayAccountError("Unsupported subscription provider")
    return provider


def _provider_label(provider: str) -> str:
    return "Claude" if provider == "claude" else "Codex"


def _state_dir() -> Path:
    path = Path(settings.AI_RELAY_STATE_DIR)
    if not path.is_absolute() or (path.exists() and path.is_symlink()):
        raise RelayAccountError("The relay account state directory is unsafe")
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.chmod(0o700)
    except OSError as error:
        raise RelayAccountError("The relay account state directory is unavailable") from error
    directory_stat = path.stat()
    if (
        not path.is_dir()
        or directory_stat.st_uid != os.getuid()
        or stat.S_IMODE(directory_stat.st_mode) != 0o700
    ):
        raise RelayAccountError("The relay account state directory is unsafe")
    return path


def _marker_path(provider: str) -> Path:
    return _state_dir() / f"{_selected_provider(provider)}.pending.json"


@contextmanager
def _provider_lock(provider: str) -> Iterator[None]:
    lock_path = _state_dir() / f"{_selected_provider(provider)}.lock"
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        lock_file: IO[bytes] = os.fdopen(descriptor, "r+b")
    except OSError as error:
        raise RelayAccountError("The relay account lock is unavailable") from error
    try:
        if not stat.S_ISREG(os.fstat(lock_file.fileno()).st_mode):
            raise RelayAccountError("The relay account lock is unsafe")
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as error:
                if time.monotonic() >= deadline:
                    raise RelayAccountError(
                        "Another laptop-wide account operation is in progress"
                    ) from error
                time.sleep(0.05)
        yield
    finally:
        lock_file.close()


def _validate_pending(value: object, provider: str) -> PendingAccountOperation:
    if not isinstance(value, dict) or set(value) != {
        "oauth_state",
        "provider",
        "operation",
        "previous_credential_id",
        "expires_at",
    }:
        raise RelayAccountError("The relay account operation state is invalid")
    oauth_state = value.get("oauth_state")
    operation = value.get("operation")
    previous_id = value.get("previous_credential_id")
    expires_at = value.get("expires_at")
    if (
        value.get("provider") != provider
        or operation not in {"connect", "reconnect"}
        or not isinstance(oauth_state, str)
        or len(oauth_state) > 128
        or not isinstance(previous_id, str)
        or len(previous_id) > 256
        or not isinstance(expires_at, int)
        or expires_at <= 0
    ):
        raise RelayAccountError("The relay account operation state is invalid")
    return PendingAccountOperation(
        oauth_state=oauth_state,
        provider=provider,
        operation=operation,
        previous_credential_id=previous_id,
        expires_at=expires_at,
    )


def _read_pending(provider: str) -> PendingAccountOperation | None:
    path = _marker_path(provider)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise RelayAccountError("The relay account operation state is unavailable") from error
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode) or stat.S_IMODE(file_stat.st_mode) != 0o600:
            raise RelayAccountError("The relay account operation state is unsafe")
        content = os.read(descriptor, MAX_MARKER_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(content) > MAX_MARKER_BYTES:
        raise RelayAccountError("The relay account operation state is invalid")
    try:
        decoded = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RelayAccountError("The relay account operation state is invalid") from error
    return _validate_pending(decoded, provider)


def _write_pending(pending: PendingAccountOperation) -> None:
    directory = _state_dir()
    path = _marker_path(pending.provider)
    encoded = json.dumps(asdict(pending), ensure_ascii=True, separators=(",", ":")).encode()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{pending.provider}.", dir=directory)
    try:
        os.fchmod(descriptor, 0o600)
        os.write(descriptor, encoded)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary_name, path)
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        raise RelayAccountError("The relay account operation state could not be saved") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _clear_pending(provider: str) -> None:
    try:
        _marker_path(provider).unlink()
    except FileNotFoundError:
        pass
    except OSError as error:
        raise RelayAccountError("The relay account operation state could not be cleared") from error


def _client() -> RelayManagementClient:
    return RelayManagementClient()


def _sorted_credentials(credentials: tuple[RelayCredential, ...]) -> list[RelayCredential]:
    return sorted(credentials, key=lambda item: (item.updated_at, item.opaque_id), reverse=True)


def _summary(
    provider: str,
    credentials: tuple[RelayCredential, ...],
    *,
    pending: PendingAccountOperation | None = None,
    action_required: bool = False,
) -> ProviderAccountSummary:
    active = [credential for credential in credentials if not credential.disabled]
    disabled = [credential for credential in credentials if credential.disabled]
    shown = next(
        (
            credential
            for credential in credentials
            if pending is not None and credential.opaque_id == pending.previous_credential_id
        ),
        None,
    )
    if shown is None:
        shown = next(iter(active or _sorted_credentials(tuple(disabled))), None)
    masked_identifier = shown.masked_identifier if shown is not None else ""
    if pending is not None:
        state = "Login in progress"
    elif action_required or len(active) > 1 or any(item.unavailable for item in active):
        state = "Action required"
    elif active:
        state = "Connected"
    else:
        state = "Disconnected"
    return ProviderAccountSummary(
        provider=provider,
        label=_provider_label(provider),
        state=state,
        masked_identifier=masked_identifier,
        has_active_account=bool(active),
        can_restore=bool(disabled),
        login_in_progress=pending is not None,
        action_required=state == "Action required",
    )


def _provider_readiness(provider: str) -> None:
    try:
        verify_account_readiness()
    except RelayFailure as error:
        raise RelayAccountError("Codex account readiness could not be verified") from error


def _rollback(client: RelayManagementClient, pending: PendingAccountOperation) -> None:
    credentials = client.credentials(pending.provider)
    for credential in sorted(
        credentials, key=lambda item: item.opaque_id == pending.previous_credential_id
    ):
        should_be_disabled = credential.opaque_id != pending.previous_credential_id
        if credential.disabled != should_be_disabled:
            client.set_disabled(
                pending.provider,
                credential.opaque_id,
                disabled=should_be_disabled,
            )
    if pending.previous_credential_id and not any(
        credential.opaque_id == pending.previous_credential_id for credential in credentials
    ):
        raise RelayAccountError("The previous relay account could not be restored")
    _clear_pending(pending.provider)


def _complete_login(
    client: RelayManagementClient, pending: PendingAccountOperation
) -> tuple[RelayCredential, ...]:
    credentials = client.credentials(pending.provider)
    active = [credential for credential in credentials if not credential.disabled]
    replacements = [
        credential
        for credential in active
        if credential.opaque_id != pending.previous_credential_id
    ]
    candidates = _sorted_credentials(tuple(replacements or active))
    if not candidates:
        _rollback(client, pending)
        raise RelayAccountError("The new relay account was not created")
    selected = candidates[0]
    try:
        for credential in active:
            if credential.opaque_id != selected.opaque_id:
                client.set_disabled(pending.provider, credential.opaque_id, disabled=True)
        _provider_readiness(pending.provider)
    except (RelayAccountError, RelayManagementError, RelayFailure) as error:
        _rollback(client, pending)
        if isinstance(error, RelayAccountError):
            raise
        raise RelayAccountError("The new relay account failed readiness verification") from error
    _clear_pending(pending.provider)
    return client.credentials(pending.provider)


def _reconcile_locked(
    provider: str, client: RelayManagementClient
) -> tuple[tuple[RelayCredential, ...], PendingAccountOperation | None]:
    pending = _read_pending(provider)
    if pending is None:
        return client.credentials(provider), None
    if not pending.oauth_state or pending.expires_at <= int(time.time()):
        if pending.oauth_state:
            client.cancel_oauth(pending.oauth_state)
        _rollback(client, pending)
        return client.credentials(provider), None
    status = client.oauth_status(pending.oauth_state)
    if status == "wait":
        return client.credentials(provider), pending
    if status == "ok":
        return _complete_login(client, pending), None
    _rollback(client, pending)
    return client.credentials(provider), None


def provider_account_summary(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    try:
        with _provider_lock(selected_provider):
            return _summary(
                selected_provider,
                _client().credentials(selected_provider),
                pending=_read_pending(selected_provider),
            )
    except (RelayAccountError, RelayManagementError, RelayFailure):
        return _summary(selected_provider, (), action_required=True)


def poll_account_login(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        credentials, pending = _reconcile_locked(selected_provider, _client())
        return _summary(selected_provider, credentials, pending=pending)


def start_account_login(provider: str) -> AccountLoginStart:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        client = _client()
        credentials, pending = _reconcile_locked(selected_provider, client)
        if pending is not None:
            raise RelayAccountError("A relay account login is already in progress")
        active = [credential for credential in credentials if not credential.disabled]
        if len(active) > 1:
            raise RelayAccountError("Resolve duplicate active relay accounts first")
        previous_id = active[0].opaque_id if active else ""
        operation = "reconnect" if previous_id else "connect"
        expires_at = int(time.time()) + OAUTH_OPERATION_SECONDS
        try:
            started = client.start_oauth(selected_provider)
        except RelayManagementError as error:
            raise RelayAccountError("The relay account login could not start") from error
        operation_state = PendingAccountOperation(
            oauth_state=started.state,
            provider=selected_provider,
            operation=operation,
            previous_credential_id=previous_id,
            expires_at=expires_at,
        )
        try:
            _write_pending(operation_state)
        except RelayAccountError:
            try:
                client.cancel_oauth(started.state)
            except RelayManagementError as cancellation_error:
                raise RelayAccountError(
                    "The relay account login state could not be saved or cancelled safely"
                ) from cancellation_error
            raise
        try:
            if previous_id:
                client.set_disabled(selected_provider, previous_id, disabled=True)
        except RelayManagementError as error:
            try:
                client.cancel_oauth(started.state)
            except RelayManagementError as cancellation_error:
                raise RelayAccountError(
                    "The relay account login could not be cancelled safely"
                ) from cancellation_error
            _rollback(client, operation_state)
            raise RelayAccountError(
                "The previous relay account could not be disabled safely"
            ) from error
        return AccountLoginStart(
            provider=selected_provider,
            authorization_url=started.authorization_url,
            expires_at=expires_at,
        )


def cancel_account_login(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        client = _client()
        pending = _read_pending(selected_provider)
        if pending is None:
            return _summary(selected_provider, client.credentials(selected_provider))
        if pending.oauth_state:
            client.cancel_oauth(pending.oauth_state)
        _rollback(client, pending)
        return _summary(selected_provider, client.credentials(selected_provider))


def disconnect_account(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        client = _client()
        credentials, pending = _reconcile_locked(selected_provider, client)
        if pending is not None:
            raise RelayAccountError("Cancel the relay account login first")
        for credential in credentials:
            if not credential.disabled:
                client.set_disabled(selected_provider, credential.opaque_id, disabled=True)
        return _summary(selected_provider, client.credentials(selected_provider))


def restore_account(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        client = _client()
        credentials, pending = _reconcile_locked(selected_provider, client)
        if pending is not None:
            raise RelayAccountError("Cancel the relay account login first")
        if any(not credential.disabled for credential in credentials):
            raise RelayAccountError("Disconnect the active account before restoring another")
        disabled = _sorted_credentials(
            tuple(credential for credential in credentials if credential.disabled)
        )
        if not disabled:
            raise RelayAccountError("No disabled relay account is available to restore")
        selected = disabled[0]
        for credential in credentials:
            should_disable = credential.opaque_id != selected.opaque_id
            if credential.disabled != should_disable:
                client.set_disabled(
                    selected_provider,
                    credential.opaque_id,
                    disabled=should_disable,
                )
        try:
            _provider_readiness(selected_provider)
        except (RelayAccountError, RelayManagementError, RelayFailure):
            client.set_disabled(selected_provider, selected.opaque_id, disabled=True)
            raise
        return _summary(selected_provider, client.credentials(selected_provider))


def forget_account(provider: str) -> ProviderAccountSummary:
    selected_provider = _selected_provider(provider)
    with _provider_lock(selected_provider):
        client = _client()
        credentials, pending = _reconcile_locked(selected_provider, client)
        if pending is not None:
            raise RelayAccountError("Cancel the relay account login first")
        active = [credential for credential in credentials if not credential.disabled]
        if len(active) > 1:
            raise RelayAccountError("Resolve duplicate active relay accounts first")
        candidates = active or _sorted_credentials(credentials)
        if not candidates:
            raise RelayAccountError("No relay account is available to forget")
        client.delete(selected_provider, candidates[0].opaque_id)
        return _summary(selected_provider, client.credentials(selected_provider))


def active_account_identity() -> str:
    """Reject a shared account switch or duplicate active accounts before publication."""
    try:
        with _provider_lock("codex"):
            if _read_pending("codex") is not None:
                raise RelayFailure(
                    "account_switching",
                    "A laptop-wide Codex login is in progress. Try again after it finishes.",
                )
            active = [item for item in _client().credentials("codex") if not item.disabled]
            if len(active) != 1 or active[0].unavailable:
                raise RelayFailure(
                    "account_unavailable",
                    "The shared Codex connection needs administrator attention.",
                )
            return hashlib.sha256(active[0].opaque_id.encode()).hexdigest()
    except (RelayManagementError, RelayAccountError) as error:
        raise RelayFailure(
            "account_unavailable", "The shared Codex connection could not be checked."
        ) from error
