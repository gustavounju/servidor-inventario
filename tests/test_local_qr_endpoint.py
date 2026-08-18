from flask import Flask

from blueprints.bp_setup import bp_setup


def test_local_qr_endpoint_returns_png():
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.register_blueprint(bp_setup)

    with app.test_client() as client:
        response = client.get("/qr-code?data=https://localhost/pc/TEST-01&size=150")

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG")
