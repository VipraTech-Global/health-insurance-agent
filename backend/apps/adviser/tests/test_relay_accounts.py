import json
from dataclasses import replace

import pytest

from apps.adviser import relay_accounts as accounts
from apps.adviser.ai import RelayFailure
from apps.adviser.relay_management import RelayCredential, RelayOAuthStart


def credential(id, disabled=False):
    return RelayCredential(id, "codex", disabled, False, "p***@e***.com", "2026-09-09T00:00:00Z")


class FakeClient:
    def __init__(self):
        self.items = [credential("old")]
        self.state = "wait"
        self.cancelled = []

    def credentials(self, provider):
        return tuple(self.items)

    def set_disabled(self, provider, id, *, disabled):
        self.items = [
            replace(item, disabled=disabled) if item.opaque_id == id else item
            for item in self.items
        ]

    def start_oauth(self, provider):
        return RelayOAuthStart("https://auth.openai.com/oauth/authorize?state=s", "s")

    def oauth_status(self, state):
        return self.state

    def cancel_oauth(self, state):
        self.cancelled.append(state)

    def delete(self, provider, id):
        self.items = [item for item in self.items if item.opaque_id != id]


@pytest.fixture
def client(tmp_path, settings, monkeypatch):
    settings.AI_RELAY_STATE_DIR = tmp_path / "shared-state"
    fake = FakeClient()
    monkeypatch.setattr(accounts, "_client", lambda: fake)
    monkeypatch.setattr(accounts, "_provider_readiness", lambda _: None)
    return fake


def test_switch_preserves_marker_permissions_and_get_is_readonly(client, settings):
    accounts.start_account_login("codex")
    marker = settings.AI_RELAY_STATE_DIR / "codex.pending.json"
    assert marker.stat().st_mode & 0o777 == 0o600
    assert set(json.loads(marker.read_text())) == {
        "oauth_state",
        "provider",
        "operation",
        "previous_credential_id",
        "expires_at",
    }
    client.items.append(credential("new"))
    client.state = "ok"
    assert accounts.provider_account_summary("codex").login_in_progress
    assert marker.exists()
    assert accounts.poll_account_login("codex").state == "Connected"
    assert [item.opaque_id for item in client.items if not item.disabled] == ["new"]
    assert not marker.exists()


@pytest.mark.parametrize("failure", ["cancel", "expiry", "readiness"])
def test_failed_oauth_restores_previous_account(client, monkeypatch, failure):
    started = accounts.start_account_login("codex")
    client.items.append(credential("new"))
    if failure == "cancel":
        accounts.cancel_account_login("codex")
    elif failure == "expiry":
        monkeypatch.setattr(accounts.time, "time", lambda: started.expires_at + 1)
        accounts.poll_account_login("codex")
    else:
        client.state = "ok"

        def fail(_):
            raise accounts.RelayAccountError("Readiness failed")

        monkeypatch.setattr(accounts, "_provider_readiness", fail)
        with pytest.raises(accounts.RelayAccountError):
            accounts.poll_account_login("codex")
    assert [item.opaque_id for item in client.items if not item.disabled] == ["old"]


def test_cancel_first_login_disables_new_credential(client):
    client.items = []
    accounts.start_account_login("codex")
    client.items.append(credential("new"))
    accounts.cancel_account_login("codex")
    assert not any(not item.disabled for item in client.items)


def test_disconnect_restore_forget(client):
    assert accounts.disconnect_account("codex").state == "Disconnected"
    assert accounts.restore_account("codex").state == "Connected"
    assert accounts.forget_account("codex").state == "Disconnected"
    assert client.items == []


def test_duplicate_accounts_and_pending_logins_block_generation(client):
    client.items.append(credential("duplicate"))
    with pytest.raises(RelayFailure):
        accounts.active_account_identity()
    client.items.pop()
    accounts.start_account_login("codex")
    with pytest.raises(RelayFailure):
        accounts.active_account_identity()


def test_marker_symlink_is_rejected(client, settings, tmp_path):
    accounts._state_dir()
    target = tmp_path / "protected"
    target.write_text("not a marker")
    (settings.AI_RELAY_STATE_DIR / "codex.pending.json").symlink_to(target)
    with pytest.raises(accounts.RelayAccountError):
        accounts.start_account_login("codex")
    assert target.read_text() == "not a marker"
