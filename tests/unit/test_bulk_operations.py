import pytest
from app.models import AcestreamChannel
from app.services.channel_service import ChannelService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def setup_channels(db_session):
    ch1 = AcestreamChannel(id="bulk1", name="Bulk 1", is_active=True)
    ch2 = AcestreamChannel(id="bulk2", name="Bulk 2", is_active=True)
    ch3 = AcestreamChannel(id="bulk3", name="Bulk 3", is_active=False)
    db_session.add_all([ch1, ch2, ch3])
    db_session.commit()
    return [ch1, ch2, ch3]

def test_bulk_edit_success(db_session):
    setup_channels(db_session)
    resp = client.put("/v1/channels/bulk_edit", json={"channel_ids": ["bulk1", "bulk2"], "fields": {"group": "TestGroup"}})
    assert resp.status_code == 200
    data = resp.json()
    assert all(ch['group'] == 'TestGroup' for ch in data)

def test_bulk_edit_partial_failure(db_session):
    setup_channels(db_session)
    resp = client.put("/v1/channels/bulk_edit", json={"channel_ids": ["bulk1", "notfound"], "fields": {"group": "TestGroup2"}})
    assert resp.status_code == 200
    data = resp.json()
    found = [ch for ch in data if ch['id'] == 'bulk1']
    assert found and found[0]['group'] == 'TestGroup2'

def test_bulk_delete_success(db_session):
    setup_channels(db_session)
    resp = client.post("/v1/channels/bulk_delete", json={"channel_ids": ["bulk1", "bulk2"]})
    assert resp.status_code == 200
    # Check that only bulk3 remains
    resp2 = client.get("/v1/channels")
    ids = [ch['id'] for ch in resp2.json()]
    assert "bulk3" in ids and "bulk1" not in ids and "bulk2" not in ids

def test_bulk_activate_success(db_session):
    setup_channels(db_session)
    resp = client.post("/v1/channels/bulk_activate", json={"channel_ids": ["bulk3"], "active": True})
    assert resp.status_code == 200
    # Check that bulk3 is now active
    resp2 = client.get("/v1/channels")
    ch3 = next(ch for ch in resp2.json() if ch['id'] == 'bulk3')
    assert ch3['is_active'] is True

def test_bulk_activate_error(db_session):
    setup_channels(db_session)
    resp = client.post("/v1/channels/bulk_activate", json={"channel_ids": ["notfound"], "active": True})
    assert resp.status_code == 200
    # Should not raise, but no channels updated
    data = resp.json()
    assert data == []
