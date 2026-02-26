from fastapi.testclient import TestClient

from pipeline_visibility.backend.main import app


client = TestClient(app)


def test_dashboard_overview_requires_org_header():
    response = client.get('/api/v1/dashboard/overview')
    assert response.status_code == 400


def test_dashboard_overview_success():
    response = client.get('/api/v1/dashboard/overview?days=30', headers={"X-Org-Id": "org-1"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 3
    assert "alerts" in body


def test_trigger_sync_requires_role():
    response = client.post('/api/v1/integrations/ga4/sync', headers={"X-Org-Id": "org-1", "X-User-Role": "viewer"})
    assert response.status_code == 403
