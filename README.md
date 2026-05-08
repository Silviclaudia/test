# Agile Web Development Project

This repository contains the starter Flask application for the CITS3403/CITS5505
group project. The current concept is a study dashboard where users can create
flashcard study sets, practise with different study modes, and view public study
sets from other users.

## Team Members

| UWA ID | Name | GitHub Username |
| --- | --- | --- |
| TODO | TODO | TODO |

## Project Structure

```text
app/
  static/css/        CSS files
  templates/         Jinja HTML templates
  __init__.py        Flask application factory
  models.py          SQLAlchemy database models
  routes.py          Flask routes
tests/               Pytest tests
config.py            App configuration
run.py               Local development entry point
```

## Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Flask development server:

```bash
python run.py
```

Open <http://127.0.0.1:5000> in your browser.

## Run Tests

```bash
pytest
```
