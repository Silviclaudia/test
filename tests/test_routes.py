from app import create_app, db
from app.models import Flashcard, StudySet, User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def test_homepage_loads():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"Good to see you" in response.data


def test_homepage_shows_recent_public_study_sets_only():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

        private_set = StudySet(
            title="Private Set",
            description="Should not appear on homepage",
            is_public=False,
            owner=user,
            flashcards=[Flashcard(question="Secret", answer="Hidden")],
        )
        public_set = StudySet(
            title="Public Biology Set",
            description="Should appear on homepage",
            is_public=True,
            owner=user,
            flashcards=[Flashcard(question="Cell", answer="Basic unit of life")],
        )
        db.session.add_all([private_set, public_set])
        db.session.commit()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"Public Biology Set" in response.data
    assert b"Private Set" not in response.data
    assert b"by studyuser" in response.data


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


def test_create_study_set_page_requires_login():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/study-sets/new")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_study_set_page_loads_for_logged_in_user():
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
        response = client.get("/study-sets/new")

    assert response.status_code == 200
    assert b"Create New Study Set" in response.data


def test_create_study_set_saves_flashcards_for_logged_in_user():
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
        response = client.post(
            "/study-sets/new",
            data={
                "title": "Biology 101",
                "description": "Cell basics",
                "term": ["Cell", "Nucleus"],
                "definition": ["Basic unit of life", "Controls the cell"],
            },
        )

    assert response.status_code == 302

    with app.app_context():
        study_set = StudySet.query.filter_by(title="Biology 101").one()
        assert response.headers["Location"].endswith(f"/study-sets/{study_set.id}")
        assert study_set.description == "Cell basics"
        assert study_set.owner.username == "studyuser"

        flashcards = Flashcard.query.order_by(Flashcard.id).all()
        assert len(flashcards) == 2
        assert flashcards[0].question == "Cell"
        assert flashcards[0].answer == "Basic unit of life"
        assert flashcards[1].question == "Nucleus"
        assert flashcards[1].answer == "Controls the cell"


def test_dashboard_navigation_links_to_working_routes():
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
        response = client.get("/")

    assert response.status_code == 200
    assert b'href="/"' in response.data
    assert b'href="/study-sets"' in response.data
    assert b'href="/study-sets/new"' in response.data
    assert b'href="/analytics"' in response.data
    assert b"nav-item-disabled" in response.data


def test_study_sets_page_requires_login():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/study-sets")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_study_sets_page_shows_current_users_sets_only():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("secure-password")
        db.session.add_all([user, other_user])
        db.session.commit()

        biology = StudySet(
            title="Biology 101",
            description="Cell basics",
            owner=user,
            flashcards=[
                Flashcard(question="Cell", answer="Basic unit of life"),
                Flashcard(question="Nucleus", answer="Controls the cell"),
            ],
        )
        chemistry = StudySet(
            title="Chemistry 101",
            description="Atoms and molecules",
            owner=other_user,
            flashcards=[
                Flashcard(question="Atom", answer="Small unit of matter"),
            ],
        )
        db.session.add_all([biology, chemistry])
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get("/study-sets")

    assert response.status_code == 200
    assert b"Biology 101" in response.data
    assert b"Cell basics" in response.data
    assert b"2 cards" in response.data
    assert b"Chemistry 101" not in response.data


def test_study_sets_page_shows_empty_state():
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
        response = client.get("/study-sets")

    assert response.status_code == 200
    assert b"No study sets yet" in response.data


