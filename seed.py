"""Seed the database with demo data for showcase purposes.

Usage:
    python seed.py             # add demo data (skip anything that already exists)
    python seed.py --reset     # wipe existing data first, then seed fresh
"""
import sys
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Flashcard, StudySet, User


USERS = [
    {
        "username": "demo",
        "email": "demo@uwa.edu.au",
        "password": "demo1234",
        "streak": 7,
        "achievements": 2,
        "last_active_days_ago": 0,
    },
    {
        "username": "alice",
        "email": "alice@student.uwa.edu.au",
        "password": "alice1234",
        "streak": 12,
        "achievements": 3,
        "last_active_days_ago": 0,
    },
    {
        "username": "jordan",
        "email": "jordan@student.uwa.edu.au",
        "password": "jordan1234",
        "streak": 5,
        "achievements": 2,
        "last_active_days_ago": 1,
    },
    {
        "username": "maya",
        "email": "maya@student.uwa.edu.au",
        "password": "maya1234",
        "streak": 30,
        "achievements": 4,
        "last_active_days_ago": 0,
    },
    {
        "username": "sam",
        "email": "sam@student.uwa.edu.au",
        "password": "sam1234",
        "streak": 1,
        "achievements": 1,
        "last_active_days_ago": 2,
    },
]


SETS = [
    {
        "owner": "alice",
        "title": "Python Basics",
        "description": "Core syntax, built-in types, and the small idioms you'll use every day.",
        "is_public": True,
        "cards": [
            ("What does len() return for a string?", "The number of characters in the string."),
            ("How do you create an empty dictionary?", "Use {} or dict()."),
            ("What is a list comprehension?", "A concise way to build a list, e.g. [x*2 for x in nums]."),
            ("What does the 'is' operator check?", "Whether two references point to the same object."),
            ("How do you open a file safely?", "Use a 'with' statement: with open(path) as f: ..."),
            ("What is a tuple?", "An immutable ordered collection of values."),
            ("How do you swap two variables?", "a, b = b, a"),
            ("What does the .strip() method do?", "Removes leading and trailing whitespace."),
        ],
    },
    {
        "owner": "alice",
        "title": "Data Structures",
        "description": "Big-O cheats and when to reach for which structure.",
        "is_public": True,
        "cards": [
            ("Average lookup time for a hash map?", "O(1)"),
            ("Worst-case insertion in a balanced BST?", "O(log n)"),
            ("Which structure is FIFO?", "A queue."),
            ("Which structure is LIFO?", "A stack."),
            ("What is a heap good for?", "Repeatedly extracting the min or max element."),
            ("Time to access an element in an array by index?", "O(1)"),
            ("What is amortized analysis?", "Average cost per operation over a sequence of operations."),
        ],
    },
    {
        "owner": "alice",
        "title": "SQL Joins",
        "description": "Notes on how each join type behaves with NULLs and duplicates.",
        "is_public": False,
        "cards": [
            ("INNER JOIN returns?", "Rows where the join condition matches in both tables."),
            ("LEFT JOIN returns?", "All rows from the left table; matching rows from the right (NULL if no match)."),
            ("FULL OUTER JOIN returns?", "All rows from both tables, with NULLs where there's no match."),
            ("What is a CROSS JOIN?", "The Cartesian product of two tables."),
            ("Difference between WHERE and HAVING?", "WHERE filters rows; HAVING filters groups after aggregation."),
        ],
    },
    {
        "owner": "jordan",
        "title": "Human Anatomy: Skeletal System",
        "description": "Bones of the appendicular and axial skeleton.",
        "is_public": True,
        "cards": [
            ("Largest bone in the human body?", "The femur."),
            ("How many bones are in the adult human body?", "206."),
            ("What is the collarbone also called?", "The clavicle."),
            ("The kneecap is also known as?", "The patella."),
            ("The smallest bone in the body?", "The stapes (in the middle ear)."),
            ("Bones of the wrist are collectively called?", "Carpals."),
            ("How many cervical vertebrae do humans have?", "Seven."),
            ("The shoulder blade is also called?", "The scapula."),
            ("Bone running along the thumb side of the forearm?", "The radius."),
            ("Bones forming the rib cage attach to which bone in front?", "The sternum."),
        ],
    },
    {
        "owner": "jordan",
        "title": "Pharmacology Essentials",
        "description": "Common drug classes and what they do.",
        "is_public": True,
        "cards": [
            ("What do beta-blockers treat?", "High blood pressure, arrhythmias, and angina."),
            ("Mechanism of action of statins?", "Inhibit HMG-CoA reductase to lower cholesterol."),
            ("What are SSRIs used for?", "Depression and anxiety disorders."),
            ("Common use of ACE inhibitors?", "Hypertension and heart failure."),
            ("Antibiotic class that ends in '-cillin'?", "Penicillins."),
            ("What is the antidote for paracetamol overdose?", "N-acetylcysteine."),
        ],
    },
    {
        "owner": "maya",
        "title": "Spanish: Common Verbs",
        "description": "High-frequency Spanish verbs, infinitive form.",
        "is_public": True,
        "cards": [
            ("ser", "to be (permanent)"),
            ("estar", "to be (temporary or location)"),
            ("tener", "to have"),
            ("hacer", "to do / to make"),
            ("ir", "to go"),
            ("poder", "to be able to / can"),
            ("decir", "to say / to tell"),
            ("ver", "to see"),
        ],
    },
    {
        "owner": "maya",
        "title": "Japanese Greetings",
        "description": "Everyday phrases, romaji and meaning.",
        "is_public": True,
        "cards": [
            ("Ohayou gozaimasu", "Good morning (polite)"),
            ("Konnichiwa", "Hello / Good afternoon"),
            ("Konbanwa", "Good evening"),
            ("Arigatou gozaimasu", "Thank you (polite)"),
            ("Sumimasen", "Excuse me / I'm sorry"),
            ("Hajimemashite", "Nice to meet you"),
        ],
    },
    {
        "owner": "sam",
        "title": "Ancient Rome",
        "description": "Key dates, figures, and turning points.",
        "is_public": True,
        "cards": [
            ("Year Rome was traditionally founded?", "753 BCE."),
            ("First Roman emperor?", "Augustus."),
            ("Year the Western Roman Empire fell?", "476 CE."),
            ("Who crossed the Rubicon in 49 BCE?", "Julius Caesar."),
            ("What was the Pax Romana?", "A roughly 200-year period of relative peace and stability across the empire."),
            ("Famous Roman road network reached how many km?", "Over 80,000 km at its peak."),
            ("Who wrote 'The Aeneid'?", "Virgil."),
        ],
    },
    {
        "owner": "sam",
        "title": "WWII Pacific Theater",
        "description": "Major battles and turning points.",
        "is_public": True,
        "cards": [
            ("Date of the attack on Pearl Harbor?", "7 December 1941."),
            ("Turning point naval battle in June 1942?", "Battle of Midway."),
            ("What was Operation Downfall?", "The planned Allied invasion of Japan, never executed."),
            ("Date Japan formally surrendered?", "2 September 1945."),
            ("Codename of the first atomic bomb dropped?", "Little Boy."),
            ("Island battle famous for the flag-raising photograph?", "Iwo Jima."),
        ],
    },
    {
        "owner": "demo",
        "title": "Web Dev Essentials",
        "description": "Concepts every web developer should know cold.",
        "is_public": True,
        "cards": [
            ("What does HTTP stand for?", "HyperText Transfer Protocol."),
            ("What is CORS?", "Cross-Origin Resource Sharing — browser policy controlling cross-origin requests."),
            ("HTTP status 404 means?", "Not Found — the requested resource doesn't exist."),
            ("HTTP status 500 means?", "Internal Server Error."),
            ("What is the DOM?", "Document Object Model — a tree representation of an HTML document."),
            ("What does REST stand for?", "Representational State Transfer."),
            ("Difference between PUT and PATCH?", "PUT replaces the entire resource; PATCH modifies part of it."),
            ("What is a CDN?", "Content Delivery Network — geographically distributed servers that cache content."),
        ],
    },
    {
        "owner": "demo",
        "title": "JavaScript Quirks",
        "description": "The bits that trip people up.",
        "is_public": False,
        "cards": [
            ("typeof null returns?", "'object' (a long-standing bug kept for backwards compatibility)."),
            ("Difference between == and ===?", "== does type coercion; === is strict equality."),
            ("What does 'this' refer to in an arrow function?", "The 'this' of the enclosing lexical scope."),
            ("What is hoisting?", "Variable and function declarations being moved to the top of their scope."),
            ("What is the event loop?", "Mechanism that handles async callbacks by processing the call stack and task queue."),
        ],
    },
]


