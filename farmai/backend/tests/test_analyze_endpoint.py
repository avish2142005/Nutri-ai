"""Integration tests for /health and POST /api/analyze endpoints.
"""
import io
from PIL import Image
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _generate_test_image(format: str = "JPEG", size=(224, 224), color=(34, 139, 34)) -> bytes:
    """Generate in-memory sample leaf image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_health_endpoint():
    """Verify /health contract."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "demo_mode" in data


def test_analyze_valid_image():
    """Verify POST /api/analyze end-to-end with mock leaf image."""
    img_bytes = _generate_test_image("JPEG")
    files = {"image": ("leaf.jpg", img_bytes, "image/jpeg")}
    data = {"crop": "Tomato", "lat": 13.3409, "lon": 74.7421}

    response = client.post("/api/analyze", data=data, files=files)
    assert response.status_code == 200
    res = response.json()

    # Verify required keys in response contract
    assert "analysis_id" in res
    SUPPORTED_CROPS = [
        "Tomato", "Potato", "Apple", "Corn", "Rice", "Grape", 
        "Pepper", "Cotton", "Wheat", "Banana", "Brinjal", "Chilli"
    ]
    assert res["crop"] in SUPPORTED_CROPS
    assert "disease" in res
    assert "severity" in res["disease"]
    assert res["disease"]["severity"]["level"] in ["Healthy", "Mild", "Moderate", "Severe"]
    assert "weather" in res
    assert "risk" in res
    assert "recommendations" in res
    assert "explanation" in res
    assert "sources" in res
    assert "warnings" in res

    # Verify explainability factors in risk
    assert len(res["risk"]["factors"]) >= 4
    assert res["risk"]["level"] in ["LOW", "MEDIUM", "HIGH", "UNCERTAIN"]
    assert 0 <= res["risk"]["score"] <= 100


def test_analyze_invalid_file_type():
    """Verify that uploading non-image file returns 422 with clear message."""
    files = {"image": ("malicious.txt", b"not an image", "text/plain")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 422
    assert "Invalid file type" in response.json()["detail"]


def test_analyze_empty_file():
    """Verify that uploading 0-byte file returns 422."""
    files = {"image": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()
