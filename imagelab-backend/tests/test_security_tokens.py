from datetime import UTC, datetime, timedelta

import freezegun
from fastapi.testclient import TestClient


def test_token_expiration_returns_http_403(client: TestClient):
    """Verify share token expiration returns HTTP 403 when time advances past expires_at using freezegun."""
    initial_time = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)

    with freezegun.freeze_time(initial_time):
        # 1. Create pipeline & share link expiring in 30 minutes
        create_res = client.post(
            "/api/pipelines/",
            json={"name": "Time Sensitive Pipeline", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"},
        )
        assert create_res.status_code == 201
        pipeline_id = create_res.json()["pipeline_id"]

        expires_at = initial_time + timedelta(minutes=30)
        share_res = client.post(
            f"/api/pipelines/{pipeline_id}/share",
            json={
                "version_number": 1,
                "permission": "view",
                "expires_at": expires_at.isoformat(),
            },
        )
        assert share_res.status_code == 201
        token = share_res.json()["token"]

        # 2. Accessing token before expiration -> Success (200 OK)
        lookup_res = client.get(f"/api/share/{token}")
        assert lookup_res.status_code == 200
        assert lookup_res.json()["pipeline_name"] == "Time Sensitive Pipeline"

    # 3. Advance time past expiration date by 31 minutes using freezegun
    future_time = initial_time + timedelta(minutes=31)
    with freezegun.freeze_time(future_time):
        # Accessing expired share link -> HTTP 403 Forbidden
        expired_lookup_res = client.get(f"/api/share/{token}")
        assert expired_lookup_res.status_code == 403
        assert "expired" in expired_lookup_res.json()["detail"].lower()

        # Attempting clone on expired share link -> HTTP 403 Forbidden
        expired_clone_res = client.post(f"/api/share/{token}/clone", json={})
        assert expired_clone_res.status_code == 403
        assert "expired" in expired_clone_res.json()["detail"].lower()

        # Attempting version push on expired share link -> HTTP 403 Forbidden
        expired_version_res = client.post(
            f"/api/share/{token}/versions",
            json={"workspace_json": {}, "pipeline_json": {}},
        )
        assert expired_version_res.status_code == 403
        assert "expired" in expired_version_res.json()["detail"].lower()
