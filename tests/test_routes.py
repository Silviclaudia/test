from app import create_app, db
from app.models import User


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


def test_register_page_loads():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/register")

    assert response.status_code == 200
    assert b"Create your account" in response.data


def test_register_creates_user():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        response = client.post(
            "/register",
            data={
                "name": "studyuser",
                "email": "study@example.com",
                "password": "secure-password",
                "confirm_password": "secure-password",
                "terms": "on",
            },
        )

    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email="study@example.com").one()
        assert user.username == "studyuser"
        assert user.password_hash != "secure-password"
        assert user.check_password("secure-password")