def seed():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            print("→ Wiping existing data...")
            Flashcard.query.delete()
            StudySet.query.delete()
            User.query.delete()
            db.session.commit()

        users_by_name = {}
        created_users = 0
        for spec in USERS:
            existing = User.query.filter_by(username=spec["username"]).first()
            if existing:
                users_by_name[spec["username"]] = existing
                continue
            user = User(
                username=spec["username"],
                email=spec["email"],
                streak=spec["streak"],
                achievements=spec["achievements"],
                last_active=datetime.now(timezone.utc) - timedelta(days=spec["last_active_days_ago"]),
            )
            user.set_password(spec["password"])
            db.session.add(user)
            users_by_name[spec["username"]] = user
            created_users += 1
        db.session.commit()

        created_sets = 0
        for spec in SETS:
            owner = users_by_name[spec["owner"]]
            existing = StudySet.query.filter_by(title=spec["title"], user_id=owner.id).first()
            if existing:
                continue
            study_set = StudySet(
                title=spec["title"],
                description=spec["description"],
                is_public=spec["is_public"],
                owner=owner,
                flashcards=[Flashcard(question=q, answer=a) for q, a in spec["cards"]],
            )
            db.session.add(study_set)
            created_sets += 1
        db.session.commit()

        print(f"→ Created {created_users} new users and {created_sets} new study sets.")
        print("\nDemo logins (username / password):")
        for spec in USERS:
            print(f"  {spec['username']:<8}/ {spec['password']}")


if __name__ == "__main__":
    seed()
