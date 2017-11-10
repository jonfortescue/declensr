 # -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
import sys
import re

# without this, encoding issues cause errors
reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
mongo = PyMongo(app) # establish MongoDB connection

# index/home page
@app.route("/")
def home():
    return render_template("index.html", title="Which language are you studying?")

@app.route("/lang/<lang>", methods=['GET', 'POST'])
def lang(lang):
    if request.method == 'GET':
        if mongo.db[lang].count() == 0:
            return render_template("create.html", title=lang)
        else:
            return "This language has definitions but this program isn't done."
    elif request.method == 'POST':
        data = request.form['langDef'].split('\n')
        display = ""
        prevIndent = 0
        breadcrumbs = list()
        bcop = list()
        for line in data:
            if line.strip() == "":
                continue
            pair = re.split(r':\s*', line)
            indent = pair[0].count('  ')
            key = pair[0].strip()
            if len(pair) > 1:
                value = pair[1].strip()

            if len(breadcrumbs) == 0:
                breadcrumbs.append(key)
            elif indent == prevIndent:
                breadcrumbs.pop()
                breadcrumbs.append(key)
            elif indent > prevIndent:
                breadcrumbs.append(key)
            elif indent < prevIndent:
                assert (prevIndent - indent + 1) <= len(breadcrumbs)
                for i in range(prevIndent - indent + 1):
                    breadcrumbs.pop()
                breadcrumbs.append(key)

            bcop.append(' -> '.join(breadcrumbs))

            if indent == 0:
                if key == "Language":
                    if value != lang:
                        return "This grammar (%s) is not for the selected language (%s)." % (value, lang)
                elif key == "Display":
                    display = value
            prevIndent = indent
        return render_template("creation-report.html", title=display, bcop='\n'.join(bcop))
    else:
        return "HTTP 405 Method Not Allowed"
