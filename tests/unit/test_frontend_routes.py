import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_frontend_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "OneWay Sentinel" in response.text
    assert '<div id="root"></div>' in response.text


def test_frontend_static_assets():
    res_css = client.get("/static/styles.css")
    assert res_css.status_code == 200
    assert "--bg-app" in res_css.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "ReactDOM" in res_js.text