def test_study_set_detail_requires_login():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/study-sets/1")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_study_set_detail_shows_flashcards_for_owner():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

        study_set = StudySet(
            title="Biology 101",
            description="Cell basics",
            owner=user,
            flashcards=[
                Flashcard(question="Cell", answer="Basic unit of life"),
                Flashcard(question="Nucleus", answer="Controls the cell"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get(f"/study-sets/{study_set_id}")

    assert response.status_code == 200
    assert b"Biology 101" in response.data
    assert b"Cell basics" in response.data
    assert b"Cell" in response.data
    assert b"Basic unit of life" in response.data
    assert b"Nucleus" in response.data
    assert b"Controls the cell" in response.data


def test_study_set_detail_hides_other_users_sets():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("secure-password")
        db.session.add_all([user, other_user])
        db.session.commit()

        study_set = StudySet(
            title="Chemistry 101",
            description="Atoms and molecules",
            owner=other_user,
            flashcards=[
                Flashcard(question="Atom", answer="Small unit of matter"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get(f"/study-sets/{study_set_id}")

    assert response.status_code == 404


def test_study_mode_requires_login():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/study-sets/1/study")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_study_mode_shows_first_flashcard_for_owner():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

        study_set = StudySet(
            title="Biology 101",
            description="Cell basics",
            owner=user,
            flashcards=[
                Flashcard(question="Cell", answer="Basic unit of life"),
                Flashcard(question="Nucleus", answer="Controls the cell"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get(f"/study-sets/{study_set_id}/study")

    assert response.status_code == 200
    assert b"Study Biology 101" in response.data
    assert b"Card <span id=\"current-card-number\">1</span> of 2" in response.data
    assert b"Cell" in response.data
    assert b"Basic unit of life" in response.data
    assert b"Show answer" in response.data


def test_study_mode_hides_other_users_sets():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("secure-password")
        db.session.add_all([user, other_user])
        db.session.commit()

        study_set = StudySet(
            title="Chemistry 101",
            description="Atoms and molecules",
            owner=other_user,
            flashcards=[
                Flashcard(question="Atom", answer="Small unit of matter"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get(f"/study-sets/{study_set_id}/study")

    assert response.status_code == 404


def test_edit_study_set_requires_login():
    app = create_app(TestConfig)

    with app.test_client() as client:
        response = client.get("/study-sets/1/edit")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_edit_study_set_updates_metadata_and_flashcards():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

        study_set = StudySet(
            title="Original Title",
            description="Original description",
            is_public=True,
            owner=user,
            flashcards=[
                Flashcard(question="Old term 1", answer="Old definition 1"),
                Flashcard(question="Old term 2", answer="Old definition 2"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id
        flashcard_one_id = study_set.flashcards[0].id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.post(
            f"/study-sets/{study_set_id}/edit",
            data={
                "title": "Updated Title",
                "description": "Updated description",
                "flashcard_id": [str(flashcard_one_id), ""],
                "term": ["Updated term 1", "New term 3"],
                "definition": ["Updated definition 1", "New definition 3"],
            },
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/study-sets/{study_set_id}")

    with app.app_context():
        updated_set = db.session.get(StudySet, study_set_id)
        assert updated_set is not None
        assert updated_set.title == "Updated Title"
        assert updated_set.description == "Updated description"
        assert updated_set.is_public is False

        flashcards = Flashcard.query.filter_by(study_set_id=study_set_id).order_by(Flashcard.id).all()
        assert len(flashcards) == 2
        assert flashcards[0].question == "Updated term 1"
        assert flashcards[0].answer == "Updated definition 1"
        assert flashcards[1].question == "New term 3"
        assert flashcards[1].answer == "New definition 3"


def test_delete_study_set_removes_flashcards():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()

        study_set = StudySet(
            title="Delete me",
            description="To be removed",
            owner=user,
            flashcards=[
                Flashcard(question="Term A", answer="Definition A"),
                Flashcard(question="Term B", answer="Definition B"),
            ],
        )
        db.session.add(study_set)
        db.session.commit()
        study_set_id = study_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.post(f"/study-sets/{study_set_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/study-sets")

    with app.app_context():
        assert db.session.get(StudySet, study_set_id) is None
        remaining_flashcards = Flashcard.query.filter_by(study_set_id=study_set_id).all()
        assert remaining_flashcards == []


def test_edit_delete_hide_other_users_study_sets():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("secure-password")
        db.session.add_all([user, other_user])
        db.session.commit()

        other_set = StudySet(
            title="Other set",
            description="Owned by someone else",
            owner=other_user,
            flashcards=[Flashcard(question="Term", answer="Definition")],
        )
        db.session.add(other_set)
        db.session.commit()
        other_set_id = other_set.id

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        edit_response = client.get(f"/study-sets/{other_set_id}/edit")
        delete_response = client.post(f"/study-sets/{other_set_id}/delete")

    assert edit_response.status_code == 404
    assert delete_response.status_code == 404


def test_analytics_shows_real_user_stats():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        user = User(username="studyuser", email="study@example.com")
        user.set_password("secure-password")
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("secure-password")
        db.session.add_all([user, other_user])
        db.session.commit()

        user_set_one = StudySet(
            title="Biology 101",
            description="Cell basics",
            is_public=True,
            owner=user,
            flashcards=[
                Flashcard(question="Cell", answer="Basic unit of life"),
                Flashcard(question="Nucleus", answer="Controls the cell"),
            ],
        )
        user_set_two = StudySet(
            title="Chemistry 101",
            description="Atoms",
            is_public=False,
            owner=user,
            flashcards=[
                Flashcard(question="Atom", answer="Small unit of matter"),
            ],
        )
        other_set = StudySet(
            title="Physics 101",
            description="For another user",
            is_public=True,
            owner=other_user,
            flashcards=[
                Flashcard(question="Force", answer="Push or pull"),
                Flashcard(question="Mass", answer="Amount of matter"),
                Flashcard(question="Energy", answer="Ability to do work"),
            ],
        )
        db.session.add_all([user_set_one, user_set_two, other_set])
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/login",
            data={
                "email": "study@example.com",
                "password": "secure-password",
            },
        )
        response = client.get("/analytics")

    assert response.status_code == 200
    assert b"Analytics" in response.data
    assert b"Total Cards" in response.data
    assert b"Total Study Sets" in response.data
    assert b"Public Study Sets" in response.data
    assert b"Avg Cards Per Set" in response.data
    assert b">3<" in response.data
    assert b">2<" in response.data
    assert b">1<" in response.data
    assert b">1.5<" in response.data
    assert b"Biology 10" in response.data
    assert b"Chemistry " in response.data
    assert b"Physics 101" not in response.data
