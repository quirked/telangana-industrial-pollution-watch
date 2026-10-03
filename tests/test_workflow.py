import io
import re
from datetime import date

import pytest

from app import create_app


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05"
    b"\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "SECRET_KEY": "test-key",
    })


@pytest.fixture()
def client(app):
    return app.test_client()


def report_payload():
    return {
        "observation_type": "Smoke / Air Emission",
        "title": "Heavy black smoke from industrial chimney",
        "description": "Continuous black smoke has been visible for approximately 30 minutes.",
        "district": "Sangareddy",
        "locality": "Patancheru",
        "address_landmark": "Industrial Area, Sector 4",
        "incident_date": date.today().isoformat(),
        "incident_time": "10:30",
        "industrial_unit_name": "Demo Steel Works",
        "industry_type": "Steel / Sponge Iron",
        "latitude": "",
        "longitude": "",
        "image": (io.BytesIO(PNG_BYTES), "black-smoke.png", "image/png"),
    }


def test_seeded_pages_and_error_handling(client):
    for path in ("/", "/report", "/reports", "/my-reports", "/authority", "/reports/INC-2026-0001"):
        assert client.get(path).status_code == 200
    reports_page = client.get("/reports").get_data(as_text=True)
    assert "Deccan BioChem Works — fictional" not in reports_page
    assert "Patancheru" in reports_page
    assert client.get("/reports/INC-DOES-NOT-EXIST").status_code == 404
    assert client.get("/health").json["status"] == "healthy"


def test_invalid_submission_has_useful_errors(client):
    response = client.post("/report", data={}, content_type="multipart/form-data")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Select what you observed." in page
    assert "Add a JPG, PNG, or WebP image as evidence." in page

    payload = report_payload()
    payload["title"] = "Smoke"
    payload["description"] = "Too short"
    response = client.post("/report", data=payload, content_type="multipart/form-data")
    page = response.get_data(as_text=True)
    assert "Use at least 8 characters for a clear title." in page
    assert "Add at least 20 characters describing what you observed." in page

    oversized = client.post(
        "/report",
        data={"image": (io.BytesIO(b"x" * (8 * 1024 * 1024 + 1)), "large.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert oversized.status_code == 413
    assert "Image is too large" in oversized.get_data(as_text=True)


def test_complete_citizen_to_authority_workflow_and_restart(app, client, tmp_path):
    response = client.post("/report", data=report_payload(), content_type="multipart/form-data")
    assert response.status_code == 302
    location = response.headers["Location"]
    match = re.search(r"/reports/(INC-\d{4}-\d{4})", location)
    assert match
    report_code = match.group(1)

    public_page = client.get(location).get_data(as_text=True)
    assert "Heavy black smoke from industrial chimney" in public_page
    assert "Demo Steel Works" in public_page
    assert "Reported" in public_page
    assert "Citizen supplied" in public_page

    assert report_code in client.get("/my-reports").get_data(as_text=True)
    assert report_code in client.get("/authority").get_data(as_text=True)

    authority_url = f"/authority/reports/{report_code}"
    response = client.post(authority_url, data={
        "status": "Under Review",
        "authority_remark": "Inspection team has been informed.",
        "action_taken": "Report assigned to the Sangareddy review team.",
    })
    assert response.status_code == 302

    response = client.post(authority_url, data={
        "status": "Action in Progress",
        "authority_remark": "Inspection team has been informed.",
        "action_taken": "Site inspection is in progress.",
    })
    assert response.status_code == 302

    updated = client.get(location).get_data(as_text=True)
    assert "Action in Progress" in updated
    assert "Inspection team has been informed." in updated
    assert "Site inspection is in progress." in updated
    assert updated.count("Under Review") >= 1
    assert updated.count("Action in Progress") >= 1
    dashboard = client.get("/authority").get_data(as_text=True)
    assert report_code in dashboard
    assert "Action in Progress" in dashboard

    evidence_match = re.search(r'src="(/uploads/[^"]+)"', updated)
    assert evidence_match
    evidence = client.get(evidence_match.group(1))
    assert evidence.status_code == 200
    assert evidence.mimetype == "image/png"

    restarted = create_app({
        "TESTING": True,
        "DATABASE": app.config["DATABASE"],
        "UPLOAD_FOLDER": app.config["UPLOAD_FOLDER"],
        "SECRET_KEY": "test-key",
    })
    restart_page = restarted.test_client().get(location).get_data(as_text=True)
    assert "Action in Progress" in restart_page
    assert report_code in restart_page
