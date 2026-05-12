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


def test_login_page_loads():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert b"Welcome Back" in response.data


def test_login_with_email_starts_session():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()
        user_id = str(user.id)

    with app.test_client() as client:
        response = client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )

        assert response.status_code == 302
        with client.session_transaction() as session:
            assert session["_user_id"] == user_id


def test_login_rejects_wrong_password():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        response = client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 400
        assert b"Invalid email/username or password." in response.data
        with client.session_transaction() as session:
            assert "_user_id" not in session


def test_logout_clears_session():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get("/logout")

        assert response.status_code == 302
        with client.session_transaction() as session:
            assert "_user_id" not in session
