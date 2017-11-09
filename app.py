from flask import *
from flask_pymongo import PyMongo
import sys

# without this, encoding issues cause errors
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
mongo = PyMongo(app) # establish MongoDB connection

# index/home page
@app.route("/")
def home():
    return render_template(title="Hello darkness my old friend")
