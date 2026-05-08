from app import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def test_homepage_loads():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"Good to see you" in response.data
