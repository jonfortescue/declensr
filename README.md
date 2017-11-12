# Declensr
## What this is
**Declensr** is a web-based utility built in [Flask](http://flask.pocoo.org/) designed to aid with studying foreign language grammars. It does this by generating worksheet-style exercises given a description of an arbitrary grammar and a schema for the exercises.

## Dependencies
Declensr depends on:
* Python 2.7
* [Flask](http://flask.pocoo.org/)
* [MongoDB](https://www.mongodb.com/)
* [PyMongo](https://api.mongodb.com/python/current/)
* [Flask_PyMongo](https://github.com/dcrosta/flask-pymongo)

It is also recommended, as per standard Python development practices, that you use `virtualenv` while developing.

## Getting started
To build Declensr:
1. Download and install MongoDB
2. Clone the repo
3. Inside the repo, run `virtualenv .` to create the virtualenv
4. On Unix-based systems, run `source bin/activate` to enter the virtualenv. On Windows, run `Scripts\activate`
5. Install the dependencies with pip. They will all be automatically installed if you run `pip flask_pymongo`.
6. In a separate terminal, navigate to the `mongod` executable and run it
7. In the original terminal, set your environment variables. On Unix-based systems, run `export FLASK_APP=app.py`, while on Windows run `set FLASK_APP=app.py`. If you would like debugging to be enable, run `export/set FLASK_DEBUG=1`, depending on your platform.
8. Run the application with the command `flask run --host=0.0.0.0`. Navigate to the web app at http://localhost:5000.
