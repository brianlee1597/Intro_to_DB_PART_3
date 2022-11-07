# Project 1, Part 3 Submission from Brian Lee, Huifeng Wu

This repository holds the Flask / Jinja stack with server.py serving SQL table queries from
REST API Endpoints. And the HTML with Jinja Templates and CSS files are in the templates folder.

## Installation

To get this project up and running on your local environment:

First, if you don't have postgresql installed on your OS, install brew (if you haven't already), then run:

```bash
  brew install postgresql
```

Then run:

```bash
  python3 -m venv venv
  . venv/bin/activate
  pip install flask
```

Then try running using

```bash
python3 server.py
```

if you are getting an error after this step, execute code below on terminal then try again:

```bash
pip install psycopg2
```

After this point, the server should get running, and you will be able to see the
HTML pages in the templates folder.
