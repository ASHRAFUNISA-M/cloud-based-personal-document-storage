import os
import tempfile
import app as app_module


def test_homepage_loads():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"CloudDocs" in response.data


def test_upload_rejects_unsupported_extension(monkeypatch):
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    response = client.post(
        "/upload",
        data={"category": "Notes", "document": ( __import__("io").BytesIO(b"bad"), "malware.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"file type is not allowed" in response.data
